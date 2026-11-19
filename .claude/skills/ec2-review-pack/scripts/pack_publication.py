"""Install one date's verified files with a durable, ordered undo journal."""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import re
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import threading

import pack_files
from pack_flow import FlowError, _atomic_json, _read, _sha

sys.path.append(str(Path(__file__).resolve().parents[4] / 'workbook'))
from pack_paths import PackPaths, checked_file

_local = threading.local()
_FD_ENV = 'EC2_DATE_LOCK_FD'


def _fsync_dir(directory):
    if os.name != 'nt':
        fd = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def _mkdirs(directory):
    if not directory.is_dir():
        _mkdirs(directory.parent)
        directory.mkdir(exist_ok=True)
        _fsync_dir(directory.parent)


def _save(path, record):
    _atomic_json(path, record)
    _fsync_dir(path.parent)


def _key(public):
    return pack_files._nfc(str(public.resolve()))


def _control(public):
    # The original concept publisher uses this inode. Never unlink a lock.
    folder = Path.home() / '.cache/ec2-concept-check/locks'
    _mkdirs(folder)
    return folder / hashlib.sha256(_key(public).encode()).hexdigest()


@contextmanager
def _posix_lock(lock):
    import fcntl
    with lock.open('a+b') as stream:
        fd = stream.fileno()
        inherited = os.environ.get(_FD_ENV)
        if inherited is not None and os.path.samestat(os.fstat(int(inherited)), os.fstat(fd)):
            fd = int(inherited)
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield fd


@contextmanager
def _date_lock(public, *, allow_pending=False):
    lock = _control(public)
    active = lock.with_suffix('.publication.json')
    key = str(lock)
    held = getattr(_local, 'held', {})
    if key in held:
        raise FlowError('date publication lock already held: ' + str(public))
    if os.name == 'nt':
        from pack_windows_lock import kernel_lock
    else:
        kernel_lock = _posix_lock
    with kernel_lock(lock) as handle:
        _local.held = {**held, key: handle}
        try:
            if active.exists() and not allow_pending:
                raise FlowError('date publication requires recovery: ' + str(active))
            yield active
        finally:
            _local.held = held


@contextmanager
def publication_lock(public_pack: Path):
    with _date_lock(Path(public_pack)):
        yield


@contextmanager
def child_lock_options(public_pack):
    """Keep the OS reservation owned by both controller and command."""
    handle = _local.held[str(_control(public_pack))]
    env = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
    if os.name == 'nt':
        from pack_windows_lock import child_options
        with child_options(handle, env) as options:
            yield options
    else:
        yield {'pass_fds': (handle,), 'env': {**env, _FD_ENV: str(handle)}}


def quiz_roots(public, date):
    roots = {}
    for base, prefix, suffix in ((public, '확인문제_', r'\.html'), (public/'.pack', '자료_확인문제_', '')):
        for path in pack_files._children(base):
            match = re.fullmatch(prefix + re.escape(date) + r'_([a-zA-Z0-9_]+)' + suffix,
                                 pack_files._nfc(path.name))
            if match:
                roots.setdefault(match[1], []).append(path.relative_to(public).as_posix())
    return roots


def quiz_inventory(public, roots):
    files, dirs = pack_files._inventory(public, roots)
    return {**files, **{d + '/':'directory' for d in dirs}}


def parent_marker(public):
    marker = _control(public).with_suffix('.parent.json')
    if not marker.exists():
        return {}
    record = _read(marker)
    if 'strict' not in record:
        record['strict'] = bool(_read(record['journal']).get('retire_concept'))
    return record


def attached_quiz(public, inventory, *, journal=None):
    marker = parent_marker(public)
    child = marker.get('child') or {}
    if (not marker.get('strict') or not inventory or child.get('inventory') != inventory
            or child.get('journal') != marker['journal'] or not child.get('action_attempt') or not child.get('review_attempt')
            or (journal and marker['journal'] != str(Path(journal).resolve()))):
        return False
    return child.get('attempt') == Path(marker['journal']).parent.parent.name


def registered_quiz_inventory(public, html, bundle, *, receipt=None):
    if receipt:
        child = parent_marker(public).get('child', {})
        if any(child.get(key) != receipt.get(key) for key in ('attempt','review_attempt','action_attempt')):
            return False
    if not html.is_file() or not bundle.is_dir():
        return False
    return attached_quiz(public, quiz_inventory(public, [html.name, bundle.relative_to(public).as_posix()]))


