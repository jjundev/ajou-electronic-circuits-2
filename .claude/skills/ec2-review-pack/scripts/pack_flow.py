"""Validated, revisioned runner state. Semantic review remains human work."""
from __future__ import annotations

from contextlib import contextmanager
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unicodedata
from uuid import UUID, uuid4
from typing import Callable


class FlowError(ValueError):
    """A state or filesystem precondition failed."""


_FIELDS = {"schema_version", "revision", "run_id", "repo", "run", "range", "lite",
           "capabilities", "phase", "status", "tasks", "actions", "hashes", "backups",
           "fix_rounds", "explain_run", "publication", "recovery"}
_STATUSES = {"ready", "waiting_agents", "running", "needs_fix", "blocked",
             "recovery_required", "withheld", "complete"}
_OWNERS = {"workers", "main", "unavailable"}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _check_extra_authorization(data: dict, state: dict) -> None:
    required = {'schema_version', 'id', 'run_id', 'category', 'extra_rounds',
                'approved_by', 'human_request', 'request_ref', 'reason'}
    if (not isinstance(data, dict) or set(data) != required
        or type(data['schema_version']) is not int or data['schema_version'] != 1
        or data['run_id'] != state['run_id'] or data['category'] != 'machine_browser'
        or type(data['extra_rounds']) is not int or data['extra_rounds'] != 1
        or data['approved_by'] != 'user'
        or any(not isinstance(data[key], str) or not data[key].strip()
               for key in ('id', 'human_request', 'request_ref', 'reason'))):
        raise FlowError('invalid explicit user authorization for one machine/browser round')


def _fix_limit(state: dict, category: str) -> int:
    if category == 'content': return 1
    if 'extra_fix_authorization' not in state: return 2
    record = state['extra_fix_authorization']
    canonical = Path(state['run']) / 'authorizations/machine-browser-extra.json'
    try:
        if (not isinstance(record, dict) or set(record) != {'path', 'sha256'}
            or record['path'] != str(canonical)
            or not canonical.resolve().is_relative_to(Path(state['run']).resolve())
            or _sha(canonical) != record['sha256']):
            raise FlowError('extra fix authorization evidence changed')
        _check_extra_authorization(_read(canonical), state)
    except (OSError, ValueError, TypeError) as exc:
        raise FlowError('invalid saved extra fix authorization: ' + str(exc)) from exc
    return 3


def _validate(state: dict, run: Path) -> None:
    def require(condition, reason):
        if not condition:
            raise FlowError(f"{run / 'run-status.json'}: {reason}")
    require(isinstance(state, dict), "state must be an object")
    require(_FIELDS <= state.keys(), "missing required state fields")
    require(type(state["schema_version"]) is int and state["schema_version"] == 1, "unsupported schema_version")
    require(type(state["revision"]) is int and state["revision"] >= 0, "invalid revision")
    try:
        UUID(state["run_id"])
    except (ValueError, TypeError, AttributeError):
        raise FlowError(f"{run}: invalid run_id") from None
    for field in ("repo", "run"):
        require(isinstance(state[field], str) and Path(state[field]).is_absolute(), f"{field} must be absolute")
        require(Path(state[field]).is_dir(), f"{field} directory missing: {state[field]}")
    require(Path(state["run"]).resolve() == run.resolve(), "run path mismatch")
    require(type(state["lite"]) is bool, "invalid lite")
    require(type(state["phase"]) is int and 0 <= state["phase"] <= 10, "invalid phase")
    require(isinstance(state["status"], str) and state["status"] in _STATUSES, "invalid status")
    require(isinstance(state["range"], str) and re.fullmatch(r"\d{4}(?:-\d{4})?", state["range"]), "invalid range")
    for field in ("tasks", "actions", "hashes", "backups", "publication", "recovery", "capabilities", "fix_rounds"):
        require(isinstance(state[field], dict), f"{field} must be an object")
    for owner in ("browser_owner", "pdf_owner"):
        value = state["capabilities"].get(owner)
        require(isinstance(value, str) and value in _OWNERS, f"invalid {owner}")
    for category in ("content", "machine_browser"):
        maximum = _fix_limit(state, category)
        value = state["fix_rounds"].get(category)
        require(type(value) is int and 0 <= value <= maximum, f"invalid {category} fix rounds")
    require(state["explain_run"] is None or (isinstance(state["explain_run"], str) and Path(state["explain_run"]).is_absolute()), "invalid explain_run")
    for path, digest in state["hashes"].items():
        require(Path(path).is_absolute() and isinstance(digest, str) and re.fullmatch(r"[a-f0-9]{64}", digest), "invalid input hash")
        candidate = Path(path).resolve()
        require(any(candidate.is_relative_to(Path(state[root]).resolve()) for root in ("repo", "run")), f"input outside repo/run: {path}")


