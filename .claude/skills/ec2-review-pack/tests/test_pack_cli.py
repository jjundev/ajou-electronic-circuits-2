"""CLI integration tests; synthetic receipts are fixture evidence only."""
import concurrent.futures
import json
import os
from pathlib import Path
import subprocess
import sys
import pytest
from _util import SCRIPTS
from pack_support import make_run, install_task, receipt_for

CLI = SCRIPTS / 'pack_cli.py'
def call(*args, cwd=None, env=None):
    p = subprocess.run([sys.executable, str(CLI), *map(str,args)], cwd=cwd, env=env,
                       capture_output=True, encoding='utf-8')
    assert p.stderr == ''
    assert len(p.stdout) <= 2000
    data = json.loads(p.stdout)
    assert data['schema_version'] == 1
    return p, data

def test_commands_work_from_foreign_cwd_with_unicode_paths(tmp_path):
    repo, run = make_run(tmp_path)
    other = tmp_path / '다른 곳'; other.mkdir()
    new = tmp_path / '새 실행'
    assert call('init','--repo',repo,'--run',new,'--range','0909','--allow-tmp',cwd=other)[0].returncode == 0
    before = {str(p): (p.stat().st_mtime_ns,p.read_bytes()) for p in run.rglob('*') if p.is_file()}
    for cmd in ('status','next'):
        assert call(cmd,'--run',run,*(['--slots','1'] if cmd=='next' else []),cwd=other)[0].returncode == 0
    assert before == {str(p): (p.stat().st_mtime_ns,p.read_bytes()) for p in run.rglob('*') if p.is_file()}


def test_new_init_defaults_to_parallel(tmp_path):
    repo, old = make_run(tmp_path)
    new = tmp_path / 'parallel'
    explicit_legacy = tmp_path / 'legacy'
    args = ('--repo', repo, '--range', '0909', '--allow-tmp')

    result, data = call('init', '--run', new, *args)
    assert result.returncode == 0
    assert json.loads((new / 'run-status.json').read_text())['workflow'] == 'parallel'
    assert set(data['next']['actions']) == {'candidate-index', 'render-preflight'}

    result, data = call('init', '--run', explicit_legacy, *args, '--workflow', 'legacy')
    assert result.returncode == 0
    assert json.loads((explicit_legacy / 'run-status.json').read_text())['workflow'] == 'legacy'
    assert data['next']['kind'] == 'wait'

    path = old / 'run-status.json'
    historical = json.loads(path.read_text())
    historical.pop('workflow')
    path.write_text(json.dumps(historical))
    result, data = call('next', '--run', old, '--slots', '1')
    assert result.returncode == 0
    assert data['next']['kind'] == 'dispatch'
    assert data['next']['tasks'][0]['id'] == 'source-prep'

def test_next_without_slots_dispatches_every_ready_worker(tmp_path):
    repo, _ = make_run(tmp_path)  # only the repo is reused; the RUN below is a new parallel one
    new = tmp_path / 'p'
    assert call('init', '--repo', repo, '--run', new, '--range', '0909', '--allow-tmp')[0].returncode == 0
    p, data = call('next', '--run', new)
    assert p.returncode == 0
    assert data['next']['dispatch'] == ['source-prep']


@pytest.mark.parametrize('args', [[],['--help'],['task','--help'],['wat'],['next'],['run','--run','x','--action','evil']])
def test_every_response_is_one_json_under_2000_chars(args):
    call(*args)

def test_long_errors_and_argparse_errors_are_bounded_json(tmp_path):
    assert call('wat' * 3000)[0].returncode == 2
    from pack_cli import format_result
    s=format_result({'status':'failed','reason':'x'*10000,'details_path':'p'*6000,'next':{'tasks':[{'brief':'x'*5000}]*100}})
    assert len(s)<=2000 and json.loads(s)['error_code']

def test_unknown_command_never_runs_shell(tmp_path):
    target=tmp_path/'executed'
    assert call('run','--run',tmp_path,'--action',f'echo p > {target}')[0].returncode==2
    assert not target.exists()

def test_init_next_claim_bind_accept_round_trip(tmp_path):
    _,run=make_run(tmp_path)
    tid=install_task(run)
    p,d=call('task','claim','--run',run,'--task',tid)
    assert p.returncode==0
    attempt=d['next']['attempt']
    assert call('task','bind','--run',run,'--task',tid,'--attempt',attempt,'--agent-id','fixture')[0].returncode==0
    receipt=receipt_for(run,tid,attempt)
    assert call('task','accept','--run',run,'--task',tid,'--attempt',attempt,'--receipt',receipt)[0].returncode==0

