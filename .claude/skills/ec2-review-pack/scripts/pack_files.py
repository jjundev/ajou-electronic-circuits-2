"""Verified first backups, narrow cleanup, and coherent pack recovery.

Unicode normalization is used only for ownership comparisons. Receipts retain
actual relative names and hashes of unmodified file bytes.
"""
from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import tempfile
import unicodedata
from pack_flow import FlowError


def _nfc(s): return unicodedata.normalize('NFC', s)
def _sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def _check(p, base):
    if p.is_symlink() or not p.resolve().is_relative_to(base.resolve()):
        raise FlowError(f'Unsafe path: {p}')


def _kind(rel, r):
    rel = _nfc(rel)
    if re.fullmatch(rf'정리노트_{r}_[^/]+\.html|복습문제_{r}_[^/]+-(문제|답안)\.pdf|\.assets/정리노트_{r}_[^/]+\.md', rel): return 'basic'
    if rel in ('.assets/problems.txt','.assets/display-titles.json','.assets/selection.json','.pack/selection-review.json',f'.assets/figures_{r}'): return 'basic'
    if re.fullmatch(rf'문제설명_{r}_[^/]+\.html|\.assets/문제설명_{r}_[^/]+\.md|\.assets/(figures|자료)_문제설명_{r}_[^/]+',rel): return 'explanations'
    return None


def _pack(repo,r):
    if not re.fullmatch(r'\d{4}(-\d{4})?',r): raise FlowError('Invalid range')
    repo=Path(repo).resolve(); notes=repo/'복습노트'; pack=notes/r
    _check(notes,repo); _check(pack,repo)
    return pack


def _children(base):
    if not base.exists(): return []
    seen={}; result=[]
    for p in base.iterdir():
        name=_nfc(p.name)
        if name in seen: raise FlowError(f'NFC name collision: {p} and {seen[name]}')
        seen[name]=p; result.append(p)
    return sorted(result)


def _roots(pack,r):
    result=[]
    for base in (pack,pack/'.assets',pack/'.pack'):
        _check(base,pack)
        for p in _children(base):
            if _kind(p.relative_to(pack).as_posix(),r): result.append(p.relative_to(pack).as_posix())
    return result


def _inventory(base,roots):
    files,dirs={},[]
    def visit(p):
        _check(p,base)
        if not p.exists(): raise FlowError(f'Missing backup path: {p}')
        rel=p.relative_to(base).as_posix()
        if p.is_dir():
            dirs.append(rel)
            for child in _children(p): visit(child)
        elif p.is_file(): files[rel]=_sha(p)
        else: raise FlowError(f'Unsupported file: {p}')
    for rel in roots: visit(base/rel)
    return files,sorted(dirs)


def inventory_at(pack: Path, range_: str) -> dict[str,str]:
    files, dirs = _inventory(pack, _roots(pack, range_))
    return {**files, **{d + "/": "directory" for d in dirs}}


def inventory_pack(repo: Path, range_: str) -> dict[str,str]:
    """Return actual relative file names -> SHA-256, plus dir/ -> directory."""
    try:
        return inventory_at(_pack(repo, range_), range_)
    except OSError as e: raise FlowError(str(e)) from e


def _copy(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True)
    if src.is_dir(): shutil.copytree(src,dst,dirs_exist_ok=True)
    else: shutil.copy2(src,dst)


