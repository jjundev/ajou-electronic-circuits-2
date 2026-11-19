"""Legacy fix authorization and candidate-bound parallel review/repair contracts."""
import json
from pathlib import Path

import pytest
from _util import SCRIPTS  # noqa: F401  (puts scripts on sys.path)
from pack_findings import blocking_findings, owner_of
from pack_support import make_run, workflow_until
import pack_flow as flow

REPORT = """# Style audit

## Critical
- none

## Important
- [s4-cheatsheet] summary panel lacks the cheat sheet
- [P12.04] selection title wording
  continued detail line

## Minor
- [s1] spacing

## Notes
- [ignored] outside the severity sections
"""

MANIFEST = {'sections': [{'id': 's1', 'topics': [{'id': 's1-intro'}]},
                         {'id': 's4', 'topics': [{'id': 's4-cheatsheet'}]}],
            'problems': [{'id': 'P12.04'}]}


def test_blocking_findings_parses_three_sections(tmp_path):
    report = tmp_path / 'report.md'; report.write_text(REPORT, encoding='utf-8')
    assert blocking_findings(report) == [('Important', 's4-cheatsheet'), ('Important', 'P12.04'), ('Minor', 's1')]


def test_owner_maps_problem_to_selection():
    assert owner_of('P12.04', MANIFEST) == 'selection'
    assert owner_of('s4-cheatsheet', MANIFEST) == 'author-s4'
    assert owner_of('s1', MANIFEST) == 'author-s1'
    assert owner_of('note-layout', MANIFEST) == 'scope-final'


def _audit_needs_fix(run, findings):
    report = run / 'work' / 'style-audit' / 'findings.md'
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text('## Important\n' + ''.join(f'- [{x}] synthetic finding\n' for x in findings), encoding='utf-8')
    def change(s):
        task = s['tasks']['style-audit']
        task['status'] = 'needs_fix'
        task['receipt'] = dict(task.get('receipt') or {}, report=str(report))
        return s
    flow.update_state(run, flow.load_state(run)['revision'], change)


def _request(run, items, **extra):
    detail = run / 'fix.md'; detail.write_text('synthetic corrections')
    path = run / 'fix.json'
    path.write_text(json.dumps(dict({'id': 'content-1', 'category': 'content',
        'items': [{'task_id': t, 'request_path': str(detail)} for t in items]}, **extra)))
    return path


def test_content_fix_rejects_missing_owner(tmp_path):
    _, run = make_run(tmp_path)
    workflow_until(run, 'browser-qa', problems=1)
    _audit_needs_fix(run, ['s1-topic', 'P10.02'])
    with pytest.raises(flow.FlowError, match=r'content fix misses findings: P10\.02→selection'):
        flow.request_fixes(run, _request(run, ['author-s1']))
    assert flow.load_state(run)['fix_rounds']['content'] == 0


def test_content_fix_accepts_waived(tmp_path):
    _, run = make_run(tmp_path)
    workflow_until(run, 'browser-qa', problems=1)
    _audit_needs_fix(run, ['s1-topic', 'P10.02'])
    flow.request_fixes(run, _request(run, ['author-s1'], waived=[{'id': 'P10.02', 'reason': 'title already fixed in PDF'}]))
    assert flow.load_state(run)['fix_rounds']['content'] == 1


def test_blocking_findings_accepts_heading_variants_and_id_lists(tmp_path):
    report = tmp_path / 'report.md'
    report.write_text('### Critical\n- [s1-intro] wrong sign\n\n## Important (2)\n'
                      '- [s4-cheatsheet, P12.04] two owners\n## Notes\n- [x] skip\n', encoding='utf-8')
    assert blocking_findings(report) == [('Critical', 's1-intro'), ('Important', 's4-cheatsheet'), ('Important', 'P12.04')]


def test_subheading_inside_severity_keeps_section(tmp_path):
    report = tmp_path / 'report.md'
    report.write_text('## Important\n### s1 섹션\n- [s1-intro] gap\n## Notes\n- [x] skip\n', encoding='utf-8')
    assert blocking_findings(report) == [('Important', 's1-intro')]


