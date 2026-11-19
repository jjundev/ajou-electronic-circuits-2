"""Audit findings and the task that owns each one.

Review reports list findings as `- [<id>] ...` under `## Critical`,
`## Important` and `## Minor`. Legacy RUNs use one content round. Parallel RUNs retain
source-backed findings across candidate revisions and charge accepted corrections.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Literal
from uuid import uuid4

import pack_flow as f

SEVERITIES = ('Critical', 'Important', 'Minor')
_HEADING = re.compile(r'^(#{2,4})\s+(.+?)\s*$')
_ITEM = re.compile(r'^\s*[-*]\s+\[([^\]]+)\]')


def blocking_findings(report_md: Path) -> list[tuple[str, str]]:
    """(severity, id) for each `- [id]` item under the three severity sections, in order."""
    found, severity = [], None
    for line in Path(report_md).read_text(encoding='utf-8').splitlines():
        heading = _HEADING.match(line)
        if heading:
            # '## Important (2)' and '### Critical' open a section; another '##' heading closes it,
            # while a deeper non-severity subheading stays inside the current section.
            word = re.match(r'[A-Za-z]+', heading[2])
            name = word[0].capitalize() if word else ''
            if name in SEVERITIES: severity = name
            elif len(heading[1]) == 2: severity = None
            continue
        item = _ITEM.match(line)
        if severity and item:
            found += [(severity, x.strip()) for x in item[1].split(',') if x.strip()]
    return found


def owner_of(item_id: str, manifest: dict) -> str:
    """Topic or section ID → author-<section>; problem ID → selection; else scope-final."""
    if item_id in {p.get('id') for p in manifest.get('problems', []) if isinstance(p, dict)}:
        return 'selection'
    for section in manifest.get('sections', []):
        if not isinstance(section, dict): continue
        topics = {t.get('id') for t in section.get('topics', []) if isinstance(t, dict)}
        if item_id == section.get('id') or item_id in topics:
            return 'author-' + section['id']
    return 'scope-final'


NOTE_REVIEWS = ('style-audit', 'content-review')
REVIEW_ROLES = (*NOTE_REVIEWS, 'browser-qa', 'standalone-svg-qa', 'pdf-qa')
MACHINE_REVIEW = 'structural-precheck'
CONFLICT = 'review-join'


def finding_key(kind, item):
    fields = [kind, *(item.get(key) for key in ('rule', 'target', 'defect'))]
    if not all(isinstance(value, str) and value.strip() for value in fields):
        raise f.FlowError('finding needs review kind, rule, stable target and specific defect')
    return hashlib.sha256(json.dumps(fields, ensure_ascii=False).encode()).hexdigest()


def _judgment(state, review_id):
    return f._record(state, review_id if review_id != CONFLICT else 'content-review')


def _current_judgment(state, tid):
    row = _judgment(state, tid)
    return (row.get('status') in ('done', 'needs_fix') and row.get('candidate_digest')
            and all(f._done(state, dep) and f._record(state, dep)['attempt'] == ver
                    for dep, ver in row['input_version'].items()))


def review_pair(state, digest):
    return all(_current_judgment(state, tid) and state['tasks'][tid]['candidate_digest'] == digest
               for tid in NOTE_REVIEWS)


def review_reports(state, review_id):
    reports = []
    for tid in (NOTE_REVIEWS if review_id == CONFLICT else (review_id,)):
        source = _judgment(state, tid)
        receipt = source.get('receipt')
        if receipt:
            private = Path(receipt['report'])
            adopted = source.get('artifacts', {}).get(private.relative_to(source['attempt_dir']).as_posix())
            verified = {i['path']: i for i in receipt['verified_files']}
            reports.append(verified.get(adopted, verified[str(private)]))
        else:
            path = source['artifacts']['check-findings.json']
            reports.append(next(i for i in source['verified_files'] if i['path'] == path))
    return reports


def record_findings(state: dict, *, review_id: str, input_digest: str, findings: list[dict]) -> dict:
    """Ingest evidence from a validated, current review receipt or machine comparison."""
    source = _judgment(state, review_id)
    if not _current_judgment(state, review_id) or source['candidate_digest'] != input_digest:
        raise f.FlowError('finding review no longer current')
    ledger = state.setdefault('findings', {})
    seen = set()
    for item in findings:
        if not isinstance(item, dict):
            raise f.FlowError('structured review finding required')
        key = finding_key(review_id, item)
        owner = item.get('owner_task')
        if (key in seen or item.get('severity') not in SEVERITIES
                or not isinstance(item.get('evidence'), str) or not item['evidence'].strip()
                or owner not in state['tasks'] or owner not in source['input_version']
                or owner in (*REVIEW_ROLES, 'explain-blind')):
            raise f.FlowError('invalid or duplicate finding, owner or evidence')
        seen.add(key)
        row = ledger.setdefault(key, dict(id=key, review_id=review_id, status='open',
                                          unsuccessful_attempts=[], repairs=[]))
        if row.get('owner_task', owner) != owner:
            raise f.FlowError('finding correction owner changed')
        row.update({name: item[name] for name in ('rule', 'target', 'defect', 'severity', 'owner_task', 'evidence')})
        row.update(input_digest=input_digest, review_attempt=source['attempt'], owner_attempt=source['input_version'][owner],
                   review_reports=review_reports(state, review_id))
        if row['status'] == 'resolved':
            row['status'] = 'open'
    return state


def fixable_findings(state: dict, *, candidate_digest: str) -> list[dict]:
    result = []
    for row in state.get('findings', {}).values():
        tid = row['review_id']
        if (row['status'] != 'open' or row.get('pending_request') or row['input_digest'] != candidate_digest
                or not _current_judgment(state, tid) or _judgment(state, tid)['attempt'] != row['review_attempt']):
            continue
        if tid in (*NOTE_REVIEWS, CONFLICT) and not review_pair(state, candidate_digest):
            continue
        result.append(row)
    return result


def record_fix_result(state: dict, *, finding_id: str, request_id: str, attempt: str,
                      outcome: Literal['resolved', 'unresolved']) -> dict:
    """Bind adjudication to the accepted repair brief and the re-reviewer's frozen inputs."""
    row = state['findings'][finding_id]
    owner = state['tasks'][row['owner_task']]
    source = _judgment(state, row['review_id'])
    if (row.get('pending_request') != request_id or row['status'] != 'open'
            or not _current_judgment(state, row['review_id']) or owner['status'] != 'done'
            or owner['attempt'] != attempt or source['input_version'].get(owner['id']) != attempt
            or owner.get('repair_bindings', {}).get(finding_id) != request_id
            or outcome not in ('resolved', 'unresolved')):
        raise f.FlowError('unverified repair attempt or adjudication')
    if outcome == 'resolved':
        row['status'] = 'resolved'
    elif attempt not in row['unsuccessful_attempts']:
        row['unsuccessful_attempts'].append(attempt)
        if len(row['unsuccessful_attempts']) >= 2:
            row['status'] = 'withheld'
    row['repairs'].append(dict(request_id=request_id, attempt=attempt, outcome=outcome,
                               review_attempt=source['attempt'], input_digest=source['candidate_digest'],
                               review_reports=review_reports(state, row['review_id'])))
    del row['pending_request']
    return state