def _validate(record,run,r):
    if record['range']!=r: raise FlowError('Backup range mismatch')
    roots,files,dirs=record['roots'],record['files'],record['dirs']
    for rel in [*roots,*files,*dirs]:
        path=Path(rel)
        if path.is_absolute() or '..' in path.parts or '\\' in rel or not any(rel==root or rel.startswith(root+'/') for root in roots): raise FlowError('Unsafe backup entry')
    if any(not _kind(rel,r) for rel in roots): raise FlowError('Unowned backup root')
    if len(set(map(_nfc,roots)))!=len(roots): raise FlowError('NFC backup collision')
    if record['backup'] is None:
        if roots or files or dirs: raise FlowError('Nonempty null backup')
    else:
        backup=Path(record['backup']); _check(backup,run)
        if _inventory(backup,roots)!=(files,sorted(dirs)): raise FlowError('Backup paths/hash mismatch')
        # Structural parent directories are implicit, but no extra files or
        # unrelated directories may be smuggled into a recorded backup.
        implicit={Path(rel).parent.as_posix() for rel in [*files,*dirs]}
        implicit |= {parent.as_posix() for rel in [*files,*dirs] for parent in Path(rel).parents if parent.as_posix()!='.'}
        all_files,all_dirs=_inventory(backup,[p.name for p in _children(backup)])
        if all_files!=files or set(all_dirs)-set(dirs)-implicit: raise FlowError('Unexpected backup paths')


def _backup(pack,run,r,kind):
    path=run/('basic-pack-backup.json' if kind=='basic' else 'explanations-backup.json')
    if path.exists():
        _check(path,run); record=json.loads(path.read_text(encoding='utf-8')); _validate(record,run,r); return record
    roots=[rel for rel in _roots(pack,r) if _kind(rel,r)==kind]
    files,dirs=_inventory(pack,roots)
    record=dict(range=r,backup=None,roots=roots,files=files,dirs=dirs)
    if roots:
        backup=Path(tempfile.mkdtemp(prefix='previous-' if kind=='basic' else 'previous-explanations-',dir=run))
        record['backup']=str(backup.resolve())
        for rel in roots: _copy(pack/rel,backup/rel)
        _validate(record,run,r)
    path.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return record


def prepare_pack(repo: Path, run: Path, manifest_path: Path) -> dict:
    """Return basic/explanations receipt paths and current inventory.

    Both immutable first receipts are validated before any published removal.
    pack-first-inventory.json freezes their shared pre-change source inventory.
    """
    try:
        run=Path(run).resolve()
        if not run.is_dir() or not (Path(repo)/'STT').is_dir(): raise FlowError('Invalid repo/RUN')
        m=json.loads(Path(manifest_path).read_text(encoding='utf-8')); r=m['range']; pack=_pack(repo,r)
        # Validate proposed destinations before any backup or cleanup mutation.
        slug=m['slug']
        if not isinstance(slug,str) or not slug or '/' in slug or '\\' in slug or slug in ('.','..'): raise FlowError('Unsafe slug')
        slug=_nfc(slug)
        for rel in (f'정리노트_{r}_{slug}.html',f'.assets/정리노트_{r}_{slug}.md',f'복습문제_{r}_{slug}-문제.pdf',f'복습문제_{r}_{slug}-답안.pdf'):
            _check(pack/rel,pack)
        current=inventory_pack(repo,r)
        first_inventory=run/'pack-first-inventory.json'
        _check(first_inventory,run)
        incomplete=not all((run/name).exists() for name in ('basic-pack-backup.json','explanations-backup.json'))
        if not first_inventory.exists():
            if any((run/name).exists() for name in ('basic-pack-backup.json','explanations-backup.json')):
                raise FlowError('First inventory missing for existing backup')
            # Persist the single first pre-change state before either backup.
            # Exclusive creation prevents a retry from replacing this evidence.
            with first_inventory.open('x',encoding='utf-8') as stream:
                json.dump({'range':r,'inventory':current},stream,ensure_ascii=False,indent=2)
                stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
        initial=json.loads(first_inventory.read_text(encoding='utf-8'))
        if initial['range']!=r: raise FlowError('First inventory range mismatch')
        if incomplete and current!=initial['inventory']:
            raise FlowError('Pack inventory changed before both first backups completed')
        basic=_backup(pack,run,r,'basic')
        if incomplete and inventory_pack(repo,r)!=initial['inventory']:
            raise FlowError('Pack inventory changed before explanation backup')
        explanations=_backup(pack,run,r,'explanations')
        for record in (basic,explanations): _validate(record,run,r)
        if incomplete and inventory_pack(repo,r)!=initial['inventory']:
            raise FlowError('Pack inventory changed while creating first backups')
        keep={f'정리노트_{r}_{slug}.html',f'.assets/정리노트_{r}_{slug}.md'}
        previous=next((pack/rel for rel in basic['roots'] if _nfc(rel)=='.assets/problems.txt'),None)
        ids=[line.split('|',1)[0].strip() for line in previous.read_text(encoding='utf-8').splitlines() if line.strip()] if previous and previous.exists() else []
        if m['problems']:
            keep.add(f'복습문제_{r}_{slug}-문제.pdf')
            if ids==[q['id'] for q in m['problems']]: keep.add(f'복습문제_{r}_{slug}-답안.pdf')
        pending=[]
        for record in (basic,explanations):
            for rel in record['roots']:
                target=pack/rel
                cleanup=record is explanations or bool(re.fullmatch(rf'정리노트_{r}_.+\.html|복습문제_{r}_.+-(문제|답안)\.pdf|\.assets/정리노트_{r}_.+\.md',_nfc(rel))) and _nfc(rel) not in keep
                if cleanup and target.exists():
                    if _inventory(pack,[rel])!=_inventory(Path(record['backup']),[rel]): raise FlowError(f'Current file changed: {rel}')
                    pending.append((target,Path(record['backup'])/rel))
        touched=[]
        try:
            for target,saved in pending:
                # Include the failing operation: rmtree can partially remove a
                # directory before raising. Pending roots were just verified
                # byte/path-equivalent to these saved copies.
                touched.append((target,saved))
                shutil.rmtree(target) if target.is_dir() else target.unlink()
        except OSError:
            for target,saved in touched:
                _copy(saved,target)
            raise
        return {'basic':str(run/'basic-pack-backup.json'),'explanations':str(run/'explanations-backup.json'),'inventory':inventory_pack(repo,r)}
    except (OSError,ValueError,KeyError,TypeError) as e: raise FlowError(str(e)) from e