def register_attached_quiz(public, receipt, journal, inventory):
    marker = parent_marker(public)
    if not marker.get('strict') or marker['journal'] != journal or Path(journal).parent.parent.name != receipt['attempt']:
        raise FlowError('quiz parent publication changed')
    marker['child'] = dict(journal=journal, inventory=inventory, **{key:receipt[key] for key in
                           ('attempt','action_attempt','review_attempt')})
    _save(_control(public).with_suffix('.parent.json'), marker)


def unmanaged_quiz_roots(public, date):
    unmanaged = []
    marker = parent_marker(public)
    recorded = marker.get('child', {}).get('inventory', {})
    for slug, roots in quiz_roots(public, date).items():
        if len(roots) == 2:
            if all(name in recorded or name + '/' in recorded for name in roots):
                try:
                    if attached_quiz(public, quiz_inventory(public, roots)):
                        continue
                except (OSError, ValueError):
                    pass
            # A coincidental name never authorizes recursive inventory or removal.
            command = Path(__file__).resolve().parents[2]/'ec2-concept-check/scripts/concept.py'
            result = subprocess.run([sys.executable, command, 'verify-legacy', '--pack', public, '--slug', slug],
                                    capture_output=True, text=True)
            if not result.returncode:
                continue
        unmanaged.extend(roots)
    return sorted(unmanaged)


def publication_inventory(root, date):
    return _checked_inventory(root, date, concepts=True, exclude=unmanaged_quiz_roots(root, date))


def current_parent_publication(public, journal):
    marker = _control(public).with_suffix('.parent.json')
    return marker.is_file() and _read(marker).get('journal') == str(Path(journal).resolve())


def _checked_inventory(root, date, *, private=False, concepts=False, exclude=()):
    for name in pack_files._roots(root, date):
        directory = re.fullmatch(rf'\.assets/(?:figures_{date}|(?:자료|figures)_문제설명_{date}_[^/]+)',
                                 pack_files._nfc(name))
        path = checked_file(root, name)
        if bool(directory) != path.is_dir():
            raise FlowError('unexpected owned root type: ' + name)
    inventory = pack_files.inventory_at(root, date)
    if concepts:
        roots = [name for names in quiz_roots(root, date).values() for name in names if name not in exclude]
        inventory.update(quiz_inventory(root, roots))
    if private:
        # Candidates and backups contain only owned files and their directories.
        files, dirs = pack_files._inventory(root, [p.name for p in pack_files._children(root)])
        allowed_dirs = {name[:-1] for name in inventory if name.endswith('/')}
        allowed_dirs.update(p.as_posix() for name in inventory for p in Path(name).parents)
        if files.keys() != {k for k in inventory if not k.endswith('/')} or set(dirs) - allowed_dirs:
            raise FlowError('unowned file or directory in publication snapshot')
    return inventory


def _canonical(inventory):
    names = {pack_files._nfc(name): digest for name, digest in inventory.items()}
    if len(names) != len(inventory):
        raise FlowError('ambiguous normalized inventory')
    return names


def _copy_stream(src, dst):
    shutil.copyfileobj(src, dst)
    dst.flush()
    if hasattr(os, 'fchmod'):
        os.fchmod(dst.fileno(), stat.S_IMODE(os.fstat(src.fileno()).st_mode))
    os.fsync(dst.fileno())


def _copy(source, destination, digest):
    with source.open('rb') as src, destination.open('xb') as dst:
        _copy_stream(src, dst)
    if _sha(destination) != digest:
        raise FlowError('publication copy changed: ' + str(source))


def _snapshot(root, target, inventory, date, *, concepts=False):
    target.mkdir()
    for name, value in inventory.items():
        source = checked_file(root, name)
        dst = checked_file(target, name)
        if name.endswith('/'):
            dst.mkdir(parents=True, exist_ok=True)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            _copy(source, dst, value)
    if _checked_inventory(target, date, private=True, concepts=concepts) != inventory:
        raise FlowError('publication snapshot verification failed')
    for directory, _, _ in os.walk(target, topdown=False):
        _fsync_dir(directory)


def _steps(before, after):
    removed = before.keys() - after.keys()
    added = after.keys() - before.keys()
    # Remove descendants before obsolete parents. Create new parents first.
    return [*sorted(n for n in removed if not n.endswith('/')),
            *sorted((n for n in removed if n.endswith('/')), key=lambda n: (-n.count('/'), n)),
            *sorted((n for n in added if n.endswith('/')), key=lambda n: (n.count('/'), n)),
            *sorted(n for n in after if not n.endswith('/') and before.get(n) != after[n])]


