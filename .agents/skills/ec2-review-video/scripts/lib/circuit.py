"""Structural evidence gate. The author performs the physics review; no equation eval."""
from pathlib import Path
import json
from .cache import digest, file_hash

DOMAINS=('model','topology','polarity','derivation','assumptions','numeric-visual')
class CircuitReviewError(ValueError): pass

def circuit_assets(run):
    """Only fragment-linked visuals; staging voice/fonts/vendor must not change review."""
    from .composition import validate_fragment
    run=Path(run).resolve();paths=set()
    for fragment in (run/'source/scene-fragments').glob('*.html'):
        parsed=validate_fragment(fragment.read_text(encoding='utf-8'),fragment.stem)
        for relative in parsed.assets:
            path=(run/relative).resolve()
            if not path.is_relative_to(run):raise CircuitReviewError('external circuit asset: '+relative)
            paths.add(path)
    return sorted(paths)

def circuit_fingerprint(run: Path, manifest: dict) -> str:
    run=Path(run)
    files={p.relative_to(run).as_posix():file_hash(p)
           for pattern in ('source/inputs.json','source/inputs/*','source/scene-fragments/*')
           for p in run.glob(pattern) if p.is_file()}
    for p in circuit_assets(run):
        files[p.relative_to(run.resolve()).as_posix()]=file_hash(p) if p.is_file() else 'missing'
    return digest({'manifest':manifest,'files':files})

def evidence_paths(run):
    """Validated local paths only; usable for stage fingerprints even when hashes stale."""
    run=Path(run).resolve()
    try: report=json.loads((run/'source/circuit-review.json').read_text(encoding='utf-8-sig'))
    except (OSError,ValueError): return []
    if not isinstance(report,dict) or not isinstance(report.get('evidence',[]),list): return []
    paths=[]
    for item in report.get('evidence',[]):
        if not isinstance(item,dict) or not isinstance(item.get('path'),str): continue
        p=(run/item['path']).resolve()
        if p.is_relative_to(run) and p.is_file(): paths.append(p)
    return paths

def validate_circuit_review(run: Path, manifest: dict) -> list[str]:
    run=Path(run).resolve();errors=[]
    try: report=json.loads((run/'source/circuit-review.json').read_text(encoding='utf-8-sig'))
    except (OSError,ValueError): return ['missing or invalid circuit-review.json']
    if not isinstance(report,dict): return ['circuit review must be an object']
    if report.get('schema_version')!=1:errors.append('circuit schema_version must be 1')
    try:
        if report.get('input_hash')!=circuit_fingerprint(run,manifest):errors.append('stale circuit review')
        if any(not p.is_file() for p in circuit_assets(run)):errors.append('missing circuit visual asset')
    except ValueError as ex:errors.append(str(ex))
    scenes=report.get('scenes');expected=[s['id'] for s in manifest['scenes']]
    source_ids={s['id'] for s in manifest['sources']}
    if not isinstance(scenes,list):return errors+['circuit scenes must be a list']
    actual=[s.get('scene_id') if isinstance(s,dict) else None for s in scenes]
    if sorted(str(x) for x in actual)!=sorted(expected):errors.append('every scene must appear exactly once')
    def nonempty_strings(value):return isinstance(value,list) and bool(value) and all(isinstance(v,str) and v.strip() for v in value)
    for scene in scenes:
        if not isinstance(scene,dict):errors.append('invalid circuit scene');continue
        checks=scene.get('checks')
        if not isinstance(checks,list):errors.append('checks must be a list');continue
        domains=[c.get('domain') if isinstance(c,dict) else None for c in checks]
        if sorted(str(x) for x in domains)!=sorted(DOMAINS):errors.append('every circuit domain must appear exactly once: '+str(scene.get('scene_id')))
        if not any(isinstance(c,dict) and c.get('status')=='passed' for c in checks):errors.append('scene cannot skip all circuit checks')
        for check in checks:
            if not isinstance(check,dict):errors.append('invalid check');continue
            if check.get('status') not in ('passed','not-applicable'):errors.append('invalid circuit check status')
            reason=check.get('reason')
            if not isinstance(reason,str) or not reason.strip():errors.append('circuit check requires reason')
            refs=check.get('source_ids',[]);locators=check.get('locators',[])
            if not isinstance(refs,list) or any(not isinstance(x,str) or x not in source_ids for x in refs):errors.append('unknown circuit source ID')
            if check.get('status')=='passed' and (not nonempty_strings(refs) or not nonempty_strings(locators)):errors.append('passed circuit check requires sources and locators')
    evidence=report.get('evidence',[])
    if not isinstance(evidence,list):errors.append('circuit evidence must be a list');evidence=[]
    for item in evidence:
        if not isinstance(item,dict) or not isinstance(item.get('path'),str) or not isinstance(item.get('sha256'),str):errors.append('invalid circuit evidence');continue
        p=(run/item['path']).resolve()
        if not p.is_relative_to(run) or not p.is_file() or file_hash(p)!=item['sha256']:errors.append('missing, external or changed numerical evidence')
    return errors

def require_circuit_review(run: Path, manifest: dict) -> None:
    errors=validate_circuit_review(run,manifest)
    if errors:raise CircuitReviewError('; '.join(errors))
