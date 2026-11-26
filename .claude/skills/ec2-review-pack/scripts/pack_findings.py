"""Audit findings and the task that owns each one.

Review reports list findings as `- [<id>] ...` under `## Critical`,
`## Important` and `## Minor`. Legacy RUNs use one content round. Parallel RUNs retain
source-backed findings across candidate revisions and charge accepted corrections.
"""
from __future__ import annotations

from collections import Counter
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


def report_items(report_md: Path):
    """Yield the severity, target and complete text of each blocking Markdown entry."""
    severity = None
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
            for target in item[1].split(','):
                if target.strip():
                    yield severity, target.strip(), line[item.end():].strip()


def blocking_findings(report_md: Path) -> list[tuple[str, str]]:
    # Legacy rounds only route the reported target to its author.
    return [(severity, target) for severity, target, _ in report_items(report_md)]


def check_report_items(report, unresolved):
    declared = {(r.get('severity'), r.get('target'), r.get('rule'), r.get('defect'))
                for r in unresolved if isinstance(r, dict)}
    for severity, target, text in report_items(report):
        match = re.fullmatch(r'\[([^]\n]+)\]\s+(.+)', text)
        identity = (severity, target, match[1], match[2]) if match else None
        if identity not in declared:
            raise f.FlowError('each blocking report entry needs its own matching [target] [rule] defect')
        declared.remove(identity)


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
LABEL_ONLY_JOIN = 2  # join_contract from which label-only mismatches are recorded, not routed
# The child coordinator judges the accepted explanation fragments. Its findings
# can only be corrected by explain-author; the blind solutions stay independent.
COORDINATOR = 'child-coordinator'
COORDINATOR_OWNER = 'explain-author'  # RUNs without problem_contract
LEDGER_REVIEWS = (*REVIEW_ROLES, COORDINATOR)
_PROBLEM_TARGET = re.compile(r'p([1-9]\d*)(?::.+)?')


def coordinator_owner(state: dict, target: str) -> str:
    """The author who corrects a coordinator finding: that problem's explain-author-pN."""
    if not state.get('problem_contract'):
        return COORDINATOR_OWNER
    ids = state['selected_ids']
    if target in ids:
        return f'explain-author-p{ids.index(target) + 1}'
    match = _PROBLEM_TARGET.fullmatch(target) if isinstance(target, str) else None
    if match and int(match[1]) <= len(ids):
        return f'explain-author-p{match[1]}'
    raise f.FlowError('coordinator finding target is not a selected problem')


def finding_key(kind, item):
    fields = [kind, *(item.get(key) for key in ('rule', 'target', 'defect'))]
    if not all(isinstance(value, str) and value.strip() for value in fields):
        raise f.FlowError('finding needs review kind, rule, stable target and specific defect')
    return hashlib.sha256(json.dumps(fields, ensure_ascii=False).encode()).hexdigest()


def _judgment(state, review_id):
    return f._record(state, review_id if review_id != CONFLICT else 'content-review')


def _current_judgment(state, tid):
    if tid == CONFLICT:
        return all(f._done(state, role) for role in NOTE_REVIEWS) and review_pair(
            state, state['tasks']['content-review'].get('candidate_digest'))
    row = _judgment(state, tid)
    return (row.get('status') in ('done', 'needs_fix') and row.get('candidate_digest')
            and all(f._done(state, dep) and f._record(state, dep)['attempt'] == ver
                    for dep, ver in row['input_version'].items()))


def review_pair(state, digest):
    return all(_current_judgment(state, tid) and state['tasks'][tid]['candidate_digest'] == digest
               for tid in NOTE_REVIEWS)


def judgment_attempt(state, tid):
    if tid == CONFLICT:
        return '+'.join(state['tasks'][role]['attempt'] for role in NOTE_REVIEWS)
    return _judgment(state, tid)['attempt']


