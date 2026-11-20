"""Keep a date reservation alive through Windows process-handle inheritance."""
from contextlib import contextmanager
import os
import subprocess
import time

from pack_flow import FlowError

_HANDLE_ENV = 'EC2_DATE_LOCK_HANDLE'
_FILE_READ_ATTRIBUTES = 0x80
_OPEN_ALWAYS = 4
_SHARE_ALL = 7
_SHARING_VIOLATION = 32


def _duplicate(handle, *, inherit):
    import _winapi
    process = _winapi.GetCurrentProcess()
    return _winapi.DuplicateHandle(process, handle, process, 0, inherit, _winapi.DUPLICATE_SAME_ACCESS)


def _stat_and_close(handle):
    import _winapi
    import msvcrt
    try:
        fd = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY)
    except BaseException:
        _winapi.CloseHandle(handle)
        raise
    try:
        return os.fstat(fd)
    finally:
        os.close(fd)


def _verify_inherited(path, handle):
    import _winapi
    # An attributes-only query is permitted while a no-sharing handle is open.
    # Compare actual Windows file IDs. Then require read access on this handle
    # and prove that an independent reader is excluded on that same file.
    metadata = _winapi.CreateFile(str(path), _FILE_READ_ATTRIBUTES, _SHARE_ALL, 0, _winapi.OPEN_EXISTING, 0, 0)
    target = _stat_and_close(metadata)
    actual = _stat_and_close(_duplicate(handle, inherit=False))
    if not target.st_ino or not os.path.samestat(actual, target):
        raise FlowError('inherited Windows lock does not own this date')
    _winapi.ReadFile(handle, 1)
    try:
        reader = _winapi.CreateFile(str(path), _winapi.GENERIC_READ, _SHARE_ALL, 0, _winapi.OPEN_EXISTING, 0, 0)
    except OSError as exc:
        if exc.winerror != _SHARING_VIOLATION:
            raise
    else:
        _winapi.CloseHandle(reader)
        raise FlowError('inherited Windows lock is not exclusive')


@contextmanager
def kernel_lock(path):
    import _winapi
    inherited = os.environ.get(_HANDLE_ENV)
    if inherited is not None:
        handle = int(inherited)
        _verify_inherited(path, handle)
        os.set_handle_inheritable(handle, False)
        yield handle
        return
    # Byte-range locks belong to the issuing process. The share mode of a
    # CreateFile handle survives the controller if a child retains a duplicate.
    while True:
        try:
            handle = _winapi.CreateFile(str(path), _winapi.GENERIC_READ | _winapi.GENERIC_WRITE,
                                        0, 0, _OPEN_ALWAYS, 0, 0)
            break
        except OSError as exc:
            if exc.winerror != _SHARING_VIOLATION:
                raise
            time.sleep(0.05)
    try:
        yield handle
    finally:
        _winapi.CloseHandle(handle)


@contextmanager
def child_options(handle, env):
    import _winapi
    child = _duplicate(handle, inherit=True)
    try:
        startup = subprocess.STARTUPINFO(lpAttributeList={'handle_list': [child]})
        yield {'startupinfo': startup, 'close_fds': True, 'env': {**env, _HANDLE_ENV: str(child)}}
    finally:
        _winapi.CloseHandle(child)