def _apply(inventory, name, value):
    if value is None:
        inventory.pop(name, None)
    else:
        inventory[name] = value


def _state(path):
    if not path.exists():
        return None
    mode = path.stat().st_mode
    if stat.S_ISDIR(mode):
        return 'directory'
    if stat.S_ISREG(mode):
        return _sha(path)
    raise FlowError('unexpected publication file type: ' + str(path))


def _check_public_root(public, identity):
    if public.parent.is_symlink() or public.is_symlink() or _key(public) != identity:
        raise FlowError('public date folder changed: ' + str(public))


def _mutate(public, identity, name, old, new, snapshot):
    _check_public_root(public, identity)
    path = checked_file(public, name)
    if _state(path) != old:
        raise FlowError('public path changed: ' + str(path))
    if new is None:
        path.rmdir() if name.endswith('/') else path.unlink()
    elif new == 'directory':
        _mkdirs(path)
    else:
        # Temp files live outside inventory-owned trees on the pack filesystem.
        # Keep them out of an owned asset directory even on abrupt termination.
        _mkdirs(path.parent)
        temp_root = snapshot.parent
        if temp_root.stat().st_dev != path.parent.stat().st_dev:
            temp_root = public.parent if public.parent.stat().st_dev == path.parent.stat().st_dev else public
        with tempfile.NamedTemporaryFile(dir=temp_root, prefix='.pack-install-', delete=False) as stream:
            temporary = Path(stream.name)
            try:
                with checked_file(snapshot, name).open('rb') as src:
                    _copy_stream(src, stream)
            except BaseException:
                temporary.unlink(missing_ok=True)
                raise
        try:
            _check_public_root(public, identity)
            if _sha(temporary) != new or _state(checked_file(public, name)) != old:
                raise FlowError('publication input or destination changed: ' + name)
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)
    _fsync_dir(path.parent)
    if _state(checked_file(public, name)) != new:
        raise FlowError('public mutation verification failed: ' + name)


def _run_steps(journal, data, public, end):
    before, after = data['before'], data['after']
    steps = _steps(before, after)
    reverse = data['direction'] == 'restore'
    source, dest = (after, before) if reverse else (before, after)
    snapshot = journal.parent / ('before' if reverse else 'after')
    while data['cursor'] != end:
        index = data['cursor'] - 1 if reverse else data['cursor']
        name = steps[index]
        data['intent'] = index
        _save(journal, data)
        _mutate(public, data['public'], name, source.get(name), dest.get(name), snapshot)
        data.update(cursor=index if reverse else index + 1, intent=None)
        _save(journal, data)


def _identity(paths):
    public = paths.public_pack
    if _key(public) != _key(pack_files._pack(paths.repo, public.name)):
        raise FlowError('wrong public date folder')
    return public