def repair_record(state, finding):
    """The accepted producer for this request, even after a later serial correction."""
    owner = state['tasks'][finding['owner_task']]
    rid = finding.get('pending_request')
    if rid:
        for record in (owner, *reversed(owner.get('history', []))):
            if record.get('status') == 'done' and record.get('repair_bindings', {}).get(finding['id']) == rid:
                return record
    return None


def repair_candidate(state, role, owner, attempt):
    """Find the accepted rendered candidate containing this exact producer correction."""
    if role == COORDINATOR:
        return None  # The coordinator inspects the corrected fragments themselves.
    tid, name = ('build-answers', 'pdf') if role == 'pdf-qa' else ('assemble-note', 'note')
    action = state['actions'].get(tid, {})
    for row in (*action.get('history', []), action):
        if row.get('input_version', {}).get(owner) != attempt:
            continue
        path = row.get('artifacts', {}).get(name)
        verified = {i['path']: i for i in row.get('verified_files', [])}
        if path in verified:
            return verified[path]
    return None


def same_repair_candidate(state, source, row, attempt):
    if source['input_version'].get(row['owner_task']) != attempt:
        return False
    first = repair_candidate(state, row['review_id'], row['owner_task'], attempt)
    return not first or first['sha256'] == source['candidate_digest']


def review_file(source, path):
    private = Path(path)
    adopted = source.get('artifacts', {}).get(private.relative_to(source['attempt_dir']).as_posix())
    verified = {r['path']: r for r in source['receipt']['verified_files']}
    return verified.get(adopted, verified[str(private)])


def review_reports(state, review_id):
    reports = []
    for tid in (NOTE_REVIEWS if review_id == CONFLICT else (review_id,)):
        source = _judgment(state, tid)
        receipt = source.get('receipt')
        if receipt:
            reports.append(review_file(source, receipt['report']))
        else:
            path = source['artifacts']['check-findings.json']
            reports.append(next(i for i in source['verified_files'] if i['path'] == path))
    return reports


def record_findings(state: dict, *, review_id: str, input_digest: str, findings: list[dict]) -> dict:
    """Ingest evidence from a validated, current review receipt or machine comparison."""
    from pack_graph import role_of
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
        if review_id == COORDINATOR and owner == COORDINATOR_OWNER:
            owner = coordinator_owner(state, item['target'])  # the problem's own author
        external = owner == 'assemble-note' and review_id in (MACHINE_REVIEW, 'precheck')
        if (key in seen or item.get('severity') not in SEVERITIES
                or not isinstance(item.get('evidence'), str) or not item['evidence'].strip()
                or (owner not in state['tasks'] and not external) or owner not in source['input_version']
                or owner in REVIEW_ROLES or role_of(owner) == 'explain-blind'):
            raise f.FlowError('invalid or duplicate finding, owner or evidence')
        if review_id == COORDINATOR and owner != coordinator_owner(state, item['target']):
            raise f.FlowError('child-coordinator findings are owned by explain-author')
        seen.add(key)
        row = ledger.setdefault(key, dict(id=key, review_id=review_id, status='open',
                                          unsuccessful_attempts=[], repairs=[]))
        if row.get('owner_task', owner) != owner:
            raise f.FlowError('finding correction owner changed')
        row.update({name: item[name] for name in ('rule', 'target', 'defect', 'severity', 'evidence')}, owner_task=owner)
        row.update(input_digest=input_digest, review_attempt=judgment_attempt(state, review_id), owner_attempt=source['input_version'][owner],
                   review_reports=review_reports(state, review_id))
        if external:
            row.update(status='withheld', reason='No writable per-RUN producer for this assembly/template diagnostic')
        elif row['status'] == 'resolved':
            row['status'] = 'withheld' if len(row['unsuccessful_attempts']) >= 2 else 'open'
    return state


