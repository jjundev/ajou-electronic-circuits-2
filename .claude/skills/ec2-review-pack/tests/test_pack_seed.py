"""Seeding a new RUN from a withheld RUN carries only current, verified work."""
import json
from pathlib import Path

import pytest
from pack_support import make_run, workflow_accept, workflow_until
import pack_flow as flow
from pack_seed import _Copier


def _withheld(tmp_path):
    repo, old = make_run(tmp_path)
    workflow_until(old, 'prepare-pack')
    flow.update_state(old, flow.load_state(old)['revision'], lambda s: dict(s, status='withheld'))
    return repo, old


def _seed(repo, old, tmp_path, **kw):
    new = tmp_path / 'run 이어받기'
    return new, flow.init_run(repo, new, '0909', browser_owner='workers', pdf_owner='workers', seed_from=old, **kw)


def test_carries_accepted_work_and_redoes_named_task(tmp_path):
    repo, old = _withheld(tmp_path)
    note = tmp_path / 'redo.md'; note.write_text('pole_naming 정의를 섹션 공통으로', encoding='utf-8')
    new, state = _seed(repo, old, tmp_path, redo=['author-s1'], redo_note=note)
    seeded = state['seeded_from']
    assert seeded['carried'] == ['source-prep', 'stt-0909', 'scope-draft', 'selection', 'scope-final', 'author-why']
    assert seeded['rejected'] == [] and state['fix_rounds'] == {'content': 0, 'machine_browser': 0}
    assert state['tasks']['author-s1']['status'] == 'pending'
    assert state['tasks']['author-why']['carried']['run_id'] == flow.load_state(old)['run_id']
    nxt = flow.next_work(new, slots=3)
    assert [t['id'] for t in nxt['tasks']] == ['author-s1']
    brief = json.loads(Path(state['tasks']['author-s1']['brief']).read_text(encoding='utf-8'))
    assert brief['request_paths'][0] == str(new / 'requests/seed-redo/redo.md')
    assert any('seed-previous' in p and p.endswith('sections/s1.html') for p in brief['request_paths'])
    assert all(Path(p).is_relative_to(new) for p in [*brief['allowed_outputs'], *brief['allowed_output_roots']])
    for task in state['tasks'].values():
        if task.get('carried'):
            assert all(item['path'].startswith(str(repo)) or item['path'].startswith(str(new))
                       for item in task['receipt']['verified_files'])
    workflow_accept(new, 'author-s1')
    assert flow.next_work(new, slots=3) == dict(kind='run', tasks=[], action='prepare-pack', reason='required machine action')


def test_changed_stt_carries_nothing(tmp_path):
    repo, old = _withheld(tmp_path)
    (repo / 'STT/0909 전회2.md').write_text('바뀐 STT', encoding='utf-8')
    _, state = _seed(repo, old, tmp_path)
    assert state['seeded_from']['carried'] == []
    assert state['seeded_from']['rejected'][0]['reason'] == 'frozen STT/profile inputs changed'
    assert state['tasks']['source-prep']['status'] == 'pending'


def test_tampered_output_rejects_only_that_task(tmp_path):
    repo, old = _withheld(tmp_path)
    (old / 'sections/why.html').write_text('tampered', encoding='utf-8')
    _, state = _seed(repo, old, tmp_path)
    assert 'author-why' not in state['seeded_from']['carried'] and 'author-s1' in state['seeded_from']['carried']
    assert [r['id'] for r in state['seeded_from']['rejected']] == ['author-why']
    assert state['tasks']['author-why']['status'] == 'pending'


@pytest.mark.parametrize('status', ['recovery_required', 'ready'])
def test_rejects_unsafe_seed_status(tmp_path, status):
    repo, old = _withheld(tmp_path)
    flow.update_state(old, flow.load_state(old)['revision'], lambda s: dict(s, status=status, backups={'basic': {}}))
    with pytest.raises(flow.FlowError, match='seed RUN must be withheld'):
        _seed(repo, old, tmp_path)


def test_rejects_unknown_redo_and_redo_without_seed(tmp_path):
    repo, old = _withheld(tmp_path)
    with pytest.raises(flow.FlowError, match='unknown redo task'):
        _seed(repo, old, tmp_path, redo=['author-nope'])
    with pytest.raises(flow.FlowError, match='require --seed-from'):
        flow.init_run(repo, tmp_path / 'other', '0909', redo=['author-s1'])


def test_copier_rewrites_embedded_run_paths(tmp_path):
    old, new = tmp_path / 'r4', tmp_path / 'r5'
    (old / 'briefs').mkdir(parents=True); new.mkdir()
    source = old / 'briefs/s0.json'
    source.write_text(json.dumps({'out': str(old / 'sections/s0.html'), 'other': str(old) + '0/x'}), encoding='utf-8')
    record = _Copier(old, new).file(source, flow._sha(source))
    data = json.loads(Path(record['path']).read_text(encoding='utf-8'))
    assert data == {'out': str(new / 'sections/s0.html'), 'other': str(old) + '0/x'}
    assert record['sha256'] == flow._sha(Path(record['path']))
