"""Seed a new RUN from a withheld RUN: carry accepted tasks, redo the rest.

Only worker tasks before the first machine action can be carried. Actions write
the repository or depend on it, so they always run again; every task after them
depends on an action and is redone through the normal dependency chain.
"""
from __future__ import annotations

from pathlib import Path
import re
import shutil

import pack_flow as f

# Never carried: the child run has its own receipts, and PDF review follows actions.
_NEVER = {'child-coordinator', 'pdf-qa'}
_TEXT = {'.json', '.md', '.txt', '.html', '.svg', '.csv', '.tex'}


def _seedable(old: dict) -> None:
    if old['status'] == 'withheld': return
    # A blocked/needs_fix RUN is safe only if it never touched the repository.
    if old['status'] in ('blocked', 'needs_fix') and not old['backups'] and not old['publication']: return
    raise f.FlowError('seed RUN must be withheld, or blocked/needs_fix before any repository write')


def _same_inputs(old: dict, new: dict) -> bool:
    def keyed(state):
        run = Path(state['run']).resolve()
        result = {}
        for path, digest in state['hashes'].items():
            p = Path(path).resolve()
            result['RUN/' + p.relative_to(run).as_posix() if p.is_relative_to(run) else str(p)] = digest
        return result
    return keyed(old) == keyed(new)


class _Copier:
    """Copy old-RUN files to the same relative path, rewriting embedded RUN paths."""

    def __init__(self, old_run: Path, new_run: Path):
        self.old, self.new = old_run, new_run
        names = sorted({str(old_run), str(old_run.resolve())}, key=len, reverse=True)
        self.pattern = re.compile('(?:' + '|'.join(map(re.escape, names)) + r')(?=[/\\"\'\s<>)]|$)')
        self.done: dict[str, dict] = {}

    def path(self, value: str) -> str:
        return self.pattern.sub(lambda _: str(self.new), value)

    def value(self, value):
        if isinstance(value, str): return self.path(value)
        if isinstance(value, list): return [self.value(x) for x in value]
        if isinstance(value, dict): return {k: self.value(v) for k, v in value.items()}
        return value

    def file(self, source: Path, expected: str | None = None) -> dict:
        source = source.resolve()
        if not source.is_relative_to(self.old.resolve()): raise f.FlowError('carried file outside seed RUN: ' + str(source))
        if expected is not None and f._sha(source) != expected:
            raise f.FlowError('changed in seed RUN: ' + str(source))
        if str(source) in self.done: return self.done[str(source)]
        target = self.new / source.relative_to(self.old.resolve())
        target.parent.mkdir(parents=True, exist_ok=True)
        data = source.read_bytes()
        if source.suffix.lower() in _TEXT:
            try:
                data = self.pattern.sub(lambda _: str(self.new), data.decode('utf-8')).encode('utf-8')
            except UnicodeDecodeError: pass
        target.write_bytes(data)
        record = {'path': str(target), 'sha256': f._sha(target)}
        self.done[str(source)] = record
        return record

    def tree(self, folder: Path) -> None:
        if folder.is_dir():
            for path in sorted(folder.rglob('*')):
                if path.is_file() and path.name != '.pack-flow.lock': self.file(path)


def _carry_receipt(copier: _Copier, receipt: dict) -> dict:
    """Copy every old-RUN file the receipt binds; keep repo records unchanged."""
    old_run = copier.old.resolve()
    def records(items):
        result = []
        for item in items:
            path = Path(item['path']).resolve()
            result.append(copier.file(path, item['sha256']) if path.is_relative_to(old_run) else dict(item))
        return result
    carried = copier.value(receipt)
    for field in ('inputs', 'outputs', 'verified_files'):
        if field in receipt: carried[field] = records(receipt[field])
    return carried


