"""Private attempts and durable handoffs for the explicit review-pack graph."""
from pathlib import Path
from uuid import uuid4
import hashlib
import tempfile
import shutil
import subprocess
import sys
import time

import pack_flow as f
from pack_graph import task_specs


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
    if state.get('stale_inputs') or state['status'] in ('blocked', 'withheld', 'recovery_required'):
        raise f.FlowError('RUN lacks current source or authorization')
    version = {}
    for tid, rec in ancestors(state, spec).items():
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


def worker_inputs(state, spec):
    row = f._record(state, 'stage-problem-index')
    if spec.id in ('explain-blind', 'explain-author'):
        return file_records(Path(p) for p in row['questions'])
    paths = set(state['hashes'])
    for dep in spec.dependencies:
        row = f._record(state, dep)
        if dep == 'source-prep':
            paths.update(x['path'] for x in row['receipt']['verified_files']
                         if Path(x['path']).is_relative_to(Path(state['repo'])))
        paths.update(row.get('artifacts', {}).values())
        if adopted := row.get('pack'):
            paths.update(str(local_path(adopted['root'], name)) for name in adopted['files'])
    return file_records(paths)


def claim_worker(state, task):
    from pack_receipts import standalone_screenshots
    spec = spec_for(state, task['id'])
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
    data = dict(workflow='parallel', run_id=state['run_id'], role=role, task_id=spec.id,
                range=state['range'], attempt=attempt, run=str(root), targets=task['targets'],
                inputs=worker_inputs(state, spec), allowed_outputs=list(required), required_outputs=required,
                allowed_output_roots=[str(root)], report=str(review), receipt=str(root/'receipt.json'),
                request_paths=task.get('request_paths', []))
    if role in ('explain-author', 'explain-blind'):
        data['questions'] = str(output(state, 'stage-problem-index', 'questions.json'))
        data['instruction'] = ('Use only the sealed question text and figures. Submit independent.json with items '
                               'keyed by pN:subpart, method, conclusion and evidence.' if role == 'explain-blind'
                               else 'Write one child explanation HTML fragment per problem using the sealed question and figures.')
    else:
        repo = Path(state['repo'])
        refs = repo / '.claude/skills/ec2-review-pack/references'
        data.update(repo=str(repo), snapshot=str(snapshot), profile=str(repo / f._read(snapshot)['path']),
                    profile_read='전체 필수', references=[str(refs / ref) for ref, _ in f._REFERENCES[role]],
                    constraints=['Read the complete profile and referenced review criteria. Perform the actual inspection.'])
    if role == 'scope-draft':
        data['instruction'] = ('Freeze the scope, slug, section and topic IDs and complete author briefs in manifest.sections. '
                               'List sections needing final problem links in link_sections.')
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
    if role in ('style-audit', 'content-review', 'browser-qa', 'standalone-svg-qa'):
        data['manifest'] = str(output(state, 'scope-final', 'manifest.json'))
        data['note'] = str(output(state, 'assemble-note', 'note'))
        data['inputs'] = file_records([*(Path(x['path']) for x in data['inputs']), Path(data['note']), Path(data['manifest'])])
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
        data['inputs'] = file_records([*(Path(x['path']) for x in data['inputs']), Path(data['overlay'])])
    if role == 'child-coordinator':
        state['explain_run'] = str(root / 'child')
        data.update(explain_run=state['explain_run'], manifest=str(output(state, 'selection', 'manifest.json')),
                    candidate_pack=state['actions']['stage-problem-index']['pack']['root'],
                    public_pack=str(public(state)), snapshot=str(snapshot),
                    instruction='Extract against this candidate pack and slug. Use the accepted fragments and independent results. Complete all child reviews.')
    path = root / 'brief.json'
    f._atomic_json(path, data)
    task.update(attempt=attempt, attempt_dir=str(root), brief=str(path), brief_sha256=f._sha(path),
                input_version=version, status='claimed', agent_id=None, receipt=None)


def scope_manifest(state, data):
    import manifest
    sections = data.get('sections')
    if (data.get('range') != state['range'] or not manifest.SLUG_RE.fullmatch(data.get('slug', ''))
            or not isinstance(sections, list) or not sections):
        raise f.FlowError('stable date, slug and nonempty sections required')
    ids = []
    for sec in sections:
        if not isinstance(sec.get('topics'), list) or not sec['topics']:
            raise f.FlowError('stable topic IDs required')
        ids.extend([sec['id'], *(t['id'] for t in sec['topics'])])
    if len(ids) != len(set(ids)) or any(not manifest.ID_RE.fullmatch(x) for x in ids):
        raise f.FlowError('invalid or duplicate section/topic IDs')
    if set(data.get('link_sections', [])) - {s['id'] for s in sections}:
        raise f.FlowError('unknown problem-link section')
    return sections