def adjudicate(state, tid, findings, results, reconciliations=()):
    source = _judgment(state, tid)
    digest = source['candidate_digest']
    if not isinstance(findings, list) or any(not isinstance(item, dict) for item in findings):
        raise f.FlowError('structured findings list required')
    ids = {finding_key(tid, item) for item in findings}
    if not isinstance(results, list):
        raise f.FlowError('fix_results must be a list')
    decisions = {}
    for result in results:
        if (not isinstance(result, dict) or not isinstance(result.get('finding_id'), str)
                or result['finding_id'] in decisions or not isinstance(result.get('evidence'), str)
                or not result['evidence'].strip()):
            raise f.FlowError('one explicit source-backed fix result required per pending finding')
        decisions[result['finding_id']] = result
    existing = [r for r in state.get('findings', {}).values() if r['review_id'] == tid and r['status'] != 'resolved']
    pending = {r['id'] for r in existing if r.get('pending_request')}
    if decisions.keys() != pending:
        raise f.FlowError('missing or unexpected repair decisions for corrected candidate')
    incidental = {r['id']: r for r in existing
                  if r['id'] not in ids | pending and r['status'] == 'open'}
    if not isinstance(reconciliations, (list, tuple)) or len(reconciliations) != len(incidental):
        raise f.FlowError('existing finding requires explicit current source comparison')
    for result in reconciliations:
        row = incidental.pop(result.get('finding_id'), None) if isinstance(result, dict) else None
        if not row or result.get('prior_review_attempt') != row['review_attempt']:
            raise f.FlowError('stale or unknown prior finding in reconciliation')
        owner = state['tasks'][row['owner_task']]
        if (owner.get('attempt') == row['owner_attempt'] or not owner.get('repair_bindings')
                or source['input_version'][owner['id']] != owner['attempt']
                or not isinstance(result.get('evidence'), str) or not result['evidence'].strip()):
            raise f.FlowError('incidental resolution needs a current accepted correction and source evidence')
        row.update(status='resolved', reconciliation=dict(result, review_attempt=source['attempt'],
                   input_digest=digest, owner_attempt=owner['attempt']))
    for row in existing:
        key = row['id']
        if key in pending:
            result = decisions[key]
            outcome = 'unresolved' if key in ids else 'resolved'
            if result.get('outcome') != outcome:
                raise f.FlowError('repair outcome conflicts with review findings')
            record_fix_result(state, finding_id=key, request_id=result.get('request_id'),
                              attempt=result.get('attempt'), outcome=outcome)
            row['repairs'][-1]['evidence'] = result['evidence']
    record_findings(state, review_id=tid, input_digest=digest, findings=findings)


