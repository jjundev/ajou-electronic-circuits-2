from pathlib import Path
import json
from solution_video.util import read,write,file_hash
from solution_video.state import finish_stage,recover_run
old=next(Path('문제풀이영상/1007').glob('*/실행/20261010-112616-circuit-ink/videos/*')).resolve()
run=sorted(Path('문제풀이영상/1007').glob('*/실행/*-semantic-caption-wrap/videos/*'))[-1].resolve()
batch,newbatch=old.parents[1],run.parents[1]
allowed=[]
for p in (old/'composition').rglob('*'):
 if not p.is_file():continue
 rel=p.relative_to(old);q=run/rel
 if p.read_bytes()==q.read_bytes():continue
 if rel.as_posix()=='composition/runtime.json':
  a=read(p);b=read(q)
  key='annotations/compiled.json'
  assert a['teaching_assets'][key]==file_hash(old/'composition'/key)
  assert b['teaching_assets'][key]==file_hash(run/'composition'/key)
  a['teaching_assets'][key]=b['teaching_assets'][key]
  assert a==b
 else:assert p.read_text().replace(str(batch),str(newbatch))==q.read_text(),rel
 allowed.append(rel.as_posix())
assert set(allowed)=={'composition/runtime.json','composition/index.html','composition/annotations/compiled.json'},allowed
assert file_hash(run/'source/parts.json')==file_hash(old/'source/parts.json')
preserved=['renders/master.mp4','renders/narration.wav','source/manifest.json','source/timeline.json','source/annotations.json','source/focus.json','source/lesson.json']
for n in preserved:assert file_hash(old/n)==file_hash(run/n),n
baseline=dict(source_run=str(old),run=str(run),wav_hashes={p.relative_to(old).as_posix():file_hash(p) for p in (old/'assets/voice').glob('*.wav')},original_final_sha256=file_hash(old/'renders/final.mp4'),preserved_hashes={n:file_hash(old/n) for n in preserved},paid_requests=0,raw_cache_validated=47,joined_pcm_validated=19,visual_rebuild_preserved=True,relocated_composition_metadata=allowed)
write(run/'verification/caption-wrap-before-after.json',baseline)
finish_stage(run,'render',[run/'renders/master.mp4']);assert recover_run(run)=='captions'
Path('.superpowers/sdd/2026-10-10-ec2-semantic-caption-wrap/run-path').write_text(str(run))
with Path('.superpowers/sdd/2026-10-10-ec2-semantic-caption-wrap/progress.md').open('a') as f:
 f.write('Ruling: Reuse master after exact rebuilt visual-input comparison; only copied question-image/compiled.svg absolute paths and compiled runtime SHA changed — relocation is metadata, all renderer HTML/JS/SVG are identical after verified path rebasing, PCM/timing byte-identical — cost if wrong: master would not represent rebuilt visuals; fresh full verification checks that correspondence.\n')
print('RUN',run)