def test_two_cli_claims_cannot_dispatch_same_task(tmp_path):
    _,run=make_run(tmp_path); tid=install_task(run)
    with concurrent.futures.ThreadPoolExecutor(2) as pool:
        results=list(pool.map(lambda _:call('task','claim','--run',run,'--task',tid)[0].returncode,range(2)))
    assert sorted(results)==[0,1]

def test_claim_without_bind_stays_reserved_after_restart(tmp_path):
    _,run=make_run(tmp_path)
    assert call('task','claim','--run',run,'--task','source-prep')[0].returncode==0
    assert call('next','--run',run,'--slots','3')[1]['next']['kind']=='wait'
    assert call('task','claim','--run',run,'--task','source-prep')[0].returncode==1

def test_report_returns_partial_for_withheld(tmp_path):
    import pack_flow as f
    _,run=make_run(tmp_path)
    f.update_state(run,f.load_state(run)['revision'],lambda s:dict(s,status='withheld'))
    p,d=call('report','--run',run)
    assert p.returncode==0 and d['status']=='withheld' and d['counts']['partial']==1
    assert json.loads(Path(d['details_path']).read_text())['status']=='withheld'

def test_import_noise_is_captured_and_queries_do_not_write(tmp_path):
    _,run=make_run(tmp_path)
    site=tmp_path/'site';site.mkdir()
    (site/'sitecustomize.py').write_text("import builtins\nold=builtins.__import__\ndef noisy(name,*a,**k):\n if name=='pack_flow':\n  import os\n  os.write(1,b'native noise\\n');os.write(2,b'warning noise\\n')\n return old(name,*a,**k)\nbuiltins.__import__=noisy\n")
    env=dict(os.environ,PYTHONPATH=str(site),PYTHONUTF8='1')
    before=set(run.rglob('*'))
    assert call('status','--run',run,env=env)[0].returncode==0
    assert before==set(run.rglob('*'))

def test_release_fix_and_validation_failures_use_json(tmp_path):
    _,run=make_run(tmp_path); tid=install_task(run)
    attempt=call('task','claim','--run',run,'--task',tid)[1]['next']['attempt']
    assert call('task','accept','--run',run,'--task',tid,'--attempt',attempt,'--receipt',run/'missing.json')[0].returncode==1
    assert call('task','release','--run',run,'--task',tid,'--attempt',attempt,'--reason','main confirmed never dispatched')[0].returncode==0
    request=run/'fix.json'; detail=run/'fix.md'; detail.write_text('fixture request')
    request.write_text(json.dumps({'id':'fix-1','category':'content','items':[{'task_id':tid,'request_path':str(detail)}]}))
    assert call('task','fix','--run',run,'--request',request)[0].returncode==0
    assert call('run','--run',run,'--action','assemble-note')[0].returncode==1
    assert call('recover','--run',run)[0].returncode==1

def test_unopened_run_failure_does_not_create_logs(tmp_path):
    run=tmp_path/'empty'; run.mkdir()
    assert call('init','--repo',tmp_path/'missing','--run',run,'--range','0909','--allow-tmp')[0].returncode==1
    assert list(run.iterdir())==[]


def test_init_rejects_removed_lite_option_before_creating_run(tmp_path):
    repo, _ = make_run(tmp_path)
    new = tmp_path / 'new'
    p, data = call('init', '--repo', repo, '--run', new, '--range', '0909', '--allow-tmp', '--lite')
    assert p.returncode == 2 and data['error_code'] == 'usage_error'
    assert not new.exists()


def test_legacy_standard_run_can_resume(tmp_path):
    _, run = make_run(tmp_path)
    path = run / 'run-status.json'
    path.write_text(json.dumps(dict(json.loads(path.read_text()), lite=False)))
    before = path.read_bytes()
    p, data = call('next', '--run', run, '--slots', '1')
    assert p.returncode == 0 and data['next']['tasks'][0]['id'] == 'source-prep'
    assert path.read_bytes() == before
    assert call('task', 'claim', '--run', run, '--task', 'source-prep')[0].returncode == 0
    assert 'lite' not in json.loads(path.read_text())


def test_legacy_lite_run_requires_a_fresh_run_for_the_same_range(tmp_path):
    _, run = make_run(tmp_path)
    path = run / 'run-status.json'
    path.write_text(json.dumps(dict(json.loads(path.read_text()), lite=True)))
    before = path.read_bytes()
    p, data = call('next', '--run', run, '--slots', '1')
    assert p.returncode == 1 and data['error_code'] == 'validation_failed'
    assert 'init' in data['reason'] and '--range 0909' in data['reason']
    assert path.read_bytes() == before


