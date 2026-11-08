"""Isolated runner fixtures; no synthetic approval is real review evidence."""
from pathlib import Path
import shutil
from _util import REPO


def make_run(tmp_path: Path, *, lite=False, browser_owner="workers", pdf_owner="workers",
             repo_name="repo 한글", init_repo=None):
    """init_repo: the spelling passed to init (default: the on-disk path)."""
    repo, run = tmp_path / repo_name, tmp_path / "run 한글"
    profile = Path(".claude/skills/ec2-review-pack/references/solution-style.md")
    (repo / profile).parent.mkdir(parents=True)
    shutil.copyfile(REPO / profile, repo / profile)
    (repo / "workbook").mkdir()
    shutil.copyfile(REPO / "workbook/learning_style.py", repo / "workbook/learning_style.py")
    (repo / "STT").mkdir()
    (repo / "STT/0909 전회2.md").write_text("실제 최소 STT 입력", encoding="utf-8")
    run.mkdir()
    from pack_flow import init_run
    init_run(init_repo or repo, run, "0909", lite=lite, browser_owner=browser_owner, pdf_owner=pdf_owner, allow_tmp=True)
    return repo, run
import json
from pathlib import Path


def install_task(run, role='author', targets=None, outputs=None):
    from pack_flow import load_state, update_state
    run = Path(run)
    task_id = role + '-synthetic'
    brief = run / 'brief.json'
    data = {'inputs': [{'path': p, 'sha256': h} for p, h in load_state(run)['hashes'].items()],
            'allowed_outputs': [str(run / p) for p in (outputs or ['sections/synthetic.html'])]}
    brief.write_text(json.dumps(data), encoding='utf-8')
    task = dict(id=task_id, role=role, targets=targets or ['synthetic'], brief=str(brief),
                status='pending', attempt=None, agent_id=None, receipt=None, dependencies=[])
    update_state(run, load_state(run)['revision'], lambda s: dict(s, tasks={task_id: task}))
    return task_id


def receipt_for(run, task_id, attempt):
    from pack_flow import load_state, _sha
    state = load_state(run)
    task = state['tasks'][task_id]
    brief = json.loads(Path(task['brief']).read_text(encoding='utf-8'))
    for name in brief['allowed_outputs']:
        path = Path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('synthetic output', encoding='utf-8')
    report = run / 'report.md'
    report.write_text('synthetic fixture report', encoding='utf-8')
    data = dict(schema_version=1, run_id=state['run_id'], task_id=task_id, attempt=attempt,
                status='done', inputs=brief['inputs'], outputs=[{'path': p, 'sha256': _sha(Path(p))} for p in brief['allowed_outputs']],
                report=str(report), reviews=[], counts={}, unresolved=[])
    path = run / 'receipt.json'
    path.write_text(json.dumps(data), encoding='utf-8')
    return path


