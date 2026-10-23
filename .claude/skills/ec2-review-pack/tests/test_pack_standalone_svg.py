"""Real converter outputs, synthetic explicit visual evidence, no production approval."""
import json
from pathlib import Path
import pytest
from _util import SCRIPTS
import pack_flow as f
from pack_support import make_run, workflow_until, workflow_action, workflow_accept


def converted(tmp_path, *, svg_count=1, problems=0, owner='workers'):
    _, run = make_run(tmp_path)
    f.update_state(run, 0, lambda s: dict(s, fixture_svg_count=svg_count))
    workflow_until(run, 'convert-md', problems=problems)
    def owner_change(s):
        s['capabilities']['browser_owner'] = owner
        return s
    f.update_state(run, f.load_state(run)['revision'], owner_change)
    workflow_action(run, 'convert-md')
    return run


@pytest.mark.parametrize('problems', [0, 1])
def test_real_conversion_requires_standalone_review_before_final_or_child(tmp_path, problems):
    run = converted(tmp_path, problems=problems)
    state = f.load_state(run)
    nxt = f.next_work(run, slots=3)
    assert nxt['kind'] == 'dispatch'
    assert nxt['tasks'][0]['id'] == 'standalone-svg-qa'
    assert state['phase'] == 8 and state['explain_run'] is None
    assert 'final-check' not in state['actions']
    task = state['tasks']['standalone-svg-qa']
    brief = json.loads(Path(task['brief']).read_text())
    actual = [x for x in state['actions']['convert-md']['outputs'] if x['path'].endswith('.svg')]
    assert task['targets'] == [x['path'] for x in actual]
    assert set(x['path'] for x in brief['inputs']) >= set(x['path'] for x in state['actions']['convert-md']['outputs'])
    attempt = f.claim_task(run, task['id'])['attempt']
    f.bind_task(run, task['id'], attempt, 'synthetic-svg-reviewer')
    assert f.next_work(run, slots=3)['kind'] == 'wait'


@pytest.mark.parametrize('owner,slots,kind', [('workers', 0, 'wait'), ('workers', 2, 'dispatch'), ('main', 0, 'review_locally'), ('unavailable', 2, 'blocked')])
def test_standalone_owner_slots_and_read_only_queries(tmp_path, owner, slots, kind):
    run = converted(tmp_path, owner=owner)
    before = {str(p): p.read_bytes() for p in run.rglob('*') if p.is_file()}
    assert f.next_work(run, slots=slots)['kind'] == kind
    f.inspect_state(run)
    assert before == {str(p): p.read_bytes() for p in run.rglob('*') if p.is_file()}


def test_real_zero_svg_conversion_skips_only_standalone_review(tmp_path):
    run = converted(tmp_path, svg_count=0)
    state = f.load_state(run)
    assert 'standalone-svg-qa' not in state['tasks']
    assert state['tasks']['browser-qa']['status'] == 'done'
    assert state['standalone_svg_qa']['status'] == 'not_required'
    assert f.next_work(run, slots=0)['action'] == 'final-check'


@pytest.mark.parametrize('suffix', ['.svg', '.md'])
def test_emitted_file_change_invalidates_standalone_and_child(tmp_path, suffix):
    run = converted(tmp_path, problems=1)
    workflow_accept(run, 'standalone-svg-qa')
    original = f.load_state(run)['explain_run']
    assert original
    output = next(Path(x['path']) for x in f.load_state(run)['actions']['convert-md']['outputs'] if x['path'].endswith(suffix))
    output.write_bytes(output.read_bytes() + b'\nchanged')
    view = f.inspect_state(run)
    assert view['tasks']['standalone-svg-qa']['status'] == 'stale'
    assert view['tasks']['child-coordinator']['status'] == 'stale'
    assert view['explain_run'] is None and original in view['stale_explain_runs']


@pytest.mark.parametrize('defect', ['missing_input', 'changed_input', 'omitted_target', 'fake_png', 'missing_report'])
def test_standalone_receipt_rejects_missing_or_false_evidence(tmp_path, defect):
    run = converted(tmp_path)
    def damage():
        state = f.load_state(run); task = state['tasks']['standalone-svg-qa']
        receipt = run / 'work/standalone-svg-qa' / (task['attempt'] + '-report.json')
        data = json.loads(receipt.read_text())
        svg = next(x for x in data['inputs'] if x['path'].endswith('.svg'))
        if defect == 'missing_input': data['inputs'].remove(svg)
        if defect == 'changed_input': Path(svg['path']).write_text('changed')
        if defect == 'omitted_target': data['counts']['targets'] = []
        if defect == 'fake_png':
            png = next(x for x in data['outputs'] if x['path'].endswith('.png'))
            Path(png['path']).write_bytes(b'not a PNG'); png['sha256'] = f._sha(Path(png['path']))
        if defect == 'missing_report': Path(data['report']).unlink()
        receipt.write_text(json.dumps(data))
    with pytest.raises(f.FlowError): workflow_accept(run, 'standalone-svg-qa', before_accept=damage)
    assert f.load_state(run)['tasks']['standalone-svg-qa']['status'] != 'done'


def test_standalone_actual_png_explicit_synthetic_review_accepts(tmp_path):
    run = converted(tmp_path)
    workflow_accept(run, 'standalone-svg-qa')
    state = f.load_state(run)
    assert state['tasks']['standalone-svg-qa']['status'] == 'done'
    assert state['actions']['final-check']['dependencies'] == ['standalone-svg-qa']
    assert f.next_work(run, slots=0)['action'] == 'final-check'


def test_absent_expected_svg_is_not_treated_as_zero(tmp_path):
    run = converted(tmp_path)
    state = f.load_state(run)
    svg = next(Path(x['path']) for x in state['actions']['convert-md']['outputs'] if x['path'].endswith('.svg'))
    svg.unlink()
    assert f.inspect_state(run)['actions']['convert-md']['status'] == 'stale'
    assert f.next_work(run, slots=3)['action'] == 'convert-md'
    assert f.load_state(run)['standalone_svg_qa']['status'] == 'required'


def test_each_svg_requires_its_own_decodable_screenshot(tmp_path):
    run = converted(tmp_path, svg_count=2)
    def damage():
        task = f.load_state(run)['tasks']['standalone-svg-qa']
        receipt = run / 'work/standalone-svg-qa' / (task['attempt'] + '-report.json')
        data = json.loads(receipt.read_text())
        png = next(x for x in data['outputs'] if x['path'].endswith('.png'))
        data['outputs'].remove(png)
        receipt.write_text(json.dumps(data))
    with pytest.raises(f.FlowError, match='every SVG'):
        workflow_accept(run, 'standalone-svg-qa', before_accept=damage)


def test_cli_routes_standalone_review_without_writing(tmp_path):
    from test_pack_cli import call
    run = converted(tmp_path, owner='main')
    before = (run / 'run-status.json').read_bytes()
    process, response = call('next', '--run', run, '--slots', '0')
    assert process.returncode == 0 and response['phase'] == 8
    assert response['next']['kind'] == 'review_locally'
    assert before == (run / 'run-status.json').read_bytes()