def fixable_findings(state: dict, *, candidate_digest: str) -> list[dict]:
    result = []
    for row in state.get('findings', {}).values():
        tid = row['review_id']
        if (row['status'] != 'open' or row.get('pending_request') or row['input_digest'] != candidate_digest
                or not _current_judgment(state, tid)):
            continue
        same_attempt = judgment_attempt(state, tid) == row['review_attempt']
        if not same_attempt and tid == CONFLICT:
            # The earlier trial recorded the content UUID plus both immutable
            # adopted report references. The content UUID alone cannot authorize it.
            same_attempt = (row['review_attempt'] == state['tasks']['content-review']['attempt']
                            and row.get('review_reports') == review_reports(state, tid))
        if not same_attempt:
            continue
        if tid in (*NOTE_REVIEWS, CONFLICT) and not review_pair(state, candidate_digest):
            continue
        result.append(row)
    return result


def record_fix_result(state: dict, *, finding_id: str, request_id: str, attempt: str,
                      outcome: Literal['resolved', 'unresolved', 'not_reviewed'],
                      current_outcome: Literal['resolved', 'unresolved'] | None = None) -> dict:
    """Bind adjudication to the accepted repair brief and the re-reviewer's frozen inputs."""
    row = state['findings'][finding_id]
    owner = state['tasks'][row['owner_task']]
    source = _judgment(state, row['review_id'])
    correction = repair_record(state, row)
    same_version = same_repair_candidate(state, source, row, attempt)
    if current_outcome is None and same_version:
        current_outcome = outcome
    historical_unknown = not same_version and row['review_id'] not in REVIEW_ROLES and outcome == 'not_reviewed'
    if (row.get('pending_request') != request_id or row['status'] != 'open'
            or not _current_judgment(state, row['review_id']) or owner['status'] != 'done'
            or not correction or correction['attempt'] != attempt
            or source['input_version'].get(owner['id']) != owner['attempt']
            or current_outcome not in ('resolved', 'unresolved') or (same_version and current_outcome != outcome)
            or (outcome not in ('resolved', 'unresolved') and not historical_unknown)):
        raise f.FlowError('unverified repair attempt or adjudication')
    if outcome == 'unresolved' and attempt not in row['unsuccessful_attempts']:
        row['unsuccessful_attempts'].append(attempt)
    if current_outcome == 'resolved':
        row['status'] = 'resolved'
    else:
        row['status'] = 'withheld' if len(row['unsuccessful_attempts']) >= 2 else 'open'
    row['repairs'].append(dict(request_id=request_id, attempt=attempt, outcome=outcome, current_outcome=current_outcome,
                               review_attempt=judgment_attempt(state, row['review_id']), reviewed_owner_attempt=owner['attempt'],
                               input_digest=source['candidate_digest'],
                               review_reports=review_reports(state, row['review_id'])))
    del row['pending_request']
    return state