@contextmanager
def _locked(run: Path):
    """Nonblocking OS-owned lock; leave its inode in place after release."""
    lock = run / ".pack-flow.lock"
    with lock.open("a+b") as handle:
        acquired = False
        try:
            if os.name == "nt":
                import msvcrt
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            acquired = True
            yield
        except OSError as exc:
            raise FlowError(f"{lock}: {'state write' if acquired else 'lock busy'}: {exc}") from exc
        finally:
            if acquired:
                if os.name == "nt":
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _atomic_json(path: Path, data: dict):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=f".{path.name}.", suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except (OSError, TypeError, ValueError) as exc:
        raise FlowError(f"{path}: atomic write failed: {exc}") from exc
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def load_state(run: Path) -> dict:
    run = Path(run).resolve()
    try:
        state = json.loads((run / "run-status.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise FlowError(f"{run / 'run-status.json'}: {exc}") from exc
    _validate(state, run)
    return state


def update_state(run: Path, expected_revision: int, change: Callable[[dict], dict]) -> dict:
    run = Path(run).resolve()
    with _locked(run):
        state = load_state(run)
        if type(expected_revision) is not int or state["revision"] != expected_revision:
            raise FlowError(f"{run}: revision conflict (expected {expected_revision}, current {state['revision']})")
        changed = change(copy.deepcopy(state))
        if ('extra_fix_authorization' in state
            and changed.get('extra_fix_authorization') != state['extra_fix_authorization']):
            raise FlowError('extra fix authorization is immutable')
        _validate(changed, run)
        for field in ("run_id", "repo", "run", "range", "lite", "schema_version", "revision"):
            if changed[field] != state[field]:
                raise FlowError(f"{run}: immutable field changed: {field}")
        changed["revision"] = expected_revision + 1
        _atomic_json(run / "run-status.json", changed)
        return changed


def init_run(repo: Path, run: Path, range_: str, *, lite: bool = False,
             browser_owner: str = "main", pdf_owner: str = "main") -> dict:
    repo, run = Path(repo).resolve(), Path(run).resolve()
    if not repo.is_dir():
        raise FlowError(f"{repo}: repo directory missing")
    if run.exists() and (not run.is_dir() or any(run.iterdir())):
        raise FlowError(f"{run}: nonempty RUN is not allowed")
    if not re.fullmatch(r"\d{4}(?:-\d{4})?", range_):
        raise FlowError(f"{run}: invalid range: {range_}")
    start, _, end = range_.partition("-")
    end = end or start
    if start > end:
        raise FlowError(f"{run}: reversed range: {range_}")
    if browser_owner not in _OWNERS or pdf_owner not in _OWNERS:
        raise FlowError(f"{run}: invalid capability owner")
    sources = []
    names = set()
    for path in sorted((repo / "STT").glob("*.md")):
        name = unicodedata.normalize("NFC", path.name)
        match = re.fullmatch(r"(\d{4}) 전회2\.md", name)
        if match and start <= match[1] <= end:
            if name in names:
                raise FlowError(f"{path}: NFC filename collision")
            names.add(name)
            sources.append(path)
    if not sources:
        raise FlowError(f"{repo / 'STT'}: no STT sessions for {range_}")
    run.mkdir(parents=True, exist_ok=True)
    with _locked(run):
        if any(p.name != ".pack-flow.lock" for p in run.iterdir()):
            raise FlowError(f"{run}: nonempty RUN is not allowed")
        snapshot_path = run / "learning-style.json"
        command = [sys.executable, str(repo / "workbook/learning_style.py"), "snapshot",
                   "--repo", str(repo), "--out", str(snapshot_path)]
        result = subprocess.run(command, capture_output=True, encoding="utf-8", errors="replace",
                                env=dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8"))
        if result.returncode:
            raise FlowError(f"{snapshot_path}: snapshot failed: {result.stderr.strip()}")
        try:
            snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
            profile = repo / snapshot["path"]
            if not profile.resolve().is_relative_to(repo) or snapshot["sha256"] != _sha(profile):
                raise ValueError("snapshot hash/path mismatch")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise FlowError(f"{snapshot_path}: invalid snapshot: {exc}") from exc
        state = dict(schema_version=1, revision=0, run_id=str(uuid4()), repo=str(repo), run=str(run),
                     range=range_, lite=lite, capabilities=dict(browser_owner=browser_owner, pdf_owner=pdf_owner),
                     phase=0, status="ready", tasks={}, actions={},
                     hashes={str(p): _sha(p) for p in [*sources, profile, snapshot_path]}, backups={},
                     fix_rounds=dict(content=0, machine_browser=0), explain_run=None,
                     publication={}, recovery={}, sessions=[p.name[:4] for p in sources])
        refresh_tasks(state)
        write_briefs(state)
        _validate(state, run)
        _atomic_json(run / "run-status.json", state)
        return state


def inspect_state(run: Path) -> dict:
    """Return a current view without writing state, locks, or snapshots."""
    state = load_state(run)
    return _current(state)


def _task_change(run, task_id, change):
    state = load_state(run)
    def apply(current):
        if task_id not in current['tasks']:
            raise FlowError('unknown task: ' + task_id)
        change(current, current['tasks'][task_id])
        return current
    return update_state(run, state['revision'], apply)


def claim_task(run: Path, task_id: str) -> dict:
    def change(state, task):
        _current(state)
        if state['stale_inputs']: raise FlowError('frozen source/profile changed')
        if task.get('invalidated_active'): raise FlowError('confirm stopped and release stale active attempt first')
        if task['status'] not in ('pending', 'needs_fix', 'stale'):
            raise FlowError('task is already claimed or unavailable')
        if any(not _done(state, dep) for dep in task['dependencies']):
            raise FlowError('task dependencies are not done')
        brief = Path(task['brief']).resolve()
        if not brief.is_relative_to(Path(state['run'])) or not brief.is_file():
            raise FlowError('brief must be a RUN file')
        task.update(status='claimed', attempt=str(uuid4()), agent_id=None,
                    brief_sha256=_sha(brief), receipt=None)
    state = _task_change(run, task_id, change)
    task = state['tasks'][task_id]
    return dict(task_id=task_id, attempt=task['attempt'], brief=task['brief'])


def _attempt(task, attempt):
    if task.get('attempt') != attempt or task['status'] not in ('claimed', 'running'):
        raise FlowError('inactive or late task attempt')
    if _sha(Path(task['brief'])) != task.get('brief_sha256'):
        raise FlowError('brief changed after claim')


def bind_task(run: Path, task_id: str, attempt: str, agent_id: str) -> dict:
    def change(state, task):
        _attempt(task, attempt)
        if not isinstance(agent_id, str) or not agent_id.strip() or task.get('agent_id'):
            raise FlowError('agent ID missing or already bound')
        task.update(status='running', agent_id=agent_id)
    return _task_change(run, task_id, change)


def accept_task(run: Path, task_id: str, attempt: str, receipt_path: Path) -> dict:
    from pack_receipts import validate_receipt
    def change(state, task):
        _current(state)
        _attempt(task, attempt)
        if any(not _done(state, dep) for dep in task['dependencies']):
            raise FlowError('task dependencies are not current')
        receipt = validate_receipt(state, task, receipt_path)
        task.update(status=receipt['task_status'], receipt=receipt)
        if task['status'] == 'done' and task['role'] in ('style-audit', 'content-review'):
            audit = Path(_read(task['brief']).get('audit_output',
                str(Path(state['run']) / ('work/' + task['role'] + '/learning-style-audit-note.json')))).resolve()
            if any(x['path'] == str(audit) for x in receipt['outputs']):
                previous_audit = state.get('active_audit')
                state['active_audit'] = str(audit)
                precheck = state['actions'].get('precheck')
                if precheck and (previous_audit != str(audit) or precheck.get('audit_sha256') != _sha(audit)):
                    precheck['status'] = 'pending'
        refresh_tasks(state)
        write_briefs(state)
    return _task_change(run, task_id, change)


def release_task(run: Path, task_id: str, attempt: str, reason: str) -> dict:
    def change(state, task):
        if task.get('invalidated_active') and task.get('attempt') == attempt and task['status'] == 'stale':
            task.pop('invalidated_active')
        else:
            _attempt(task, attempt)
        if not isinstance(reason, str) or not reason.strip():
            raise FlowError('release reason required')
        task.setdefault('history', []).append(dict(attempt=attempt, agent_id=task.get('agent_id'), reason=reason))
        task.update(status='pending', attempt=None, agent_id=None, receipt=None)
    return _task_change(run, task_id, change)

# Fixed workflow, not a user-configurable graph. Action runners persist dependencies
# and nonempty verified_files; status alone is never completion evidence.
def _record(state, name):
    return state['tasks'].get(name, state['actions'].get(name, {}))


def _done(state, name):
    return _record(state, name).get('status') == 'done'


def _read(path):
    try:
        value = json.loads(Path(path).read_text(encoding='utf-8'))
        if not isinstance(value, dict): raise ValueError('object required')
        return value
    except (OSError, ValueError) as exc:
        raise FlowError(f'{path}: {exc}') from exc


def _current(state):
    from pack_receipts import verify_receipt_files
    stale = []
    for path, digest in state['hashes'].items():
        try:
            if _sha(Path(path)) == digest: continue
        except OSError: pass
        stale.append(path)
    state['stale_inputs'] = stale
    records = {**state['tasks'], **state['actions']}
    for name, record in records.items():
        if record.get('status') != 'done': continue
        evidence = record.get('receipt') if name in state['tasks'] else record
        if not evidence or not evidence.get('verified_files') or verify_receipt_files(evidence):
            record['status'] = 'stale'
    if stale:
        for task in state['tasks'].values():
            if task.get('status') == 'done': task['status'] = 'stale'
    changed = True
    while changed:
        changed = False
        for record in records.values():
            if record.get('status') in ('done', 'pending', 'claimed', 'running') and any(
                _record(state, dep).get('status') in ('stale', 'needs_fix') for dep in record.get('dependencies', [])):
                if record['status'] in ('claimed', 'running'):
                    record['invalidated_active'] = True
                record['status'] = 'stale'; changed = True
    if any(r.get('status') == 'stale' for r in records.values()) or stale:
        if state['status'] not in ('recovery_required', 'withheld', 'blocked'):
            state['status'] = 'needs_fix'
    child = state['tasks'].get('child-coordinator')
    if state.get('explain_run') and child and child.get('status') == 'stale':
        state.setdefault('stale_explain_runs', []).append(state['explain_run'])
        state['explain_run'] = None
    return state


def _converted_assets(state):
    """Read only the successful converter's explicit, current output inventory."""
    from manifest import note_name
    from pack_receipts import records
    action = state['actions'].get('convert-md', {})
    if action.get('status') != 'done': raise FlowError('current successful convert-md required')
    repo = Path(state['repo']).resolve()
    manifest = _read(Path(state['run']) / 'manifest.json')
    pack = repo / '복습노트' / state['range']
    note = (pack / note_name(manifest)).resolve()
    md = (pack / '.assets' / Path(note_name(manifest)).with_suffix('.md')).resolve()
    figures = (pack / '.assets' / ('figures_' + state['range'])).resolve()
    if not all(p.is_relative_to(pack.resolve()) for p in (note, md, figures)):
        raise FlowError('converter outputs escape pack')
    outputs = records(action.get('outputs', []), [repo])
    evidence = records(action.get('verified_files', []), [repo, Path(state['run']).resolve()])
    actual = {str(p.resolve()) for p in figures.glob('*.svg')}
    expected = {p for p in outputs if Path(p).suffix.lower() == '.svg'}
    if set(outputs) != {str(md), *expected} or actual != expected:
        raise FlowError('converter MD/SVG inventory incomplete or changed')
    if not {str(note), *outputs} <= evidence.keys() or any(evidence[p] != h for p, h in outputs.items()):
        raise FlowError('converter outputs/note lack verified hashes')
    return dict(note={'path': str(note), 'sha256': evidence[str(note)]},
                md={'path': str(md), 'sha256': outputs[str(md)]},
                svgs=[{'path': p, 'sha256': outputs[p]} for p in sorted(expected)])


def _stages(state):
    """Only read dynamic identities after the corresponding producer is accepted."""
    run = Path(state['run'])
    stages = [(1, 'task', [('source-prep', 'source-prep', state['sessions'])])]
    if not _done(state, 'source-prep'): return stages
    source = _read(run / 'source-map.json')
    stages.append((1, 'task', [('stt-' + s['date'], 'stt', [s['date']]) for s in source['sessions']]))
    stages.extend([(2, 'task', [('scope-draft', 'scope-draft', state['sessions'])]),
                   (2, 'task', [('selection', 'selection', state['sessions'])])])
    if not _done(state, 'selection'): return stages
    selected = _read(run / 'work/selection/manifest.json')
    sections = [s['id'] for s in selected['sections']]
    if not sections or len(sections) != len(set(sections)) or any(not re.fullmatch(r'[A-Za-z][A-Za-z0-9-]*', s) for s in sections):
        raise FlowError('invalid section identities')
    stages.append((2, 'task', [('scope-final', 'scope-final', sections)]))
    if not _done(state, 'scope-final'): return stages
    manifest = _read(run / 'manifest.json')
    sections = [s['id'] for s in manifest['sections']]
    if sections != [s['id'] for s in selected['sections']]:
        raise FlowError('scope-final section identities differ from section briefs')
    topics = [t['id'] for s in manifest['sections'] for t in s['topics']]
    stages.append((3, 'task', [('author-' + sid, 'author', [sid]) for sid in sections]))
    def action(phase, name): stages.append((phase, 'action', [(name, '', [])]))
    def task(phase, name, targets): stages.append((phase, 'task', [(name, name, targets)]))
    action(4, 'prepare-pack'); action(4, 'assemble-note')
    if manifest['problems']: action(4, 'build-problems')
    task(5, 'style-audit', topics); action(6, 'precheck')
    if not state['lite']: task(6, 'content-review', topics)
    task(7, 'browser-qa', topics); action(8, 'convert-md')
    if not _done(state, 'convert-md'): return stages
    converted = _converted_assets(state)
    if converted['svgs']:
        task(8, 'standalone-svg-qa', [x['path'] for x in converted['svgs']])
    if manifest['problems']:
        task(9, 'child-coordinator', [p['id'] for p in manifest['problems']])
        action(9, 'publish-explanation'); action(9, 'build-answers')
        task(9, 'pdf-qa', [p['id'] for p in manifest['problems']])
        action(9, 'publish-answer')
    action(10, 'final-check')
    return stages


def refresh_tasks(state: dict) -> dict:
    """Reconcile current evidence and register only the next fixed stage, in memory."""
    _current(state)
    if _done(state, 'convert-md'):
        converted = _converted_assets(state)
        state['standalone_svg_qa'] = dict(status='required' if converted['svgs'] else 'not_required',
            reason='review every emitted SVG' if converted['svgs'] else 'successful conversion emitted zero SVG',
            md=converted['md'], targets=[x['path'] for x in converted['svgs']])
    previous = []
    for phase, kind, group in _stages(state):
        destination = state['tasks'] if kind == 'task' else state['actions']
        for name, role, targets in group:
            if name not in destination:
                destination[name] = dict(id=name, status='pending', dependencies=list(previous))
                if kind == 'task':
                    destination[name].update(role=role, targets=targets, attempt=None, agent_id=None,
                        receipt=None, brief=str(Path(state['run']) / 'work' / name / 'brief.json'))
            elif destination[name]['status'] in ('pending', 'needs_fix', 'stale') and not destination[name].get('invalidated_active'):
                destination[name]['dependencies'] = list(previous)
                if kind == 'task': destination[name]['targets'] = targets
            if kind == 'task' and role == 'child-coordinator' and not state.get('explain_run'):
                state['explain_run'] = str(Path(state['run']) / 'problem-explain' / str(uuid4()))
        if any(not _done(state, name) for name, _, _ in group):
            state['phase'] = phase
            return state
        previous = [name for name, _, _ in group]
    state['phase'] = 10
    return state


_REFERENCES = {
    'source-prep': [('execution-guide.md', '1. 범위 파악')],
    'stt': [('stt-summary-prompt.md', '전체')],
    'scope-draft': [('manifest-guide.md', '전체')],
    'selection': [('problem-selection.md', '전체')],
    'scope-final': [('manifest-guide.md', '전체'), ('delegation.md', 'manifest 소유권')],
    'author': [('content-rules.md', '전체'), ('execution-guide.md', '3. 작성')],
    'style-audit': [('review-prompt.md', '개인화 감사')],
    'content-review': [('review-prompt.md', '전체')],
    'browser-qa': [('browser-check.md', '전체')],
    'standalone-svg-qa': [('execution-guide.md', '8. MD 변환'), ('browser-check.md', '전체')],
    'child-coordinator': [('problem-explain-integration.md', '전체')],
    'pdf-qa': [('problem-explain-integration.md', '답안 PDF 렌더 검토 기록')],
}
_COMMON_SECTIONS = ['기본 근사와 회로 표기', '전압이득의 계산 순서', '확정한 문제 해설 형식',
                    '본문과 페이지 요약의 계약', '수치 표시', 'HTML 가독성 생성·검사']


def _inputs(state, task):
    paths = set(state['hashes'])
    ancestors = set()
    def visit(name):
        if name in ancestors: return
        ancestors.add(name)
        for dep in _record(state, name).get('dependencies', []): visit(dep)
    for dep in task['dependencies']: visit(dep)
    for name in ancestors:
        record = _record(state, name)
        if record.get('status') != 'done': continue
        if name in state['tasks']:
            receipt = record.get('receipt') or {}
            evidence = receipt.get('verified_files', []) if record.get('role') == 'source-prep' else receipt.get('outputs', [])
        else:
            evidence = record.get('verified_files', [])
        for item in evidence:
            # Canonical audit is a machine staging copy. Reviewers freeze the
            # immutable active producer audit instead of this replaceable copy.
            if Path(item['path']) == Path(state['run']) / 'learning-style-audit.json': continue
            paths.add(item['path'])
    if state.get('active_audit') and task['role'] in ('content-review', 'browser-qa', 'child-coordinator', 'pdf-qa'):
        paths.add(state['active_audit'])
    return [{'path': p, 'sha256': _sha(Path(p))} for p in sorted(paths)]


def write_briefs(state: dict) -> None:
    """Called in init/accept/fix/action write transactions; never from next/status."""
    from pack_receipts import ROLE_OUTPUTS, standalone_screenshots
    run, repo = Path(state['run']), Path(state['repo'])
    skill = repo / '.claude/skills/ec2-review-pack'
    for task in state['tasks'].values():
        if task.get('invalidated_active') or task['status'] not in ('pending', 'needs_fix', 'stale') or any(not _done(state, d) for d in task['dependencies']): continue
        # Only scheduler-owned briefs; imported test/custom tasks retain their contract.
        brief_path = run / 'work' / task['id'] / 'brief.json'
        if Path(task['brief']) != brief_path: continue
        role = task['role']
        outputs = sorted({str(run / pattern.format(target=target)) for pattern in ROLE_OUTPUTS[role] for target in task['targets']})
        if role in ('style-audit', 'content-review'):
            previous_outputs = {x['path'] for x in (task.get('receipt') or {}).get('outputs', [])}
            if not task.get('audit_output') or task['audit_output'] in previous_outputs:
                task['audit_output'] = str(run / 'work' / role / 'audits' / str(uuid4()) / 'learning-style-audit-note.json')
            outputs = [task['audit_output']]
        refs = [{'path': str(skill / 'references' / name), 'sections': [section]} for name, section in _REFERENCES[role]]
        refs.append({'path': str(skill / 'references/delegation.md'), 'sections': ['전체']})
        if role in ('author', 'style-audit', 'content-review'):
            refs.append({'path': str(skill / 'references/execution-guide.md'), 'sections': _COMMON_SECTIONS})
        snapshot = _read(run / 'learning-style.json')
        data = dict(task_id=task['id'], role=role, range=state['range'], lite=state['lite'],
            repo=str(repo), run=str(run), skill=str(skill), profile=str(repo / snapshot['path']),
            profile_read='전체 필수', snapshot=str(run / 'learning-style.json'), references=refs,
            targets=task['targets'], inputs=_inputs(state, task), allowed_outputs=outputs,
            allowed_output_roots=[str(run / 'work' / task['id'])],
            report=str(run / 'work' / task['id'] / 'report.md'), receipt=str(run / 'work' / task['id'] / 'receipt.json'),
            return_limit=800, request_paths=task.get('request_paths', []),
            constraints=['원본 읽기 전용; RUN/repo 링크도 예외 없음', '실제 검토 없이 pass 생성 금지',
                         '1920×1080 하단 180px 자막 여백; PDF 16:9', '렌더 오류로 문항 교체 금지'])
        if role in ('style-audit', 'content-review'): data['audit_output'] = task['audit_output']
        if role == 'selection': data['manifest'] = str(run / 'work/scope-draft/manifest.json')
        elif role == 'scope-final': data['manifest'] = str(run / 'work/selection/manifest.json')
        elif role in ('author', 'style-audit', 'content-review', 'browser-qa', 'child-coordinator', 'pdf-qa'):
            data['manifest'] = str(run / 'manifest.json')
        if role == 'author': data['section_brief'] = str(run / 'briefs' / (task['targets'][0] + '.json'))
        if role in ('content-review', 'browser-qa'): data['audit'] = state.get('active_audit')
        if role == 'browser-qa': data['allowed_output_roots'].append(str(run / 'work/browser'))
        if role == 'standalone-svg-qa':
            converted = _converted_assets(state)
            data['converted_assets'] = converted
            data['manifest'] = str(run / 'manifest.json')
            data['svg_screenshots'] = standalone_screenshots(run, task['targets'])
            data['allowed_outputs'].extend(data['svg_screenshots'].values())
            data['coverage_contract'] = 'counts.targets는 실제 검토한 SVG 절대 경로 배열이며 brief.targets와 중복 없이 정확히 같은 집합이어야 한다.'
            data['inspection_criteria'] = [
                'PROFILE 전체와 NOTATION-01/CIRCUIT-02를 읽고 MD가 참조하는 각 SVG를 독립 문서로 직접 연다.',
                'HTML CSS에 의존하지 않는 실제 Pretendard 600 정체 face, native text/tspan 첨자(기본 78%), 폰트 로딩을 확인한다.',
                '라이트/다크 가시성, 노드·전압 색, 출력/시험 접속 배치, 라벨 간격·겹침·클리핑을 실제 화면에서 확인한다.',
                '각 SVG의 지정 PNG를 남기고 report.json/report.md에 대상 경로·해시·사용 face·검사 결과·미해결을 기록한다.',
                '발행 MD/SVG/노트는 읽기 전용. 결함은 기존 작성자 수정과 재변환 후 재검토하며 machine_browser 공통 예산을 따른다.']
        if role == 'pdf-qa':
            data['report'] = str(run / 'answer-review.md')
            data['allowed_output_roots'].append(str(run / 'answer-pages'))
            for field in ('answer_pdf', 'answer_overlay'):
                path = Path(state.get(field, ''))
                if not path.is_absolute() or not path.resolve().is_relative_to(run) or not path.is_file():
                    raise FlowError('PDF action must record an actual RUN ' + field)
            data['pdf'] = state['answer_pdf']
            data['overlay'] = state['answer_overlay']
        if role == 'child-coordinator':
            data['explain_run'] = state['explain_run']
            data['allowed_output_roots'].append(state['explain_run'])
            data['leaf_contract'] = '메인+조정자+가용 leaf, 중첩 조정자 금지; 독립 검산자·내용 리뷰어 분리'
        owner = _owner(state, task)
        if owner != 'workers':
            data['inspection_request'] = dict(owner=owner, targets=task['targets'],
                instruction='메인이 실제 전체 토픽/화면/PDF 페이지를 검토하고 기존 검토 근거와 receipt를 제출한다. 미실시는 blocked.')
        brief_path.parent.mkdir(parents=True, exist_ok=True)
        # Avoid touching an identical brief on unrelated acceptance.
        if not brief_path.exists() or _read(brief_path) != data: _atomic_json(brief_path, data)


def _owner(state, task):
    if task['role'] == 'style-audit' and state['lite']: return 'main'
    if task['role'] in ('browser-qa', 'standalone-svg-qa'): return state['capabilities']['browser_owner']
    if task['role'] == 'pdf-qa': return state['capabilities']['pdf_owner']
    return 'workers'


def next_work(run: Path, *, slots: int) -> dict:
    if type(slots) is not int or slots < 0: raise FlowError('slots must be a nonnegative integer')
    state = inspect_state(run)
    def result(kind, tasks=None, action=None, reason=''):
        return dict(kind=kind, tasks=tasks or [], action=action, reason=reason)
    if state['status'] == 'recovery_required': return result('recover', reason='interrupted mutation requires recovery')
    if state['stale_inputs']: return result('blocked', reason='frozen source/profile changed; explicit correction required')
    for _, kind, group in _stages(state):
        unfinished = [_record(state, name) for name, _, _ in group if not _done(state, name)]
        if not unfinished: continue
        if not all(unfinished): return result('blocked', reason='stage not materialized; finish preceding write transaction')
        if any(t['status'] == 'blocked' for t in unfinished): return result('blocked', unfinished if kind == 'task' else [], reason='required work blocked')
        if kind == 'action':
            if unfinished[0].get('invalidated_active'):
                return result('wait', reason='invalidated active machine action requires explicit reconciliation')
            if unfinished[0]['status'] in ('running', 'claimed'):
                return result('wait', reason='machine action already running')
            return result('run', action=group[0][0], reason='required machine action')
        ready = [t for t in unfinished if not t.get('invalidated_active') and t['status'] in ('pending', 'needs_fix', 'stale') and all(_done(state, d) for d in t['dependencies'])]
        if not ready: return result('wait', reason='waiting for active attempts or predecessors')
        owner = _owner(state, ready[0])
        if owner == 'unavailable': return result('blocked', ready, reason='actual inspection capability unavailable')
        if owner == 'main': return result('review_locally', ready, reason='main must perform actual review from brief')
        if slots == 0: return result('wait', reason='no worker slots available')
        return result('dispatch', ready[:slots], reason='claim before dispatch')
    return result('report', reason='final check current; generate final report')


def request_fixes(run: Path, request_path: Path) -> dict:
    run, request_path = Path(run).resolve(), Path(request_path).resolve()
    if not request_path.is_relative_to(run): raise FlowError('fix request must be inside RUN')
    request = _read(request_path)
    state = load_state(run)
    def change(s):
        category, rid, items = request.get('category'), request.get('id'), request.get('items')
        if category not in ('content', 'machine_browser') or not isinstance(rid, str) or not rid or not isinstance(items, list) or not items:
            raise FlowError('invalid fix request')
        prior = s.setdefault('fix_requests', {})
        if rid in prior:
            if prior[rid] != request: raise FlowError('fix request ID reused with different content')
            return s
        maximum = _fix_limit(s, category)
        if s['fix_rounds'][category] >= maximum: raise FlowError('shared fix budget exhausted')
        seen = set()
        _current(s)
        for item in items:
            tid = item.get('task_id'); path = Path(item.get('request_path', '')).resolve()
            if tid not in s['tasks'] or tid in seen or not path.is_relative_to(run) or not path.is_file():
                raise FlowError('invalid fix target/request path')
            seen.add(tid); task = s['tasks'][tid]
            if task.get('invalidated_active') or task['status'] in ('claimed', 'running'): raise FlowError('release active attempt before requesting fixes')
            task.setdefault('history', []).append(dict(attempt=task.get('attempt'), agent_id=task.get('agent_id'), receipt=task.get('receipt'), reason='fix ' + rid))
            task.update(status='needs_fix', attempt=None, receipt=None, agent_id=None)
            task.pop('audit_output', None)
            task.setdefault('request_paths', []).append(str(path))
        s['fix_rounds'][category] += 1; prior[rid] = request
        refresh_tasks(s); write_briefs(s)
        return s
    return update_state(run, state['revision'], change)


def authorize_extra_fix(run: Path, authorization_path: Path) -> dict:
    """Main records an explicit user grant; local evidence is not authentication."""
    run = Path(run).resolve()
    authorization_path = Path(authorization_path)
    if not authorization_path.is_absolute(): raise FlowError('absolute authorization path required')
    try:
        authorization = _read(authorization_path)
    except (OSError, ValueError) as exc:
        raise FlowError('authorization file missing/invalid: ' + str(exc)) from exc
    state = load_state(run)
    def change(s):
        _check_extra_authorization(authorization, s)
        if 'extra_fix_authorization' in s: raise FlowError('one extra round already authorized')
        canonical = run / 'authorizations/machine-browser-extra.json'
        if not canonical.resolve().is_relative_to(run): raise FlowError('authorization path outside RUN')
        canonical.parent.mkdir(parents=True, exist_ok=True)
        # Reuse only identical evidence left by interruption before state commit.
        if canonical.exists():
            if _read(canonical) != authorization: raise FlowError('immutable authorization file already exists')
        else: _atomic_json(canonical, authorization)
        s['extra_fix_authorization'] = dict(path=str(canonical), sha256=_sha(canonical))
        return s
    return update_state(run, state['revision'], change)
