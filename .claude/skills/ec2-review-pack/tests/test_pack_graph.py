"""Dependency tests and an opt-in CLI run, using isolated lecture fixtures."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from _util import REPO, SCRIPTS
from pack_support import make_run
import pack_flow as flow


def parallel(tmp_path):
    repo, _ = make_run(tmp_path)
    run = tmp_path / 'parallel'
    state = flow.init_run(repo, run, '0909', workflow='parallel', allow_tmp=True,
                          browser_owner='workers', pdf_owner='workers')
    return repo, run, state


def seed(state, tids):
    from pack_graph import refresh
    for tid in tids:
        refresh(state)
        record = flow._record(state, tid)
        assert record, tid
        marker = Path(state['run']) / (tid + '-synthetic.json')
        marker.write_text('{"synthetic_fixture":true}')
        evidence = [{'path': str(marker), 'sha256': flow._sha(marker)}]
        record.update(status='done', attempt='synthetic-test-' + tid, receipt={'verified_files': evidence},
                      verified_files=evidence)


def selected(tmp_path, problems):
    _, _, state = parallel(tmp_path)
    seed(state, ['source-prep', 'stt-0909', 'candidate-index', 'scope-draft'])
    state['scope_sections'] = [{'id': 'why', 'topics': [{'id': 'why-topic'}]}]
    state['selected_ids'] = problems
    seed(state, ['selection', 'render-preflight'])
    return state


def test_source_and_render_preflight_are_independent(tmp_path):
    _, run, _ = parallel(tmp_path)
    initial = flow.next_work(run, slots=1)
    assert set(initial['actions']) == {'render-preflight', 'candidate-index'}
    assert initial['dispatch'] == ['source-prep']
    assert not flow.next_work(run, slots=0)['dispatch']


def test_selection_unlocks_pdf_and_blind_before_note_qa(tmp_path):
    from pack_graph import ready_work
    state = selected(tmp_path, ['P10.02'])
    seed(state, ['stage-problem-index'])
    nxt = ready_work(state, slots=6)
    assert 'build-problems' in nxt['actions']
    assert {'explain-author', 'explain-blind', 'author-why'} <= set(nxt['dispatch'])


def test_fixed_html_unlocks_browser_and_svg_conversion(tmp_path):
    from pack_graph import ready_work
    state = selected(tmp_path, ['P10.02'])
    seed(state, ['scope-final', 'author-why', 'stage-problem-index', 'assemble-note',
                 'build-problems', 'style-audit', 'content-review', 'precheck'])
    nxt = ready_work(state, slots=6)
    assert 'browser-qa' in nxt['dispatch'] and 'convert-md' in nxt['actions']


def test_zero_problems_omits_every_workbook_action(tmp_path):
    from pack_graph import task_specs
    state = selected(tmp_path, [])
    ids = {spec.id for spec in task_specs(state)}
    assert {'stage-problem-index', 'build-problems', 'explain-author', 'explain-blind',
            'child-coordinator', 'explain-verify', 'build-answers', 'pdf-qa'}.isdisjoint(ids)
    assert 'publish-pack' in ids


def test_existing_state_uses_legacy_scheduler(tmp_path):
    _, run = make_run(tmp_path)
    path = run / 'run-status.json'
    state = json.loads(path.read_text())
    state.pop('workflow', None)
    path.write_text(json.dumps(state))
    assert flow.next_work(run, slots=2)['kind'] == 'dispatch'


def cli(*args):
    proc = subprocess.run([sys.executable, SCRIPTS / 'pack_cli.py', *args], capture_output=True, text=True)
    data = json.loads(proc.stdout)
    assert proc.returncode == 0, data
    return data


def test_opt_in_cli_runs_candidate_action_and_isolates_worker_attempts(tmp_path):
    repo, _ = make_run(tmp_path)
    run = tmp_path / 'trial'
    public = repo / '복습노트/0909'
    public.mkdir(parents=True)
    existing = public / '정리노트_0909_Previous.html'
    existing.write_text('previous note')
    shutil.copytree(REPO / '교과서/마이크로전자회로/_tools', repo/'교과서/마이크로전자회로/_tools')
    shutil.copytree(REPO / 'from_the_past/md/_tools', repo/'from_the_past/md/_tools')
    for module in (REPO / 'workbook').glob('*.py'):
        shutil.copyfile(module, repo / 'workbook' / module.name)
    cli('init', '--repo', repo, '--run', run, '--range', '0909', '--workflow', 'parallel', '--allow-tmp')
    assert flow.load_state(run)['public_baseline'] == {existing.name: flow._sha(existing)}
    claim = cli('task', 'claim', '--task', 'source-prep', '--run', run)['next']
    brief = json.loads(Path(claim['brief']).read_text())
    assert all(Path(name).is_relative_to(Path(brief['report']).parent) for name in brief['allowed_outputs'])
    cli('run', '--action', 'candidate-index', '--run', run)
    state = flow.inspect_state(run)
    assert state['tasks']['source-prep']['status'] == 'claimed'
    assert state['actions']['candidate-index']['status'] == 'done'
    assert existing.read_text() == 'previous note'
    cli('task', 'release', '--task', 'source-prep', '--attempt', claim['attempt'], '--reason', 'stopped', '--run', run)
    retry = cli('task', 'claim', '--task', 'source-prep', '--run', run)['next']
    assert Path(retry['brief']).parent != Path(claim['brief']).parent


def test_sections_which_need_final_links_wait_for_selection(tmp_path):
    from pack_graph import ready_work
    state = selected(tmp_path, [])
    state['scope_sections'].append({'id': 'links', 'topics': [{'id': 'links-topic'}]})
    state['link_sections'] = ['links']
    ready = ready_work(state, slots=10)
    assert 'author-why' in ready['dispatch']
    assert 'author-links' not in ready['dispatch']
    seed(state, ['scope-final'])
    assert 'author-links' in ready_work(state, slots=10)['dispatch']


@pytest.mark.parametrize('scope_change', [None, 'sessions', 'preview_topic', 'forbidden_outside_preview', 'early_link', 'owned_link'])
def test_zero_problem_cli_publishes_only_after_actual_converter_and_review_receipts(tmp_path, monkeypatch, scope_change):
    import pymupdf
    from PIL import Image
    from _util import prepare_mini_run
    from pack_support import parallel_worker
    from problem_index import record_selection
    repo, run, _ = parallel(tmp_path)
    fixture = prepare_mini_run(tmp_path/'fixture', repo)
    shutil.copytree(REPO/'교과서/마이크로전자회로/_tools', repo/'교과서/마이크로전자회로/_tools')
    shutil.copytree(REPO/'from_the_past/md/_tools', repo/'from_the_past/md/_tools')
    for module in (REPO/'workbook').glob('*.py'):
        shutil.copyfile(module, repo/'workbook'/module.name)
    m = json.loads((fixture/'manifest.json').read_text())
    m.update(range='0909', problems=[], links=[], link_sections=['s2'], selection_policy='exam-first-v2')
    m['sessions'][0].update(date='0909', stt='STT/0909 전회2.md')
    pdf = repo/'lecture.pdf'
    with pymupdf.open() as doc:
        doc.new_page()
        doc.save(pdf)
    source = dict(schema_version=1, sessions=[dict(date='0909', stt=str(repo/'STT/0909 전회2.md'),
                                                    pdfs=[str(pdf)], status='ready', missing=[])])
    def write(brief, outputs):
        extra = []
        for target in outputs:
            if target.name == 'source-map.json':
                target.write_text(json.dumps(source))
            elif target.name == 'manifest.json':
                target.write_text(json.dumps(m))
            elif target.name in ('selection.json', 'selection-review.json'):
                rows = json.loads(Path(brief['candidates']).read_text())
                review = dict(policy='exam-first-v2', catalog_sha256=rows['catalog_sha256'], candidates=[], coverage=[])
                target.write_text(json.dumps(review if target.name == 'selection-review.json' else record_selection(m, rows, review)))
            elif target.name == 'learning-style-audit-note.json':
                shutil.copyfile(fixture/'learning-style-audit.json', target)
            elif target.suffix == '.html':
                raw = (fixture/'sections'/target.name).read_text()
                raw = raw.replace('<ul><li><a href="{{PROBLEM_PDF}}">복습문제 PDF</a></li><li><a href="{{ANSWER_PDF}}">복습문제 답안 PDF</a></li></ul>',
                                  '<p>이번 범위에는 복습문제가 없어요.</p>')
                target.write_text(raw)
            else:
                target.write_text('{}')
        if brief['role'] in ('browser-qa', 'standalone-svg-qa'):
            names = brief.get('svg_screenshots', {'browser': str(Path(brief['run'])/'browser.png')})
            for name in names.values():
                p = Path(name)
                p.parent.mkdir(parents=True, exist_ok=True)
                Image.new('RGB', (16, 9)).save(p)
                extra.append(p)
        return extra
    def worker(tid):
        parallel_worker(run, tid, write)
    def action(tid):
        cli('run', '--action', tid, '--run', run)
    action('candidate-index')
    for tid in ['source-prep', 'stt-0909', 'scope-draft', 'author-why', 'author-s1', 'selection',
                'scope-final', 'author-s2']:
        if tid == 'scope-final' and scope_change:
            if scope_change == 'sessions':
                m['sessions'][0]['slides'] = 'different source'
            elif scope_change == 'preview_topic':
                m['preview_topic'] = 's1-mean'
            elif scope_change == 'forbidden_outside_preview':
                m['forbidden_outside_preview'] = []
            elif scope_change == 'owned_link':
                m['links'] = [{'topic': 's2-links', 'href': '#s1-mean'}]
                worker(tid)
                assert 'author-s2' in flow.next_work(run, slots=8)['dispatch']
                return
            else:
                m['links'] = [{'topic': 's1-mean', 'href': '#s2-links'}]
            with pytest.raises(flow.FlowError, match='scope|link'):
                worker(tid)
            assert 'assemble-note' not in flow.next_work(run, slots=8)['actions']
            return
        worker(tid)
    action('assemble-note')
    worker('content-review')
    worker('style-audit')
    action('precheck')
    action('convert-md')
    assert not (repo/'복습노트/0909').exists()
    assert 'publish-pack' not in flow.next_work(run, slots=1)['actions']
    worker('browser-qa')
    worker('standalone-svg-qa')
    from pack_actions import run_action
    audit = Path(flow.load_state(run)['active_audit'])
    approved_bytes = audit.read_bytes()
    audit.chmod(0o644)
    audit.write_text('{}')
    with pytest.raises(flow.FlowError):
        run_action(run, 'publish-pack')
    assert not (repo/'복습노트/0909').exists()
    audit.write_bytes(approved_bytes)

    # Another same-date transaction crashed with a durable reservation and no writes.
    import pack_publication as pub
    from pack_paths import PackPaths
    foreign = tmp_path/'foreign-run'
    candidate = tmp_path/'foreign-candidate'
    candidate.mkdir()
    html = candidate/'정리노트_0909_Other.html'
    html.write_text('pending foreign transaction')
    paths = PackPaths(repo, repo/'복습노트/0909', candidate)
    class Interrupted(BaseException): pass
    def crash(*args):
        raise Interrupted()
    with monkeypatch.context() as patch:
        patch.setattr(pub, '_run_steps', crash)
        with pytest.raises(Interrupted):
            pub.publish_pack(paths, foreign, expected={}, candidate_inventory={html.name: flow._sha(html)}, verify=lambda root: None)
    try:
        blocked = run_action(run, 'publish-pack')
        assert blocked['error_code'] == 'pending_publication'
        assert flow.load_state(run)['status'] != 'recovery_required'
        assert not (Path(blocked['attempt_dir'])/'publication/journal.json').exists()
    finally:
        result = pub.reconcile_publication(paths, foreign/'publication/journal.json', verify=lambda root: None)
    assert result['status'] == 'restored'
    # Earlier trial RUNs persisted someone else's reservation as a local recovery.
    def previous_trial(s):
        foreign_journal = str(foreign/'publication/journal.json')
        s['actions']['publish-pack'].update(status='recovery_required', error_code='pending_publication',
                publication_result=dict(status='recovery_required', error_code='pending_publication', journal=foreign_journal))
        s['status'] = 'recovery_required'
        return s
    flow.update_state(run, flow.load_state(run)['revision'], previous_trial)
    from pack_actions import reconcile_action
    released = reconcile_action(run, 'publish-pack')
    assert released['error_code'] == 'pending_publication'
    assert flow.load_state(run)['status'] != 'recovery_required'
    assert json.loads((foreign/'publication/journal.json').read_text())['status'] == 'restored'
    action('publish-pack')
    state = flow.inspect_state(run)
    assert state['status'] == 'complete'
    assert state['actions']['final-check']['attempt'] == state['actions']['publish-pack']['attempt']
    assert (repo/'복습노트/0909/정리노트_0909_Mini_Test.html').is_file()
    assert flow.next_work(run, slots=0)['kind'] == 'concept_check'
    cli('report', '--run', run)
    assert json.loads((run/'report.json').read_text())['selection']['problems'] == []


def test_early_index_seals_real_questions_for_independent_attempts(tmp_path):
    from pack_graph import refresh
    from _util import REPO
    repo, run, state = parallel(tmp_path)
    import subprocess
    # Copy a real question and its original figure into the isolated source fixture.
    helper = REPO/'.claude/skills/ec2-problem-explain/tests'
    subprocess.run([sys.executable, '-c', 'import sys; from pathlib import Path; '
        'sys.path.insert(0, sys.argv[1]); from _util import _copy_problem; '
        '_copy_problem("P10.02", Path(sys.argv[2]))', helper, repo], check=True)
    marker = run/'synthetic-upstream.json'
    marker.write_text('{"synthetic_fixture":true}')
    evidence = [dict(path=str(marker), sha256=flow._sha(marker))]
    def mark(tid):
        refresh(state)
        row = flow._record(state, tid)
        row.update(status='done', attempt='synthetic-'+tid, verified_files=evidence, receipt={'verified_files': evidence})
        return row
    for tid in ('source-prep', 'candidate-index', 'stt-0909', 'scope-draft'):
        mark(tid)
    state['scope_sections'] = [dict(id='why', topics=[dict(id='why-circuit')])]
    selection = mark('selection')
    state['selected_ids'] = ['P10.02']
    q = dict(id='P10.02', kind='장말문제', why='practice', priority='core',
             estimated_minutes=10, learning_goals=['gain'], subpart_count=1)
    data = {'manifest.json': dict(problems=[q], range='0909', slug='Test', selection_policy='exam-first-v2'),
            'selection.json': dict(schema_version=2, policy='exam-first-v2', problems=[q],
                workload=dict(estimated_minutes=10), review=dict(candidates=[], coverage=[])),
            'display-titles.json': {'P10.02':'Practice'}}
    selection['artifacts'] = {}
    for name, obj in data.items():
        p = run/'fixture-selection'/name
        p.parent.mkdir(exist_ok=True)
        p.write_text(json.dumps(obj))
        selection['artifacts'][name] = str(p)
    refresh(state)
    flow.update_state(run, state['revision'], lambda old: state)
    cli('run', '--run', run, '--action', 'stage-problem-index')
    first = flow.claim_task(run, 'explain-author')
    second = flow.claim_task(run, 'explain-blind')
    author, blind = (json.loads(Path(r['brief']).read_text()) for r in (first, second))
    assert blind['questions'] == author['questions']
    assert set(a['path'] for a in blind['inputs']) == {str(p) for p in Path(blind['questions']).parent.iterdir()}
    question, = json.loads(Path(blind['questions']).read_text())['problems']
    assert question['id'] == 'p1' and question['ask_html'] and question['figures']
    assert not {'reference_steps', 'reference_answer', 'source'} & question.keys()
    assert not list(Path(blind['questions']).parent.parent.rglob('source.json'))
    assert not (repo/'복습노트/0909').exists()

    from pack_support import genuine_child_run, parallel_worker
    for tid, attempt in [('explain-author', first), ('explain-blind', second)]:
        flow.release_task(run, tid, attempt['attempt'], 'released synthetic fixture reviewer')
    def write(brief, outputs):
        if brief['role'] == 'child-coordinator':
            genuine_child_run(tmp_path, existing=(repo, run))
        elif brief['role'] == 'explain-author':
            expr = ('import sys; from types import SimpleNamespace; from pathlib import Path; import json; '
                    'sys.path.insert(0,sys.argv[1]); from _util import fragment; '
                    'Path(sys.argv[3]).write_text(fragment(SimpleNamespace(subparts=json.loads(sys.argv[2]))))')
            subprocess.run([sys.executable, '-c', expr, helper, json.dumps(question['subparts']), outputs[0]], check=True)
        else:
            items = {f'p1:{key}': dict(reviewer='synthetic-explain-blind', evidence='test fixture',
                    method='exact', conclusion='1=1') for key in question['subparts']}
            outputs[0].write_text(json.dumps(dict(items=items)))
    for tid in ('explain-blind', 'explain-author', 'child-coordinator'):
        parallel_worker(run, tid, write)
    shutil.copytree(REPO/'.claude/skills/ec2-problem-explain', repo/'.claude/skills/ec2-problem-explain')
    shutil.copytree(REPO/'.claude/skills/ec2-review-pack/scripts', repo/'.claude/skills/ec2-review-pack/scripts')
    for module in (REPO/'workbook').glob('*.py'):
        shutil.copyfile(module, repo/'workbook'/module.name)
    for name in ('교과서/마이크로전자회로/_tools', 'from_the_past/md/_tools'):
        shutil.copytree(REPO/name, repo/name)
    cli('run', '--run', run, '--action', 'explain-verify')
    verified = flow.inspect_state(run)['actions']['explain-verify']
    assert verified['status'] == 'done' and Path(verified['artifacts']['overlay']).is_file()
    assert not (repo/'복습노트/0909').exists()

    shutil.copytree(REPO/'workbook/templates', repo/'workbook/templates')
    cli('run', '--run', run, '--action', 'render-preflight')
    for tid in ('build-problems', 'build-answers'):
        cli('run', '--run', run, '--action', tid)
    import pymupdf
    pdf = Path(flow.load_state(run)['actions']['build-answers']['artifacts']['pdf'])
    def inspect_pdf(brief, outputs):
        root = Path(brief['run'])
        report = Path(brief['report'])
        report.write_text('Synthetic fixture review only.')
        pages = root/'answer-pages'
        pages.mkdir()
        images = []
        with pymupdf.open(pdf) as document:
            assert len(document) >= 1
            for i, page in enumerate(document, 1):
                img = pages/f'page-{i:0{len(str(len(document)))}d}.png'
                page.get_pixmap(matrix=pymupdf.Matrix(.1, .1)).save(img)
                images.append(img)
        overlay = Path(brief['overlay'])
        review = dict(schema_version=1, status='pass', reviewer='synthetic-pdf-qa', overflow=[],
                      pdf_sha256=flow._sha(pdf), overlay_sha256=flow._sha(overlay),
                      learning_style_sha256=json.loads(overlay.read_text())['learning_style']['sha256'],
                      evidence=[dict(path=str(p.relative_to(root)), sha256=flow._sha(p)) for p in [report, *images]])
        (root/'answer-review.json').write_text(json.dumps(review))
        return images
    pdf_review = parallel_worker(run, 'pdf-qa', inspect_pdf)['tasks']['pdf-qa']
    assert pdf_review['status'] == 'done'
    assert Path(pdf_review['artifacts']['answer-review.json']).is_file()
    assert not (repo/'복습노트/0909').exists()


def test_completed_producer_loses_approval_when_frozen_attempt_is_superseded(tmp_path):
    _, _, state = parallel(tmp_path)
    marker = Path(state['run'])/'proof.json'
    marker.write_text('{}')
    files = [{'path': str(marker), 'sha256': flow._sha(marker)}]
    state['tasks']['source-prep'].update(status='done', attempt='replacement', receipt={'verified_files':files})
    state['actions']['test-consumer'] = dict(status='done', input_version={'source-prep':'original'},
                                           verified_files=files, dependencies=['source-prep'])
    assert flow._current(state)['actions']['test-consumer']['status'] == 'stale'


def test_compact_parallel_next_preserves_ready_ids():
    from pack_cli import format_result
    result = dict(next=dict(kind='parallel', actions=['build-problems'], dispatch=['explain-blind'],
                            waiting=[('publish-pack','explanation '*1000)], revision=3))
    message = json.loads(format_result(result))
    assert message['next']['actions'] == ['build-problems']
    assert message['next']['dispatch'] == ['explain-blind']


def test_ready_work_rechecks_accepted_evidence(tmp_path):
    from pack_graph import ready_work
    state = selected(tmp_path, ['P10.02'])
    seed(state, ['stage-problem-index'])
    Path(state['actions']['stage-problem-index']['verified_files'][0]['path']).write_text('edited')
    ready = ready_work(state, slots=4)
    assert 'build-problems' not in ready['actions'] and 'explain-blind' not in ready['dispatch']

@pytest.mark.parametrize('crash_before_adoption', [False, True])
def test_matching_stopped_stale_attempt_can_be_discarded_and_retried(tmp_path, monkeypatch, crash_before_adoption):
    import pack_parallel as runner
    from pack_graph import refresh
    state = selected(tmp_path, ['P10.02'])
    run = Path(state['run'])
    refresh(state)
    flow.update_state(run, state['revision'], lambda old: state)
    def execute(s, spec, root):
        pred = s['tasks']['selection']
        Path(pred['verified_files'][0]['path']).write_text('changed during work')
        def invalidate(current):
            return flow._current(current)
        runner.transact(run, invalidate)
        return {'verified_files': []}
    class Interrupted(BaseException): pass
    with monkeypatch.context() as patch:
        patch.setattr(runner, 'execute_action', execute)
        if crash_before_adoption:
            def crash(*args):
                raise Interrupted()
            patch.setattr(runner, 'finish', crash)
            with pytest.raises(Interrupted):
                runner.run_action(run, 'stage-problem-index')
        else:
            runner.run_action(run, 'stage-problem-index')
    if crash_before_adoption:
        runner.run_action(run, 'stage-problem-index', reconcile=True)
    discarded = flow.load_state(run)['actions']['stage-problem-index']
    assert discarded['status'] != 'done' and not discarded.get('invalidated_active')
    def repair(current):
        row = current['tasks']['selection']
        digest = flow._sha(Path(row['verified_files'][0]['path']))
        row['verified_files'][0]['sha256'] = row['receipt']['verified_files'][0]['sha256'] = digest
        row.update(status='done', attempt='new-selection')
        return current
    runner.transact(run, repair)
    monkeypatch.setattr(runner, 'execute_action', lambda *args: {'artifacts':{}, 'verified_files':[]})
    fresh = runner.run_action(run, 'stage-problem-index')
    assert fresh['status'] == 'done' and fresh['attempt'] != discarded['attempt']


@pytest.mark.parametrize('wrong_identity', ['some-other-attempt', 17])
def test_stopped_identity_cannot_replace_scheduler_attempt(tmp_path, monkeypatch, wrong_identity):
    import pack_parallel as runner
    _, run, _ = parallel(tmp_path)
    write = flow._atomic_json
    def wrong(path, data):
        write(path, dict(data, attempt=wrong_identity) if path.name=='stopped.json' else data)
    monkeypatch.setattr(flow, '_atomic_json', wrong)
    monkeypatch.setattr(runner, 'execute_action', lambda *args: {'verified_files': []})
    result = runner.run_action(run, 'candidate-index')
    assert result['status'] == 'recovery_required'
    assert result['attempt'] == Path(result['attempt_dir']).name
    with pytest.raises(flow.FlowError, match='identity'):
        runner.run_action(run, 'candidate-index', reconcile=True)
    with pytest.raises(flow.FlowError, match='active'):
        runner.run_action(run, 'candidate-index')
    marker = Path(result['attempt_dir'])/'stopped.json'
    write(marker, dict(status='done', attempt=result['attempt'], verified_files=[]))
    repaired = runner.run_action(run, 'candidate-index', reconcile=True)
    assert repaired['attempt'] == result['attempt'] and repaired['status'] == 'done'
    assert json.loads((marker.parent/'result.json').read_text())['attempt'] == repaired['attempt']
