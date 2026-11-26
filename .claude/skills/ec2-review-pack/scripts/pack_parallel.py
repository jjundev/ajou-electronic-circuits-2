"""Private attempts and durable handoffs for the explicit review-pack graph."""
from pathlib import Path
from uuid import uuid4
import copy
import hashlib
import json
import tempfile
import shutil
import subprocess
import sys
import time

import pack_flow as f
import pack_findings as findings
from pack_graph import explain_ids, problem_key, problem_keys, role_of, task_specs


def counterpart(task_id: str) -> str:
    """The other half of one problem's independence pair: author <-> blind solver."""
    role = role_of(task_id)
    other = {'explain-author': 'explain-blind', 'explain-blind': 'explain-author'}[role]
    return other if task_id == role else f'{other}-{problem_key(task_id)}'


def sealed_question_paths(state, spec):
    """The sealed files one explanation worker may read: all of them, or one problem's folder."""
    row = f._record(state, 'stage-problem-index')
    if state.get('problem_contract'):
        return list(map(Path, row['problem_questions'][problem_key(spec.id)]))
    return list(map(Path, row['questions']))


def spec_for(state, tid):
    for spec in task_specs(state):
        if spec.id == tid:
            return spec
    raise f.FlowError('task outside current graph: ' + tid)


def ancestors(state, spec):
    found = {}
    def visit(tid):
        if tid not in found:
            rec = f._record(state, tid)
            found[tid] = rec
            for dep in rec['dependencies']:
                visit(dep)
    for dep in spec.dependencies:
        visit(dep)
    return found


def proof(state, spec):
    if state.get('stale_inputs'):
        raise f.StaleInputsError('RUN frozen source changed')
    if state['status'] in ('blocked', 'withheld', 'recovery_required'):
        raise f.FlowError('RUN lacks current source or authorization')
    if reason := findings.blocked_reason(state, spec.id):
        raise f.FlowError(reason)
    version = {}
    for tid, rec in ancestors(state, spec).items():
        if rec.get('status') == 'stale':
            raise f.StaleInputsError('stale predecessor: ' + tid)
        if rec.get('status') != 'done' or not rec.get('attempt'):
            raise f.FlowError('missing current predecessor: ' + tid)
        version[tid] = rec['attempt']
    return version


def file_records(paths):
    return [dict(path=str(f.nfc_path(p)), sha256=f._sha(Path(p))) for p in sorted(set(paths))]


def local_path(root, name):
    import manifest
    from pack_paths import checked_file
    return checked_file(Path(root), name)


def output(state, tid, name):
    row = f._record(state, tid)
    return Path(row['artifacts'][name])


def public(state):
    return Path(state['repo']) / '복습노트' / state['range']


def original_worker_inputs(state, spec):
    if role_of(spec.id) in ('explain-blind', 'explain-author'):
        return file_records(sealed_question_paths(state, spec))
    paths = set(state['hashes'])
    for dep in spec.dependencies:
        row = f._record(state, dep)
        if dep == 'source-prep':
            frozen = row['receipt']['verified_files'] if dep in state['tasks'] else row.get('source_inputs', [])
            paths.update(x['path'] for x in frozen
                         if Path(x['path']).is_relative_to(Path(state['repo'])))
        paths.update(row.get('artifacts', {}).values())
        if adopted := row.get('pack'):
            paths.update(str(local_path(adopted['root'], name)) for name in adopted['files'])
    return file_records(paths)


def worker_inputs(state, spec):
    if not state.get('approval_contract'):
        return original_worker_inputs(state, spec)
    role = f._record(state, spec.id)['role']
    if role_of(spec.id) in ('explain-blind', 'explain-author'):
        return file_records(sealed_question_paths(state, spec))
    snapshot = Path(state['run'])/'learning-style.json'
    paths = set() if role in f.PROFILE_EXEMPT else {snapshot, Path(state['repo'])/f._read(snapshot)['path']}
    if role == 'concept-review':
        source = output(state, 'concept-draft', 'source.json')
        paths.update([source, *map(Path, f._read(source)['inputs'])])
    elif role == 'source-prep':
        paths.update(map(Path, state['hashes']))
    elif role == 'stt':
        source = f._record(state, 'source-prep')
        paths.add(Path(source['artifacts']['source-map.json']))
        sessions = f._read(source['artifacts']['source-map.json'])['sessions']
        session, = [item for item in sessions if item['date'] == spec.id[4:]]
        paths.update(map(Path, [session['stt'], *session['pdfs']]))
        paths.add(Path(source['artifacts']['slides.txt']))
    elif role == 'pdf-qa':
        paths.update((output(state, 'build-answers', 'pdf'), output(state, 'explain-verify', 'overlay')))
    elif role in ('style-audit', 'content-review', 'browser-qa', 'standalone-svg-qa'):
        paths.update((output(state, 'scope-final', 'manifest.json'), output(state, 'assemble-note', 'note')))
        if role == 'standalone-svg-qa':
            converted = state['converted_assets']
            paths.update(Path(r['path']) for r in [converted['md'], *converted['svgs']])
        if role == 'browser-qa':
            if state.get('active_audit'):
                paths.add(Path(state['active_audit']))
            pack = state['actions'].get('build-problems', {}).get('pack', {})
            candidate = state['actions']['precheck']['candidate_root']
            paths.update(local_path(candidate, name) for name in pack.get('files', {}) if name.endswith('.pdf'))
    else:
        for tid in spec.direct_inputs:
            source = f._record(state, tid)
            artifacts = source.get('artifacts', {})
            if tid in state['tasks']:
                names = spec_for(state, tid).outputs
            else:
                names = artifacts
            paths.update(Path(artifacts[key]) for key in names if key in artifacts)
        if role == 'child-coordinator':
            paths.add(output(state, 'selection', 'manifest.json'))
    if role in ('scope-draft', 'author', 'style-audit', 'content-review'):
        source = f._record(state, 'source-prep').get('artifacts', {})
        if source_map := source.get('source-map.json'):
            # These roles verify the lecture's teaching content against its
            # actual sources. They do not need any prior worker's QA screenshots.
            paths.add(Path(source_map))
            for session in f._read(source_map)['sessions']:
                paths.update(map(Path, [session['stt'], *session['pdfs']]))
            paths.add(Path(source['slides.txt']))
    return file_records(paths)


