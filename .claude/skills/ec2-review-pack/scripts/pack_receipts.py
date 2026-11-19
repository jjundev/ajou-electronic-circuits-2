"""File handoffs bind existing review records; they do not grant publication."""
import hashlib
import json
from pathlib import Path
import sys
from pack_flow import FlowError, nfc_path, within

ROLE_OUTPUTS = {
    'source-prep': ('source-map.json', 'slides.txt'), 'stt': ('summaries/stt-{target}.md',),
    'scope-draft': ('scope.json', 'work/scope-draft/manifest.json'), 'scope-final': ('manifest.json', 'briefs/{target}.json'),
    'selection': ('candidates.json', 'catalog.json', 'selection.json', 'selection-review.json', 'display-titles.json', 'work/selection/manifest.json'),
    'author': ('sections/{target}.html',), 'style-audit': ('work/style-audit/learning-style-audit-note.json',),
    'content-review': (), 'browser-qa': ('work/browser/report.json',),
    'standalone-svg-qa': ('work/standalone-svg-qa/report.json', 'work/standalone-svg-qa/report.md'),
    'explain-author': (), 'explain-blind': (), 'child-coordinator': (), 'pdf-qa': ('answer-review.json', 'answer-review.md')}


def require(ok, message):
    if not ok: raise FlowError(message)


def obj(path):
    value = json.loads(Path(path).read_text(encoding='utf-8'))
    require(isinstance(value, dict), 'JSON object required: ' + str(path))
    return value


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def records(items, roots):
    require(isinstance(items, list), 'file records must be a list')
    result = {}
    for item in items:
        require(isinstance(item, dict) and isinstance(item.get('path'), str), 'invalid file record')
        path = Path(item['path'])
        require(path.is_absolute(), 'absolute file path required')
        path = nfc_path(path.resolve())
        require(any(within(path, root) for root in roots), 'file outside allowed roots: ' + str(path))
        require(str(path) not in result and path.is_file(), 'missing or duplicate file: ' + str(path))
        require(item.get('sha256') == sha(path), 'file hash changed: ' + str(path))
        result[str(path)] = item['sha256']
    return result


def verify_receipt_files(receipt: dict) -> list[str]:
    errors = []
    for item in receipt.get('verified_files', receipt.get('inputs', []) + receipt.get('outputs', [])):
        try:
            if sha(item['path']) != item['sha256']: errors.append('changed: ' + item['path'])
        except (OSError, KeyError, TypeError) as exc: errors.append(str(exc))
    return errors


def _png(path):
    from PIL import Image
    try:
        with Image.open(path) as image:
            require(image.format == 'PNG' and min(image.size) > 0, 'PNG image required')
            image.verify()
        with Image.open(path) as image: image.load()
    except (OSError, ValueError) as exc:
        raise FlowError('invalid PNG: ' + str(path)) from exc


def _pdf_pages(path):
    try:
        import pymupdf
        with pymupdf.open(path) as document:
            require(document.is_pdf and len(document) > 0 and not document.needs_pass, 'actual readable PDF required')
            for page in document: page.get_text()
            return len(document)
    except ImportError:
        from pypdf import PdfReader
        document = PdfReader(path)
        require(not document.is_encrypted and len(document.pages) > 0, 'actual readable PDF required')
        return len(document.pages)
    except (OSError, ValueError, RuntimeError) as exc:
        raise FlowError('invalid PDF: ' + str(path)) from exc


def _source(state, run):
    source = obj(run / 'source-map.json')
    sessions = source.get('sessions')
    require(source.get('schema_version') == 1 and isinstance(sessions, list), 'invalid source-map')
    require(len(sessions) == len(state['sessions']) and {x['date'] for x in sessions} == set(state['sessions']), 'source-map dates mismatch')
    repo = Path(state['repo'])
    for session in sessions:
        require(session.get('status') in ('ready', 'missing') and isinstance(session.get('missing'), list), 'invalid material status')
        if session['status'] == 'missing': return 'blocked'
        require(not session['missing'] and session.get('pdfs'), 'required PDF material missing')
        stt = Path(session['stt'])
        require(stt.name[:4] == session['date'] and str(nfc_path(stt.resolve())) in state['hashes'], 'STT date/frozen source mismatch')
        for path in [stt, *map(Path, session['pdfs'])]:
            require(path.is_absolute() and within(path.resolve(), repo) and path.is_file(), 'source material missing/outside REPO')
        for path in session['pdfs']: _pdf_pages(path)
    return 'done'