def check_selection(state, root):
    import problem_index
    m = f._read(root / 'manifest.json')
    scope = f._read(output(state, 'scope-draft', 'manifest.json'))
    if (m.get('range'), m.get('slug')) != (scope['range'], scope['slug']):
        raise f.FlowError('selection changed frozen scope')
    candidates = f._read(output(state, 'candidate-index', 'candidates.json'))
    live, errors = problem_index.candidate_data(Path(state['repo']), public(state).parent, exclude_range=state['range'])
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
    return [dict(path=p, sha256=h) for p, h in sorted(verified.items())]


def check_leaf_join(state, child_root):
    child = f._read(child_root / 'child-receipt.json')
    author = state['tasks']['explain-author']
    folder = child_root / child['bucket']
    for name in spec_for(state, 'explain-author').outputs:
        if f._sha(output(state, 'explain-author', name)) != f._sha(local_path(folder, name)):
            raise f.FlowError('child replaced accepted author fragment')
    items = f._read(output(state, 'explain-blind', 'independent.json'))['items']
    reviewed = f._read(folder / 'review.json')['independent']['items']
    if set(items) != set(reviewed) or any(any(reviewed[k].get(field) != val for field, val in item.items())
                                          for k, item in items.items()):
        raise f.FlowError('child independent review differs from accepted blind solution')
    if any(agent != author['agent_id'] for agent in child['reviewers']['authors'].values()):
        raise f.FlowError('child author identity mismatch')


def validate_worker(state, task, receipt_path):
    from pack_receipts import validate_receipt
    spec = spec_for(state, task['id'])
    if proof(state, spec) != task['input_version']:
        raise f.FlowError('frozen worker inputs superseded')
    receipt = validate_receipt(state, task, receipt_path)
    if receipt['task_status'] != 'done':
        return receipt
    root = Path(task['attempt_dir'])
    role = task['role']
    if role == 'scope-draft':
        scope_manifest(state, f._read(root / 'manifest.json'))
    if role == 'selection':
        receipt['verified_files'].extend(check_selection(state, root))
    if role == 'scope-final':
        import manifest
        m = manifest.load(root / 'manifest.json', repo=Path(state['repo']))
        selected = f._read(output(state, 'selection', 'manifest.json'))
        if m['range'] != state['range'] or m.get('selection_policy') != selected.get('selection_policy'):
            raise f.FlowError('scope-final date or policy differs from frozen selection')
        if (m['slug'], m['problems'], m['sections']) != (selected['slug'], selected['problems'], state['scope_sections']):
            raise f.FlowError('final links changed accepted selection or section brief')
    if role in ('explain-author', 'explain-blind'):
        if not task.get('agent_id'):
            raise f.FlowError('bound leaf reviewer identity required')
        other = state['tasks']['explain-blind' if role == 'explain-author' else 'explain-author']
        if other.get('agent_id') == task['agent_id']:
            raise f.FlowError('independent solver must differ from author')
    if role == 'explain-blind':
        questions = f._read(output(state, 'stage-problem-index', 'questions.json'))['problems']
        keys = {p['id'] + ':' + sub for p in questions for sub in p['subparts']}
        items = f._read(root/'independent.json')['items']
        if set(items) != keys or any(item.get('reviewer') != task['agent_id'] or
                not all(isinstance(item.get(k), str) and item[k].strip() for k in ('method', 'conclusion', 'evidence'))
                for item in items.values()):
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