def genuine_child_run(tmp_path, *, existing=None):
    """Real child extract/build/check with explicitly synthetic review records."""
    import importlib.util
    import json
    import subprocess
    import sys
    from pack_flow import load_state, update_state, _sha
    util_path = REPO / '.claude/skills/ec2-problem-explain/tests/_util.py'
    spec = importlib.util.spec_from_file_location('runner_child_test_util', util_path)
    # Child and parent each have assemble.py; isolate the fixture import like separate CLIs.
    previous = sys.modules.pop('assemble', None)
    sys.path.insert(0, str(REPO / 'workbook'))
    try:
        util = importlib.util.module_from_spec(spec); spec.loader.exec_module(util)
    finally:
        sys.path.remove(str(REPO / 'workbook'))
        if previous is not None: sys.modules['assemble'] = previous
        else: sys.modules.pop('assemble', None)
    repo, run = existing or make_run(tmp_path)
    parent_note = repo / '복습노트/0909/정리노트_0909_Synthetic.html'
    parent_bytes = parent_note.read_bytes() if existing and parent_note.exists() else None
    util.make_repo(repo, range_='0909', slug='Synthetic', ids=('P10.02',))
    if parent_bytes is not None: parent_note.write_bytes(parent_bytes)
    child_run = Path(load_state(run)['explain_run']) if existing else run / 'problem-explain' / 'synthetic'
    cli = REPO / '.claude/skills/ec2-problem-explain/scripts/epe_cli.py'
    def call(*args):
        result = subprocess.run([sys.executable, str(cli), *map(str, args)], capture_output=True, text=True, encoding='utf-8')
        assert result.returncode == 0, result.stderr
    call('extract', '--repo', repo, '--target', '0909', '--run', child_run)
    from epe_cli import load_run, load_artifacts, load_fragments
    item = load_run(child_run)[0]
    for p in item['pack'].problems:
        (item['folder'] / 'explanations' / (p.id + '.html')).write_text(util.fragment(p), encoding='utf-8')
    call('build', '--run', child_run); call('check', '--run', child_run)
    artifacts = load_artifacts(item)
    review = util.approved(item['pack'], load_fragments(item), artifacts)
    review['content']['reviewer'] = 'synthetic-content-reviewer'
    review['browser']['reviewer'] = 'synthetic-browser-reviewer'
    (item['folder'] / 'review.json').write_text(json.dumps(review), encoding='utf-8')
    manifest = run / 'manifest.json'
    if not existing:
        manifest.write_text(json.dumps({'range': '0909', 'slug': 'Synthetic', 'problems': [{'id': 'P10.02'}], 'learning_style': item['pack'].learning_style}), encoding='utf-8')
    child = dict(schema_version=1, status='ready-for-publish', range='0909', slug='Synthetic', run=str(child_run),
        bucket=item['folder'].name, stage=str(artifacts.html.parent), input_hash=review['input_hash'], review_policy_version=review['review_policy_version'],
        counts={'problems': 1}, reviews={}, unresolved=[], reviewers={
            'authors': {p.id: 'synthetic-author' for p in item['pack'].problems},
            'independent': {k: v['reviewer'] for k,v in review['independent']['items'].items()},
            'content': review['content']['reviewer'], 'browser': review['browser']['reviewer']})
    files = {*[p for p in child_run.rglob('*') if p.is_file()], manifest, run / 'learning-style.json', *map(Path, item['pack'].inputs), *[Path(x['path']) for x in review['references']]}
    child['files'] = [{'path': str(p.resolve()), 'sha256': _sha(p)} for p in files]
    (child_run / 'child-receipt.json').write_text(json.dumps(child), encoding='utf-8')
    if existing: return repo, run, 'child-coordinator', child_run
    tid = install_task(run, 'child-coordinator', outputs=['work/child/result.json'])
    brief = Path(load_state(run)['tasks'][tid]['brief'])
    data = json.loads(brief.read_text()); data['manifest'] = str(manifest)
    data['inputs'].append({'path': str(manifest), 'sha256': _sha(manifest)})
    brief.write_text(json.dumps(data))
    update_state(run, load_state(run)['revision'], lambda s: dict(s, explain_run=str(child_run)))
    return repo, run, tid, child_run


