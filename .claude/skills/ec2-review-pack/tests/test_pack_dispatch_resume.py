"""Dispatch and recovery against isolated RUNs. All judgments are fixture evidence."""
from pathlib import Path
import json

from pack_support import make_run
import pack_flow as f
from test_pack_approvals import blind_run, compact, write
from test_pack_cli import call
from test_pack_graph import seed, selected


def invoke(run, *args):
    proc, data = call(*args, '--run', run)
    assert proc.returncode == 0, data
    if data['error_code'] == 'details_compacted':
        return f._read(data['details_path'])
    return data


def solver(run, reviewer):
    brief, decisions, submission = compact(run, 'explain-blind', reviewer)
    write(decisions, {key: dict(status='pass', method='exact', conclusion=reviewer, evidence='fixture calculation')
                      for key in brief['approval_plan']['pending']})
    args = ['--task', 'explain-blind', '--attempt', brief['attempt']]
    invoke(run, 'task', 'build-receipt', *args, '--submission', submission)
    invoke(run, 'task', 'check', *args, '--receipt', brief['receipt'])
    return dict(task_id='explain-blind', attempt=brief['attempt'], receipt=brief['receipt'])


def batch(run, *items):
    path = write(run/'batch.json', list(items))
    return invoke(run, 'task', 'accept-batch', '--submissions', path)


def test_batch_duplicate_is_idempotent(tmp_path):
    run, _ = blind_run(tmp_path)
    item = solver(run, 'fixture solver')
    result = batch(run, item, item)
    assert [r['status'] for r in result['items']] == ['accepted', 'already_accepted']
    before = f.load_state(run)
    replay = batch(run, item)
    assert replay['items'][0]['status'] == 'already_accepted'
    assert f.load_state(run)['approval_ledger'] == before['approval_ledger']
    assert f.load_state(run)['tasks'] == before['tasks']
    fake = batch(run, dict(item, receipt=str(run/'other.json')))
    assert fake['items'][0]['status'] == 'rejected'


def test_late_receipt_cannot_replace_new_attempt(tmp_path):
    run, _ = blind_run(tmp_path)
    first = solver(run, 'earlier')
    invoke(run, 'task', 'release', '--task', first['task_id'], '--attempt', first['attempt'],
           '--reason', 'host confirmed stopped')
    second = solver(run, 'successor')
    result = batch(run, second, first)
    assert result['items'][0]['status'] == 'accepted'
    new_output = Path(f.load_state(run)['tasks']['explain-blind']['artifacts']['independent.json'])
    successor_bytes = new_output.read_bytes()
    late = batch(run, first)['items'][0]
    assert late['error_code'] == 'inactive_attempt'
    assert new_output.read_bytes() == successor_bytes
    assert 'successor' in successor_bytes.decode()


def test_resume_reuses_completed_child_and_marks_gap(tmp_path, monkeypatch):
    monkeypatch.setenv("EC2_CLI_TRACE_DIR", str(tmp_path/"trace"))
    run, _ = blind_run(tmp_path)
    item = solver(run, 'retained solver')
    attempt = item['attempt']
    state = f.load_state(run)
    host = dict(run_id=state['run_id'], task_id='explain-blind', attempt=attempt,
                agent_id='retained solver', status='completed', receipt=item['receipt'],
                host_gap=dict(interrupted='2026-01-01T10:00:00Z', resumed='2026-01-01T11:40:00Z'))
    foreign = write(Path(item['receipt']).parent/'self-reported.json', host)
    mapping = write(run/'stops.json', {attempt:str(foreign)})
    assert invoke(run, 'resume', '--stopped-attempts', mapping)['rejected']
    assert f.load_state(run)['tasks']['explain-blind']['status'] == 'running'
    stop = write(run/'host-stops'/f'{attempt}.json', host)
    write(mapping, {attempt:str(stop)})
    resumed = invoke(run, 'resume', '--stopped-attempts', mapping)
    assert resumed['reused'] == ['explain-blind']
    invoke(run, 'resume', '--stopped-attempts', mapping)
    # Supply actual paths for the test-only completed predecessor records.
    def add_paths(state):
        for name, file in [('scope-draft','scope.json'),('selection','selection.json')]:
            state['tasks'][name]['artifacts'] = {file:str(write(run/file, {}))}
        return state
    f.update_state(run, f.load_state(run)['revision'], add_paths)
    report = f._read(invoke(run, 'report')['details_path'])
    metrics = report['metrics']
    assert metrics['confirmed_host_gap_seconds'] == 6000
    recorded = [e for e in metrics['events'] if e['attempt']==attempt]
    completed = next(e for e in recorded if e['event']=='completed')
    accepted = next(e for e in recorded if e['event']=='accepted')
    assert completed['at'] < accepted['at']
    assert 'receipt_sha256' in completed
    assert metrics['brief_bytes'] > 0
    assert metrics['cli_counts']['task check'] == 1
    assert 'model_usage' not in metrics
    assert metrics['attempts'][attempt]['claim_to_complete_seconds'] >= 0
    assert metrics['attempts'][attempt]['ready_to_claim_seconds'] >= 0
    assert {'interrupted','resumed','completed','accepted','reused'} <= {e['event'] for e in metrics['events']}


