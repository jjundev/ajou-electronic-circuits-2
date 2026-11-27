"""Run `pack_cli.py` for tests, in this process by default.

A fresh Python process per call costs about a second on Windows, and the suite makes
thousands of calls. `pack_cli.main(argv)` returns the exit code and turns every
error into the same one-line JSON a process would print, so tests call it directly.

Set EC2_TEST_CLI=subprocess to run every call as a real process again (full fidelity;
the `layout` stub cannot reach a child process, so the real browser probe runs).
Tests about the process boundary itself (cwd, env, concurrency, crashes) call
`call_process` directly.

Because of that, a monkeypatch on a scripts/ module other than pack_cli, pack_flow and
pack_probe does not reach an in-process call: the call imports a fresh copy, as a process would.

`run_concept` runs `concept.py` as a process. Its `browser` command gets a synthetic
report (quiz_browser_stub.py) instead of Chromium; set EC2_TEST_BROWSER=real for the real one.
"""
from collections import namedtuple
import contextlib
import functools
import io
import os
from pathlib import Path
import site
import subprocess
import sys
import threading
from unittest import mock

from _util import SCRIPTS

CLI = SCRIPTS / 'pack_cli.py'
TESTS = Path(__file__).resolve().parent
Result = namedtuple('Result', 'returncode stdout stderr')
# Output redirection and pack_cli's fd capture are process-wide: one call at a time.
_ONE_AT_A_TIME = threading.Lock()


def call_process(*args, cwd=None, env=None):
    proc = subprocess.run([sys.executable, str(CLI), *map(str, args)], cwd=cwd, env=env,
                          capture_output=True, encoding='utf-8')
    return Result(proc.returncode, proc.stdout, proc.stderr)


_INSTALLED = tuple({Path(p).resolve() for p in (sys.prefix, sys.base_prefix, *site.getsitepackages(),
                                                site.getusersitepackages())})


@functools.cache
def _classify(file):
    # Path.resolve() touches the disk; every call checks every loaded module, so resolve each file once.
    path = Path(file).resolve()
    return None if any(path.is_relative_to(root) for root in _INSTALLED) else path


_STARTUP_PROBE = """import sys
before = set(sys.modules)
import pack_cli, pack_probe
print(*sorted(set(sys.modules) - before))"""


@functools.cache
def _startup_scripts():
    """The scripts/ modules a new `pack_cli.py` process has loaded when main() starts.

    Any other scripts/ module the test process imported (test_assemble imports
    scripts/assemble.py) is hidden during a call: once product code puts workbook/ first,
    `import assemble` must find workbook/assemble.py, as it would in a new process.
    """
    # -E: the result is cached for the process, so a test's PYTHONPATH (a sitecustomize that
    # preloads pack_flow) must not decide it for every later call.
    proc = subprocess.run([sys.executable, '-E', '-c', _STARTUP_PROBE], cwd=SCRIPTS,
                          capture_output=True, text=True, check=True)
    return frozenset(n for n in proc.stdout.split() if (SCRIPTS / f'{n}.py').is_file())


def _project_file(module):
    """The module's file when it is project or fixture code, not the interpreter or a package."""
    path = getattr(module, '__file__', None)
    return _classify(path) if isinstance(path, str) and path else None


@contextlib.contextmanager
def _like_a_new_process():
    """Give one call what a new process would have, and take back what the call changed.

    Product code prepends workbook/_tools folders (of the RUN's own repo) to sys.path and
    imports modules whose names collide (scripts/assemble.py vs workbook/assemble.py, or
    the same workbook module from another test's temporary repo). A process starts
    without them and drops them on exit; here they would leak between calls. So during
    a call only the scripts/ modules a new process starts with stay loaded, and project modules the call imported are
    dropped afterwards. `python pack_cli.py` puts the script folder first on sys.path;
    entries that already-imported modules appended stay behind it.
    """
    saved_path, saved_env, saved_cwd = list(sys.path), dict(os.environ), os.getcwd()
    hidden = {}
    startup = _startup_scripts()
    for name, module in list(sys.modules.items()):
        path = _project_file(module)
        if path is not None and (path.parent != SCRIPTS or name not in startup):
            hidden[name] = sys.modules.pop(name)
    loaded = set(sys.modules)
    sys.path[:] = [str(SCRIPTS), *(p for p in saved_path if p != str(SCRIPTS))]
    try:
        yield
    finally:
        for name in set(sys.modules) - loaded:
            if _project_file(sys.modules[name]) is not None:  # extensions and packages stay loaded
                del sys.modules[name]
        sys.modules.update(hidden)
        sys.path[:] = saved_path
        if dict(os.environ) != saved_env:
            os.environ.clear(); os.environ.update(saved_env)
        os.chdir(saved_cwd)


def run_in_process(*args, layout=None):
    import pack_cli
    import pack_probe
    if not _ONE_AT_A_TIME.acquire(blocking=False):
        raise RuntimeError('concurrent CLI calls need EC2_TEST_CLI=subprocess or call_process')
    try:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.ExitStack() as stack:
            if layout is not None:
                stack.enter_context(mock.patch.object(pack_probe, 'run_layout', layout))
            stack.enter_context(_like_a_new_process())
            stack.enter_context(contextlib.redirect_stdout(out))
            stack.enter_context(contextlib.redirect_stderr(err))
            try:
                code = pack_cli.main([str(a) for a in args])
            except SystemExit as exc:  # main() never exits itself; kept so a regression still reports
                code = exc.code if isinstance(exc.code, int) else 1
        return Result(code, out.getvalue(), err.getvalue())
    finally:
        _ONE_AT_A_TIME.release()


def run_pack_cli(*args, layout=None):
    """`layout` replaces pack_probe.run_layout for an in-process `task probe`."""
    if os.environ.get('EC2_TEST_CLI') == 'subprocess':
        return call_process(*args)
    return run_in_process(*args, layout=layout)


# Same pattern as the race wrapper in test_pack_graph.py: patch one function, then run main.
_STUB_BROWSER = """import sys
sys.path.insert(0, sys.argv.pop(1)); sys.path.append(sys.argv.pop(1))
import browser_check, concept, quiz_browser_stub
browser_check.check = quiz_browser_stub.check
sys.exit(concept.main(sys.argv[1:]))"""


def run_concept(cli, *args, real_browser=False):
    """`python concept.py ...`; only `browser` runs the stub unless the real browser is asked for."""
    args = [str(a) for a in args]
    stub = (args[:1] == ['browser'] and not real_browser
            and os.environ.get('EC2_TEST_BROWSER') != 'real')
    argv = ([sys.executable, '-c', _STUB_BROWSER, str(Path(cli).parent), str(TESTS), *args] if stub
            else [sys.executable, str(cli), *args])
    proc = subprocess.run(argv, capture_output=True, text=True)
    return Result(proc.returncode, proc.stdout, proc.stderr)