def _signature(data):
    fields = [data['public'], data['before'], data['after']]
    if data.get('retire_concept'):
        fields.append('retire_concept')
    if 'unmanaged_quiz' in data:
        fields.append(data['unmanaged_quiz'])
    return hashlib.sha256(json.dumps(fields, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def _result(data, journal, status, **extra):
    return dict(status=status, before=data['before'], after=data['after'], journal=str(journal), **extra)


def _finish(journal, data, active, status):
    data['status'] = status
    _save(journal, data)
    if status == 'published':
        _save(_control(Path(data['public'])).with_suffix('.parent.json'), dict(journal=str(journal.resolve()), strict=bool(data.get('retire_concept'))))
    active.unlink()
    _fsync_dir(active.parent)
    return _result(data, journal, status)


def _verify_snapshot(paths, root, expected, *, concepts=False, exclude=()):
    if _checked_inventory(root, paths.public_pack.name, concepts=concepts, exclude=exclude) != expected:
        raise FlowError('owned inventory changed: ' + str(root))


def publish_pack(paths: PackPaths, run: Path, *, expected: dict[str, str],
                 candidate_inventory: dict[str, str], verify, retire_concept=False) -> dict:
    public = _identity(paths)
    identity = _key(public)
    if not paths.candidate_pack or not paths.work_file('.').is_dir():
        raise FlowError('private candidate pack required')
    run = Path(run).absolute()
    if run.is_symlink() or run.resolve().is_relative_to(public.parent.resolve()):
        raise FlowError('publication RUN must be outside public notes')
    run_identity = run.resolve()
    folder = checked_file(run, 'publication')
    if folder.resolve().is_relative_to(paths.work_pack.resolve()) or paths.work_pack.resolve().is_relative_to(folder.resolve()):
        raise FlowError('publication journal overlaps candidate')
    journal = folder / 'journal.json'
    initial = dict(before=expected, after=candidate_inventory)
    with _date_lock(public, allow_pending=True) as active:
        _check_public_root(public, identity)
        if active.exists():
            return _result(initial, _read(active)['journal'], 'recovery_required', error_code='pending_publication')
        unmanaged = unmanaged_quiz_roots(public, public.name) if retire_concept else []
        before = _checked_inventory(public, public.name, concepts=retire_concept, exclude=unmanaged)
        for relative in candidate_inventory:
            note = re.fullmatch(r'정리노트_(.+)\.html', pack_files._nfc(relative))
            if note and {f'확인문제_{note[1]}.html', f'.pack/자료_확인문제_{note[1]}'} & set(map(pack_files._nfc, unmanaged)):
                return _result(initial, journal, 'conflict', error_code='unowned_quiz_overlap')
        if _canonical(before) != _canonical(expected):
            return _result(initial, journal, 'conflict', error_code='publication_conflict')
        verify(paths.work_pack)
        _check_public_root(public, identity)
        after = _checked_inventory(paths.work_file('.'), public.name, private=True)
        supplied = _canonical(candidate_inventory)
        complete = _canonical(after)
        if supplied != complete:
            files = {name: value for name, value in complete.items() if not name.endswith('/')}
            parents = {parent.as_posix() + '/' for name in files for parent in Path(name).parents}
            if supplied != files or set(complete) - files.keys() - parents:
                raise FlowError('adopted candidate inventory mismatch')
        if run.resolve() != run_identity or checked_file(run, 'publication') != folder:
            raise FlowError('publication RUN changed')
        _mkdirs(folder.parent)
        folder.mkdir(exist_ok=False)
        _fsync_dir(folder.parent)
        _snapshot(public, folder / 'before', before, public.name, concepts=retire_concept)
        _snapshot(paths.work_pack, folder / 'after', after, public.name)
        _verify_snapshot(paths, public, before, concepts=retire_concept, exclude=unmanaged)
        _check_public_root(public, identity)
        data = dict(schema_version=1, public=identity, before=before, after=after, retire_concept=retire_concept,
                    status='applying', direction='publish', cursor=0, intent=None)
        if retire_concept:
            data['unmanaged_quiz'] = unmanaged
        _save(journal, data)
        _save(active, dict(journal=str(journal.resolve()), signature=_signature(data)))
        try:
            _mkdirs(public)
            _run_steps(journal, data, public, len(_steps(data['before'], data['after'])))
            _verify_snapshot(paths, public, after, concepts=retire_concept, exclude=unmanaged)
            verify(public)
            _check_public_root(public, identity)
            _verify_snapshot(paths, public, after, concepts=retire_concept, exclude=unmanaged)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            return _result(data, journal, 'recovery_required', error_code='publication_interrupted', detail=str(exc))
        return _finish(journal, data, active, 'published')


@contextmanager
def reconciliation_lock(public):
    # Recovery may already hold the date lock through its enclosing RUN commit.
    control = _control(public)
    if getattr(_local, 'reconciliation', None) == control:
        yield control.with_suffix('.publication.json')
    else:
        with _date_lock(public, allow_pending=True) as active:
            prior = getattr(_local, 'reconciliation', None)
            _local.reconciliation = control
            try:
                yield active
            finally:
                _local.reconciliation = prior


def reconcile_publication(paths: PackPaths, journal: Path, *, verify) -> dict:
    public = _identity(paths)
    journal = Path(journal).absolute()
    with reconciliation_lock(public) as active:
        data = {}
        try:
            if (journal.name != 'journal.json' or journal.parent.name != 'publication' or journal.is_symlink()
                    or journal.parent.is_symlink() or journal.resolve().is_relative_to(public.parent.resolve())):
                raise FlowError('unsafe publication journal')
            record = _read(journal)
            if not isinstance(record, dict):
                raise FlowError('invalid publication journal')
            data = record
            _check_public_root(public, data['public'])
            if data['schema_version'] != 1:
                raise FlowError('journal does not belong to this date')
            if active.exists():
                owner = _read(active)
                if owner != dict(journal=str(journal.resolve()), signature=_signature(data)):
                    raise FlowError('different active transaction')

            retire_concept = data.get('retire_concept', False)
            unmanaged = data.get('unmanaged_quiz', [])
            before, after = data['before'], data['after']
            # Never use journal-provided names to access files. Compare entire
            # inventories obtained by walking owned roots, including backups.
            for name in ('before', 'after'):
                snapshot = checked_file(journal.parent, name)
                if not snapshot.is_dir() or _checked_inventory(snapshot, public.name, private=True, concepts=retire_concept and name == 'before') != data[name]:
                    raise FlowError('publication backup or staged snapshot damaged')
            current = _checked_inventory(public, public.name, concepts=retire_concept, exclude=unmanaged)
            if not active.exists() and data['status'] == 'applying':
                # The journal is durable before its date reservation is created.
                # In this narrow crash window the protocol permits no public write.
                if (current != before or data['direction'] != 'publish' or data['cursor'] != 0
                        or data['intent'] is not None):
                    raise FlowError('missing active transaction')
                data['status'] = 'restored'
                _save(journal, data)
                return _result(data, journal, 'restored')
            if data['status'] == 'published' and not active.exists() and not current_parent_publication(public, journal):
                raise FlowError('settled publication belongs to a different journal')
            if data['status'] == 'published' and retire_concept and not active.exists():
                # This parent may have acquired its own authorized child after its journal settled.
                child = {name:current[name] for name in current.keys() - after.keys()}
                if attached_quiz(public, child, journal=journal):
                    roots = [name for names in quiz_roots(public, public.name).values() for name in names
                             if name in child or name + '/' in child]
                    unmanaged = [*unmanaged, *roots]
                    current = _checked_inventory(public, public.name, concepts=True, exclude=unmanaged)
            if data['status'] in ('published', 'restored'):
                if current != (after if data['status'] == 'published' else before):
                    raise FlowError('settled publication changed')
                if data['status'] == 'published':
                    verify(public)
                    _check_public_root(public, data['public'])
                    _verify_snapshot(paths, public, after, concepts=retire_concept, exclude=unmanaged)
                return (_finish(journal, data, active, data['status']) if active.exists()
                        else _result(data, journal, data['status']))
            steps = _steps(before, after)
            cursor, intent = data['cursor'], data['intent']
            reverse = data['direction'] == 'restore'
            if (data['status'] != 'applying' or data['direction'] not in ('publish', 'restore')
                    or type(cursor) is not int or not 0 <= cursor <= len(steps)):
                raise FlowError('invalid journal progress')
            known = before.copy()
            for name in steps[:cursor]:
                _apply(known, name, after.get(name))
            if intent is not None:
                if type(intent) is not int or intent != (cursor - 1 if reverse else cursor) or not 0 <= intent < len(steps):
                    raise FlowError('invalid pending operation')
                advanced = known.copy()
                _apply(advanced, steps[intent], (before if reverse else after).get(steps[intent]))
                if current == advanced:
                    # A process may have died between the rename/unlink/mkdir
                    # and its directory fsync. Persist this observed mutation
                    # before any recovered cursor or terminal status is saved.
                    _check_public_root(public, data['public'])
                    _fsync_dir(checked_file(public, steps[intent]).parent)
                    cursor += -1 if reverse else 1
                    known = advanced
            if current != known:
                raise FlowError('public bytes do not match the journaled operation order')
            if not reverse and cursor == len(steps):
                try:
                    verify(public)
                except (OSError, ValueError, KeyError, TypeError):
                    pass  # The new bytes are known, but their current proof failed.
                else:
                    _check_public_root(public, data['public'])
                    _verify_snapshot(paths, public, after, concepts=retire_concept, exclude=unmanaged)
                    data.update(cursor=cursor, intent=None)
                    return _finish(journal, data, active, 'published')
            data.update(direction='restore', cursor=cursor, intent=None)
            _save(journal, data)
            _run_steps(journal, data, public, 0)
            _verify_snapshot(paths, public, before, concepts=retire_concept, exclude=unmanaged)
            return _finish(journal, data, active, 'restored')
        except (OSError, ValueError, KeyError, TypeError) as exc:
            return dict(status='recovery_required', error_code='unverified_publication', journal=str(journal),
                        before=data.get('before'), after=data.get('after'), detail=str(exc))