def test_advance_stops_at_review_gate(tmp_path):
    state = selected(tmp_path, ['P1'])
    state['concept_check_enabled'] = False
    seed(state, ['scope-final','author-why','stage-problem-index','explain-author','explain-blind','child-coordinator',
                 'explain-verify','build-answers','build-problems','assemble-note','structural-precheck','style-audit',
                 'content-review','precheck','browser-qa','convert-md'])
    state['converted_assets'] = {'svgs':[]}
    run = Path(state['run'])
    f.update_state(run, state['revision'], lambda _: f.refresh_tasks(state))
    advanced = invoke(run, 'advance', '--max-actions','8')
    assert advanced['waiting_for'] == ['pdf-qa']
    assert advanced['executed'] == []
    assert not f._done(f.inspect_state(run), 'publish-pack')


def test_legacy_graph_is_not_upgraded_by_resume(tmp_path):
    _, run = make_run(tmp_path)
    path = write(run/'stops.json', {})
    proc, data = call('resume','--run',run,'--stopped-attempts',path)
    assert proc.returncode == 1 and data['error_code'] == 'validation_failed'
    assert invoke(run, 'next', '--slots', '1')['next']['kind'] == 'dispatch'


def test_resume_rejects_machine_marker_with_no_bound_outputs(tmp_path):
    from test_pack_graph import parallel
    _, run, state = parallel(tmp_path)
    tid, attempt = 'candidate-index', 'synthetic-machine'
    root = run/'attempts'/tid/attempt
    path = write(root/'stopped.json', dict(task_id=tid, attempt=attempt, input_version={}, status='done',
                                           artifacts={}, verified_files=[dict(path=str(run/'learning-style.json'),
                                                                               sha256=f._sha(run/'learning-style.json'))]))
    row = state['actions'][tid]
    row.update(status='running', attempt=attempt, attempt_dir=str(root), input_version={})
    f.update_state(run, state['revision'], lambda _: state)
    mapping = write(run/'stops.json', {attempt:str(path)})
    result = invoke(run, 'resume', '--stopped-attempts', mapping)
    assert result['rejected'] and not f._done(f.load_state(run),tid)


def test_stopped_unfinished_worker_release_replays_without_resetting_successor(tmp_path):
    run, _ = blind_run(tmp_path)
    first = invoke(run, 'task', 'claim','--task','explain-blind')['next']
    attempt = first['attempt']
    path = write(run/'host-stops'/f'{attempt}.json', dict(run_id=f.load_state(run)['run_id'], task_id='explain-blind',
                                                         attempt=attempt, agent_id=None, status='stopped'))
    mapping = write(run/'stops.json',{attempt:str(path)})
    assert invoke(run, 'resume','--stopped-attempts',mapping)['released'] == ['explain-blind']
    second = invoke(run, 'task','claim','--task','explain-blind')['next']
    replay = invoke(run, 'resume','--stopped-attempts',mapping)
    assert replay['released'] == ['explain-blind'] and not replay['rejected']
    assert f.load_state(run)['tasks']['explain-blind']['attempt'] == second['attempt']


def test_cli_advances_one_action_and_recovers_its_real_stopped_marker(tmp_path, monkeypatch):
    import shutil
    from _util import REPO
    from test_pack_graph import parallel
    repo,run,state = parallel(tmp_path)
    for source in ('교과서/마이크로전자회로/_tools','from_the_past/md/_tools'):
        shutil.copytree(REPO/source, repo/source)
    for module in (REPO/'workbook').glob('*.py'):
        shutil.copyfile(module,repo/'workbook'/module.name)
    invoke(run,'task','claim','--task','source-prep')
    result = invoke(run,'advance','--max-actions','1')
    assert result['executed'] == ['candidate-index']
    state = f.load_state(run)
    row = state['actions']['candidate-index']
    root = Path(row['attempt_dir'])
    marker = root/'stopped.json'
    original = marker.read_bytes()
    # Recreate a controller crash between durable stop and state adoption.
    row.update(status='running')
    row.pop('artifacts')
    f.update_state(run,state['revision'],lambda _:state)
    mapping = write(run/'stops.json',{row['attempt']:str(marker)})
    import pack_actions as actions
    validate = actions.verify_machine_stop
    def concurrent_reader(*args):
        with f._locked(run):
            return validate(*args)
    monkeypatch.setattr(actions,'verify_machine_stop',concurrent_reader)
    result = actions.resume_run(run,stopped_attempts=f._read(mapping))
    assert result['reused'] == ['candidate-index'], result
    assert invoke(run,'resume','--stopped-attempts',mapping)['reused'] == ['candidate-index']
    assert (root/'candidates.json').is_file() and marker.read_bytes() == original
    assert f._done(f.inspect_state(run),'candidate-index')


