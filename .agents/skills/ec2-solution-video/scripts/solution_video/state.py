from pathlib import Path
from .util import S,digest,file_hash,read,write,local
from .review_adapter import adapter_hash
from .contracts import InputError
STAGES=['inputs','layers','script','voice','timing','composition','render','captions','verify','publish']
FACTORS={
 'inputs':['source/inputs.json','source/pair.json','source/snapshots/*'],
 'layers':['source/map.json','layers/candidates.json','layers/original.svg'],
 'script':['source/manifest.json','source/coverage.json','source/circuit-review.json','verification/gate.json'],
 'voice':['source/config.json'], 'timing':['source/audio.json','assets/voice/*.wav'],
 'composition':['source/timeline.json'], 'render':['source/parts.json','composition/*'],
 'captions':['renders/master.mp4'], 'verify':['renders/final.mp4','renders/captions.srt','verification/audio-review.json','verification/visual-review.json'], 'publish':['verification/report.json']}
MODULES={'inputs':['sources'],'layers':['pdf_pages'],'script':['manifest'],'voice':['review_adapter'],'timing':['reveal'],'composition':['composition'],'render':['media'],'captions':['subtitles'],'verify':['verify'],'publish':['publication']}
def stage_fingerprint(run,stage):
    run=Path(run); n=STAGES.index(stage); files={}
    for s in STAGES[:n+1]:
        for pattern in FACTORS[s]:
            for p in run.glob(pattern):
                if p.is_file(): files[p.relative_to(run).as_posix()]=file_hash(p)
        for module in MODULES[s]:
            p=S/'scripts/solution_video'/(module+'.py')
            if p.exists(): files['tool:'+module]=file_hash(p)
    for module in ['util','contracts','page_layout']:
        p=S/'scripts/solution_video'/(module+'.py'); files['tool:'+module]=file_hash(p)
    if n>=1: files['tool:browser_check']=file_hash(S/'tests/browser_check.mjs')
    if n>=3: files['tool:adapter']=adapter_hash()
    if n>=5:
        for p in (S/'assets').glob('*'):
            if p.suffix in ('.js','.css'): files['asset:'+p.name]=file_hash(p)
    return digest(files)
def recover_run(run):
    run=Path(run); path=run/'state.json'; state=read(path) if path.is_file() else {'stages':{}}
    for s in STAGES:
        record=state['stages'].get(s)
        if not record or record['fingerprint']!=stage_fingerprint(run,s): return s
        if any(not local(run,p).is_file() or file_hash(local(run,p))!=sha for p,sha in record['outputs'].items()): return s
        if s=='publish':
            try:
                receipt=read(run/'verification/publication.json')
                for path,sha in receipt['published'].items():
                    if not Path(path).is_file() or file_hash(path)!=sha:return s
            except (OSError,KeyError,ValueError):return s
    return None
def finish_stage(run,stage,outputs):
    run=Path(run).resolve(); state=read(run/'state.json') if (run/'state.json').exists() else {'schema_version':1,'stages':{}}
    hashes={}
    for p in outputs:
        p=Path(p).resolve()
        if not p.is_relative_to(run) or not p.is_file(): raise InputError('stage output missing or outside run')
        hashes[p.relative_to(run).as_posix()]=file_hash(p)
    state['stages'][stage]={'fingerprint':stage_fingerprint(run,stage),'outputs':hashes}; write(run/'state.json',state)