# All judgments below are synthetic fixture decisions. The assembly, receipt
# checks, acceptance, refresh, correction dispatch and review join are real.
@pytest.fixture
def note_run(tmp_path):
    from _util import prepare_mini_run
    from test_pack_graph import parallel, seed
    from pack_graph import refresh
    from test_pack_graph import cli
    repo, run, state = parallel(tmp_path)
    fixture = prepare_mini_run(run/'note-fixture', repo)
    manifest = json.loads((fixture/'manifest.json').read_text())
    manifest.update(range='0909', problems=[], links=[])
    manifest['sessions'][0].update(date='0909', stt='STT/0909 전회2.md')
    (fixture/'manifest.json').write_text(json.dumps(manifest))
    links = fixture/'sections/s2.html'
    links.write_text(links.read_text().replace('<ul><li><a href="{{PROBLEM_PDF}}">복습문제 PDF</a></li>'
        '<li><a href="{{ANSWER_PDF}}">복습문제 답안 PDF</a></li></ul>', '<p>이번 범위에는 복습문제가 없어요.</p>'))
    def setup(s):
        seed(s, ['source-prep', 'stt-0909', 'candidate-index', 'scope-draft'])
        s['scope_sections'] = manifest['sections']
        s['link_sections'] = []
        s['selected_ids'] = []
        authors = ['author-' + sec['id'] for sec in manifest['sections']]
        seed(s, ['selection', 'scope-final', *authors])
        for tid, name in [('scope-draft', 'scope.json'), ('selection', 'selection.json')]:
            path = fixture/name
            path.write_text('{}')
            s['tasks'][tid].setdefault('artifacts', {})[name] = str(path)
        for tid in ('scope-draft', 'scope-final'):
            s['tasks'][tid].setdefault('artifacts', {})['manifest.json'] = str(fixture/'manifest.json')
        for tid in authors:
            name = 'sections/' + tid[7:] + '.html'
            s['tasks'][tid]['artifacts'] = {name: str(fixture/name)}
        return refresh(s)
    flow.update_state(run, state['revision'], setup)
    cli('run', '--run', run, '--action', 'assemble-note')
    return run, fixture


def defect(rule, target='s1-mean'):
    return dict(rule=rule, target=target, defect='missing ' + rule, severity='Important',
                owner_task='author-s1', evidence='synthetic: source section 1')


def submit_review(ctx, tid, findings=(), results=None, reviewer=None, disposition=None, report_text=None, reconciliations=()):
    run, fixture = ctx
    claim = flow.claim_task(run, tid)
    reviewer = reviewer or 'reviewer-' + tid
    flow.bind_task(run, tid, claim['attempt'], reviewer)
    brief = flow._read(claim['brief'])
    root = Path(brief['run'])
    report = Path(brief['report'])
    report.write_text(report_text or 'Synthetic fixture source comparison')
    outputs = []
    if not findings:
        path = Path(brief['required_outputs'][0])
        audit = flow._read(fixture/'learning-style-audit.json')
        for item in audit['items'].values():
            item['reviewer'] = reviewer
        if disposition:
            item = audit['items']['s1-mean']
            next(iter(item['rules'].values()))['disposition'] = disposition
        path.write_text(json.dumps(audit))
        outputs.append(dict(path=str(path), sha256=flow._sha(path)))
    receipt = root/'receipt.json'
    receipt.write_text(json.dumps(dict(schema_version=1, run_id=brief['run_id'], task_id=tid,
        attempt=claim['attempt'], status='needs-fix' if findings else 'done', inputs=brief['inputs'],
        outputs=outputs, report=str(report), reviews=[str(report)], counts=dict(targets=brief['targets']),
        unresolved=list(findings), fix_results=results or [], reconciliations=list(reconciliations))))
    return flow.accept_task(run, tid, claim['attempt'], receipt)