def _audit_output(brief, role, run):
    """Optional controller-frozen audit revision; receipts cannot select a path."""
    if 'audit_output' not in brief: return None
    path = Path(brief['audit_output'])
    root = (run if brief.get('workflow') == 'parallel' else run / 'work' / role / 'audits').resolve()
    require(path.is_absolute() and root.is_relative_to(run.resolve()) and
            path.resolve().is_relative_to(root) and path.name == 'learning-style-audit-note.json',
            'audit output must be an absolute role-owned revision path')
    path = path.resolve()
    require(str(path) in {str(Path(p).resolve()) for p in brief.get('allowed_outputs', [])},
            'audit output must be explicitly declared')
    require(str(path) not in {str(Path(x['path']).resolve()) for x in brief['inputs']},
            'audit output must differ from every frozen input')
    return path


def _audit(state, task, run):
    sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'workbook'))
    from learning_style import validate_style_audit
    targets = task['targets']
    brief = obj(task['brief'])
    parallel = state.get('workflow') == 'parallel'
    manifest_path = Path(brief['manifest']) if parallel else run / 'manifest.json'
    if manifest_path.is_file():
        targets = [topic['id'] for section in obj(manifest_path)['sections'] for topic in section['topics']]
        require(set(targets) == set(task['targets']), 'audit task omits actual manifest topics')
    audit_path = _audit_output(brief, task['role'], run) or run / ('work/style-audit/learning-style-audit-note.json' if task['role'] == 'style-audit' else 'work/content-review/learning-style-audit-note.json')
    if task['role'] == 'content-review' and not audit_path.is_file():
        brief = obj(task['brief'])
        audit_path = Path(brief['audit'])
        require(str(audit_path.resolve()) in {str(Path(x['path']).resolve()) for x in brief['inputs']}, 'active audit must be frozen input')
    snapshot = Path(brief['snapshot']) if parallel else run / 'learning-style.json'
    audit = obj(audit_path)
    errors = validate_style_audit(audit, obj(snapshot), targets)
    if parallel and not errors:
        require(all(i['reviewer'] == task.get('agent_id') for i in audit['items'].values()),
                'audit judgments require the bound reviewer identity')
    require(not errors, 'style audit: ' + '; '.join(errors))
    return audit_path.resolve()


def _pdf(brief, run):
    from publish_answer import _review
    pdf, overlay_path = Path(brief['pdf']), Path(brief['overlay'])
    review_path = run / 'answer-review.json'
    review = _review(review_path, pdf, overlay_path, obj(overlay_path))
    count = _pdf_pages(pdf)
    images = {str(p.resolve()) for p in (run / 'answer-pages').glob('page-*.png')}
    evidence = {str((run / x['path']).resolve()) for x in review['evidence'] if Path(x['path']).suffix.lower() == '.png'}
    expected = {str((run / 'answer-pages' / ('page-' + str(n).zfill(len(str(count))) + '.png')).resolve()) for n in range(1, count + 1)}
    require(images == evidence == expected, 'all actual PDF pages required')
    report = Path(brief.get('report', run / 'answer-review.md')).resolve()
    require(str(report) in {str((run / x['path']).resolve()) for x in review['evidence']}, 'PDF brief report evidence required')
    for path in images: _png(path)
    return [pdf, overlay_path, *[(run / x['path']).resolve() for x in review['evidence']]]


def standalone_screenshots(run, targets):
    return {target: str(Path(run) / 'work/standalone-svg-qa/screenshots' / f'svg-{i:04d}.png')
            for i, target in enumerate(sorted(targets), 1)}


