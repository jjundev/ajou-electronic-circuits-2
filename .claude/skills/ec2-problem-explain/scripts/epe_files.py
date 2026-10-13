"""Backed-up multi-file replacement with rollback and kernel-owned locks.

This is recoverable publication, not an OS-atomic multi-file transaction.
"""
from contextlib import contextmanager, ExitStack
from pathlib import Path
try:
    import fcntl
except ImportError:  # Windows: msvcrt byte-range lock, released when the handle closes
    fcntl = None
    import msvcrt
import hashlib
import os
import shutil
import tempfile
import uuid
from epe_types import ExplainError


def _try_lock(stream):
    if fcntl:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return
    stream.seek(0)
    try:
        msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError as exc:
        raise BlockingIOError(str(exc)) from exc


@contextmanager
def publication_lock(destinations):
    lock_root = Path(tempfile.gettempdir()) / 'ec2-problem-explain-locks'
    lock_root.mkdir(exist_ok=True)
    parents = sorted({str(Path(p).resolve().parent) for p in destinations})
    with ExitStack() as stack:
        for parent in parents:
            name = hashlib.sha256(parent.encode()).hexdigest() + '.lock'
            stream = stack.enter_context((lock_root / name).open('a+'))
            try:
                _try_lock(stream)
            except BlockingIOError as exc:
                raise ExplainError(f'발행 잠금 중: {parent}') from exc
        yield
    # Closing the descriptors releases locks; never unlink a live lock inode.


def _replace_copy(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.explain-', dir=destination.parent)
    temp = Path(name)
    try:
        with os.fdopen(fd, 'wb') as stream:
            with source.open('rb') as src:
                shutil.copyfileobj(src, stream)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, destination)
    finally:
        temp.unlink(missing_ok=True)


def publish_files(staged, backup_dir):
    mapping = {Path(dst): Path(src) for dst, src in staged.items()}
    if not mapping:
        raise ExplainError('발행할 파일 없음')
    for dst, src in mapping.items():
        if not src.is_file():
            raise ExplainError(f'스테이지 파일 없음: {src}')
        if dst.is_symlink() or (dst.exists() and not dst.is_file()):
            raise ExplainError(f'발행 위치 부적합: {dst}')
        if dst.resolve() == src.resolve():
            raise ExplainError(f'스테이지와 목적지 동일: {dst}')
    with publication_lock(mapping):
        backup = Path(backup_dir) / uuid.uuid4().hex
        backup.mkdir(parents=True, exist_ok=False)
        originals, replaced = {}, []
        for i, dst in enumerate(mapping):
            if dst.exists():
                saved = backup / f'{i}-{dst.name}'
                shutil.copy2(dst, saved)
                originals[dst] = saved
            else:
                originals[dst] = None
        try:
            for dst, src in mapping.items():
                _replace_copy(src, dst)
                replaced.append(dst)
        except BaseException:
            for dst in reversed(replaced):
                if originals[dst] is None:
                    dst.unlink(missing_ok=True)
                else:
                    _replace_copy(originals[dst], dst)
            raise