def request_and_repair(ctx, rows, rid):
    from test_pack_graph import cli
    from pack_support import parallel_worker
    run, fixture = ctx
    request = run/(rid + '.json')
    request.write_text(json.dumps(dict(id=rid, items=[dict(finding_id=r['id'],
        review_attempt=r['review_attempt'], input_digest=r['input_digest']) for r in rows])))
    cli('task', 'fix', '--run', run, '--request', request)
    cli('task', 'fix', '--run', run, '--request', request)
    claim = flow.claim_task(run, 'author-s1')
    flow.release_task(run, 'author-s1', claim['attempt'], 'interrupted before delivery')
    def write(brief, paths):
        assert {r['id'] for r in brief['repair_findings']} == {r['id'] for r in rows}
        paths[0].write_text((fixture/'sections/s1.html').read_text() + '<!-- ' + rid + ' -->')
    state = parallel_worker(run, 'author-s1', write)
    cli('run', '--run', run, '--action', 'assemble-note')
    return state['tasks']['author-s1']['attempt']


def test_two_review_findings_are_batched(note_run):
    import pack_findings as ledger
    run, _ = note_run
    state = submit_review(note_run, 'style-audit', [defect('widget')])
    note = state['actions']['assemble-note']['artifacts']['note']
    digest = flow._sha(Path(note))
    assert ledger.fixable_findings(state, candidate_digest=digest) == []
    state = submit_review(note_run, 'content-review', [defect('circuit')])
    both = ledger.fixable_findings(state, candidate_digest=digest)
    assert {row['rule'] for row in both} == {'widget', 'circuit'}
    assert len({row['id'] for row in both}) == 2
    assert not state.get('active_audit')
    assert 'precheck' not in flow.next_work(run, slots=2)['actions']


def test_late_new_finding_accepts_fix_in_same_run(note_run):
    state = submit_review(note_run, 'style-audit')
    assert not state.get('active_audit'), 'a single audit cannot grant approval'
    state = submit_review(note_run, 'content-review', [defect('sign')])
    original_id = state['run_id']
    row, = state['findings'].values()
    attempt = request_and_repair(note_run, [row], 'correct-sign')
    result = dict(finding_id=row['id'], request_id='correct-sign', attempt=attempt,
                  outcome='resolved', evidence='source equation and corrected polarity agree')
    submit_review(note_run, 'style-audit')
    state = submit_review(note_run, 'content-review', [defect('label')], [result])
    assert state['findings'][row['id']]['status'] == 'resolved'
    late, = [r for r in state['findings'].values() if r['rule'] == 'label']
    assert late['status'] == 'open'
    request_and_repair(note_run, [late], 'correct-label')
    state = submit_review(note_run, 'content-review', results=[dict(result, finding_id=late['id'],
        request_id='correct-label', attempt=flow.load_state(note_run[0])['tasks']['author-s1']['attempt'])])
    state = submit_review(note_run, 'style-audit')
    assert state['run_id'] == original_id
    assert Path(state['active_audit']).is_file()
    assert state['active_audit'] not in {
        state['tasks'][tid]['artifacts']['learning-style-audit-note.json'] for tid in ('style-audit', 'content-review')}


def test_two_failed_repairs_block_only_same_finding(note_run):
    submit_review(note_run, 'content-review')
    state = submit_review(note_run, 'style-audit', [defect('sign')])
    row, = state['findings'].values()
    for n in range(2):
        rid = 'try-' + str(n)
        attempt = request_and_repair(note_run, [row], rid)
        submit_review(note_run, 'content-review')
        state = submit_review(note_run, 'style-audit', [defect('sign'), *([defect('label')] if n else [])],
                              [dict(finding_id=row['id'], request_id=rid, attempt=attempt,
                                    outcome='unresolved', evidence='the source still shows the other sign')])
        row = state['findings'][row['id']]
    assert row['status'] == 'withheld'
    late, = [r for r in state['findings'].values() if r['rule'] == 'label']
    assert late['status'] == 'open'
    assert len(row['unsuccessful_attempts']) == 2
    for repair in row['repairs']:
        evidence, = repair['review_reports']
        assert flow._sha(Path(evidence['path'])) == evidence['sha256']
    from test_pack_graph import cli
    cli('report', '--run', note_run[0])
    assert flow._read(note_run[0]/'report.json')['findings'][row['id']] == row
    request_and_repair(note_run, [late], 'fix-other')
    assert 'publish-pack' not in flow.next_work(note_run[0], slots=0)['actions']


