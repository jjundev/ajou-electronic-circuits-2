"""The in-process CLI runner must answer exactly like a real `pack_cli.py` process."""
import json
import os
import sys
import types

import pytest

import cli_runner
from _util import REPO, SCRIPTS
from pack_support import make_run


def outcome(result):
    data = json.loads(result.stdout)
    next_ = data.get('next') or {}
    return (result.returncode, data['schema_version'], data['status'], data['error_code'],
            next_.get('kind'), result.stderr, len(result.stdout) <= 2000)


@pytest.mark.parametrize('args', [
    ('next', '--slots', '2'),
    ('status',),
    ('report',),
    ('wat',),
    ('task', 'check', '--task', 'nope', '--attempt', 'x', '--receipt', 'missing.json'),
])
def test_in_process_matches_a_real_process(tmp_path, args):
    runs = {}
    for mode in ('process', 'inprocess'):
        _, runs[mode] = make_run(tmp_path / mode)
    process = cli_runner.call_process(*args, '--run', runs['process'])
    inprocess = cli_runner.run_in_process(*args, '--run', runs['inprocess'])
    assert outcome(inprocess) == outcome(process)


def test_usage_error_keeps_exit_code_two():
    assert cli_runner.run_in_process('wat').returncode == 2


def test_concurrent_in_process_calls_are_refused(tmp_path):
    _, run = make_run(tmp_path)
    with cli_runner._ONE_AT_A_TIME:
        with pytest.raises(RuntimeError, match='EC2_TEST_CLI=subprocess'):
            cli_runner.run_in_process('status', '--run', run)
    assert cli_runner.run_in_process('status', '--run', run).returncode == 0


def fake_main(monkeypatch, body):
    import pack_cli
    def main(argv):
        body()
        sys.stdout.write('{}')
        return 0
    monkeypatch.setattr(pack_cli, 'main', main)


def test_each_call_puts_the_script_folder_first(monkeypatch):
    """Product code prepends workbook/_tools to sys.path; `python pack_cli.py` starts with scripts/."""
    workbook = str(REPO / 'workbook')
    monkeypatch.syspath_prepend(workbook)
    seen = []
    fake_main(monkeypatch, lambda: seen.append(list(sys.path)))
    cli_runner.run_in_process('status')
    assert seen[0][0] == str(SCRIPTS)
    assert sys.path[0] == workbook


def test_a_call_leaves_no_path_module_env_or_cwd_behind(monkeypatch, tmp_path):
    before = (list(sys.path), set(sys.modules), dict(os.environ), os.getcwd())
    def pollute():
        sys.path.insert(0, str(tmp_path))
        module = types.ModuleType('ec2_call_only_module')
        module.__file__ = str(SCRIPTS / 'ec2_call_only_module.py')
        sys.modules['ec2_call_only_module'] = module
        os.environ['EC2_CALL_ONLY'] = '1'
        os.chdir(tmp_path)
    fake_main(monkeypatch, pollute)
    cli_runner.run_in_process('status')
    assert (list(sys.path), set(sys.modules), dict(os.environ), os.getcwd()) == before


def test_a_module_shadowing_a_script_is_hidden_during_the_call(monkeypatch):
    """`import assemble` must find scripts/assemble.py, as in a new process."""
    shadow = types.ModuleType('assemble')
    shadow.__file__ = str(REPO / 'workbook/assemble.py')
    monkeypatch.setitem(sys.modules, 'assemble', shadow)
    seen = []
    fake_main(monkeypatch, lambda: seen.append(sys.modules.get('assemble')))
    cli_runner.run_in_process('status')
    assert seen == [None] and sys.modules['assemble'] is shadow


def test_a_module_from_another_tests_repo_is_hidden_during_the_call(monkeypatch, tmp_path):
    """pack_actions imports `render` from the RUN's repo; an older repo's copy must not answer."""
    stale = types.ModuleType('render')
    stale.__file__ = str(tmp_path / 'old-repo/workbook/render.py')
    monkeypatch.setitem(sys.modules, 'render', stale)
    seen = []
    fake_main(monkeypatch, lambda: seen.append((sys.modules.get('render'), sys.modules.get('pack_flow'))))
    import pack_flow
    cli_runner.run_in_process('status')
    assert seen == [(None, pack_flow)] and sys.modules['render'] is stale


def test_mode_switch_selects_the_runner(monkeypatch, tmp_path):
    _, run = make_run(tmp_path)
    used = []
    monkeypatch.setattr(cli_runner, 'call_process', lambda *a, **k: used.append('process') or 'p')
    monkeypatch.setattr(cli_runner, 'run_in_process', lambda *a, **k: used.append('inprocess') or 'i')
    monkeypatch.setenv('EC2_TEST_CLI', 'subprocess')
    cli_runner.run_pack_cli('status', '--run', run)
    monkeypatch.delenv('EC2_TEST_CLI')
    cli_runner.run_pack_cli('status', '--run', run)
    assert used == ['process', 'inprocess']