def test_quiz_crash_reuses_only_matching_public_receipt_marker_and_blind_proof(tmp_path,monkeypatch):
    import test_pack_graph as scenario
    original_cli = scenario.cli
    observations = []
    def cli(*args):
        result = original_cli(*args)
        if args[:3] == ('run','--action','publish-pack'):
            run = Path(args[-1])
            state = f.load_state(run)
            row = state['actions']['publish-pack']
            journal = Path(state['publication']['journal'])
            mapping = write(run/'stops.json',{row['attempt']:str(journal)})
            foreign = write(run/'stops-foreign.json',{row['attempt']:str(run/'foreign/journal.json')})
            row['status'] = 'running'
            state['actions']['final-check'].update(status='pending',attempt=None)
            state.update(status='ready',phase=9)
            f.update_state(run,state['revision'],lambda _:state)
            assert invoke(run,'resume','--stopped-attempts',foreign)['rejected']
            note = next((Path(state['repo'])/'복습노트/0909').glob('정리노트*.html'))
            approved = note.read_bytes()
            note.write_bytes(b'external change')
            assert invoke(run,'resume','--stopped-attempts',mapping)['rejected']
            assert f.load_state(run)['status'] == 'recovery_required'
            assert note.read_bytes() == b'external change'
            note.write_bytes(approved)
            resumed = invoke(run,'resume','--stopped-attempts',mapping)
            assert resumed['reused'] == ['publish-pack'], resumed
        if args[:3] != ('run','--action','concept-publish'):
            return result
        run = Path(args[-1])
        state = f.load_state(run)
        row = state['actions']['concept-publish']
        row.update(status='running')
        private = Path(row['attempt_dir'])
        for name in ('stopped.json','result.json','concept-check-result.json'):
            (private/name).unlink()
        for key in ('verified_files','source_inputs','artifacts'):
            row.pop(key)
        f.update_state(run,state['revision'],lambda _:state)
        path = run/'concept-check-result.json'
        mapping = write(run/'stops.json',{row['attempt']:str(path)})
        before = path.read_bytes()
        write(path,dict(f._read(path), action_attempt='wrong-owner'))
        assert invoke(run,'resume','--stopped-attempts',mapping)['rejected']
        path.write_bytes(before)
        certificate = Path(state['tasks']['concept-review']['receipt']['blind_certificate']['path'])
        certificate.rename(certificate.with_suffix('.held'))
        assert invoke(run,'resume','--stopped-attempts',mapping)['rejected']
        certificate.with_suffix('.held').rename(certificate)
        resumed = invoke(run,'resume','--stopped-attempts',mapping)
        assert resumed['reused'] == ['concept-publish'], resumed
        observations.append(f.concept_check_result(f.inspect_state(run))['action_attempt'])
        assert path.read_bytes() == before
        return result
    monkeypatch.setattr(scenario, 'cli', cli)
    scenario.exercise_zero_problem_cli(tmp_path,monkeypatch,None)
    assert len(observations) == 1


def test_batch_rechecks_input_after_validation_before_revision_commit(tmp_path,monkeypatch):
    import pack_parallel as runner
    run, questions = blind_run(tmp_path)
    item = solver(run,'original solver')
    original = f.update_state
    def race(target, revision, change):
        if questions.is_file():
            questions.unlink()
        return original(target,revision,change)
    monkeypatch.setattr(f,'update_state',race)
    result = runner.accept_batch(run, [item])
    assert result['items'][0]['status'] == 'rejected'
    assert not f._done(f.load_state(run),'explain-blind')


def test_host_can_release_confirmed_stopped_private_machine_only(tmp_path):
    from test_pack_graph import parallel
    _, run, state = parallel(tmp_path)
    tid = 'render-preflight'
    root = run/'attempts'/tid/'crashed-fixture'
    root.mkdir(parents=True)
    row = state['actions'][tid]
    row.update(status='running',attempt=root.name,attempt_dir=str(root),input_version={})
    f.update_state(run,state['revision'],lambda _:state)
    path = write(run/'host-stops'/f'{root.name}.json',dict(run_id=state['run_id'], task_id=tid,
                                                         attempt=root.name,agent_id=None,status='stopped'))
    mapping = write(run/'stops.json',{root.name:str(path)})
    with f._locked(root.parent):
        assert invoke(run,'resume','--stopped-attempts',mapping)['rejected']
    assert invoke(run,'resume','--stopped-attempts',mapping)['released'] == [tid]
    assert tid in invoke(run,'next','--slots','1')['next']['actions']


def test_advance_keeps_failed_action_blocked_until_explicit_retry(tmp_path):
    from test_pack_graph import parallel
    _, run,state = parallel(tmp_path)
    state['actions']['candidate-index'].update(status='failed',attempt='failed-fixture',error_code='execution_failed')
    f.update_state(run,state['revision'],lambda _:state)
    assert 'candidate-index' in invoke(run,'advance','--max-actions','4')['blocked']
    metrics = f._read(invoke(run,'report')['details_path'])['metrics']
    assert 'candidate-index' in metrics['blocker_ids']
