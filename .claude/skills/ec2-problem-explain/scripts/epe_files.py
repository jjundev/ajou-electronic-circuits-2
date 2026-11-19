"""Backed-up multi-file replacement with rollback and kernel-owned locks.

This is recoverable publication, not an OS-atomic multi-file transaction.
"""
from contextlib import contextmanager
import os
from pathlib import Path
import shutil
import tempfile
import uuid

from epe_types import ExplainError
from pack_flow import FlowError
from pack_publication import publication_lock as date_lock


@contextmanager
def publication_lock(destinations):
    # Legacy callers pass a collection of EPE output files. The top-level
    # HTML identifies the single date folder shared by all bundle members.
    destinations = tuple(map(Path, destinations))
    roots = {p.parent for p in destinations if p.suffix == '.html' and p.parent.name.isascii()
             and p.parent.name.replace('-', '').isdigit()}
    if len(roots) != 1:
        raise ExplainError('발행 날짜 폴더가 하나여야 합니다')
    pack = roots.pop()
    if any(not p.resolve().is_relative_to(pack.resolve()) for p in destinations):
        raise ExplainError('발행 파일 경로가 날짜 폴더 밖에 있습니다')
    try:
        with date_lock(pack):
            yield
    except FlowError as exc:
        raise ExplainError(f'발행 잠금: {exc}') from exc


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


def _install_locked(staged, backup_dir):
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


def publish_files(staged, backup_dir):
    with publication_lock(staged):
        _install_locked(staged, backup_dir)