def workflow_accept(run, tid, *, supplement=False, problems=0, before_accept=None, section_ids=("why", "s1"), audit_evidence="synthetic fixture only"):
    """Drive public lifecycle with real files, explicitly synthetic reviewer evidence."""
    import json
    import pymupdf
    from PIL import Image
    import pack_flow as f
    state = f.load_state(run)
    task = state['tasks'][tid]
    attempt = f.claim_task(run, tid)['attempt']
    f.bind_task(run, tid, attempt, 'synthetic-' + tid)
    brief = json.loads(Path(task['brief']).read_text(encoding='utf-8'))
    outputs = [Path(p) for p in brief['allowed_outputs']]
    role = task['role']
    if role == 'child-coordinator': genuine_child_run(run.parent, existing=(Path(state['repo']), run))
    manifest = {'range': '0909', 'slug': 'Synthetic', 'sections': [
        {'id': sid, 'topics': [{'id': sid + '-topic'}]} for sid in section_ids],
        'problems': [{'id': 'P10.02'}] * problems,
        'learning_style': json.loads((run / 'learning-style.json').read_text())}
    for path in outputs:
        if role == 'pdf-qa': continue  # Produce only the documented review, report and rendered pages below.
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and role == 'content-review': continue
        if role == 'standalone-svg-qa' and path.suffix == '.png': Image.new('RGB', (100, 50)).save(path)
        else: path.write_text(json.dumps(manifest) if path.name == 'manifest.json' else '{}', encoding='utf-8')
    if role == 'selection':
        (run / 'display-titles.json').write_text(json.dumps({q['id']: 'Synthetic title' for q in manifest['problems']}))
    if role == 'source-prep':
        pdf = Path(state['repo']) / 'lecture.pdf'
        with pymupdf.open() as document:
            document.new_page(); document.save(pdf)
        (run / 'source-map.json').write_text(json.dumps({'schema_version': 1, 'sessions': [
            {'date': '0909', 'stt': str(Path(state['repo']) / 'STT/0909 전회2.md'), 'pdfs': [str(pdf)], 'status': 'ready', 'missing': []}]}))
    if role in ('style-audit', 'content-review'):
        path = Path(brief.get('audit_output', str(run / ('work/' + role + '/learning-style-audit-note.json'))))
        if role == 'style-audit' or supplement:
            snapshot = manifest['learning_style']
            audit = {'learning_style': snapshot, 'items': {target: {'status': 'pass', 'reviewer': 'synthetic-reviewer',
                'rules': {rule: {'disposition': 'applied', 'evidence': audit_evidence} for rule in snapshot['rule_ids']}} for target in task['targets']}}
            path.write_text(json.dumps(audit))
            if path not in outputs: outputs.append(path)
        elif path in outputs:
            outputs.remove(path); path.unlink(missing_ok=True)
    if role == 'browser-qa':
        path = run / 'work/browser/synthetic.png'; Image.new('RGB', (16, 9)).save(path); outputs.append(path)
    report = Path(brief['report']) if role == 'pdf-qa' else run / 'work' / tid / ('report.md' if role == 'standalone-svg-qa' else attempt + '-report.md')
    report.parent.mkdir(parents=True, exist_ok=True); report.write_text('Synthetic fixture review only')
    if role == 'pdf-qa':
        images = [run / 'answer-pages' / ('page-' + str(i) + '.png') for i in (1, 2)]
        for image in images:
            image.parent.mkdir(exist_ok=True); Image.new('RGB', (16, 9)).save(image)
        overlay = Path(brief['overlay']); pdf = Path(brief['pdf'])
        review = {'schema_version': 1, 'status': 'pass', 'reviewer': 'synthetic-pdf-reviewer', 'overflow': [],
            'pdf_sha256': f._sha(pdf), 'overlay_sha256': f._sha(overlay),
            'learning_style_sha256': json.loads(overlay.read_text())['learning_style']['sha256'],
            'evidence': [{'path': str(p.relative_to(run)), 'sha256': f._sha(p)} for p in [*images, report]]}
        (run / 'answer-review.json').write_text(json.dumps(review))
        outputs.extend(images)
    receipt = run / 'work' / tid / (attempt + '-report.json')
    receipt.write_text(json.dumps(dict(schema_version=1, run_id=state['run_id'], task_id=tid, attempt=attempt,
        status='done', inputs=brief['inputs'], outputs=[{'path': str(p), 'sha256': f._sha(p)} for p in outputs],
        report=str(report), reviews=[str(report), *([str(run / 'work/standalone-svg-qa/report.json')] if role == 'standalone-svg-qa' else [])], counts={'targets': task['targets']}, unresolved=[])))
    if before_accept: before_accept()
    return f.accept_task(run, tid, attempt, receipt)