def test_fixture_workflow_cannot_finish_with_missing_reviews(tmp_path):
    """Synthetic scheduling evidence cannot replace the real final gate."""
    from pack_support import workflow_until, workflow_accept
    import pack_flow as f
    repo, run = make_run(tmp_path)
    # Install the actual checker runtime so rejection crosses the genuine gate.
    import shutil
    from _util import SKILL, REPO
    shutil.copytree(SKILL / 'scripts', repo / '.claude/skills/ec2-review-pack/scripts')
    for module in (REPO / 'workbook').glob('*.py'):
        shutil.copyfile(module, repo / 'workbook' / module.name)
    workflow_until(run, 'style-audit')
    assert call('run', '--run', run, '--action', 'final-check')[0].returncode == 1
    assert call('report', '--run', run)[1]['counts']['partial'] == 1
    workflow_accept(run, 'style-audit')
    workflow_until(run, 'content-review')
    assert call('run', '--run', run, '--action', 'final-check')[0].returncode == 1
    workflow_until(run, 'browser-qa')
    assert call('run', '--run', run, '--action', 'final-check')[0].returncode == 1
    workflow_until(run, 'final-check')
    # The scheduler's synthetic note is deliberately invalid: run the genuine checker.
    p, result = call('run', '--run', run, '--action', 'final-check')
    assert p.returncode == 1
    state = f.inspect_state(run)
    assert state['actions']['final-check']['status'] != 'done'
    logs = list((run / 'work/actions/final-check').glob('*/stderr.log'))
    assert logs and all("can't open file" not in p.read_text(encoding='utf-8') for p in logs)
    assert call('report', '--run', run)[1]['counts']['partial'] == 1


def test_zero_problem_cli_workflow_requires_worker_reviews(tmp_path):
    """Synthetic roles exercise CLI routing; no semantic approval is claimed."""
    from pack_support import workflow_until, workflow_accept
    import pack_flow as f
    _, run = make_run(tmp_path)
    workflow_until(run, 'style-audit')
    next_ = call('next', '--run', run, '--slots', '1')[1]['next']
    assert next_['kind'] == 'dispatch'
    assert next_['tasks'][0]['id'] == 'style-audit'
    workflow_accept(run, 'style-audit')
    workflow_until(run, 'content-review')
    next_ = call('next', '--run', run, '--slots', '1')[1]['next']
    assert next_['kind'] == 'dispatch'
    assert next_['tasks'][0]['id'] == 'content-review'
    workflow_until(run, 'final-check')
    state = f.load_state(run)
    assert 'browser-qa' in state['tasks']
    assert 'child-coordinator' not in state['tasks']
    assert 'build-answers' not in state['actions']
    assert call('next', '--run', run, '--slots', '0')[1]['next']['action'] == 'final-check'
    assert call('report', '--run', run)[1]['counts']['partial'] == 1


def interrupted_cli_run(tmp_path):
    """Real subprocess completes; controller exits before saving result/state."""
    from pack_support import action_run
    import pack_flow as f
    _, run = action_run(tmp_path, action='prepare-pack')
    assert call('run', '--run', run, '--action', 'prepare-pack')[0].returncode == 0
    f.update_state(run, f.load_state(run)['revision'], lambda s: dict(s, actions={**s['actions'],
        'assemble-note': dict(id='assemble-note', status='pending', dependencies=['prepare-pack'])}))
    boot = tmp_path / 'interrupted.py'
    boot.write_text("import sys, os\nsys.path.insert(0, " + repr(str(SCRIPTS)) + ")\nimport pack_actions as a\nimport pack_cli\n"
        "def command(state, action):\n"
        " output = a._paths(state)['note']\n"
        " output.parent.mkdir(parents=True, exist_ok=True)\n"
        " return [sys.executable, '-c', 'from pathlib import Path; Path(' + repr(str(output)) + ').write_text(\"note\", encoding=\"utf-8\")']\n"
        "a.action_argv = command\n"
        "a._save_result = lambda *args: os._exit(77)\n"
        "pack_cli.main(sys.argv[1:])\n", encoding='utf-8')
    result = subprocess.run([sys.executable, str(boot), 'run', '--run', str(run), '--action', 'assemble-note'], capture_output=True)
    assert result.returncode == 77 and not result.stderr
    record = f.load_state(run)['actions']['assemble-note']
    folder = Path(record['attempt_dir'])
    assert record['status'] == 'running' and not (folder / 'result.json').exists()
    assert json.loads((folder / 'stopped.json').read_text())['exit_code'] == 0
    return run, folder


def test_cli_reconciles_completed_interrupted_subprocess_without_replay(tmp_path):
    import pack_flow as f
    run, folder = interrupted_cli_run(tmp_path)
    assert call('run', '--run', run, '--action', 'assemble-note')[0].returncode == 1
    stopped = (folder / 'stopped.json').read_bytes()
    p, data = call('reconcile', '--run', run, '--action', 'assemble-note')
    assert p.returncode == 0
    assert f.load_state(run)['actions']['assemble-note']['status'] == 'done'
    assert (folder / 'stopped.json').read_bytes() == stopped
    assert len(list(folder.parent.iterdir())) == 1
    # execute returns slots=0: worker-slot wait is legitimate after adoption.
    assert data['next']['reason'] != 'machine action already running'
    assert call('next', '--run', run, '--slots', '1')[1]['next']['kind'] == 'dispatch'