def historical_worker_evidence(source, row, decision, current_outcome):
    """Bind both judgments to what this reviewer received and actually submitted."""
    brief = f._read(source['brief'])
    frozen = next((r for r in brief['recheck_findings'] if r['id'] == row['id']), {})
    receipt = source['receipt']
    inputs = {r['path']: r for r in receipt['inputs']}
    original = decision.get('repair_input')
    candidate = frozen.get('repair_candidate')
    artifacts = frozen.get('repair_outputs', {})
    expected_inputs = [candidate] if candidate else artifacts.values()
    if (decision.get('current_outcome') != current_outcome or not isinstance(decision.get('current_evidence'), str)
            or not decision['current_evidence'].strip() or frozen.get('repair_attempt') != decision.get('attempt')
            or not isinstance(original, str) or original not in inputs or original not in expected_inputs):
        raise f.FlowError('superseded repair needs its frozen input and a separate current candidate judgment')
    evidence = dict(repair_input=inputs[original], current_evidence=decision['current_evidence'])
    if source['id'] in ('browser-qa', 'standalone-svg-qa', 'pdf-qa'):
        from pack_receipts import _png
        screens = {r['path']: r for r in receipt['outputs'] if Path(r['path']).suffix.lower() == '.png'}
        old = decision.get('repair_screen')
        current = decision.get('current_screen')
        if old == current or old not in screens or current not in screens:
            raise f.FlowError('separate original and current screenshot evidence required')
        for field, path in [('repair_screen', old), ('current_screen', current)]:
            _png(path)
            evidence[field] = review_file(source, path)
    return evidence


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
        fresh_comparison = tid == CONFLICT and row['review_attempt'] != judgment_attempt(state, tid)
        corrected = owner.get('attempt') != row['owner_attempt'] and owner.get('repair_bindings')
        if (not (fresh_comparison or corrected) or source['input_version'][owner['id']] != owner['attempt']
                or not isinstance(result.get('evidence'), str) or not result['evidence'].strip()):
            raise f.FlowError('incidental resolution needs a current accepted correction and source evidence')
        row.update(status='resolved', reconciliation=dict(result, review_attempt=judgment_attempt(state, tid),
                   input_digest=digest, owner_attempt=owner['attempt']))
    for row in existing:
        key = row['id']
        if key in pending:
            result = decisions[key]
            current_outcome = 'unresolved' if key in ids else 'resolved'
            outcome = result.get('outcome')
            evidence = dict(evidence=result['evidence'])
            if not same_repair_candidate(state, source, row, result.get('attempt')):
                if tid in REVIEW_ROLES:
                    evidence.update(historical_worker_evidence(source, row, result, current_outcome))
                else:
                    # This check or pair ran only on the later candidate. There
                    # is no accepted original decision from which to charge a failure.
                    outcome = 'not_reviewed'
                    evidence.update(evidence='Original candidate was superseded before this check',
                                    current_evidence=result['evidence'])
            elif outcome != current_outcome or result.get('current_outcome', outcome) != current_outcome:
                raise f.FlowError('repair outcome conflicts with review findings')
            record_fix_result(state, finding_id=key, request_id=result.get('request_id'),
                              attempt=result.get('attempt'), outcome=outcome, current_outcome=current_outcome)
            row['repairs'][-1].update(evidence)
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
        # One explain-author correction answers the whole coordinator judgment.
        if eligible[key]['review_id'] == COORDINATOR:
            required = {k for k, r in eligible.items() if r['review_id'] == COORDINATOR}
            if not required <= {i.get('finding_id') for i in request['items'] if isinstance(i, dict)}:
                raise f.FlowError('batch every current child-coordinator finding')
    for owner in owners:
        task = state['tasks'][owner]
        if task['status'] != 'done':
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
    repairs = [r for r in state.get('findings', {}).values() if r['review_id'] == task['id'] and r.get('pending_request')]
    authors = [t for r in repairs for t in (state['tasks'][r['owner_task']], repair_record(state, r)) if t]
    if any(t.get('agent_id') == reviewer for t in authors):
        raise f.FlowError('the correction author cannot approve their own repair')
    if task['id'] == COORDINATOR:
        from pack_graph import explain_ids
        authors = [state['tasks'].get(tid, {}) for tid in explain_ids(state, 'explain-author')]
        if reviewer in {a for t in authors for a in (t.get('agent_id'), *(r.get('agent_id') for r in t.get('history', [])))}:
            raise f.FlowError('the child coordinator cannot review explanations it authored')
    if task['id'] in NOTE_REVIEWS:
        other = next(tid for tid in NOTE_REVIEWS if tid != task['id'])
        forbidden = [state['tasks'][other], *(t for t in state['tasks'].values() if t['role'] == 'author')]
        if any(t.get('agent_id') == reviewer for t in forbidden):
            raise f.FlowError('distinct independent note reviewers and authors required')