def _standalone_svg(state, task, brief, inputs, outputs, report, reviews):
    from pack_flow import _converted_assets
    converted = _converted_assets(state)
    targets = [x['path'] for x in converted['svgs']]
    require(targets and task['targets'] == targets, 'standalone SVG target inventory mismatch')
    required = [converted['note'], converted['md'], *converted['svgs']]
    require(all(inputs.get(x['path']) == x['sha256'] for x in required), 'standalone current MD/SVG/note inputs required')
    run = Path(task.get('attempt_dir', state['run']))
    root = run / 'work/standalone-svg-qa'
    require(report == (root / 'report.md').resolve() and str((root / 'report.json').resolve()) in
            {str(Path(p).resolve()) for p in reviews}, 'standalone report paths required')
    screens = standalone_screenshots(run, targets)
    require(brief.get('svg_screenshots') == screens, 'standalone screenshot contract mismatch')
    require(set(screens.values()) <= outputs.keys(), 'standalone screenshot evidence required for every SVG')
    for path in screens.values(): _png(path)


def validate_receipt(state: dict, task: dict, receipt_path: Path) -> dict:
    try:
        run, repo = nfc_path(Path(state['run']).resolve()), nfc_path(Path(state['repo']).resolve())
        parent_run = run
        if state.get('workflow') == 'parallel':
            run = nfc_path(Path(task['attempt_dir']).resolve())
            require(within(run, parent_run), 'attempt outside RUN')
        receipt_path = nfc_path(Path(receipt_path).resolve())
        require(within(receipt_path, run), 'receipt outside RUN')
        receipt = obj(receipt_path)
        require(receipt.get('schema_version') == 1 and receipt.get('run_id') == state['run_id'] and receipt.get('task_id') == task['id'] and receipt.get('attempt') == task['attempt'], 'receipt identity mismatch')
        status = receipt.get('status')
        require(status in ('done', 'needs-fix', 'blocked', 'ready-for-publish', 'withheld'), 'invalid receipt status')
        require(isinstance(receipt.get('unresolved'), list) and isinstance(receipt.get('counts'), dict), 'counts/unresolved required')
        require(status not in ('done', 'ready-for-publish') or not receipt['unresolved'], 'unresolved successful receipt')
        brief = obj(task['brief'])
        expected = records(brief['inputs'], [repo, parent_run])
        inputs = records(receipt['inputs'], [repo, parent_run])
        require(inputs == expected, 'receipt must include all frozen brief inputs')
        outputs = records(receipt['outputs'], [run])
        allowed = {str(nfc_path(Path(p).resolve())) for p in brief.get('allowed_outputs', [])}
        roots = [nfc_path(Path(p).resolve()) for p in brief.get('allowed_output_roots', [])]
        require(all(within(p, run) and p != parent_run and not within(repo, p) for p in roots), 'invalid output root')
        require(all(p in allowed or any(within(p, root) for root in roots) for p in outputs), 'receipt expands allowed outputs')
        role = task['role']
        require(role in ROLE_OUTPUTS, 'unknown role')
        required = {str(nfc_path((run / pattern.format(target=target)).resolve())) for pattern in ROLE_OUTPUTS[role] for target in task['targets']}
        if state.get('workflow') == 'parallel':
            required = set(brief['required_outputs'])
            require(all(within(p, run) for p in required), 'required output outside attempt')
        if role in ('style-audit', 'content-review'):
            audit_output = _audit_output(brief, role, run)
            if role == 'style-audit' and audit_output is not None: required = {str(audit_output)}
        if status in ('done', 'ready-for-publish'): require(required <= outputs.keys(), 'required role outputs missing')
        report = nfc_path(Path(receipt['report']).resolve())
        require(within(report, run) and report.is_file(), 'report missing/outside RUN')
        reviews = receipt['reviews']
        require(isinstance(reviews, list), 'review paths required')
        verified = dict(inputs, **outputs)
        for path in [receipt_path, report, *map(Path, reviews)]:
            path = nfc_path(path.resolve())
            require(within(path, run) and path.is_file(), 'review evidence missing/outside RUN')
            verified[str(path)] = sha(path)
        if state.get('workflow') == 'parallel':
            from pack_findings import REVIEW_ROLES, blocking_findings
            if role in REVIEW_ROLES and status in ('done', 'ready-for-publish', 'needs-fix'):
                require(report == Path(brief['report']).resolve(), 'review report must match the claimed brief')
                declared = {(r.get('severity'), r.get('target')) for r in receipt['unresolved'] if isinstance(r, dict)}
                require(set(blocking_findings(report)) <= declared, 'blocking report findings missing from receipt')
                if status == 'needs-fix' and role in ('browser-qa', 'pdf-qa', 'standalone-svg-qa'):
                    screens = [p for p in outputs if Path(p).suffix.lower() == '.png']
                    require(screens, 'actual screenshot required for a visual finding')
                    for p in screens: _png(p)
        task_status = {'needs-fix': 'needs_fix', 'withheld': 'blocked'}.get(status, 'done' if status == 'ready-for-publish' else status)
        if status in ('done', 'ready-for-publish'):
            if role == 'selection':
                titles = obj(run / 'display-titles.json')
                selected = obj(run / ('manifest.json' if state.get('workflow') == 'parallel' else 'work/selection/manifest.json'))
                require(set(titles) == {q['id'] for q in selected['problems']}
                        and all(isinstance(v, str) and v.strip() for v in titles.values()),
                        'display title map must match selected IDs with nonempty titles')
            if role == 'source-prep':
                task_status = _source(state, run)
                for session in obj(run / 'source-map.json')['sessions']:
                    for path in [session.get('stt'), *session.get('pdfs', [])]:
                        if path and Path(path).is_file(): verified[str(nfc_path(Path(path).resolve()))] = sha(path)
            if role in ('style-audit', 'content-review'):
                audit_path = _audit(state, task, run)
                require(str(nfc_path(audit_path)) in verified, 'audit must be declared frozen input or owned output')
            if role == 'pdf-qa':
                require(report == Path(brief['report']).resolve(), 'PDF report must match brief')
                for path in _pdf(brief, run):
                    require(within(path.resolve(), parent_run), 'PDF evidence outside RUN')
                    verified[str(nfc_path(path.resolve()))] = sha(path)
            if role == 'child-coordinator': _child(state, brief, receipt, verified)
            if role == 'standalone-svg-qa':
                _standalone_svg(state, task, brief, inputs, outputs, report, reviews)
                coverage = receipt['counts'].get('targets')
                require(isinstance(coverage, list) and len(coverage) == len(task['targets']) and
                        set(coverage) == set(task['targets']), 'standalone review target coverage mismatch')
            if role in ('content-review', 'browser-qa'):
                require(reviews, 'existing review evidence required')
                require(set(receipt['counts'].get('targets', [])) == set(task['targets']), 'review target coverage mismatch')
                if role == 'browser-qa':
                    screens = [path for path in outputs if Path(path).suffix.lower() == '.png']
                    require(screens, 'actual browser screenshot evidence required')
                    for path in screens: _png(path)
        return dict(receipt, task_status=task_status, verified_files=[{'path': p, 'sha256': h} for p, h in verified.items()])
    except FlowError: raise
    except (OSError, ValueError, KeyError, TypeError, AttributeError, ImportError, RuntimeError) as exc:
        raise FlowError('invalid receipt: ' + str(exc)) from exc