@pytest.mark.parametrize('damage', ['stopped', 'inventory', 'inputs'])
def test_cli_reconciliation_rejects_insufficient_or_changed_evidence(tmp_path, damage):
    import pack_flow as f
    run, folder = interrupted_cli_run(tmp_path)
    started = json.loads((folder / 'started.json').read_text())
    if damage == 'stopped': (folder / 'stopped.json').unlink()
    elif damage == 'inventory':
        import pack_actions as a
        a._paths(f.load_state(run))['note'].write_text('external edit')
    else: Path(started['inputs'][0]['path']).write_text('changed input')
    p, data = call('reconcile', '--run', run, '--action', 'assemble-note')
    assert p.returncode == 1 and data['error_code'] == 'incomplete_evidence'
    assert f.load_state(run)['actions']['assemble-note']['status'] == 'recovery_required'
    assert (folder / 'reconcile-error.txt').is_file()


def test_cli_reconciliation_obeys_live_action_lock(tmp_path):
    import pack_actions as a
    run, _ = interrupted_cli_run(tmp_path)
    with a._action_lock(run):
        p, data = call('reconcile', '--run', run, '--action', 'assemble-note')
    assert p.returncode == 1 and Path(data['details_path']).is_file()


def _repo_only(tmp_path):
    repo, _ = make_run(tmp_path)
    return repo


def test_init_rejects_tmp_run(tmp_path):
    repo = _repo_only(tmp_path)
    p, d = call('init', '--repo', repo, '--run', tmp_path / 'fresh', '--range', '0909')
    assert p.returncode == 1 and d['error_code'] == 'validation_failed' and 'temporary' in d['reason']
    assert not (tmp_path / 'fresh').exists()


def test_init_allows_tmp_with_flag(tmp_path):
    repo = _repo_only(tmp_path)
    assert call('init', '--repo', repo, '--run', tmp_path / 'fresh', '--range', '0909', '--allow-tmp')[0].returncode == 0


def test_init_without_run_uses_cache_dir(tmp_path):
    repo = _repo_only(tmp_path)
    p, d = call('init', '--repo', repo, '--range', '0909', '--allow-tmp', env=dict(os.environ, EC2_CACHE_ROOT=str(tmp_path / '.cache')))
    assert p.returncode == 0, d
    run = Path(d['details_path']).parent
    assert run.parent == (tmp_path / '.cache/ec2-review-pack').resolve() and run.name.startswith('0909-')
    assert Path(d['details_path']).is_file()


def _check_setup(tmp_path):
    import hashlib
    _, run = make_run(tmp_path)
    tid = install_task(run)
    attempt = call('task', 'claim', '--run', run, '--task', tid)[1]['next']['attempt']
    receipt = receipt_for(run, tid, attempt)
    sha = lambda: hashlib.sha256((run / 'run-status.json').read_bytes()).hexdigest()
    return run, tid, attempt, receipt, sha


def test_task_check_passes_valid_receipt_without_state_change(tmp_path):
    run, tid, attempt, receipt, sha = _check_setup(tmp_path)
    before = sha()
    p, d = call('task', 'check', '--run', run, '--task', tid, '--attempt', attempt, '--receipt', receipt)
    assert p.returncode == 0 and d['status'] == 'ok' and d['error_code'] is None
    assert sha() == before and not (run / 'work' / 'cli').exists()


def test_task_check_reports_unresolved(tmp_path):
    run, tid, attempt, receipt, sha = _check_setup(tmp_path)
    data = json.loads(receipt.read_text()); data['unresolved'] = ['note']; receipt.write_text(json.dumps(data))
    before = sha()
    p, d = call('task', 'check', '--run', run, '--task', tid, '--attempt', attempt, '--receipt', receipt)
    assert p.returncode == 1 and d['status'] == 'failed' and d['error_code'] == 'validation_failed'
    assert d['reason'] == 'unresolved successful receipt' and sha() == before


def test_task_check_reports_identity_mismatch(tmp_path):
    run, tid, attempt, receipt, sha = _check_setup(tmp_path)
    data = json.loads(receipt.read_text()); data['run_id'] = 'wrong'; receipt.write_text(json.dumps(data))
    p, d = call('task', 'check', '--run', run, '--task', tid, '--attempt', attempt, '--receipt', receipt)
    assert p.returncode == 1 and d['reason'] == 'receipt identity mismatch'