def workflow_action(run, name):
    """Synthetic action completion evidence; never a real CLI or semantic approval."""
    import pack_flow as f
    state = f.load_state(run)
    path = run / 'work/actions' / name / 'synthetic-result.json'
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text('{"synthetic": true}')
    def change(s):
        action = s['actions'][name]
        action.update(status='done', verified_files=[{'path': str(path), 'sha256': f._sha(path)}])
        if name == 'assemble-note':
            note = run / 'note.html'
            svgs = ''.join(f'<svg id="synthetic-{i}" xmlns="http://www.w3.org/2000/svg" width="100" height="50"><text x="5" y="20">synthetic</text></svg>' for i in range(s.get('fixture_svg_count', 0)))
            note.write_text('<html><body><main><div class="hero"><h1>Synthetic</h1></div><article class="topic" id="synthetic"><h2>Synthetic</h2><div class="layer eli5"><p>Fixture</p>' + svgs + '</div></article></main></body></html>')
            from manifest import note_name
            published_note = Path(s['repo']) / '복습노트' / s['range'] / note_name(json.loads((run / 'manifest.json').read_text()))
            published_note.parent.mkdir(parents=True, exist_ok=True); published_note.write_bytes(note.read_bytes())
            action['verified_files'].append({'path': str(published_note), 'sha256': f._sha(published_note)})
            s['note_path'] = str(note)
            action['verified_files'].append({'path': str(note), 'sha256': f._sha(note)})
        if name == 'convert-md':
            from html2md import convert_note, check_md
            from manifest import note_name
            note = Path(s['repo']) / '복습노트' / s['range'] / note_name(json.loads((run / 'manifest.json').read_text()))
            md, count = convert_note(note)
            assert check_md(str(note), md) == []
            emitted = [Path(md), *sorted((Path(md).parent / ('figures_' + s['range'])).glob('*.svg'))]
            assert len(emitted) == count + 1
            action['outputs'] = [{'path': str(p), 'sha256': f._sha(p)} for p in emitted]
            action['verified_files'].extend([{'path': str(note), 'sha256': f._sha(note)}, *action['outputs']])
        if name == 'build-answers':
            import pymupdf
            pdf = run / 'answers' / 'synthetic-answers.pdf'; pdf.parent.mkdir(exist_ok=True)
            with pymupdf.open() as document:
                document.new_page(); document.new_page(); document.save(pdf)
            child = json.loads((Path(s['explain_run']) / 'child-receipt.json').read_text())
            overlay = run / 'answers' / 'answer-overlay.json'
            shutil.copyfile(next(Path(x['path']) for x in child['files'] if Path(x['path']).name == 'answer-overlay.json' and Path(x['path']).is_relative_to(Path(child['stage']))), overlay)
            s['answer_pdf'], s['answer_overlay'] = str(pdf), str(overlay)
            action['verified_files'].extend({'path': str(p), 'sha256': f._sha(p)} for p in (pdf, overlay))
        if name == 'precheck': action['audit_sha256'] = f._sha(Path(s['active_audit']))
        f.refresh_tasks(s); f.write_briefs(s)
        return s
    return f.update_state(run, state['revision'], change)


def workflow_until(run, target, *, problems=0):
    import pack_flow as f
    for _ in range(30):
        nxt = f.next_work(run, slots=3)
        if nxt.get('action') == target or any(t['id'] == target for t in nxt['tasks']): return nxt
        if nxt['kind'] == 'run': workflow_action(run, nxt['action'])
        elif nxt['kind'] in ('dispatch', 'review_locally'):
            for task in nxt['tasks']: workflow_accept(run, task['id'], problems=problems)
        else: raise AssertionError(nxt)
    raise AssertionError('workflow did not reach ' + target)


def action_run(tmp_path, *, action='assemble-note'):
    """Isolated machine boundary with genuine manifest/template inputs, no approval claim."""
    import json
    import pack_flow as f
    from _util import prepare_mini_run, SKILL
    repo,run=make_run(tmp_path)
    fixture=prepare_mini_run(tmp_path/'fixture',repo)
    m=json.loads((fixture/'manifest.json').read_text(encoding='utf-8'))
    m.update(range='0909',slug='Synthetic',problems=[],links=[])
    m['sessions'][0].update(date='0909',stt='STT/0909 전회2.md')
    (run/'manifest.json').write_text(json.dumps(m),encoding='utf-8')
    shutil.copytree(fixture/'sections',run/'sections')
    shutil.copytree(SKILL/'scripts',repo/'.claude/skills/ec2-review-pack/scripts')
    shutil.copytree(SKILL/'assets',repo/'.claude/skills/ec2-review-pack/assets')
    for module in (REPO/'workbook').glob('*.py'): shutil.copyfile(module,repo/'workbook'/module.name)
    (run/'display-titles.json').write_text('{}')
    def change(s):
        s['actions'][action]=dict(id=action,status='pending',dependencies=[])
        return s
    f.update_state(run,f.load_state(run)['revision'],change)
    return repo,run