def apply_request(state, request):
    """Schedule one correction per owner, atomically invalidating its downstream proof."""
    rid = request.get('id')
    if not isinstance(rid, str) or not rid.strip() or set(request) != {'id', 'items'}:
        raise f.FlowError('parallel fix requires id and finding items; waivers are unsupported')
    prior = state.setdefault('fix_requests', {})
    if rid in prior:
        if prior[rid] != request:
            raise f.FlowError('fix request ID reused with different content')
        return state
    f._current(state)
    if state['status'] in ('complete', 'blocked', 'withheld', 'recovery_required') or state['stale_inputs']:
        raise f.FlowError('RUN unavailable for correction')
    if not isinstance(request['items'], list) or not request['items']:
        raise f.FlowError('fix items required')
    keys = set()
    owners = set()
    for item in request['items']:
        if not isinstance(item, dict) or set(item) != {'finding_id', 'input_digest', 'review_attempt'}:
            raise f.FlowError('fix needs finding ID, candidate digest and review attempt')
        eligible = {r['id']: r for r in fixable_findings(state, candidate_digest=item['input_digest'])}
        key = item['finding_id']
        if key not in eligible or key in keys or eligible[key]['review_attempt'] != item['review_attempt']:
            raise f.FlowError('unavailable or superseded finding')
        keys.add(key)
        owners.add(eligible[key]['owner_task'])
        # Both independent reviews on this candidate must reach their authors together.
        if eligible[key]['review_id'] in (*NOTE_REVIEWS, CONFLICT):
            required = {k for k, r in eligible.items() if r['review_id'] in (*NOTE_REVIEWS, CONFLICT)}
            if not required <= {i.get('finding_id') for i in request['items'] if isinstance(i, dict)}:
                raise f.FlowError('batch every current note review finding')
    for owner in owners:
        task = state['tasks'][owner]
        if task['status'] != 'done' or any(r.get('pending_request') and r['owner_task'] == owner
                                            for r in state['findings'].values()):
            raise f.FlowError('correction owner unavailable')
        task.setdefault('history', []).append({k:v for k,v in task.items() if k != 'history'})
        task.update(status='stale', receipt=None, attempt=None, agent_id=None)
        task.pop('repair_bindings', None)
    for key in keys:
        state['findings'][key]['pending_request'] = rid
    prior[rid] = request
    return f.refresh_tasks(f._current(state))


def check_reviewer(state, task):
    reviewer = task.get('agent_id')
    if not isinstance(reviewer, str) or not reviewer.strip():
        raise f.FlowError('bound reviewer identity required')
    repair_owners = {r['owner_task'] for r in state.get('findings', {}).values()
                     if r['review_id'] == task['id'] and r.get('pending_request')}
    if any(state['tasks'][owner].get('agent_id') == reviewer for owner in repair_owners):
        raise f.FlowError('the correction author cannot approve their own repair')
    if task['id'] in NOTE_REVIEWS:
        other = next(tid for tid in NOTE_REVIEWS if tid != task['id'])
        forbidden = [state['tasks'][other], *(t for t in state['tasks'].values() if t['role'] == 'author')]
        if any(t.get('agent_id') == reviewer for t in forbidden):
            raise f.FlowError('distinct independent note reviewers and authors required')