def _child(state, brief, receipt, verified):
    """Read the genuine child runtime state without calling its publisher."""
    scripts = Path(__file__).resolve().parents[2] / 'ec2-problem-explain/scripts'
    # The child modules import workbook's assemble.py; this scripts folder has its own
    # assemble.py, so put workbook first and hide our module while they load.
    workbook = Path(__file__).resolve().parents[4] / 'workbook'
    ours = sys.modules.pop('assemble', None)
    sys.path[:0] = [str(scripts), str(workbook)]
    try:
        from epe_cli import load_run, load_fragments, load_artifacts
        from epe_contract import validate_reviews, payload_hash, validate_fragment
        from epe_render import artifact_hashes, check_artifacts
        from epe_core import make_overlay
        from epe_rerender import verified_references
    finally:
        if ours is not None: sys.modules['assemble'] = ours
    child_run = nfc_path(Path(state['explain_run']).resolve())
    require(within(child_run, Path(state['run']).resolve()), 'child RUN outside parent RUN')
    child_path = child_run / 'child-receipt.json'
    child = obj(child_path)
    require(child.get('schema_version') == 1 and child.get('status') == 'ready-for-publish' and not child.get('unresolved'), 'child is not ready')
    require(nfc_path(Path(child['run']).resolve()) == child_run and child['range'] == state['range'], 'child identity mismatch')
    files = records(child['files'], [Path(state['repo']).resolve(), child_run, Path(state['run']).resolve()])
    required = {str(Path(brief['manifest']).resolve()), str(Path(brief.get('snapshot', Path(state['run']) / 'learning-style.json')).resolve()), str((child_run / 'run.json').resolve())}
    items = load_run(child_run)
    require(len(items) == 1, 'one child bucket required for parent pack')
    for item in items:
        folder, pack = item['folder'], item['pack']
        parent = obj(brief['manifest'])
        require(Path(item['repo']).resolve() == Path(state['repo']).resolve(), 'child parent REPO mismatch')
        require(pack.range == parent['range'] == state['range'] and pack.slug == parent['slug'] == child['slug'], 'child parent identity mismatch')
        require([p.workbook_id for p in pack.problems] == [p['id'] for p in parent['problems']], 'child parent problem IDs/order mismatch')
        expected_source = Path(state['repo']) / '복습노트' / parent['range'] / '.assets/problems.txt'
        require(pack.path.resolve() == expected_source.resolve(), 'child parent source mismatch')
        snapshot = obj(Path(state['run']) / 'learning-style.json')
        parent_style = parent.get('learning_style', snapshot) if state.get('workflow') == 'parallel' else parent['learning_style']
        require(pack.learning_style == parent_style == snapshot, 'child parent style mismatch')
        fragments, artifacts = load_fragments(item), load_artifacts(item)
        review_path = folder / 'review.json'
        reviews = obj(review_path)
        machine = obj(folder / 'machine.json')
        require(machine.get('status') == 'pass' and machine.get('errors') == [] and machine.get('artifact_hashes') == artifact_hashes(artifacts), 'child machine evidence stale or failed')
        errors = validate_reviews(pack, fragments, reviews) + check_artifacts(pack, artifacts)
        errors += [e for p in pack.problems for e in validate_fragment(p, fragments[p.id])]
        require(not errors, 'child review/artifact validation: ' + '; '.join(errors))
        manifest = obj(artifacts.manifest)
        require(child['input_hash'] == manifest['input_hash'] == payload_hash(pack, fragments) and child['review_policy_version'] == reviews['review_policy_version'], 'child input/policy mismatch')
        require(reviews['artifact_hashes'] == artifact_hashes(artifacts), 'child artifacts changed')
        require(verified_references(reviews['references'], item['repo'], item['repo'])[1], 'child references incomplete')
        overlay_path = artifacts.html.parent / manifest['answer_overlay']
        require(obj(overlay_path) == make_overlay(pack, artifacts.html, item['repo']), 'child overlay mismatch')
        require(Path(child['stage']).resolve() == artifacts.html.parent.resolve() and child['bucket'] == folder.name, 'child stage mismatch')
        required.update(str(Path(p).resolve()) for p in [folder / 'source.json', folder / 'stage.json', folder / 'machine.json', review_path, overlay_path, *artifacts.files, *[pack.pack_paths.source_file(p) if pack.pack_paths else Path(p) for p in pack.inputs], *[folder / 'explanations' / (p.id + '.html') for p in pack.problems]])
        required.update(str(Path(x['path']).resolve()) for x in reviews['references'])
        identities = child['reviewers']
        authors, solvers = identities['authors'], identities['independent']
        for problem in pack.problems:
            require(isinstance(authors.get(problem.id), str) and authors[problem.id].strip(), 'child author ID required')
            for subpart in problem.subparts:
                key = problem.id + ':' + subpart
                require(solvers.get(key) == reviews['independent']['items'][key]['reviewer'] and solvers[key] != authors[problem.id], 'independent reviewer must differ from author')
        require(reviews['content']['reviewer'] not in set(authors.values()), 'content reviewer authored child problem')
        require(identities['content'] == reviews['content']['reviewer'] and identities['browser'] == reviews['browser']['reviewer'], 'child reviewer IDs mismatch')
    require(required <= files.keys(), 'child files omit current inputs/stage/reviews')
    verified.update(files)
    verified[str(child_path)] = sha(child_path)