def join_reviews(state):
    """Publish a combined audit once both note reviews are adopted (contract 1 also needs agreeing labels)."""
    tasks = state['tasks']
    style, content = (tasks[tid] for tid in NOTE_REVIEWS)
    digest = content.get('candidate_digest')
    if not digest or not review_pair(state, digest) or any(t['status'] != 'done' for t in (style, content)):
        return
    if style['agent_id'] == content['agent_id'] or style['input_version'] != content['input_version']:
        raise f.FlowError('independent reviews must approve the same candidate version')
    label_only = state.get('join_contract', 1) >= LABEL_ONLY_JOIN
    if label_only and any(row['review_id'] == CONFLICT and row['status'] != 'resolved'
                          for row in state.get('findings', {}).values()):
        raise f.FlowError('label-only join cannot carry review-join findings')
    audits = [f._read(t['artifacts']['learning-style-audit-note.json']) for t in (style, content)]
    merged = audits[0]
    conflicts = []
    disagreements = []
    for target, item in merged['items'].items():
        other = audits[1]['items'][target]
        item['reviewer'] = f"{style['agent_id']} + {content['agent_id']}"
        for rule, decision in item['rules'].items():
            second = other['rules'][rule]
            evidence = (f"{style['agent_id']} ({decision['disposition']}): {decision['evidence']}\n"
                        f"{content['agent_id']} ({second['disposition']}): {second['evidence']}")
            if decision['disposition'] != second['disposition'] and label_only:
                decision['disagreement'] = True
                disagreements.append(dict(candidate_digest=digest, target=target, rule=rule,
                    style=dict(reviewer=style['agent_id'], disposition=decision['disposition'], evidence=decision['evidence']),
                    content=dict(reviewer=content['agent_id'], disposition=second['disposition'], evidence=second['evidence'])))
            elif decision['disposition'] != second['disposition']:
                conflicts.append(dict(rule=rule, target=target, defect='conflicting rule dispositions',
                    severity='Important', owner_task=owner_of(target, dict(sections=state['scope_sections'])),
                    evidence=evidence))
            decision['evidence'] = evidence
    if label_only:
        existing = state.get('applicability_disagreements', [])
        state['applicability_disagreements'] = [d for d in existing if d['candidate_digest'] != digest] + disagreements
    else:
        _adjudicate_conflicts(state, merged, conflicts)
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



def applicability_summary(state):
    """Count label-only note-review disagreements on the joined candidate, per rule."""
    history = state.get('applicability_disagreements', [])
    digest = state.get('joined_review', {}).get('candidate_digest')
    items = [d for d in history if digest and d['candidate_digest'] == digest]
    audit = state.get('active_audit')
    cells = sum(len(i['rules']) for i in f._read(Path(audit))['items'].values()) if audit else None
    return dict(current=len(items), history=len(history), by_rule=dict(Counter(d['rule'] for d in items)),
                cells=cells, items=items)

def _adjudicate_conflicts(state, merged, conflicts):
    """Contract 1: route label mismatches between the note reviews as review-join findings."""
    conflict_ids = {finding_key(CONFLICT, row) for row in conflicts}
    rechecks = []
    for row in state.get('findings', {}).values():
        if row['review_id'] == CONFLICT and row.get('pending_request'):
            correction = repair_record(state, row) or {}
            item = merged['items'][row['target']]['rules'][row['rule']]
            rechecks.append(dict(finding_id=row['id'], request_id=row['pending_request'], attempt=correction.get('attempt'),
                                 outcome='unresolved' if row['id'] in conflict_ids else 'resolved', evidence=item['evidence']))
    compared = []
    for row in state.get('findings', {}).values():
        if (row['review_id'] == CONFLICT and row['status'] == 'open'
                and not row.get('pending_request') and row['id'] not in conflict_ids):
            compared.append(dict(finding_id=row['id'], prior_review_attempt=row['review_attempt'],
                                 evidence=merged['items'][row['target']]['rules'][row['rule']]['evidence']))
    adjudicate(state, CONFLICT, conflicts, rechecks, compared)


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
            attempt=(repair_record(state, row) or {}).get('attempt'),
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