def _previous(copier: _Copier, task: dict) -> list[str]:
    """Copy a redo task's last report and outputs so the worker revises instead of restarting."""
    receipt = task.get('receipt') or {}
    run = copier.old.resolve()
    folder = Path(task['brief']).parent.relative_to(run) if Path(task['brief']).resolve().is_relative_to(run) else None
    paths = []
    for item in [*receipt.get('outputs', []), {'path': receipt.get('report')}]:
        source = Path(item['path']).resolve() if item.get('path') else None
        if not source or not source.is_relative_to(run) or not source.is_file(): continue
        relative = source.relative_to(run)
        target = copier.new / (folder or Path('work') / task['id']) / 'seed-previous' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        paths.append(str(target))
    return paths


def seed_state(state: dict, seed_run: Path, redo: list[str], note: Path | None) -> None:
    """Install carried tasks into a fresh in-memory state, then refresh stages."""
    seed_run, run = Path(seed_run).resolve(), Path(state['run']).resolve()
    if seed_run == run: raise f.FlowError('seed RUN must differ from the new RUN')
    old = f.load_state(seed_run)
    if old['range'] != state['range'] or old['lite'] != state['lite']: raise f.FlowError('seed RUN range/lite differ')
    if Path(old['repo']).resolve() != Path(state['repo']).resolve(): raise f.FlowError('seed RUN repo differs')
    _seedable(old)
    unknown = [tid for tid in redo if tid not in old['tasks']]
    if unknown: raise f.FlowError('unknown redo task: ' + ','.join(unknown))
    if any(t.get('status') in ('claimed', 'running') or t.get('invalidated_active') for t in old['tasks'].values()):
        raise f.FlowError('seed RUN has active attempts')
    summary = dict(run=str(seed_run), run_id=old['run_id'], carried=[], redo=list(redo), rejected=[])
    state['seeded_from'] = summary
    if not _same_inputs(old, state):
        summary['rejected'].append(dict(id='*', reason='frozen STT/profile inputs changed'))
        f.refresh_tasks(state)
        return
    copier = _Copier(seed_run, run)
    with f._locked(seed_run):
        if note is not None:
            target = run / 'requests' / 'seed-redo' / Path(note).name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(note, target)
            summary['redo_note'] = str(target)
        for tid in redo:
            summary.setdefault('previous', {})[tid] = _previous(copier, old['tasks'][tid])
        tried = set()
        while True:
            f.refresh_tasks(state)
            changed = False
            for tid, task in state['tasks'].items():
                prior = old['tasks'].get(tid)
                if (tid in tried or task['status'] != 'pending' or tid in redo or not prior
                        or prior.get('status') != 'done' or task['role'] in _NEVER
                        or any(not f._done(state, d) for d in task['dependencies'])):
                    continue
                tried.add(tid)
                if (prior['role'], prior['targets'], prior['dependencies']) != (task['role'], task['targets'], task['dependencies']):
                    summary['rejected'].append(dict(id=tid, reason='task shape differs')); continue
                try:
                    from pack_receipts import verify_receipt_files
                    errors = verify_receipt_files(prior['receipt'] or {})
                    if errors or not (prior['receipt'] or {}).get('verified_files'):
                        raise f.FlowError('; '.join(errors) or 'no verified files')
                    receipt = _carry_receipt(copier, prior['receipt'])
                    copier.tree(Path(prior['brief']).parent)
                except (f.FlowError, OSError, KeyError, TypeError) as exc:
                    summary['rejected'].append(dict(id=tid, reason=str(exc)[:200])); continue
                task.update(status='done', attempt=prior['attempt'], agent_id=prior.get('agent_id'),
                            receipt=receipt, brief=copier.path(prior['brief']),
                            carried=dict(run=str(seed_run), run_id=old['run_id'], attempt=prior['attempt']))
                summary['carried'].append(tid)
                changed = True
            if not changed: break
    for tid in redo:
        attach_redo(state, tid)


def attach_redo(state: dict, tid: str) -> None:
    """Give a redo task the seed note and its previous outputs once it is registered."""
    seeded = state.get('seeded_from') or {}
    task = state['tasks'].get(tid)
    if tid not in seeded.get('redo', []) or not task: return
    paths = task.setdefault('request_paths', [])
    for path in [seeded.get('redo_note'), *seeded.get('previous', {}).get(tid, [])]:
        if path and path not in paths: paths.append(path)