def explanation_digest(state):
    """The child coordinator's candidate: the accepted fragment set of every explanation author."""
    files = {}
    for tid in explain_ids(state, 'explain-author'):
        author = state['tasks'][tid]
        files.update({name: f._sha(Path(author['artifacts'][name])) for name in spec_for(state, tid).outputs})
    return hashlib.sha256(json.dumps(files, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def claim_worker(state, task):
    from pack_receipts import standalone_screenshots
    spec = spec_for(state, task['id'])
    if task['status'] == 'needs_fix' and (task['role'] in findings.REVIEW_ROLES or task.get('candidate_digest')):
        raise f.FlowError('request correction for the accepted findings before re-review')
    version = proof(state, spec)
    if f._owner(state, task) == 'unavailable':
        raise f.FlowError('required inspection unavailable')
    attempt = str(uuid4())
    root = Path(state['run']) / 'attempts' / spec.id / attempt
    root.mkdir(parents=True, exist_ok=False)
    required = [str(local_path(root, name)) for name in spec.outputs]
    role = task['role']
    snapshot = Path(state['run']) / 'learning-style.json'
    review = root / 'report.md'
    if role == 'standalone-svg-qa':
        review = root / 'work/standalone-svg-qa/report.md'
    if role == 'pdf-qa':
        review = root / 'answer-review.md'
    data = dict(workflow='parallel', python=sys.executable, run_id=state['run_id'], role=role, task_id=spec.id,
                range=state['range'], attempt=attempt, run=str(root), targets=task['targets'],
                inputs=worker_inputs(state, spec), allowed_outputs=list(required), required_outputs=required,
                allowed_output_roots=[str(root)], report=str(review), receipt=str(root/'receipt.json'),
                request_paths=task.get('request_paths', []))
    if role in ('explain-author', 'explain-blind'):
        if state.get('problem_contract'):
            data['questions'] = str(output(state, 'stage-problem-index', 'questions.json').parent
                                    / problem_key(spec.id) / 'questions.json')
        else:
            data['questions'] = str(output(state, 'stage-problem-index', 'questions.json'))
        if role == 'explain-blind':
            data['instruction'] = ('Use only the sealed question text and figures. Submit independent.json with items '
                                   'keyed by pN:subpart, method, conclusion and evidence.')
        else:
            repo = Path(state['repo'])
            explain_skill = repo / '.claude/skills/ec2-problem-explain'
            explain_refs = [str(explain_skill / name) for name in ('SKILL.md', 'references/authoring.md')]
            data.update(
                references=explain_refs,
                reference_sections={path: ['전체'] for path in explain_refs},
                profile=str(repo / f._read(snapshot)['path']),
                profile_read='전체 필수',
                snapshot=str(snapshot),
                instruction=('봉인된 문항과 그림, 지정한 스킬과 개인 풀이 명세를 읽고 문항별 간략 해설 HTML 조각을 작성한다. '
                             '회로 위치 표지에서 첫 판단과 식으로 이어가고 필수 중간식과 소문항별 답을 담는다.'),
            )
    else:
        repo = Path(state['repo'])
        refs = repo / '.claude/skills/ec2-review-pack/references'
        sections = {}
        for ref, section in f._REFERENCES.get(role, []):
            sections.setdefault(str(refs / ref), []).append(section)
        if role in ('author', 'style-audit', 'content-review'):
            guide = str(refs / 'execution-guide.md')
            sections[guide] = [*sections.get(guide, []), *f._COMMON_SECTIONS]
        data.update(repo=str(repo), references=list(sections), reference_sections=sections)
        if state.get('approval_contract') and role in f.PROFILE_EXEMPT:
            data['constraints'] = ['Read the referenced review criteria sections. Perform the actual inspection.']
        else:
            data.update(snapshot=str(snapshot), profile=str(repo / f._read(snapshot)['path']), profile_read='전체 필수',
                        constraints=['Read the complete profile and referenced review criteria. Perform the actual inspection.'])
    if role == 'concept-review':
        quiz = root/'quiz'
        quiz.mkdir()
        shutil.copyfile(output(state, 'concept-draft', 'source.json'), quiz/'source.json')
        origin = (task.get('receipt') or {}).get('blind_certificate')
        approved = prior_blind_approval(Path(state['run']), state['run_id'], task.get('attempt'), origin,
                                        f._read(quiz/'source.json')['logical_inputs'])
        retained = retain_quiz_evidence(task, quiz, approved=approved)
        task.pop('blind_origin', None)
        if approved:
            task['blind_origin'] = dict(recipient_attempt=attempt, previous_attempt=task['attempt'], file=origin)
            data['inputs'].append(origin)
        data.update(quiz_run=str(quiz), concept_cli=str(CONCEPT_CLI), retained_quiz=retained,
                    instruction='Follow ec2-concept-check/SKILL.md in quiz_run. Use a separate author and blind solver, '
                                'send only the answer-free packet, then inspect the four browser views. '
                                'Record their identities during blind-record. Submit evidence without publishing.')
    if role == 'scope-draft':
        data['instruction'] = ('Complete the teaching manifest, including sessions, preview rules, style and all section/topic briefs. '
                               'Declare the section IDs that may receive final links in link_sections before early authoring.')
    if role in ('author', 'selection', 'scope-final'):
        data['manifest'] = str(output(state, 'scope-draft', 'manifest.json'))
    if role == 'author':
        data['section_brief'] = next(s for s in state['scope_sections'] if s['id'] == task['targets'][0])
        if 'scope-final' in spec.dependencies:
            data['manifest'] = str(output(state, 'scope-final', 'manifest.json'))
    if role == 'selection':
        data['candidates'] = str(output(state, 'candidate-index', 'candidates.json'))
        data['instruction'] = 'Freeze the selection order, slug, display titles and selection review against the accepted scope.'
    if role == 'scope-final':
        data['selection_manifest'] = str(output(state, 'selection', 'manifest.json'))
        data['link_sections'] = state['link_sections']
        data['instruction'] = ('Use the frozen scope manifest and accepted selection fields. Resolve final links only '
                               'for topics in the declared link sections.')
    if role in ('style-audit', 'content-review', 'browser-qa', 'standalone-svg-qa'):
        data['manifest'] = str(output(state, 'scope-final', 'manifest.json'))
        data['note'] = str(output(state, 'assemble-note', 'note'))
    if role == 'content-review' and state.get('approval_contract'):
        index = state['actions']['candidate-index']['artifacts']
        catalog = [p for name,p in index.items() if name.startswith('catalog/') and name.endswith('.json')]
        if 'catalog/index.json' not in index:
            raise f.FlowError('content review requires the accepted exam catalog')
        summaries = [str(output(state, 'stt-'+date, 'summaries/stt-'+date+'.md')) for date in state['sessions']]
        selection = state['tasks']['selection']['artifacts']
        data.update(summaries=summaries, candidates=index['candidates.json'], exam_catalog=index['catalog/index.json'],
                    selection=selection['selection.json'], selection_review=selection['selection-review.json'])
        evidence = [*summaries, *catalog, data['candidates'], data['selection'], data['selection_review']]
        originals = {}
        for item in f._read(data['candidates']).get('problems', []):
            if item['id'] not in state['selected_ids'] and (item['kind'] != '기출' or item['used']):
                continue
            detail = f._read(index['catalog/' + item['detail_path']]) if item.get('detail_path') else item
            for name, expected in detail['input_hashes'].items():
                path = local_path(Path(state['repo']), name)
                if originals.setdefault(str(path), expected) != expected:
                    raise f.FlowError('inconsistent content review source: ' + name)
        from pack_receipts import records
        sources = [{'path':p,'sha256':h} for p,h in originals.items()]
        records(sources, [Path(state['repo'])])
        data['original_sources'] = list(originals)
        data['inputs'].extend([*file_records(map(Path, evidence)), *sources])
        refs = Path(state['repo'])/'.claude/skills/ec2-review-pack/references'
        data['references'].extend(str(refs/name) for name in ('content-rules.md','problem-selection.md'))
    if role in ('style-audit', 'content-review'):
        data['audit_output'] = required[0]
    if role == 'browser-qa':
        data.update(public_pack=str(public(state)), candidate_pack=state['actions']['precheck']['candidate_root'])
    if role == 'standalone-svg-qa':
        data['converted_assets'] = state['converted_assets']
        data['svg_screenshots'] = standalone_screenshots(root, task['targets'])
        data['allowed_outputs'].extend(data['svg_screenshots'].values())
    if role == 'pdf-qa':
        data.update(pdf=str(output(state, 'build-answers', 'pdf')), overlay=str(output(state, 'explain-verify', 'overlay')))
    if role == 'child-coordinator':
        state['explain_run'] = str(root / 'child')
        data.update(explain_run=state['explain_run'], manifest=str(output(state, 'selection', 'manifest.json')),
                    candidate_pack=state['actions']['stage-problem-index']['pack']['root'],
                    public_pack=str(public(state)), snapshot=str(snapshot),
                    instruction=('Extract against this candidate pack and slug. Use the accepted fragments and independent results. '
                                 'For a new pack, apply the optional circuit lab selection in problem-explain-integration.md '
                                 'before the final explanation build. Complete all child reviews.'))
        if state.get('problem_contract'):
            joined = Path(state['run']) / 'adopted' / 'blind-join' / str(uuid4()) / 'independent.json'
            joined.parent.mkdir(parents=True)
            f._atomic_json(joined, dict(items=blind_items(state)))
            joined.chmod(0o444)
            data['independent'] = str(joined)
            data['inputs'].extend(file_records([joined]))
    repairs = [r for r in state.get('findings', {}).values()
               if r['owner_task'] == task['id'] and r.get('pending_request') and not findings.repair_record(state, r)]
    if repairs:
        data['repair_findings'] = repairs
        data['previous_outputs'] = {name: task['artifacts'][name] for name in spec.outputs}
        data['inputs'] = file_records([*(Path(x['path']) for x in data['inputs']),
                                       *map(Path, data['previous_outputs'].values())])
    if role in findings.LEDGER_REVIEWS:
        if role == findings.COORDINATOR:
            data['candidate_digest'] = explanation_digest(state)
        else:
            candidate = data['pdf'] if role == 'pdf-qa' else data['note']
            data['candidate_digest'] = f._sha(Path(candidate))
        data['recheck_findings'] = []
        inputs = {i['path']: i for i in data['inputs']}
        for row in state.get('findings', {}).values():
            if row['review_id'] != role or row['status'] == 'resolved':
                continue
            item = dict(row, repair_attempt=None)
            correction = findings.repair_record(state, row)
            if correction:
                verified = {i['path']: i for i in correction['receipt']['verified_files']}
                outputs = {name: correction['artifacts'][name] for name in spec_for(state, row['owner_task']).outputs}
                item.update(repair_attempt=correction['attempt'], repair_outputs=outputs)
                inputs.update({path: verified[path] for path in outputs.values()})
                if candidate_file := findings.repair_candidate(state, role, row['owner_task'], correction['attempt']):
                    item['repair_candidate'] = candidate_file['path']
                    inputs[candidate_file['path']] = candidate_file
            data['recheck_findings'].append(item)
        data['inputs'] = list(inputs.values())
    from pack_approvals import make_plan
    if state.get('approval_contract'):
        frozen = {r['path']:r for r in data['inputs']}
        refs = [Path(p) for p in data.get('references', []) if Path(p).is_file()]
        frozen.update({r['path']:r for r in file_records(refs)})
        data['inputs'] = list(frozen.values())
        data['input_paths'] = list(frozen)
        make_plan(state, data)
    else:
        keys = ('note', 'manifest') if 'note' in data else ('overlay',) if role == 'pdf-qa' else ()
        extra = [Path(data[k]) for k in keys]
        data['inputs'] = file_records([*(Path(r['path']) for r in data['inputs']), *extra])
    path = root / 'brief.json'
    f._atomic_json(path, data)
    task.update(attempt=attempt, attempt_dir=str(root), brief=str(path), brief_sha256=f._sha(path),
                input_version=version, status='claimed', agent_id=None, receipt=None)


def scope_manifest(state, data):
    import manifest
    # The selector owns the problem list. All teaching fields must already be
    # usable by an early author, including the source sessions and preview rules.
    errors = manifest.validate(dict(data, problems=[], links=[]), repo=Path(state['repo']))
    if errors or data.get('range') != state['range']:
        raise f.FlowError('invalid frozen teaching scope: ' + '; '.join(errors))
    sections = data['sections']
    if any(not s['topics'] for s in sections):
        raise f.FlowError('stable topic IDs required for every section')
    section_ids = {s['id'] for s in sections}
    late = data.get('link_sections', [])
    if not isinstance(late, list) or any(not isinstance(x, str) or x not in section_ids for x in late):
        raise f.FlowError('unknown problem-link section')
    topics = {t['id'] for s in sections for t in s['topics']}
    links = data.get('links', [])
    if not isinstance(links, list) or any(not isinstance(link, dict) or link.get('topic') not in topics for link in links):
        raise f.FlowError('scope link has no topic owner')
    return sections


def check_final_scope(state, final):
    draft = f._read(output(state, 'scope-draft', 'manifest.json'))
    selected = f._read(output(state, 'selection', 'manifest.json'))
    # Only the selected workbook fields and late link list have other producers.
    # link_sections is optional scheduler metadata, never a new grant of ownership.
    variable = {'links', 'problems', 'selection_policy', 'link_sections'}
    def teaching(m):
        return {key: value for key, value in m.items() if key not in variable}
    if teaching(final) != teaching(draft):
        raise f.FlowError('scope-final changed frozen teaching scope')
    if any(final.get(k) != selected.get(k) for k in ('range', 'slug', 'problems', 'selection_policy')):
        raise f.FlowError('scope-final changed accepted selection')
    if 'link_sections' in final and final['link_sections'] != draft.get('link_sections', []):
        raise f.FlowError('scope-final changed frozen link owners')
    allowed = {t['id'] for section in state['scope_sections'] if section['id'] in state['link_sections']
               for t in section['topics']}
    if any(link['topic'] not in allowed for link in final['links']):
        raise f.FlowError('new final link belongs to an already fixed section')


def check_selection(state, root):
    import problem_index
    m = f._read(root / 'manifest.json')
    scope = f._read(output(state, 'scope-draft', 'manifest.json'))
    if (m.get('range'), m.get('slug')) != (scope['range'], scope['slug']):
        raise f.FlowError('selection changed frozen scope')
    candidates = f._read(output(state, 'candidate-index', 'candidates.json'))
    notes = public(state).parent
    history, files = problem_index.history_snapshot(notes,state['range'])
    live, errors = problem_index.candidate_data(Path(state['repo']), notes, exclude_range=state['range'],history=history)
    if errors or (candidates['catalog_sha256'], candidates['problems']) != (live['catalog_sha256'], live['problems']):
        raise f.FlowError('candidate source or previous use changed')
    review = f._read(root / 'selection-review.json')
    expected = problem_index.record_selection(m, candidates, review)
    if expected != f._read(root / 'selection.json'):
        raise f.FlowError('selection record does not match accepted candidates and manifest')
    if m.get('selection_policy') != 'exam-first-v2':
        raise f.FlowError('parallel selection requires exam-first-v2 review')
    # Bind external question/figure sources as well as the candidate JSON snapshot.
    verified = {}
    selected = {q['id'] for q in m['problems']}
    for item in candidates['problems']:
        if item['id'] not in selected: continue
        details = item
        if item.get('detail_path'):
            details = f._read(output(state, 'candidate-index', 'catalog/' + item['detail_path']))
        for name, digest in details['input_hashes'].items():
            path = local_path(Path(state['repo']), name)
            if f._sha(path) != digest:
                raise f.FlowError('selected question or figure changed: ' + name)
            verified[str(path)] = digest
    return [dict(path=p, sha256=h) for p, h in sorted(verified.items())], files


class SelectionHistoryChanged(f.FlowError):
    def __init__(self, attempt):
        super().__init__('previous pack history changed during selection adoption')
        self.attempt = attempt


def _missing_file(exc):
    """A vanished file, by type: Windows translates the OS error message."""
    while exc is not None:
        if isinstance(exc, FileNotFoundError):
            return True
        exc = exc.__cause__ or (None if exc.__suppress_context__ else exc.__context__)
    return False


def check_selection_history(state, receipt):
    if 'selection_history' not in receipt:
        return
    from problem_index import history_digests
    try:
        current = history_digests(public(state).parent, state['range'])
    except OSError as exc:
        raise SelectionHistoryChanged(receipt['attempt']) from exc
    if current != receipt['selection_history']:
        raise SelectionHistoryChanged(receipt['attempt'])


def blind_items(state: dict) -> dict:
    """All accepted independent solutions, joined across the blind solver tasks."""
    joined = {}
    for tid in explain_ids(state, 'explain-blind'):
        for key, item in f._read(output(state, tid, 'independent.json'))['items'].items():
            if key in joined:
                raise f.FlowError('duplicate independent item')
            joined[key] = item
    return joined


def check_leaf_join(state, child_root):
    child = f._read(child_root / 'child-receipt.json')
    folder = child_root / child['bucket']
    for tid in explain_ids(state, 'explain-author'):
        for name in spec_for(state, tid).outputs:
            if f._sha(output(state, tid, name)) != f._sha(local_path(folder, name)):
                raise f.FlowError('child replaced accepted author fragment')
    items = blind_items(state)
    reviewed = f._read(folder / 'review.json')['independent']['items']
    if set(items) != set(reviewed) or any(any(reviewed[k].get(field) != val for field, val in item.items())
                                          for k, item in items.items()):
        raise f.FlowError('child independent review differs from accepted blind solution')
    authors = child['reviewers']['authors']
    if state.get('problem_contract'):
        if set(authors) != set(problem_keys(state)) or any(
                authors[k] != state['tasks'][f'explain-author-{k}']['agent_id'] for k in authors):
            raise f.FlowError('child author identity mismatch')
    elif any(agent != state['tasks'][explain_ids(state, 'explain-author')[0]]['agent_id'] for agent in authors.values()):
        raise f.FlowError('child author identity mismatch')


def fragment_probe_records(task, root):
    """A done author hands off only the fragment bytes its own passing `task probe` measured."""
    from pack_probe import AUTHOR
    path = root/'probe'/'probe.json'
    fragment = root/'sections'/(task['id'][len(AUTHOR):] + '.html')
    try:
        probe = json.loads(path.read_text(encoding='utf-8'))
        current = (probe.get('status') == 'pass' and probe.get('task_id') == task['id']
                   and probe.get('attempt') == task.get('attempt')
                   and probe.get('fragment_sha256') == f._sha(fragment))
    except (OSError, ValueError, AttributeError):
        current = False
    if not current:
        raise f.FlowError('fragment probe missing, stale or failing')
    return file_records([path])


def validate_worker(state, task, receipt_path):
    from pack_receipts import validate_receipt
    spec = spec_for(state, task['id'])
    if proof(state, spec) != task['input_version']:
        raise f.FlowError('frozen worker inputs superseded')
    receipt = validate_receipt(state, task, receipt_path)
    # Never trust worker-supplied approval identities or computed provenance.
    for name in ('fresh_approvals', 'reused_approvals', 'render_environment', 'joined_independent', 'selection_history'):
        receipt.pop(name, None)
    brief = f._read(task['brief'])
    receipt['verified_files'].append(dict(path=task['brief'], sha256=task['brief_sha256']))
    if environment := brief.get('render_environment'):
        from pack_approvals import environment_current
        from pack_receipts import records
        records([environment], [Path(task['attempt_dir'])])
        manifest = f._read(environment['path'])
        if not environment_current(state, brief, manifest):
            raise f.FlowError('render environment changed after claim')
        records(manifest['files'], [Path(state['repo'])])
        records(manifest['served'], [Path(state['run'])])
        receipt['verified_files'].extend([environment, *manifest['files'], *manifest['served']])
        if hints := brief.get('geometry_hints'):
            records([hints], [Path(task['attempt_dir'])])
            receipt['verified_files'].append(hints)
        receipt['render_environment'] = environment
    compact = receipt.get('worker_submission')
    if compact:
        from pack_receipts import records, submission_fields
        root = Path(task['attempt_dir'])
        records([compact], [root])
        worker_fields = submission_fields(root, compact['path'])
        expected_outputs = set(worker_fields.pop('outputs'))
        if any(receipt.get(k) != value for k,value in worker_fields.items()) or any(
                k in receipt and k not in worker_fields for k in ('fix_results', 'reconciliations')):
            raise f.FlowError('receipt differs from original worker submission')
        receipt['verified_files'].append(compact)
        if brief.get('approval_plan') and receipt['task_status'] == 'done' and not receipt.get('target_reviews'):
            raise f.FlowError('compact success requires complete target judgments')
    from pack_approvals import ROLES, review_policy
    if state.get('approval_contract') == 1 and task['role'] in ROLES:
        policy = review_policy(task['role'])
        if brief.get('approval_policy') != policy:
            raise f.FlowError('claimed approval policy has changed')
        receipt['approval_policy'] = policy
        if receipt['task_status'] == 'done' and not receipt.get('target_reviews'):
            raise f.FlowError('claimed contract requires complete current target judgments')
    if 'target_reviews' in receipt:
        from pack_approvals import target_contract
        if receipt['task_status'] != 'done' or receipt['target_reviews'] != str(Path(task['attempt_dir'])/'target-reviews.json'):
            raise f.FlowError('invalid target review path/status')
        result = target_contract(state, task, receipt)
        if not set(result['outputs']) <= {x['path'] for x in receipt['outputs']}:
            raise f.FlowError('target screens/results must be declared outputs')
        if task['role'] == 'explain-blind':
            receipt['joined_independent'] = result['independent']
        if compact:
            expected_outputs.update(result['outputs'])
        receipt.update(fresh_approvals=result['fresh'], reused_approvals=result['reused'])
        receipt['verified_files'].extend(dict(path=p, sha256=h) for p,h in result['evidence'].items())
    if compact and expected_outputs != {r['path'] for r in receipt['outputs']}:
        raise f.FlowError('output inventory differs from worker submission and computed target proof')
    if task['role'] in findings.LEDGER_REVIEWS and receipt['task_status'] in ('done', 'needs_fix'):
        # task check exercises the same decision rules without changing RUN state.
        trial = copy.deepcopy(state)
        register_review(trial, trial['tasks'][task['id']], receipt)
    if receipt['task_status'] != 'done':
        if task['role'] == 'concept-review' and receipt['status'] == 'withheld' and not receipt['unresolved']:
            raise f.FlowError('withheld quiz requires an unresolved reason')
        return receipt
    root = Path(task['attempt_dir'])
    previous = f._read(task['brief']).get('previous_outputs', {})
    if previous and all(f._sha(Path(path)) == f._sha(local_path(root, name)) for name, path in previous.items()):
        raise f.FlowError('unchanged repair output')
    role = task['role']
    if role == 'author' and state.get('probe_contract') == 1:
        receipt['verified_files'].extend(fragment_probe_records(task, root))
    if role == 'concept-review':
        quiz = root/'quiz'
        if f._sha(quiz/'source.json') != f._sha(output(state, 'concept-draft', 'source.json')):
            raise f.FlowError('quiz_input_changed')
        validated = json.loads(concept_command('evidence', '--run', quiz))
        for path in map(Path, validated):
            if not path.resolve().is_relative_to(quiz):
                raise f.FlowError('quiz evidence escapes its attempt')
        quiz_files = file_records(map(Path, validated))
        receipt['quiz_files'] = {Path(r['path']).relative_to(quiz).as_posix():r['sha256'] for r in quiz_files}
        receipt['verified_files'].extend(quiz_files)
    if role == 'scope-draft':
        scope_manifest(state, f._read(root / 'manifest.json'))
    if role == 'selection':
        sources, receipt['selection_history'] = check_selection(state, root)
        receipt['verified_files'].extend(sources)
    if role == 'scope-final':
        import manifest
        m = manifest.load(root / 'manifest.json', repo=Path(state['repo']))
        check_final_scope(state, m)
    if role in ('explain-author', 'explain-blind'):
        if not task.get('agent_id'):
            raise f.FlowError('bound leaf reviewer identity required')
        other = state['tasks'][counterpart(task['id'])]
        if role == 'explain-author' and other['status'] == 'done':
            solved = f._read(output(state, counterpart(task['id']), 'independent.json'))['items']
            if any(item['reviewer'] == task['agent_id'] for item in solved.values()):
                raise f.FlowError('independent solver cannot author their reused solution')
        if other.get('agent_id') == task['agent_id']:
            raise f.FlowError('independent solver must differ from author')
    if role == 'explain-blind':
        questions = f._read(brief['questions'] if state.get('problem_contract')
                            else output(state, 'stage-problem-index', 'questions.json'))['problems']
        keys = {p['id'] + ':' + sub for p in questions for sub in p['subparts']}
        items = (receipt['joined_independent'] if 'joined_independent' in receipt
                 else f._read(root/'independent.json')['items'])
        plan = brief.get('approval_plan', {})
        from pack_approvals import collect_current_reviews
        old = collect_current_reviews(receipt.get('reused_approvals', {}), state.get('approval_ledger', []),
                                      run_root=Path(state['run']))['current']
        solvers = {plan['targets'][t]['item']:r['reviewer'] for t,r in old.items()}
        if set(items) != keys or any(item.get('reviewer') != solvers.get(k, task['agent_id']) or
                item.get('reviewer') == state['tasks'][counterpart(task['id'])].get('agent_id') or
                not all(isinstance(item.get(k), str) and item[k].strip() for k in ('method', 'conclusion', 'evidence'))
                for k,item in items.items()):
            raise f.FlowError('blind solution must cover every subpart with the bound solver')
    if role == 'child-coordinator':
        check_leaf_join(state, root/'child')
    return receipt


def freeze_files(root, paths, expected, destination):
    """Adopt only named, verified bytes. No accepted destination is overwritten."""
    result = {}
    for path in paths:
        path = Path(path)
        name = path.relative_to(root).as_posix()
        local_path(root, name)
        target = local_path(destination, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        with path.open('rb') as src, target.open('xb') as dst:
            shutil.copyfileobj(src, dst)
        if f._sha(target) != expected[str(f.nfc_path(path))]:
            raise f.FlowError('output changed during adoption: ' + name)
        target.chmod(0o444)
        result[name] = str(target)
    return result


def register_review(state, task, receipt):
    findings.check_reviewer(state, task)
    brief = f._read(task['brief'])
    digest = brief.get('candidate_digest')
    if digest is None and task['id'] == findings.COORDINATOR:
        # A coordinator claimed before the finding ledger reviewed the same
        # accepted fragments; its frozen input_version pins that author attempt.
        digest = explanation_digest(state)
    task.update(status=receipt['task_status'], receipt=receipt, candidate_digest=digest)
    if task['status'] == 'needs_fix' and not receipt['unresolved']:
        raise f.FlowError('needs-fix requires structured findings')
    findings.adjudicate(state, task['id'], receipt['unresolved'], receipt.get('fix_results', []),
                        receipt.get('reconciliations', []))


def adopt_worker(state, task, receipt):
    task.update(status=receipt['task_status'], receipt=receipt)
    if task['status'] != 'done' and not (task['role'] in findings.LEDGER_REVIEWS and task['status'] == 'needs_fix'):
        return
    root = Path(task['attempt_dir'])
    dst = Path(state['run']) / 'adopted' / task['id'] / str(uuid4())
    verified = {x['path']: x['sha256'] for x in receipt['verified_files']}
    # Child receipt/run semantics use absolute paths; its validated files remain hash-bound.
    owned = [Path(x['path']) for x in receipt['outputs']]
    if task['role'] == 'concept-review':
        owned.extend(local_path(root/'quiz', name) for name in receipt['quiz_files'])
    owned.extend(Path(x) for x in (receipt['report'], *receipt['reviews']))
    if state.get('approval_contract'):
        owned.append(Path(task['brief']))
    if compact := receipt.get('worker_submission'):
        owned.extend([Path(compact['path']), Path(f._read(task['brief'])['receipt'])])
    if task['role'] == 'pdf-qa':
        owned.extend(Path(x) for x in verified if Path(x).is_relative_to(root / 'answer-pages'))
    task['artifacts'] = freeze_files(root, sorted(set(owned)), verified, dst)
    receipt['verified_files'].extend(file_records(Path(p) for p in task['artifacts'].values()))
    if task['role'] == 'concept-review':
        certificate = seal_blind_approval(state, task, dst/'quiz', receipt['quiz_files'])
        receipt['blind_certificate'] = certificate
        receipt['verified_files'].append(certificate)
    if 'joined_independent' in receipt:
        joined = receipt.pop('joined_independent')
        # The complete answer-bearing file exists only on the runner's adopted
        # side after the worker has returned. Keep its original submission too.
        separate = dst.parent/str(uuid4())
        separate.mkdir()
        compiled = separate/'independent.json'
        f._atomic_json(compiled, dict(items=joined))
        compiled.chmod(0o444)
        task['artifacts']['independent.json'] = str(compiled)
        receipt['verified_files'].extend(file_records([compiled]))
    if task['role'] == 'scope-draft':
        m = f._read(dst / 'manifest.json')
        state['scope_sections'] = scope_manifest(state, m)
        link_topics = {link['topic'] for link in m.get('links', [])}
        state['link_sections'] = sorted(set(m.get('link_sections', [])) | {
            s['id'] for s in m['sections'] if any(t['id'] in link_topics for t in s['topics'])})
    if task['role'] == 'selection':
        state['selected_ids'] = [q['id'] for q in f._read(dst / 'manifest.json')['problems']]



def prepare_worker(snapshot, tid, attempt, receipt_path):
    task = snapshot['tasks'][tid]
    f._attempt(task, attempt)
    receipt = validate_worker(snapshot, task, receipt_path)
    adopt_worker(snapshot, task, receipt)
    return receipt


def install_worker(current, snapshot, tid, receipt):
    row = current['tasks'][tid]
    task = snapshot['tasks'][tid]
    if 'approval_policy' in receipt:
        from pack_approvals import review_policy
        if receipt['approval_policy'] != review_policy(row['role']):
            raise f.FlowError('target review policy changed during adoption')
    if environment := receipt.get('render_environment'):
        from pack_approvals import environment_current
        if not environment_current(current, f._read(row['brief']), f._read(environment['path'])):
            raise f.FlowError('render environment changed during adoption')
    row.update(status=task['status'], receipt=receipt)
    if row['status'] == 'done' or (tid in findings.LEDGER_REVIEWS and row['status'] == 'needs_fix'):
        row['artifacts'] = task['artifacts']
        from pack_approvals import adopt_targets
        adopt_targets(current, row, receipt)
        if tid in findings.LEDGER_REVIEWS:
            register_review(current, row, receipt)
            if tid in findings.NOTE_REVIEWS:
                findings.join_reviews(current)
        if tid not in findings.REVIEW_ROLES:
            row['repair_bindings'] = {r['id']: r['pending_request']
                                      for r in f._read(row['brief']).get('repair_findings', [])}
        keys = {'scope-draft': ('scope_sections', 'link_sections'), 'selection': ('selected_ids',)}.get(tid, ())
        for key in keys:
            current[key] = snapshot[key]
    return f.refresh_tasks(current)


def accept_worker(run, tid, attempt, receipt_path):
    from pack_receipts import verify_receipt_files
    snapshot = f.inspect_state(run)
    receipt = prepare_worker(snapshot, tid, attempt, receipt_path)

    def apply(current):
        f._current(current)
        row = current['tasks'][tid]
        f._attempt(row, attempt)
        if proof(current, spec_for(current, tid)) != snapshot['tasks'][tid]['input_version'] or verify_receipt_files(receipt):
            raise f.FlowError('worker input or file version changed during adoption')
        check_selection_history(current, receipt)
        return install_worker(current, snapshot, tid, receipt)
    return transact(run, apply)


def file_identity(path):
    stat = Path(path).stat()
    return stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns


def witness(records):
    """Hash bytes outside the lock, pin the exact file identities spanning that read."""
    result = {}
    for path, digest in records.items():
        identity = file_identity(path)
        if f._sha(Path(path)) != digest or file_identity(path) != identity:
            raise f.FlowError('evidence changed during validation: ' + path)
        result[path] = identity
    return result


def prepare_batch_item(state, item):
    if not isinstance(item, dict) or any(not isinstance(item.get(k), str) or not item[k]
                                        for k in ('task_id', 'attempt', 'receipt')):
        raise f.FlowError('invalid submission')
    tid, attempt = item['task_id'], item['attempt']
    path = Path(item['receipt'])
    if not path.is_absolute():
        raise f.FlowError('absolute receipt path required')
    task = state['tasks'].get(tid, {})
    if task.get('attempt') != attempt or task.get('invalidated_active') or task.get('status') == 'stale':
        raise f.FlowError('inactive_attempt')
    if str(path) != f._read(task['brief'])['receipt']:
        raise f.FlowError('receipt must match the claimed brief')
    if task['status'] not in ('claimed', 'running'):
        saved = task.get('receipt') or {}
        pinned = {r['path']:r['sha256'] for r in saved.get('verified_files', [])}
        if pinned.get(str(path)) == f._sha(path):
            return state, 'already_accepted', pinned
        raise f.FlowError('different or inactive receipt')
    snapshot = copy.deepcopy(state)
    receipt = prepare_worker(snapshot, tid, attempt, path)
    # A rejected item cannot leave partial changes in the rest of this batch.
    candidate = install_worker(copy.deepcopy(state), snapshot, tid, receipt)
    status = candidate['tasks'][tid]['status']
    if status != receipt['task_status']:
        raise f.FlowError('input version changed during adoption')
    pinned = dict(state['hashes'])
    pinned.update({r['path']:r['sha256'] for r in receipt['verified_files']})
    for dep in ancestors(state, spec_for(state, tid)).values():
        source = dep.get('receipt') or dep
        pinned.update({r['path']:r['sha256'] for r in source['verified_files']})
    return candidate, 'accepted', pinned


def accept_batch(run: Path, submissions: list[dict]) -> dict:
    return _accept_batch(run, submissions)


def _accept_batch(run, submissions, *, stop=None):
    """Prepare independent receipts privately, then publish one revision or retry."""
    if not isinstance(submissions, list):
        raise f.FlowError('submissions must be an array')
    changed_selections = set()
    for retry in range(24):
        original = f.parallel_state(run)
        state = f._current(copy.deepcopy(original))
        items, bindings, identities = [], [], {}
        for entry in submissions:
            item = {k:entry.get(k) for k in ('task_id','attempt')} if isinstance(entry, dict) else {}
            try:
                if item.get('task_id') == 'selection' and item.get('attempt') in changed_selections:
                    raise SelectionHistoryChanged(item['attempt'])
                candidate, status, records = prepare_batch_item(state, entry)
                if stop:
                    if candidate is state:
                        candidate = copy.deepcopy(state)
                    from pack_actions import host_stop, record_resume
                    path, signature, data = stop
                    if host_stop(state,state['tasks'][item['task_id']],path) != data:
                        raise f.FlowError('stop evidence changed')
                    records[str(path)] = signature
                    record_resume(candidate,item['task_id'],item['attempt'],'reused',path,signature,data.get('host_gap'))
                stamps = witness(records)
                if any(identities[p]!=stamp for p,stamp in stamps.items() if p in identities):
                    raise f.FlowError('shared evidence changed during batch')
                identities.update(stamps)
                state = candidate
                if status == 'accepted':
                    bindings.append((item['task_id'], item['attempt'], state['tasks'][item['task_id']]['input_version']))
                item['status'] = status
            except (OSError, ValueError, TypeError, KeyError) as exc:
                item.update(status='rejected', error_code='inactive_attempt' if str(exc)=='inactive_attempt'
                            else 'validation_failed', reason=str(exc))
            items.append(item)

        def commit(current):
            for tid, attempt, version in bindings:
                row = current['tasks'][tid]
                f._attempt(row, attempt)
                if row['input_version'] != version or proof(current, spec_for(current, tid)) != version:
                    raise f.FlowError('batch snapshot changed')
                receipt = state['tasks'][tid]['receipt']
                check_selection_history(current, receipt)
                if environment := receipt.get('render_environment'):
                    from pack_approvals import environment_current
                    if not environment_current(current,f._read(row['brief']),f._read(environment['path'])):
                        raise f.FlowError('batch snapshot changed')
            if any(file_identity(path) != stamp for path,stamp in identities.items()):
                raise f.FlowError('batch snapshot changed')
            return state
        try:
            if bindings or state != original:
                f.update_state(run, original['revision'], commit)
            else:
                current = f.load_state(run)
                if current['revision'] != original['revision']:
                    raise f.FlowError('revision conflict')
                commit(current)
            return dict(items=items, next=f.next_work(run, slots=0))
        except SelectionHistoryChanged as exc:
            changed_selections.add(exc.attempt)
        except (OSError, f.FlowError) as exc:
            if retry == 23 or not _missing_file(exc) and not any(reason in str(exc) for reason in
                                      ('revision conflict','lock busy','batch snapshot changed','No such file','brief changed after claim')):
                raise
            time.sleep(0.01 * (retry + 1))


def seal_questions(state, paths, root, slug):
    """Export only question fields and their figure bytes to the two early workers."""
    from urllib.parse import unquote
    import xml.etree.ElementTree as ET
    script = Path(__file__).resolve().parents[2] / 'ec2-problem-explain/scripts/epe_cli.py'
    with tempfile.TemporaryDirectory(prefix='ec2-question-extract-') as tmp:
        extracted = Path(tmp) / 'extract'
        args = [sys.executable, script, 'extract', '--repo', paths.repo, '--public-pack', paths.public_pack,
                '--candidate-pack', paths.work_pack, '--run', extracted, '--target', state['range'], '--slug', slug]
        result = subprocess.run(args, capture_output=True, text=True)
        if result.returncode:
            raise f.FlowError('question extraction failed: ' + result.stderr)
        bucket, = f._read(extracted / 'run.json')['targets']
        source = f._read(extracted / bucket / 'source.json')
    sealed = root / 'sealed'
    sealed.mkdir()
    problems = []
    display = paths.work_file('.assets/display-titles.json')
    titles = f._read(display) if state.get('approval_contract') and display.is_file() else {}
    for problem in source['problems']:
        item = {key: problem[key] for key in ('id', 'workbook_id', 'subparts', 'title', 'original_html',
                                              'conditions_html', 'ask_html')}
        if problem['workbook_id'] in titles:
            from display_titles import numbered_title
            if problem['title'] != numbered_title(titles, problem['workbook_id'], problem['number']):
                raise f.FlowError('sealed question title differs from approved display title')
            item['display_title'] = titles[problem['workbook_id']]
        item['figures'] = []
        for i, markup in enumerate(problem['figures_html']):
            img = ET.fromstring(markup.replace('></figure>', '/></figure>')).find('img')
            src = paths.link(paths.public_pack, unquote(img.attrib['src']))
            name = f"{item['id']}-figure-{i+1}{src.suffix}"
            shutil.copyfile(src, sealed/name)
            item['figures'].append(name)
        problems.append(item)
    f._atomic_json(sealed/'questions.json', dict(problems=problems))
    per_problem = {}
    if state.get('problem_contract'):
        from pack_graph import problem_keys
        if [item['id'] for item in problems] != problem_keys(state):
            raise f.FlowError('sealed question IDs differ from the selection order')
        # Each per-problem worker gets a folder holding only its own question and figures.
        for item in problems:
            folder = sealed / item['id']
            folder.mkdir()
            for name in item['figures']:
                shutil.copyfile(sealed/name, folder/name)
            f._atomic_json(folder/'questions.json', dict(problems=[item]))
            per_problem[item['id']] = sorted(folder.iterdir())
    inputs = [paths.source_file(p) for p in source['inputs']]
    digest = hashlib.sha256(''.join(f._sha(p) for p in inputs).encode()).hexdigest()
    if digest != source['sha256']:
        raise f.FlowError('question inputs changed during extraction')
    return sealed, inputs, per_problem


def input_bundle(state, spec, root):
    """Materialize the exact filenames expected by the existing candidate producers."""
    bundle = root / 'input'
    bundle.mkdir()
    final = 'scope-final' in ancestors(state, spec)
    chosen = 'scope-final' if final else 'selection'
    wanted = {'manifest.json': output(state, chosen, 'manifest.json')}
    if spec.id == 'stage-problem-index':
        for name in ('selection.json', 'display-titles.json'):
            wanted[name] = output(state, 'selection', name)
    if spec.id == 'assemble-note':
        for section in state['scope_sections']:
            tid = 'author-' + section['id']
            name = 'sections/' + section['id'] + '.html'
            wanted[name] = output(state, tid, name)
    for name, src in wanted.items():
        dest = local_path(bundle, name)
        dest.parent.mkdir(exist_ok=True, parents=True)
        shutil.copyfile(src, dest)
        if f._sha(dest) != f._sha(src):
            raise f.FlowError('input changed while composing private bundle')
    return bundle


def adopted_packs(state, spec):
    return {tid: row['pack'] for tid, row in ancestors(state, spec).items() if row.get('pack')}


def common_diagnostics(markup, note, paths):
    from check_html import check_common, parse_html
    doc = parse_html(markup)
    return doc, {(p.code, p.detail) for p in check_common(doc, markup, note, pack_paths=paths) if p.code != 'lang'}


def fragment_diagnostics(state, manifest, note, paths):
    """Index each accepted fragment by the same diagnostics used for the assembled page."""
    from assemble import read_fragment
    result = {}
    for section in manifest['sections']:
        sid = section['id']
        path = output(state, 'author-' + sid, 'sections/' + sid + '.html')
        source = read_fragment(path, manifest)
        result[sid] = common_diagnostics(source, note, paths)
    return result


def metadata_diagnostics(manifest, note, paths):
    from html import escape
    # Match build_note's substitution rules: labels and headings are text;
    # the footer is an HTML fragment supplied by the teaching manifest.
    markup = {k: escape(manifest[k]) for k in ('note_title', 'note_subtitle')}
    markup['footer_note'] = manifest['footer_note']
    markup.update({s['id'] + '.' + k: escape(s[k]) for s in manifest['sections'] for k in ('short', 'title')})
    return {field: common_diagnostics(value, note, paths) for field, value in markup.items()}


def diagnostic_source(code, detail, entry):
    """Whether one `common_diagnostics` entry (doc, diagnostics) produces the page diagnostic."""
    doc, diagnostics = entry
    return (code, detail) in diagnostics or (code == 'duplicate-id' and detail in doc.ids)


def fragment_owns(code, detail, fragment, metadata):
    """machine_report's attribution of one page diagnostic to the section fragment.

    A duplicate id that a manifest field also carries goes only to scope-draft, and a
    diagnostic the fragment itself does not produce goes to the metadata or template owner.
    """
    if code == 'duplicate-id' and any(diagnostic_source(code, detail, entry) for entry in metadata.values()):
        return False
    return diagnostic_source(code, detail, fragment)


def machine_report(state, root, problems, note, manifest, paths=None):
    issues = []
    sections = None
    metadata = None
    for problem in problems:
        owner = findings.owner_of(problem.where, manifest)
        targets = [(owner, problem.where)]
        links = [link for link in manifest['links'] if link['href'] == problem.detail]
        if problem.code == 'broken-link' and links:
            # The literal href is part of the manifest contract, so a fragment-only
            # edit would instead fail missing-link after the next assembly.
            draft = f._read(output(state, 'scope-draft', 'manifest.json'))
            targets = [('scope-draft' if link in draft['links'] else 'scope-final', link['topic'])
                       for link in links]
        elif owner == 'scope-final':
            if sections is None:
                sections = fragment_diagnostics(state, manifest, note, paths)
            targets = [('author-' + sid, sid if problem.where == note.name else problem.where)
                       for sid, entry in sections.items()
                       if diagnostic_source(problem.code, problem.detail, entry) or problem.where in entry[0].ids]
            if metadata is None:
                metadata = metadata_diagnostics(manifest, note, paths)
            metadata_targets = [('scope-draft', field) for field, entry in metadata.items()
                                if diagnostic_source(problem.code, problem.detail, entry)]
            if problem.code == 'duplicate-id' and metadata_targets:
                # Renaming the manifest occurrence can preserve the section or
                # template anchor. Reassembly checks any remaining duplicates.
                targets = metadata_targets
            else:
                targets.extend(metadata_targets)
            if not targets:
                targets = [('assemble-note', problem.where)]
        for owner, target in targets:
            issues.append(dict(rule=problem.code, target=target, defect=problem.detail, severity='Important',
                               owner_task=owner, evidence=str(problem)))
    path = root/'check-findings.json'
    f._atomic_json(path, dict(candidate_digest=f._sha(note), findings=issues))
    return {path.name: path}


CONCEPT_CLI = Path(__file__).resolve().parents[2]/'ec2-concept-check/scripts/concept.py'


def quiz_teaching_digest(logical_inputs):
    teaching = {key:value for key,value in logical_inputs.items() if not key.startswith(('vendor/', 'interaction/'))}
    return hashlib.sha256(json.dumps(teaching, sort_keys=True).encode()).hexdigest()


def seal_blind_approval(state, task, adopted, hashes):
    """Certify only actual accepted targets, against the previously frozen packet and answers."""
    source = f._read(adopted/'source.json')
    ledger = f._read(adopted/'blind-ledger.json')
    rows = {}
    for item in f._read(adopted/'items.json')['items']:
        cid = item['id']
        row = ledger[cid]
        answers = Path(row['proof'])
        issue = answers.parent.parent/'issued.json'
        if (hashes.get(answers.as_posix()) != row['answers_sha256'] or hashes.get(issue.as_posix()) != row['issued_sha256']
                or hashes.get(answers.with_name('submission.json').as_posix()) != row['submission_sha256']):
            raise f.FlowError('independent packet or answer differs from accepted evidence')
        rows[cid] = row
    # A worker can supply files only inside its attempt. The scheduler allocates
    # this separate immutable record after validating and adopting its outputs.
    directory = Path(state['run'])/'blind-approvals'/str(uuid4())
    directory.mkdir(parents=True, exist_ok=False)
    path = directory/'approved.json'
    f._atomic_json(path, dict(run_id=state['run_id'], attempt=task['attempt'],
                   source_sha256=hashes['source.json'], teaching_sha256=quiz_teaching_digest(source['logical_inputs']), rows=rows))
    path.chmod(0o444)
    return dict(file_records([path])[0], solver_history_version=f.BLIND_HISTORY_VERSION)


def prior_blind_approval(run, run_id, attempt, record, logical_inputs):
    if not record or record.get('solver_history_version') != f.BLIND_HISTORY_VERSION:
        return {}
    try:
        base = Path(run)/'blind-approvals'
        path = local_path(base, Path(record['path']).relative_to(base))
        if f._sha(path) != record['sha256']:
            return {}
        data = f._read(path)
        if (data['run_id'], data['attempt'], data['teaching_sha256']) == (
                run_id, attempt, quiz_teaching_digest(logical_inputs)):
            return data['rows']
    except (ValueError, KeyError, OSError):
        pass
    return {}


def retain_quiz_evidence(task, quiz, *, approved=None):
    """Copy only independently current parts of a previously accepted review."""
    receipt = task.get('receipt') or {}
    if receipt.get('task_status') != 'done':
        return []
    previous = Path(task['attempt_dir'])/'quiz'
    hashes = {Path(r['path']).relative_to(previous).as_posix(): r['sha256']
              for r in receipt['verified_files'] if Path(r['path']).is_relative_to(previous)}

    def current(name):
        try:
            contents = local_path(previous, name).read_bytes()
            if hashlib.sha256(contents).hexdigest() == hashes.get(name):
                return contents
        except (OSError, ValueError):
            pass
        return None

    def copy_group(names):
        files = {name: current(name) for name in names}
        if any(contents is None for contents in files.values()):
            return False
        for name, contents in files.items():
            path = local_path(quiz, name)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(contents)
        return True

    prior = current('source.json')
    if prior is None:
        return []
    old = json.loads(prior)['logical_inputs']
    new = f._read(quiz/'source.json')['logical_inputs']
    if quiz_teaching_digest(old) != quiz_teaching_digest(new) or not copy_group(('objectives.json', 'items.json')):
        return []
    retained = ['objectives.json', 'items.json']
    ledger = {}
    if approved is None:
        parent = Path(f._read(quiz/'source.json')['parent_run'])
        approved = prior_blind_approval(parent, receipt['run_id'], task['attempt'], receipt.get('blind_certificate'), new)
    for cid,row in approved.items():
        answers = Path(row['proof']).as_posix()  # older Windows ledgers stored '\'
        folder = Path(answers).parent.parent
        names = [name for name in hashes if Path(name).is_relative_to(folder/'packet')]
        if names and copy_group([answers, Path(answers).with_name('submission.json').as_posix(),
                                (folder/'issued.json').as_posix(), *names]):
            ledger[cid] = row
    if ledger:
        f._atomic_json(quiz/'blind-ledger.json', ledger)
        retained.extend(sorted(ledger))
    shots = [name for name in hashes if name.startswith('shots/')]
    if old == new and shots and copy_group(['browser.json', *shots]):
        retained.append('browser.json')
        if copy_group(['visual-review.json']):
            retained.append('visual-review.json')
    return retained


def concept_command(*args):
    result = subprocess.run([sys.executable, CONCEPT_CLI, *args], capture_output=True, text=True)
    if result.returncode:
        raise f.FlowError(result.stderr.strip() or 'concept command failed')
    return result.stdout.strip()


def execute_action(state, spec, root):
    import manifest
    import pack_actions as actions
    tid = spec.id
    repo = Path(state['repo'])
    extras = {}
    if tid == 'concept-draft':
        path = concept_command('prepare', state['range'], '--repo', repo, '--parent-run', state['run'],
                               '--run', root/'quiz', '--candidate-pack', state['actions']['convert-md']['candidate_root'])
        files = {'source.json': Path(path)}
        extras['source_inputs'] = [dict(path=p, sha256=h) for p,h in f._read(path)['inputs'].items()]
    elif tid == 'concept-publish':
        worker = state['tasks']['concept-review']
        concept_command('publish', '--run', Path(worker['attempt_dir'])/'quiz', '--review-attempt', worker['attempt'],
                        '--action-attempt', state['actions'][tid]['attempt'])
        result = Path(state['run'])/'concept-check-result.json'
        files = {'concept-check-result.json': root/'concept-check-result.json'}
        shutil.copyfile(result, files['concept-check-result.json'])
        extras['source_inputs'] = file_records([result, *map(Path, f._read(result)['files'])])
    elif tid == 'source-prep':
        from pack_sources import lecture_pdfs, prepare_sources
        stt = {date: Path(p) for date in state['sessions'] for p in state['hashes']
               if f.nfc_path(p).parent.name == 'STT' and f.nfc_path(p).name == f'{date} 전회2.md'}
        pdfs = [path for _, path in lecture_pdfs(repo)]
        files = prepare_sources(repo, state['sessions'], stt, root)
        # The STTs and every lecture PDF, readable or not, are frozen here instead of in a
        # worker receipt, so repairing a damaged PDF stales this action.
        extras['source_inputs'] = file_records([*stt.values(), *pdfs])
    elif tid == 'render-preflight':
        from render import render_preflight
        result = render_preflight(root)
        result['pdf'] = str(result['pdf']) if result['pdf'] else None
        f._atomic_json(root/'render-preflight.json', result)
        if result['status'] != 'pass':
            raise f.FlowError(result['error_code'] or 'render preflight failed')
        files = {'render-preflight.json': root/'render-preflight.json', 'render-preflight.pdf': Path(result['pdf'])}
    elif tid == findings.MACHINE_REVIEW:
        from check_html import check_guide, check_note, parse_html
        note = output(state, 'assemble-note', 'note')
        source = note.read_text(encoding='utf-8')
        m = f._read(output(state, 'scope-final', 'manifest.json'))
        problems = check_note(parse_html(source), m) + check_guide(source, m)
        files = machine_report(state, root, problems, note, m)
    elif tid == 'candidate-index':
        import problem_index
        data, errors = problem_index.candidate_data(repo, public(state).parent, exclude_range=state['range'])
        if errors:
            raise f.FlowError('candidate index: ' + '\n'.join(errors))
        from exam_catalog import write_catalog
        catalog_root = root/'catalog'
        catalog = write_catalog(repo, catalog_root)
        if catalog['catalog_sha256'] != data['catalog_sha256']:
            raise f.FlowError('catalog changed during indexing')
        data['catalog_root'] = str(catalog_root)
        f._atomic_json(root/'candidates.json', data)
        files = {p.relative_to(root).as_posix(): p for p in [root/'candidates.json', *catalog_root.rglob('*.json')]}
    else:
        paths = actions.compose_candidate_view(repo, public(state), root, adopted_packs(state, spec))
        bundle = input_bundle(state, spec, root)
        files = {}
        if tid == 'precheck':
            m = f._read(bundle/'manifest.json')
            problems = actions.note_problems(m, paths, state['active_audit'], preliminary=True)
            files = machine_report(state, root, problems, paths.work_file(manifest.note_name(m)), m, paths)
            produced = []
        else:
            produced = actions.candidate_action(dict(state, run=str(bundle)), tid, paths, root,
                                                audit=state.get('active_audit'), explain_run=state.get('explain_run'))
        roster = {p.relative_to(paths.work_pack).as_posix(): f._sha(p) for p in produced}
        extras.update(pack=dict(root=str(paths.work_pack), files=roster), candidate_root=str(paths.work_pack))
        if tid == 'stage-problem-index':
            sealed, sources, per_problem = seal_questions(state, paths, root, f._read(bundle/'manifest.json')['slug'])
            extras.update(questions=[str(p) for p in sorted(sealed.iterdir()) if p.is_file()],
                          source_inputs=file_records(sources))
            if state.get('problem_contract'):
                extras['problem_questions'] = {k: [str(p) for p in v] for k, v in per_problem.items()}
            files['questions.json'] = sealed/'questions.json'
        if tid == 'assemble-note': files['note'], = produced
        if tid == 'build-answers':
            files['pdf'], = produced
            if state.get('approval_contract'):
                files['page-order.json'] = root/'page-order.json'
        if tid == 'explain-verify':
            files['overlay'], = (p for p in produced if p.name == 'answer-overlay.json')
        if tid == 'convert-md':
            extras['converted_assets'] = dict(note=file_records([output(state, 'assemble-note', 'note')])[0],
                                               md=file_records(produced[:1])[0], svgs=file_records(produced[1:]))
    extras['artifacts'] = {key: str(path) for key, path in files.items()}
    evidence = set(files.values()) | set(map(Path, extras.get('questions', [])))
    evidence.update(Path(p) for group in extras.get('problem_questions', {}).values() for p in group)
    for name in extras.get('pack', {}).get('files', {}):
        evidence.add(paths.work_file(name))
    if tid == 'precheck':
        # Browser approval binds every byte served from this assembled review view.
        evidence.update(p for p in paths.work_pack.rglob('*') if p.is_file())
    verified = file_records(evidence)
    for item in verified:
        Path(item['path']).chmod(0o444)
    extras['verified_files'] = verified + extras.get('source_inputs', [])
    return extras


def transact(run, callback):
    """Unrelated concurrent completions may advance the revision before the CAS."""
    for retry in range(24):
        revision = f.load_state(run)['revision']
        try:
            return f.update_state(run, revision, callback)
        except f.FlowError as exc:
            if retry == 23 or ('revision conflict' not in str(exc) and 'lock busy' not in str(exc)):
                raise
            time.sleep(0.01 * (retry + 1))


def same_attempt(state, tid, attempt):
    record = state['actions'].get(tid, {})
    if record.get('attempt') != attempt or record.get('status') != 'running':
        raise f.FlowError('inactive machine attempt')
    spec = spec_for(state, tid)
    if proof(state, spec) != record['input_version']:
        raise f.StaleInputsError('machine inputs superseded')
    return spec


def foreign_reservation():
    # The owner may reconcile its transaction; this claimant may retry afterwards.
    return dict(status='failed', error_code='pending_publication', detail='date reservation belongs to another attempt')


def publish(state, spec, attempt, root, *, recover=False):
    import manifest
    from pack_actions import compose_candidate_view, publication_verifier
    from pack_publication import publish_pack, reconcile_publication
    from pack_paths import PackPaths
    packs = adopted_packs(state, spec)
    files = {name: digest for record in packs.values() for name, digest in record['files'].items()}
    if recover:
        paths = PackPaths(Path(state['repo']), public(state), root/'복습노트'/state['range'])
    else:
        paths = compose_candidate_view(Path(state['repo']), public(state), root, packs)
    final_manifest = f._read(output(state, 'scope-final', 'manifest.json'))
    answer = output(state, 'pdf-qa', 'answer-review.json') if state['selected_ids'] else None
    strict = publication_verifier(final_manifest, paths, state['active_audit'], answer_review=answer)
    def verify(target):
        # This entire state change holds the RUN lock. Recheck external files on both sides.
        fresh = f.inspect_state(Path(state['run']))
        if recover and fresh['status'] == 'recovery_required':
            fresh['status'] = 'ready'
            fresh['actions'][spec.id]['status'] = 'running'
        same_attempt(fresh, spec.id, attempt)
        strict(target)
    if recover:
        result = reconcile_publication(paths, root/'publication/journal.json', verify=verify)
    else:
        result = publish_pack(paths, root, expected=state['public_baseline'], candidate_inventory=files, verify=verify,
                              retire_concept=bool(state.get('concept_contract')))
    if result.get('error_code') == 'pending_publication':
        return foreign_reservation()
    if result['status'] != 'published':
        return dict(status='recovery_required' if result['status'] == 'recovery_required' else 'failed',
                    error_code=result.get('error_code', result['status']), publication_result=result)
    proof_files = [Path(result['journal']), *(paths.public_pack/name for name in files)]
    return dict(status='done', publication_result=result, verified_files=file_records(proof_files))


class InvalidStop(f.FlowError):
    """No durable completion record for this attempt."""


def stopped_candidate(state, tid, attempt, root):
    from pack_receipts import verify_receipt_files
    try:
        record = f._read(root/'stopped.json')
    except f.FlowError as exc:
        raise InvalidStop('stopped completion missing or unreadable') from exc
    if type(record.get('attempt')) is not str or record['attempt'] != attempt:
        raise InvalidStop('stopped completion identity mismatch')
    if record.get('status') not in ('done', 'failed'):
        raise InvalidStop('invalid stopped completion status')
    row = state['actions'][tid]
    if row.get('attempt') != attempt or row.get('attempt_dir') != str(root):
        raise f.FlowError('late machine result')
    # Only matching durable stopped evidence can retire an invalidated owner.
    if row['status'] == 'recovery_required':
        row['status'] = 'running'
    f._current(state)
    superseded = any(f._record(state, dep).get('attempt') != version or not f._done(state, dep)
                     for dep, version in row['input_version'].items())
    if row.get('invalidated_active') or row['status'] == 'stale' or state['stale_inputs'] or superseded:
        row.pop('invalidated_active', None)
        return dict(status='failed', error_code='stale_attempt', detail='discarded stopped attempt')
    same_attempt(state, tid, attempt)
    if record['status'] == 'done' and verify_receipt_files(record):
        raise f.FlowError('completed attempt files changed')
    fields = ('status', 'error_code', 'detail', 'artifacts', 'pack', 'candidate_root', 'questions',
              'problem_questions', 'source_inputs', 'verified_files', 'converted_assets', 'completed_at')
    return {key: record[key] for key in fields if key in record}


def finish(state, tid, attempt, root, result):
    row = state['actions'][tid]
    if row.get('attempt') != attempt:
        raise f.FlowError('late machine result')
    if tid in (findings.MACHINE_REVIEW, 'precheck') and result['status'] == 'done':
        row.update(result)
        report = f._read(output(state, tid, 'check-findings.json'))
        row['candidate_digest'] = report['candidate_digest']
        findings.machine_judgment(state, tid, report['findings'])
        result.update(status=row['status'])
        if row['status'] == 'needs_fix':
            result.update(error_code=row['error_code'], detail=row['artifacts']['check-findings.json'])
    marker = root/'result.json'
    f._atomic_json(marker, dict(result, attempt=attempt, task_id=tid))
    if result['status'] in ('done', 'needs_fix'):
        result['verified_files'] = [*result.get('verified_files', []), *file_records([marker])]
    row.update(result)
    if row['status'] == 'done':
        row.pop('error_code', None)
        row.pop('detail', None)
    if tid == 'convert-md' and row['status'] == 'done':
        state['converted_assets'] = row['converted_assets']
    if tid == 'publish-pack':
        if row['status'] == 'done':
            state['publication'] = row['publication_result']
            state['actions']['final-check'].update(status='done', attempt=attempt, verified_files=row['verified_files'])
            state.update(status='complete', phase=10)
        elif row['status'] == 'recovery_required':
            state['status'] = 'recovery_required'
    f.refresh_tasks(state)
    return state


def run_action(run, tid, *, reconcile=False):
    run = Path(run).resolve()
    state = f.load_state(run)
    if tid not in state['actions'] or tid == 'final-check':
        raise f.FlowError('action not separately runnable: ' + tid)
    lock = run/'attempts'/tid
    lock.mkdir(parents=True, exist_ok=True)
    with f._locked(lock):
        if reconcile:
            return reconcile_attempt(run, tid)
        spec = spec_for(state, tid)
        attempt = str(uuid4())
        root = lock/attempt
        def start(s):
            f._current(s)
            current = spec_for(s, tid)
            version = proof(s, current)
            row = s['actions'][tid]
            if row['status'] in ('done', 'running', 'needs_fix', 'recovery_required') or row.get('invalidated_active'):
                raise f.FlowError('machine action already active or complete')
            root.mkdir(exist_ok=False)
            if row.get('attempt'):
                row.setdefault('history', []).append({k:v for k,v in row.items() if k != 'history'})
            s['actions'][tid] = dict(id=tid, dependencies=row['dependencies'], history=row.get('history', []),
                                     attempt=attempt, attempt_dir=str(root), status='running', input_version=version,
                                     stdout_path=str(root/'stdout.log'))
            return s
        state = transact(run, start)
        def commit(s):
            try:
                if tid == 'publish-pack':
                    f._current(s)
                    result = publish(s, same_attempt(s, tid, attempt), attempt, root)
                else:
                    result = stopped_candidate(s, tid, attempt, root)
            except InvalidStop as exc:
                result = dict(status='recovery_required', error_code='unverified_stop', detail=str(exc))
            except (ValueError, OSError, KeyError) as exc:
                interrupted = tid == 'publish-pack' and (root/'publication/journal.json').is_file()
                result = dict(status='recovery_required' if interrupted else 'failed',
                              error_code='publication_interrupted' if interrupted else getattr(exc, 'error_code', 'validation_failed'), detail=str(exc))
            return finish(s, tid, attempt, root, result)
        if tid != 'publish-pack':
            try:
                outputs = execute_action(state, spec, root)
                result = dict(status='done', **outputs)
            except Exception as exc:
                result = dict(status='failed', error_code='execution_failed', detail=str(exc))
            f._atomic_json(root/'stopped.json', dict(result, attempt=attempt, task_id=tid, input_version=state['actions'][tid]['input_version'], completed_at=f.utc_now()))
        return transact(run, commit)['actions'][tid]


def reconcile_attempt(run, tid):
    """Only adopt stopped candidate work or reconcile this attempt's own journal."""
    def apply(s):
        row = s['actions'][tid]
        if not row.get('attempt_dir') or (
                row.get('status') not in ('running', 'recovery_required', 'stale') and not row.get('invalidated_active')):
            raise f.FlowError('no interrupted attempt')
        root = Path(row['attempt_dir'])
        attempt = row['attempt']
        if tid == 'publish-pack':
            own_journal = root/'publication/journal.json'
            previous = row.get('publication_result', {})
            if (previous.get('error_code') == 'pending_publication' and previous.get('journal')
                    and Path(previous['journal']) != own_journal and not own_journal.exists()):
                # Earlier trial records counted a foreign reservation as local recovery.
                row.pop('publication_result')
                s['status'] = 'ready'
                result = foreign_reservation()
            else:
                result = publish(s, spec_for(s, tid), attempt, root, recover=True)
                if result.get('publication_result', {}).get('status') == 'restored':
                    s['status'] = 'ready'
        else:
            result = stopped_candidate(s, tid, attempt, root)
        return finish(s, tid, attempt, root, result)
    return transact(run, apply)['actions'][tid]