def test_same_reviewer_and_conflicting_source_judgments_cannot_join(note_run):
    run, _ = note_run
    submit_review(note_run, 'style-audit', reviewer='one')
    with pytest.raises(flow.FlowError, match='independent|distinct'):
        submit_review(note_run, 'content-review', reviewer='one')
    current = flow.load_state(run)['tasks']['content-review']
    flow.release_task(run, 'content-review', current['attempt'], 'new independent reviewer')
    state = submit_review(note_run, 'content-review', disposition='applied')
    assert not state.get('active_audit')
    assert any(r['status'] == 'open' and r['target'] == 's1-mean' for r in state['findings'].values())


def test_structural_error_accepts_and_rechecks_its_own_correction(note_run):
    from test_pack_graph import cli
    run, fixture = note_run
    source = fixture/'sections/s1.html'
    original = source.read_text()
    # Simulate a newly adopted bad author fragment, then execute the machine CLI.
    source.write_text(original.replace('id="s1-mean"', 'id="not-the-manifest-topic"'))
    state = flow.load_state(run)
    def supersede(s):
        s['actions']['assemble-note']['status'] = 'stale'
        return s
    flow.update_state(run, state['revision'], supersede)
    cli('run', '--run', run, '--action', 'assemble-note')
    import subprocess, sys
    result = subprocess.run([sys.executable, SCRIPTS/'pack_cli.py', 'run', '--run', run,
                             '--action', 'structural-precheck'], capture_output=True, text=True)
    state = flow.load_state(run)
    assert result.returncode and state['actions']['structural-precheck']['status'] == 'needs_fix'
    rows = list(state['findings'].values())
    assert rows and all(r['owner_task'] == 'author-s1' for r in rows)
    source.write_text(original)
    request_and_repair(note_run, rows, 'structural')
    cli('run', '--run', run, '--action', 'structural-precheck')
    assert all(r['status'] == 'resolved' for r in flow.load_state(run)['findings'].values())


@pytest.mark.parametrize('missing', ['decision', 'attempt', 'changed-owner-output'])
def test_unverified_repair_cannot_close_a_finding(note_run, missing):
    run, _ = note_run
    submit_review(note_run, 'style-audit')
    state = submit_review(note_run, 'content-review', [defect('gap')])
    row, = state['findings'].values()
    attempt = request_and_repair(note_run, [row], 'update')
    request = dict(finding_id=row['id'], request_id='update', attempt=attempt, outcome='resolved',
                   evidence='source and repair compared')
    if missing == 'attempt':
        request['attempt'] = row['review_attempt']
    if missing == 'changed-owner-output':
        adopted = Path(flow.load_state(run)['tasks']['author-s1']['artifacts']['sections/s1.html'])
        adopted.chmod(0o644)
        adopted.write_text('replaced after acceptance')
    with pytest.raises(flow.FlowError):
        submit_review(note_run, 'content-review', results=[] if missing == 'decision' else [request])
    assert flow.load_state(run)['findings'][row['id']]['unsuccessful_attempts'] == []


def test_parallel_waiver_and_extra_authorization_are_rejected(note_run):
    run, _ = note_run
    path = run/'invalid.json'
    path.write_text(json.dumps(dict(id='waive', items=[], waived=[dict(id='target', reason='skip')])))
    with pytest.raises(flow.FlowError, match='waiver'):
        flow.request_fixes(run, path)
    with pytest.raises(flow.FlowError, match='legacy'):
        flow.authorize_extra_fix(run, path)


