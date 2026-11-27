"""The in-process CLI runner must answer exactly like a real `pack_cli.py` process."""
import json
import os
import subprocess
import sys
import types

import pytest

import cli_runner
from _util import REPO, SCRIPTS
from pack_parallel import CONCEPT_CLI
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


def test_a_script_module_a_new_process_has_not_loaded_is_hidden(monkeypatch):
    """test_assemble imports scripts/assemble.py; a later call must still find workbook/assemble.py
    once product code puts workbook first, as a new `pack_cli.py` process would."""
    script = types.ModuleType('assemble')
    script.__file__ = str(SCRIPTS / 'assemble.py')
    monkeypatch.setitem(sys.modules, 'assemble', script)
    seen = []
    fake_main(monkeypatch, lambda: seen.append(sys.modules.get('assemble')))
    cli_runner.run_in_process('status')
    assert seen == [None] and sys.modules['assemble'] is script


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


def test_run_concept_wraps_only_the_browser_command(monkeypatch, tmp_path):
    seen = []
    monkeypatch.delenv('EC2_TEST_BROWSER', raising=False)
    monkeypatch.setattr(cli_runner.subprocess, 'run',
                        lambda argv, **k: seen.append(argv) or types.SimpleNamespace(returncode=0, stdout='', stderr=''))
    cli_runner.run_concept(CONCEPT_CLI, 'blind-make', '--out', 'browser', '--run', tmp_path)
    cli_runner.run_concept(CONCEPT_CLI, 'browser', '--run', tmp_path)
    assert seen[0] == [sys.executable, str(CONCEPT_CLI), 'blind-make', '--out', 'browser', '--run', str(tmp_path)]
    assert seen[1][1] == '-c' and seen[1][3:5] == [str(CONCEPT_CLI.parent), str(cli_runner.TESTS)]
    assert seen[1][5:] == ['browser', '--run', str(tmp_path)]


def test_real_browser_runs_concept_unwrapped(monkeypatch, tmp_path):
    seen = []
    monkeypatch.setattr(cli_runner.subprocess, 'run',
                        lambda argv, **k: seen.append(argv) or types.SimpleNamespace(returncode=0, stdout='', stderr=''))
    cli_runner.run_concept(CONCEPT_CLI, 'browser', '--run', tmp_path, real_browser=True)
    monkeypatch.setenv('EC2_TEST_BROWSER', 'real')
    cli_runner.run_concept(CONCEPT_CLI, 'browser', '--run', tmp_path)
    assert seen == [[sys.executable, str(CONCEPT_CLI), 'browser', '--run', str(tmp_path)]] * 2


# A child process: `import concept` would load concept's `render`/`items`, whose names
# collide with project modules, into the test process.
STUB_GATE = r"""
import sys
from pathlib import Path
concept_tests, tests, tmp, drop_hint = sys.argv[1:]
sys.path.insert(0, concept_tests); sys.path.append(tests)
from test_browser_transport import synthetic_quiz
import concept, quiz_browser_stub
from PIL import Image
html, data = synthetic_quiz(Path(tmp))
if drop_hint == '1':
    data['items'][0]['hint'] = ''
shots = Path(tmp) / 'shots'
report = quiz_browser_stub.check(html, Path(tmp) / 'browser.json', shots, source=data)
assert report['status'] == 'pass' and report['stub']
concept.checked_browser(html, report, data)
names = concept.shot_names(data)
assert sorted(p.name for p in shots.iterdir()) == sorted(names)
assert len({(shots / n).read_bytes() for n in names}) == len(names)
for name in names:
    with Image.open(shots / name) as frame:
        assert frame.format == 'PNG' and frame.size == tuple(map(int, name.split('-', 1)[0].split('x')))
print('OK')
"""


def stub_gate(tmp_path, drop_hint):
    return subprocess.run([sys.executable, '-c', STUB_GATE, str(CONCEPT_CLI.parents[1] / 'tests'),
                           str(cli_runner.TESTS), str(tmp_path), drop_hint], capture_output=True, text=True)


def test_stub_report_passes_concept_browser_gates(tmp_path):
    proc = stub_gate(tmp_path, '0')
    assert (proc.returncode, proc.stdout.strip()) == (0, 'OK'), proc.stderr


def test_stub_report_fails_when_an_item_has_no_hint(tmp_path):
    proc = stub_gate(tmp_path, '1')
    assert proc.returncode != 0 and '4모드' in proc.stderr, proc.stderr


def test_receipt_code_imports_workbook_assemble_after_a_test_loaded_the_script_one():
    """xdist gives a worker test_assemble (scripts/assemble.py) and then a direct pdf-qa receipt,
    whose import chain (publish_answer -> epe_shared) needs workbook/assemble.py."""
    order = ('import sys, pytest; sys.path.insert(0, sys.argv[1]); import _util, assemble; '
             'from publish_answer import _review; import epe_shared; print(epe_shared.TEXTBOOK_ID_RE.pattern)')
    proc = subprocess.run([sys.executable, '-c', order, str(cli_runner.TESTS)], capture_output=True, text=True)
    assert proc.returncode == 0 and proc.stdout.strip(), proc.stderr


def test_startup_probe_ignores_the_callers_pythonpath(monkeypatch, tmp_path):
    """A test may set PYTHONPATH to a sitecustomize that imports pack_flow; if that test makes
    the first call, the cached probe must still see what a plain `pack_cli.py` process loads."""
    (tmp_path / 'sitecustomize.py').write_text(f'import sys; sys.path.insert(0, {str(SCRIPTS)!r}); import pack_flow\n')
    monkeypatch.setenv('PYTHONPATH', str(tmp_path))
    cli_runner._startup_scripts.cache_clear()
    try:
        assert {'pack_cli', 'pack_flow', 'pack_probe'} <= cli_runner._startup_scripts()
    finally:
        cli_runner._startup_scripts.cache_clear()
