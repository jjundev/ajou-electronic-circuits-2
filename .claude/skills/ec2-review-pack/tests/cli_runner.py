"""Run `pack_cli.py` for tests, in this process by default.

A fresh Python process per call costs about a second on Windows, and the suite makes
thousands of calls. `pack_cli.main(argv)` returns the exit code and turns every
error into the same one-line JSON a process would print, so tests call it directly.

Set EC2_TEST_CLI=subprocess to run every call as a real process again (full fidelity;
the `layout` stub cannot reach a child process, so the real browser probe runs).
Tests about the process boundary itself (cwd, env, concurrency, crashes) call
`call_process` directly.
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
    a call only scripts/ modules stay loaded, and project modules the call imported are
    dropped afterwards. `python pack_cli.py` puts the script folder first on sys.path;
    entries that already-imported modules appended stay behind it.
    """
    saved_path, saved_env, saved_cwd = list(sys.path), dict(os.environ), os.getcwd()
    hidden = {}
    for name, module in list(sys.modules.items()):
        path = _project_file(module)
        if path is not None and path.parent != SCRIPTS:
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