def test_repair_brief_binds_previous_output_and_rejects_unchanged_fragment(note_run):
    run, _ = note_run
    from test_pack_graph import cli
    from pack_support import parallel_worker
    submit_review(note_run, 'style-audit')
    state = submit_review(note_run, 'content-review', [defect('equation')])
    row, = state['findings'].values()
    p = run/'correct-equation.json'
    p.write_text(json.dumps(dict(id='correction', items=[{k: row[k] for k in ('input_digest', 'review_attempt')}
                                                         | {'finding_id': row['id']}])))
    cli('task', 'fix', '--run', run, '--request', p)
    def unchanged(brief, outputs):
        old = Path(brief['previous_outputs']['sections/s1.html'])
        assert str(old) in {i['path'] for i in brief['inputs']}
        outputs[0].write_bytes(old.read_bytes())
    with pytest.raises(flow.FlowError, match='unchanged'):
        parallel_worker(run, 'author-s1', unchanged)
    assert not flow.load_state(run)['findings'][row['id']]['unsuccessful_attempts']


def test_full_precheck_defect_can_be_fixed_in_the_same_run(note_run):
    from test_pack_graph import cli
    import subprocess, sys
    run, fixture = note_run
    # The structural-only stage checks teaching structure; the full checker
    # also verifies actual widget fallbacks and link targets on the joined view.
    p = fixture/'sections/s1.html'
    original = p.read_text()
    p.write_text(original.replace('class="widget-static"', 'class="missing-static"'))
    flow.update_state(run, flow.load_state(run)['revision'], lambda s: dict(s, actions={
        **s['actions'], 'assemble-note': dict(s['actions']['assemble-note'], status='stale')}))
    cli('run', '--run', run, '--action', 'assemble-note')
    cli('run', '--run', run, '--action', 'structural-precheck')
    submit_review(note_run, 'style-audit')
    submit_review(note_run, 'content-review')
    proc = subprocess.run([sys.executable, SCRIPTS/'pack_cli.py', 'run', '--run', run,
                          '--action', 'precheck'], capture_output=True, text=True)
    state = flow.load_state(run)
    assert proc.returncode and state['actions']['precheck']['status'] == 'needs_fix'
    widget, = [r for r in state['findings'].values() if r['rule'] == 'widget-static-missing']
    assert widget['owner_task'] == 'author-s1'
    p.write_text(original)
    request_and_repair(note_run, [widget], 'fix-widget')
    cli('run', '--run', run, '--action', 'structural-precheck')
    submit_review(note_run, 'style-audit')
    submit_review(note_run, 'content-review')
    cli('run', '--run', run, '--action', 'precheck')
    assert flow.load_state(run)['findings'][widget['id']]['status'] == 'resolved'


def test_passing_envelope_cannot_hide_its_own_blocking_report(note_run):
    with pytest.raises(flow.FlowError, match='report'):
        submit_review(note_run, 'style-audit', report_text='## Important\n- [s1-mean] wrong source equation')


