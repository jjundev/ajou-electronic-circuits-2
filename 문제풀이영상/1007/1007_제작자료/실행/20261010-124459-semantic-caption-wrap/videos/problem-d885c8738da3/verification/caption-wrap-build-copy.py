from pathlib import Path
import json,shutil,datetime,zoneinfo,wave,re,importlib.util,argparse
from solution_video.util import read,write,file_hash,digest,local,S
from solution_video.manifest import content_fingerprint,validate_manifest
from solution_video.state import finish_stage,STAGES,recover_run
from solution_video.speech_chunks import validate_chunk_audio,speech_items
from solution_video.speech_tts import make_speech_payload,POLICY
from solution_video.pdf_pages import compare_completed
from solution_video.subtitles import write_srt
from solution_video.annotations import load_teaching
from solution_video.lesson import load_lesson
old=next(Path('문제풀이영상/1007').glob('*/실행/20261010-112616-circuit-ink/videos/*')).resolve()
batch=old.parents[1];newbatch=batch.with_name(datetime.datetime.now(zoneinfo.ZoneInfo('Asia/Seoul')).strftime('%Y%m%d-%H%M%S')+'-semantic-caption-wrap');run=newbatch/'videos'/old.name
baseline=dict(source_run=str(old),wav_hashes={p.relative_to(old).as_posix():file_hash(p) for p in (old/'assets/voice').glob('*.wav')},original_final_sha256=file_hash(old/'renders/final.mp4'),preserved_hashes={p:file_hash(old/p) for p in ['renders/master.mp4','renders/narration.wav','source/manifest.json','source/timeline.json','source/annotations.json','source/focus.json','source/lesson.json']})
assert len(baseline['wav_hashes'])==66
shutil.copytree(batch,newbatch)
relocated=[]
for p in newbatch.rglob('*.json'):
 raw=p.read_text();changed=raw.replace(str(batch),str(newbatch))
 if changed!=raw:p.write_text(changed);relocated.append(p.relative_to(newbatch).as_posix())
# Path-independent source content remains unchanged; reviews are rebased only
# after this equality proof, not by granting new mathematical approval.
m,l,c,r=[read(run/p) for p in ['source/manifest.json','layers/layers.json','source/coverage.json','source/circuit-review.json']]
for n in ['source/manifest.json','source/annotations.json','source/focus.json','source/lesson.json']:
 assert file_hash(run/n)==file_hash(old/n),n
oldl=read(old/'layers/layers.json');assert json.dumps(oldl,ensure_ascii=False).replace(str(batch),str(newbatch))==json.dumps(l,ensure_ascii=False)
h=content_fingerprint(m,l,c)
for n in ['source/coverage.json','source/circuit-review.json']:
 d=read(run/n);d['input_hash']=h;write(run/n,d)
validate_manifest(m,l,read(run/'source/coverage.json'),read(run/'source/circuit-review.json'))
plan=load_teaching(run,m,l);load_lesson(run,m,l,plan)
# Fresh exact original SVG pixel gate in the relocated run.
g=compare_completed(l,run/'verification/gate-frames')
assert all(g[k]==0 for k in ['pixel_diff','non_target_diff','hidden_leaks']),g
g['input_hash']=digest(l);g['evidence']=[Path(p).relative_to(run).as_posix() for p in g['evidence']];g['evidence_hashes']={p:file_hash(local(run,p)) for p in g['evidence']};g['source_hashes']={k:file_hash(Path(l[k])) for k in ['original_svg','animated_svg','reference_png']};write(run/'verification/gate.json',g)
# Inputs and layers were copied verbatim except validated path relocations.
for stage in ['inputs','layers']:
 outputs=list(read(run/'state.json')['stages'][stage]['outputs']);finish_stage(run,stage,[run/p for p in outputs])
spec=importlib.util.spec_from_file_location('ec2_video_entry',S/'scripts/video.py');cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
args=argparse.Namespace(writing_config=None,runtime=str(S.parent/'ec2-review-video/assets/runtime/vendor/gsap.min.js'))
print('check',cli.run_stage('check',run,args),flush=True)
# Validate all 47 raw cache keys/payloads/receipts and 19 joined WAVs offline.
cfg=read(run/'source/config.json')
for item in speech_items(m['segments']):
 payload=make_speech_payload(item['text'],cfg);key=digest(dict(policy=POLICY,text=item['text'],pronunciation=cfg.get('pronunciation',{}),model=cfg['model'],payload=payload))
 p=run/'assets/voice'/(item['id']+'-'+key[:16]+'.wav');receipt=read(p.with_suffix('.json'))
 assert receipt['key']==key and receipt['policy']==POLICY and receipt['payload_hash']==digest(payload)
 assert receipt['sha256']==receipt['output_sha256']==file_hash(p)
 assert receipt['id']==item['id'] and receipt['path']==p.relative_to(run).as_posix()
 with wave.open(str(p),'rb') as w:assert (w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getnframes())==(1,2,24000,receipt['samples'])
audio=read(run/'source/audio.json')['voices'];validate_chunk_audio(m['segments'],audio,run)
finish_stage(run,'voice',[run/'source/audio.json',run/'source/chunk-audio.json',*[run/p for p in baseline['wav_hashes']]])
print('retime',cli.run_stage('retime',run,args),flush=True)
print('assemble',cli.run_stage('assemble',run,args),flush=True)
assert file_hash(run/'source/timeline.json')==baseline['preserved_hashes']['source/timeline.json']
# Rebuilt visual inputs must be byte-identical to prior rendering inputs;
# normalize only the already verified path relocation in JSON metadata.
differences=[]
for p in (old/'composition').rglob('*'):
 if not p.is_file():continue
 rel=p.relative_to(old);q=run/rel
 if p.read_bytes()!=q.read_bytes():
  try:assert p.read_text().replace(str(batch),str(newbatch))==q.read_text()
  except (UnicodeError,AssertionError):differences.append(str(rel))
assert not differences,differences
assert file_hash(run/'source/parts.json')==file_hash(old/'source/parts.json')
assert file_hash(run/'renders/master.mp4')==baseline['preserved_hashes']['renders/master.mp4']
finish_stage(run,'render',[run/'renders/master.mp4'])
assert recover_run(run)=='captions'
write_srt(read(run/'source/timeline.json'),run/'verification/proposed.srt')
baseline.update(run=str(run),relocated_files=relocated,paid_requests=0,raw_cache_validated=47,joined_pcm_validated=19,visual_rebuild_preserved=True)
write(run/'verification/caption-wrap-before-after.json',baseline)
Path('.superpowers/sdd/2026-10-10-ec2-semantic-caption-wrap/run-path').write_text(str(run))
print('RUN',run,flush=True)