def recover_pack(repo: Path, run: Path, range_: str, expected_current: dict[str,str]) -> dict:
    """Return status(restored|withheld), withheld path and current inventory.

    expected_current must be the runner's last saved post-write inventory.
    Backups and verified withheld copies remain available on I/O failure.
    """
    try:
        run=Path(run).resolve(); pack=_pack(repo,range_)
        if inventory_pack(repo,range_)!=expected_current: raise FlowError('External pack edit blocks recovery')
        records=[json.loads((run/name).read_text(encoding='utf-8')) for name in ('basic-pack-backup.json','explanations-backup.json')]
        for record in records: _validate(record,run,range_)
        roots=_roots(pack,range_); before=_inventory(pack,roots)
        withheld=Path(tempfile.mkdtemp(prefix='withheld-',dir=run))
        for rel in roots: _copy(pack/rel,withheld/rel)
        if _inventory(withheld,roots)!=before: raise FlowError('Withheld copy verification failed')
        try:
            for rel in roots:
                target=pack/rel
                shutil.rmtree(target) if target.is_dir() else target.unlink()
            for record in records:
                for rel in record['roots']: _copy(Path(record['backup'])/rel,pack/rel)
                if _inventory(pack,record['roots'])!=(record['files'],sorted(record['dirs'])): raise FlowError('Restore verification failed')
        except OSError as failure:
            # Best effort completion in the same basic -> explanation order.
            # Never turn a partial I/O failure into a success receipt.
            try:
                for record in records:
                    for rel in record['roots']: _copy(Path(record['backup'])/rel,pack/rel)
            except OSError as restore_failure:
                raise FlowError(f'Recovery I/O failed; backups and withheld retained at {withheld}: {failure}; restore: {restore_failure}') from restore_failure
            raise FlowError(f'Recovery I/O failed; backups and withheld retained at {withheld}: {failure}') from failure
        return {'status':'restored' if any(x['roots'] for x in records) else 'withheld','withheld':str(withheld),'inventory':inventory_pack(repo,range_)}
    except (OSError,ValueError,KeyError,TypeError) as e: raise FlowError(str(e)) from e