def test_visual_finding_requires_screenshot_and_can_be_repaired(note_run):
    from PIL import Image
    from test_pack_graph import cli
    run, _ = note_run
    def reach_browser():
        cli('run', '--run', run, '--action', 'structural-precheck')
        submit_review(note_run, 'content-review')
        submit_review(note_run, 'style-audit')
        cli('run', '--run', run, '--action', 'precheck')
    reach_browser()
    claim = flow.claim_task(run, 'browser-qa')
    flow.bind_task(run, 'browser-qa', claim['attempt'], 'visual reviewer')
    brief = flow._read(claim['brief'])
    report = Path(brief['report'])
    report.write_text('Synthetic clipping evidence in topic s1-mean.')
    path = Path(brief['receipt'])
    receipt = dict(schema_version=1, run_id=brief['run_id'], task_id='browser-qa', attempt=claim['attempt'],
        status='needs-fix', inputs=brief['inputs'], outputs=[], report=str(report), reviews=[str(report)],
        counts={'targets': brief['targets']}, unresolved=[defect('clipping')])
    path.write_text(json.dumps(receipt))
    assert flow.check_task(run, 'browser-qa', claim['attempt'], path)['status'] == 'failed'
    screen = report.with_suffix('.png')
    Image.new('RGB', (20, 20)).save(screen)
    receipt['outputs'].append(dict(path=str(screen), sha256=flow._sha(screen)))
    path.write_text(json.dumps(receipt))
    state = flow.accept_task(run, 'browser-qa', claim['attempt'], path)
    finding, = state['findings'].values()
    attempt = request_and_repair(note_run, [finding], 'correct-clipping')
    reach_browser()
    claim = flow.claim_task(run, 'browser-qa')
    flow.bind_task(run, 'browser-qa', claim['attempt'], 'visual reviewer')
    current = flow._read(claim['brief'])
    new_report = Path(current['report'])
    new_report.write_text('Synthetic corrected screen.')
    new_screen = new_report.with_suffix('.png')
    Image.new('RGB', (20, 20)).save(new_screen)
    visual = Path(current['required_outputs'][0])
    visual.parent.mkdir(parents=True)
    visual.write_text('{}')
    receipt.update(attempt=claim['attempt'], status='done', inputs=current['inputs'], report=str(new_report),
        reviews=[str(new_report)], outputs=[dict(path=str(p), sha256=flow._sha(p)) for p in (new_screen, visual)],
        unresolved=[], fix_results=[dict(finding_id=finding['id'], attempt=attempt, request_id='correct-clipping',
                                         outcome='resolved', evidence='compared corrected screen to source')])
    path = Path(current['receipt'])
    path.write_text(json.dumps(receipt))
    state = flow.accept_task(run, 'browser-qa', claim['attempt'], path)
    assert state['findings'][finding['id']]['status'] == 'resolved'


def test_precheck_rejects_pointer_to_one_independent_report(note_run):
    from test_pack_graph import cli
    from pack_parallel import run_action
    run, _ = note_run
    cli('run', '--run', run, '--action', 'structural-precheck')
    submit_review(note_run, 'style-audit')
    state = submit_review(note_run, 'content-review')
    lone = state['tasks']['style-audit']['artifacts']['learning-style-audit-note.json']
    flow.update_state(run, state['revision'], lambda s: dict(s, active_audit=lone))
    with pytest.raises(flow.FlowError, match='joined'):
        run_action(run, 'precheck')


def test_incidental_correction_needs_a_fresh_source_comparison(note_run):
    from test_pack_graph import cli
    import subprocess, sys
    run, fixture = note_run
    p = fixture/'sections/s1.html'
    original = p.read_text()
    p.write_text(original.replace('id="s1-mean"', 'id="wrong-topic"'))
    flow.update_state(run, flow.load_state(run)['revision'], lambda s: dict(s, actions={
        **s['actions'], 'assemble-note': dict(s['actions']['assemble-note'], status='stale')}))
    cli('run', '--run', run, '--action', 'assemble-note')
    state = submit_review(note_run, 'style-audit', [defect('topic-order')])
    original_finding, = state['findings'].values()
    # A structural correction starts before content-review has finished.
    subprocess.run([sys.executable, SCRIPTS/'pack_cli.py', 'run', '--run', run, '--action', 'structural-precheck'],
                   capture_output=True, text=True, check=False)
    fixes = [r for r in flow.load_state(run)['findings'].values() if r['review_id'] == 'structural-precheck']
    p.write_text(original)
    request_and_repair(note_run, fixes, 'fix-structure-first')
    with pytest.raises(flow.FlowError):
        submit_review(note_run, 'style-audit')
    claim = flow.load_state(run)['tasks']['style-audit']
    flow.release_task(run, 'style-audit', claim['attempt'], 'add required source comparison')
    state = submit_review(note_run, 'style-audit', reconciliations=[dict(finding_id=original_finding['id'],
        prior_review_attempt=original_finding['review_attempt'], evidence='corrected source topic and order compared')])
    assert state['findings'][original_finding['id']]['status'] == 'resolved'
    assert not state['findings'][original_finding['id']]['unsuccessful_attempts']
    assert not state.get('active_audit')