def adopt_worker(state, task, receipt):
    task.update(status=receipt['task_status'], receipt=receipt)
    if task['status'] != 'done':
        return
    root = Path(task['attempt_dir'])
    dst = Path(state['run']) / 'adopted' / task['id'] / str(uuid4())
    verified = {x['path']: x['sha256'] for x in receipt['verified_files']}
    # Child receipt/run semantics use absolute paths; its validated files remain hash-bound.
    owned = [Path(x['path']) for x in receipt['outputs']]
    owned.extend(Path(x) for x in (receipt['report'], *receipt['reviews']))
    if task['role'] == 'pdf-qa':
        owned.extend(Path(x) for x in verified if Path(x).is_relative_to(root / 'answer-pages'))
    task['artifacts'] = freeze_files(root, sorted(set(owned)), verified, dst)
    receipt['verified_files'].extend(file_records(Path(p) for p in task['artifacts'].values()))
    if task['role'] == 'scope-draft':
        m = f._read(dst / 'manifest.json')
        state['scope_sections'] = scope_manifest(state, m)
        link_topics = {link['topic'] for link in m.get('links', [])}
        state['link_sections'] = sorted(set(m.get('link_sections', [])) | {
            s['id'] for s in m['sections'] if any(t['id'] in link_topics for t in s['topics'])})
    if task['role'] == 'selection':
        state['selected_ids'] = [q['id'] for q in f._read(dst / 'manifest.json')['problems']]
    if task['role'] == 'style-audit':
        state['active_audit'] = str(dst / 'learning-style-audit-note.json')



def accept_worker(run, tid, attempt, receipt_path):
    from pack_receipts import verify_receipt_files
    snapshot = f.inspect_state(run)
    task = snapshot['tasks'][tid]
    f._attempt(task, attempt)
    receipt = validate_worker(snapshot, task, receipt_path)
    adopt_worker(snapshot, task, receipt)
    def apply(current):
        f._current(current)
        row = current['tasks'][tid]
        f._attempt(row, attempt)
        version = proof(current, spec_for(current, tid))
        if version != task['input_version'] or verify_receipt_files(receipt):
            raise f.FlowError('worker input or file version changed during adoption')
        row.update(status=task['status'], receipt=receipt)
        if row['status'] == 'done':
            row['artifacts'] = task['artifacts']
            keys = {'scope-draft': ('scope_sections', 'link_sections'), 'selection': ('selected_ids',),
                    'style-audit': ('active_audit',)}.get(tid, ())
            for key in keys:
                current[key] = snapshot[key]
        return f.refresh_tasks(current)
    return transact(run, apply)


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
    for problem in source['problems']:
        item = {key: problem[key] for key in ('id', 'workbook_id', 'subparts', 'title', 'original_html',
                                              'conditions_html', 'ask_html')}
        item['figures'] = []
        for i, markup in enumerate(problem['figures_html']):
            img = ET.fromstring(markup.replace('></figure>', '/></figure>')).find('img')
            src = paths.link(paths.public_pack, unquote(img.attrib['src']))
            name = f"{item['id']}-figure-{i+1}{src.suffix}"
            shutil.copyfile(src, sealed/name)
            item['figures'].append(name)
        problems.append(item)
    f._atomic_json(sealed/'questions.json', dict(problems=problems))
    inputs = [paths.source_file(p) for p in source['inputs']]
    digest = hashlib.sha256(''.join(f._sha(p) for p in inputs).encode()).hexdigest()
    if digest != source['sha256']:
        raise f.FlowError('question inputs changed during extraction')
    return sealed, inputs


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


def execute_action(state, spec, root):
    import manifest
    import pack_actions as actions
    tid = spec.id
    repo = Path(state['repo'])
    extras = {}
    if tid == 'render-preflight':
        from render import render_preflight
        result = render_preflight(root)
        result['pdf'] = str(result['pdf']) if result['pdf'] else None
        f._atomic_json(root/'render-preflight.json', result)
        if result['status'] != 'pass':
            raise f.FlowError(result['error_code'] or 'render preflight failed')
        files = {'render-preflight.json': root/'render-preflight.json', 'render-preflight.pdf': Path(result['pdf'])}
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
        produced = actions.candidate_action(dict(state, run=str(bundle)), tid, paths, root,
                                            audit=state.get('active_audit'), explain_run=state.get('explain_run'))
        roster = {p.relative_to(paths.work_pack).as_posix(): f._sha(p) for p in produced}
        extras.update(pack=dict(root=str(paths.work_pack), files=roster), candidate_root=str(paths.work_pack))
        if tid == 'stage-problem-index':
            sealed, sources = seal_questions(state, paths, root, f._read(bundle/'manifest.json')['slug'])
            extras.update(questions=[str(p) for p in sorted(sealed.iterdir())],
                          source_inputs=file_records(sources))
            files['questions.json'] = sealed/'questions.json'
        if tid == 'assemble-note': files['note'], = produced
        if tid == 'build-answers': files['pdf'], = produced
        if tid == 'explain-verify':
            files['overlay'], = (p for p in produced if p.name == 'answer-overlay.json')
        if tid == 'convert-md':
            extras['converted_assets'] = dict(note=file_records([output(state, 'assemble-note', 'note')])[0],
                                               md=file_records(produced[:1])[0], svgs=file_records(produced[1:]))
    extras['artifacts'] = {key: str(path) for key, path in files.items()}
    evidence = set(files.values()) | set(map(Path, extras.get('questions', [])))
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
        raise f.FlowError('machine inputs superseded')
    return spec


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
        result = publish_pack(paths, root, expected=state['public_baseline'], candidate_inventory=files, verify=verify)
    if result['status'] != 'published':
        return dict(status='recovery_required' if result['status'] == 'recovery_required' else 'failed',
                    error_code=result.get('error_code', result['status']), publication_result=result)
    proof_files = [Path(result['journal']), *(paths.public_pack/name for name in files)]
    return dict(status='done', publication_result=result, verified_files=file_records(proof_files))


