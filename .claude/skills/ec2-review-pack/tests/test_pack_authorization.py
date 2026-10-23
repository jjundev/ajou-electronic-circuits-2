"""Explicit user exception is per RUN, bounded, durable and auditable."""
import json
from pathlib import Path
import pytest
from _util import SCRIPTS
import pack_flow as f
from pack_support import make_run, install_task
from test_pack_cli import call


def request(run, tid, number, category='machine_browser'):
    detail = run / 'repair.md'; detail.write_text('Synthetic repair request')
    path = run / 'fix.json'
    path.write_text(json.dumps(dict(id=f'{category}-{number}', category=category,
        items=[dict(task_id=tid, request_path=str(detail))])))
    return path


def authorization(run, **changes):
    data = dict(schema_version=1, id='user-extra-1', run_id=f.load_state(run)['run_id'],
        category='machine_browser', extra_rounds=1, approved_by='user',
        human_request='Allow one extra machine/browser repair for this RUN.',
        request_ref='current chat human message', reason='Repair observed keyboard regression')
    data.update(changes)
    path = run / 'user-authorization.json'; path.write_text(json.dumps(data))
    return path


def test_default_third_round_still_rejected(tmp_path):
    _, run = make_run(tmp_path); tid = install_task(run)
    for n in (1, 2): f.request_fixes(run, request(run, tid, n))
    with pytest.raises(f.FlowError, match='budget'): f.request_fixes(run, request(run, tid, 3))
    assert f.load_state(run)['fix_rounds']['machine_browser'] == 2


def test_grant_persists_one_extra_without_resetting_counters(tmp_path):
    _, run = make_run(tmp_path); tid = install_task(run)
    for n in (1, 2): f.request_fixes(run, request(run, tid, n))
    path = authorization(run)
    f.authorize_extra_fix(run, path)
    state = f.load_state(run)
    assert state['fix_rounds'] == dict(content=0, machine_browser=2)
    record = state['extra_fix_authorization']
    evidence = Path(record['path'])
    assert evidence != path and evidence.read_bytes() and f._sha(evidence) == record['sha256']
    path.unlink()  # External submission is not the durable authorization.
    f.request_fixes(run, request(run, tid, 3))
    f.request_fixes(run, request(run, tid, 3))  # Existing request idempotence, no extra count.
    assert f.load_state(run)['fix_rounds']['machine_browser'] == 3
    with pytest.raises(f.FlowError, match='budget'): f.request_fixes(run, request(run, tid, 4))
    f.request_fixes(run, request(run, tid, 1, 'content'))
    with pytest.raises(f.FlowError, match='budget'): f.request_fixes(run, request(run, tid, 2, 'content'))
    with pytest.raises(f.FlowError):
        f.authorize_extra_fix(run, authorization(run))
    with pytest.raises(f.FlowError):
        f.authorize_extra_fix(run, authorization(run, id='another-user-grant'))
    assert f.load_state(run)['fix_rounds'] == dict(content=1, machine_browser=3)


@pytest.mark.parametrize('changes', [dict(category='content'), dict(extra_rounds=2),
    dict(extra_rounds=True), dict(approved_by='main'), dict(human_request=''),
    dict(request_ref=''), dict(reason=''), dict(run_id='other-run'), dict(schema_version=2)])
def test_invalid_grants_do_not_change_state(tmp_path, changes):
    _, run = make_run(tmp_path)
    path = authorization(run, **changes)
    before = (run / 'run-status.json').read_bytes()
    with pytest.raises(f.FlowError): f.authorize_extra_fix(run, path)
    assert (run / 'run-status.json').read_bytes() == before
    assert not (run / 'authorizations/machine-browser-extra.json').exists()


def test_authorization_evidence_and_state_are_immutable(tmp_path):
    _, run = make_run(tmp_path)
    f.authorize_extra_fix(run, authorization(run))
    state = f.load_state(run)
    with pytest.raises(f.FlowError):
        f.update_state(run, state['revision'], lambda s: {k:v for k,v in s.items() if k != 'extra_fix_authorization'})
    Path(state['extra_fix_authorization']['path']).write_text('{}')
    with pytest.raises(f.FlowError): f.load_state(run)


def test_cli_authorization_is_compact_and_missing_grant_fails(tmp_path):
    _, run = make_run(tmp_path)
    assert call('task', 'authorize-fix', '--run', run, '--authorization', run / 'missing.json')[0].returncode == 1
    path = authorization(run)
    assert call('task', 'authorize-fix', '--run', run, '--authorization', path)[0].returncode == 0
    assert call('task', 'authorize-fix', '--run', run, '--authorization', path)[0].returncode == 1
    assert f.load_state(run)['fix_rounds'] == dict(content=0, machine_browser=0)


def test_grant_cannot_transfer_to_another_run(tmp_path):
    _, run = make_run(tmp_path / 'first')
    path = authorization(run)
    f.authorize_extra_fix(run, path)
    _, other = make_run(tmp_path / 'second')
    with pytest.raises(f.FlowError): f.authorize_extra_fix(other, path)
    assert 'extra_fix_authorization' not in f.load_state(other)
    assert f._fix_limit(f.load_state(other), 'machine_browser') == 2