def join_reviews(state):
    """Publish a new combined audit only after both adopted, agreeing judgments."""
    tasks = state['tasks']
    style, content = (tasks[tid] for tid in NOTE_REVIEWS)
    digest = content.get('candidate_digest')
    if not digest or not review_pair(state, digest) or any(t['status'] != 'done' for t in (style, content)):
        return
    if style['agent_id'] == content['agent_id'] or style['input_version'] != content['input_version']:
        raise f.FlowError('independent reviews must approve the same candidate version')
    audits = [f._read(t['artifacts']['learning-style-audit-note.json']) for t in (style, content)]
    merged = audits[0]
    conflicts = []
    for target, item in merged['items'].items():
        other = audits[1]['items'][target]
        item['reviewer'] = f"{style['agent_id']} + {content['agent_id']}"
        for rule, decision in item['rules'].items():
            second = other['rules'][rule]
            evidence = (f"{style['agent_id']} ({decision['disposition']}): {decision['evidence']}\n"
                        f"{content['agent_id']} ({second['disposition']}): {second['evidence']}")
            if decision['disposition'] != second['disposition']:
                conflicts.append(dict(rule=rule, target=target, defect='conflicting rule dispositions',
                    severity='Important', owner_task=owner_of(target, dict(sections=state['scope_sections'])),
                    evidence=evidence))
            decision['evidence'] = evidence
    conflict_ids = {finding_key(CONFLICT, row) for row in conflicts}
    rechecks = []
    for row in state.get('findings', {}).values():
        if row['review_id'] == CONFLICT and row.get('pending_request'):
            owner = tasks[row['owner_task']]
            item = merged['items'][row['target']]['rules'][row['rule']]
            rechecks.append(dict(finding_id=row['id'], request_id=row['pending_request'], attempt=owner['attempt'],
                                 outcome='unresolved' if row['id'] in conflict_ids else 'resolved', evidence=item['evidence']))
    compared = []
    for row in state.get('findings', {}).values():
        if (row['review_id'] == CONFLICT and row['status'] == 'open'
                and not row.get('pending_request') and row['id'] not in conflict_ids):
            compared.append(dict(finding_id=row['id'], prior_review_attempt=row['review_attempt'],
                                 evidence=merged['items'][row['target']]['rules'][row['rule']]['evidence']))
    adjudicate(state, CONFLICT, conflicts, rechecks, compared)
    if conflicts:
        return
    merged.update(candidate_digest=digest, assemble_attempt=style['input_version']['assemble-note'],
                  review_attempts={t['id']: t['attempt'] for t in (style, content)})
    path = Path(state['run'])/'adopted'/'review-join'/str(uuid4())/'learning-style-audit.json'
    path.parent.mkdir(parents=True, exist_ok=False)
    f._atomic_json(path, merged)
    path.chmod(0o444)
    record = dict(path=str(path), sha256=f._sha(path))
    state['active_audit'] = str(path)
    state['joined_review'] = dict(file=record, candidate_digest=digest,
                                  review_attempts=merged['review_attempts'])
    for task in (style, content):
        task['receipt']['verified_files'].append(record)


def current_audit(state):
    joined = state.get('joined_review', {})
    path = state.get('active_audit')
    if not path or joined.get('file', {}).get('path') != path:
        return False
    return (review_pair(state, joined['candidate_digest'])
            and all(f._done(state, tid) and state['tasks'][tid]['attempt'] == joined['review_attempts'][tid]
                    for tid in NOTE_REVIEWS))


def blocked_reason(state, tid):
    if tid in ('precheck', 'publish-pack') and not current_audit(state):
        return 'current joined note audit required'
    if tid == 'publish-pack':
        open_ids = [r['id'] for r in state.get('findings', {}).values() if r['status'] != 'resolved']
        if open_ids:
            return 'blocking findings: ' + ', '.join(open_ids)
    return None


def machine_judgment(state, tid, issues):
    """A complete deterministic check can adjudicate each previously requested rule."""
    source = _judgment(state, tid)
    current = {finding_key(tid, item): item for item in issues}
    rechecks = []
    for row in state.get('findings', {}).values():
        if row['review_id'] != tid or not row.get('pending_request'):
            continue
        key = row['id']
        rechecks.append(dict(finding_id=key, request_id=row['pending_request'],
            attempt=source['input_version'].get(row['owner_task']),
            outcome='unresolved' if key in current else 'resolved',
            evidence=current[key]['evidence'] if key in current else
                f"Complete {tid} check passed {row['rule']} for {row['target']}"))
    if issues:
        source.update(status='needs_fix', error_code='structural_findings')
    compared = [dict(finding_id=r['id'], prior_review_attempt=r['review_attempt'],
                     evidence=f"Complete {tid} check passed {r['rule']} for {r['target']}")
                for r in state.get('findings', {}).values() if r['review_id'] == tid and r['status'] == 'open'
                and not r.get('pending_request') and r['id'] not in current]
    adjudicate(state, tid, list(current.values()), rechecks, compared)