def finish(state, tid, attempt, root, result):
    row = state['actions'][tid]
    if row.get('attempt') != attempt:
        raise f.FlowError('late machine result')
    if result['status'] == 'done':
        marker = root/'result.json'
        f._atomic_json(marker, result)
        result['verified_files'] = [*result.get('verified_files', []), *file_records([marker])]
    else:
        f._atomic_json(root/'result.json', result)
    row.update(result)
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
    from pack_receipts import verify_receipt_files
    run = Path(run).resolve()
    state = f.load_state(run)
    spec = spec_for(state, tid)
    if spec.kind != 'action' or tid == 'final-check':
        raise f.FlowError('action not separately runnable: ' + tid)
    lock = run/'attempts'/tid
    lock.mkdir(parents=True, exist_ok=True)
    with f._locked(lock):
        if reconcile:
            return reconcile_attempt(run, tid)
        attempt = str(uuid4())
        root = lock/attempt
        def start(s):
            f._current(s)
            current = spec_for(s, tid)
            version = proof(s, current)
            row = s['actions'][tid]
            if row['status'] in ('done', 'running', 'recovery_required') or row.get('invalidated_active'):
                raise f.FlowError('machine action already active or complete')
            root.mkdir(exist_ok=False)
            if row.get('attempt'):
                row.setdefault('history', []).append({k:v for k,v in row.items() if k != 'history'})
            row.update(attempt=attempt, attempt_dir=str(root), status='running', input_version=version,
                       stdout_path=str(root/'stdout.log'))
            return s
        state = transact(run, start)
        def commit(s):
            try:
                f._current(s)
                spec = same_attempt(s, tid, attempt)
                result = publish(s, spec, attempt, root) if tid == 'publish-pack' else f._read(root/'stopped.json')
                if result['status'] == 'done' and verify_receipt_files(result):
                    raise f.FlowError('completed attempt files changed')
            except (ValueError, OSError, KeyError) as exc:
                interrupted = tid == 'publish-pack' and (root/'publication/journal.json').is_file()
                result = dict(status='recovery_required' if interrupted else 'failed',
                              error_code='publication_interrupted' if interrupted else 'validation_failed', detail=str(exc))
            return finish(s, tid, attempt, root, result)
        if tid != 'publish-pack':
            try:
                outputs = execute_action(state, spec, root)
                result = dict(status='done', **outputs)
            except Exception as exc:
                result = dict(status='failed', error_code='execution_failed', detail=str(exc))
            f._atomic_json(root/'stopped.json', dict(result, attempt=attempt))
        return transact(run, commit)['actions'][tid]


def reconcile_attempt(run, tid):
    """Only adopt stopped candidate work or reconcile this attempt's own journal."""
    def apply(s):
        row = s['actions'][tid]
        if row.get('status') not in ('running', 'recovery_required', 'stale') or not row.get('attempt_dir'):
            raise f.FlowError('no interrupted attempt')
        root = Path(row['attempt_dir'])
        attempt = row['attempt']
        if tid == 'publish-pack':
            result = publish(s, spec_for(s, tid), attempt, root, recover=True)
            if result.get('publication_result', {}).get('status') == 'restored':
                s['status'] = 'ready'
        else:
            f._current(s)
            same_attempt(s, tid, attempt)
            result = f._read(root/'stopped.json')
            from pack_receipts import verify_receipt_files
            if result.get('attempt') != attempt or verify_receipt_files(result):
                raise f.FlowError('stopped result does not match current attempt')
        return finish(s, tid, attempt, root, result)
    return transact(run, apply)['actions'][tid]
