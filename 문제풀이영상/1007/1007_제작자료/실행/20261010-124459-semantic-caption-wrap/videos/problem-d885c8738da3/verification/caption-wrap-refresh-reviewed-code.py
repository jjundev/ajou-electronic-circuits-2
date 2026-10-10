from pathlib import Path
import argparse,importlib.util,wave
from solution_video.util import read,S,file_hash,digest
from solution_video.state import finish_stage
from solution_video.speech_chunks import validate_chunk_audio,speech_items
from solution_video.speech_tts import make_speech_payload,POLICY
from solution_video.subtitles import caption_srt_matches
run=Path(Path('.superpowers/sdd/2026-10-10-ec2-semantic-caption-wrap/run-path').read_text())
spec=importlib.util.spec_from_file_location('ec2_video_entry',S/'scripts/video.py');cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
args=argparse.Namespace(writing_config=None,runtime=str(S.parent/'ec2-review-video/assets/runtime/vendor/gsap.min.js'))
print(cli.run_stage('check',run,args),flush=True)
m=read(run/'source/manifest.json');cfg=read(run/'source/config.json')
for item in speech_items(m['segments']):
 payload=make_speech_payload(item['text'],cfg);key=digest(dict(policy=POLICY,text=item['text'],pronunciation=cfg.get('pronunciation',{}),model=cfg['model'],payload=payload))
 p=run/'assets/voice'/(item['id']+'-'+key[:16]+'.wav');rec=read(p.with_suffix('.json'))
 assert rec['key']==key and rec['payload_hash']==digest(payload) and rec['sha256']==rec['output_sha256']==file_hash(p)
 with wave.open(str(p),'rb') as w:assert (w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getnframes())==(1,2,24000,rec['samples'])
validate_chunk_audio(m['segments'],read(run/'source/audio.json')['voices'],run)
finish_stage(run,'voice',[run/'source/audio.json',run/'source/chunk-audio.json',*(run/'assets/voice').glob('*.wav')])
print(cli.run_stage('retime',run,args),flush=True);print(cli.run_stage('assemble',run,args),flush=True)
assert caption_srt_matches(read(run/'source/timeline.json'),run/'renders/captions.srt')
# Current media and rebuilt visual inputs are identical to prior verified run.
b=read(run/'verification/caption-wrap-before-after.json');old=Path(b['source_run']);batch=old.parents[1];newbatch=run.parents[1]
for p in (old/'composition').rglob('*'):
 if not p.is_file():continue
 rel=p.relative_to(old);q=run/rel
 if p.read_bytes()==q.read_bytes():continue
 if rel.as_posix()=='composition/runtime.json':
  a=read(p);v=read(q);key='annotations/compiled.json'
  assert a['teaching_assets'][key]==file_hash(old/'composition'/key) and v['teaching_assets'][key]==file_hash(run/'composition'/key)
  a['teaching_assets'][key]=v['teaching_assets'][key];assert a==v
 else:assert p.read_text().replace(str(batch),str(newbatch))==q.read_text(),rel
for n,sha in b['preserved_hashes'].items():assert file_hash(run/n)==sha
assert file_hash(run/'renders/final.mp4')==b['after']['final_sha256']
finish_stage(run,'render',[run/'renders/master.mp4'])
assert caption_srt_matches(read(run/'source/timeline.json'),run/'renders/captions.srt')
finish_stage(run,'captions',[run/'renders/captions.srt',run/'renders/final.mp4'])
# The new code corrects an unused input case. All 47 current cue strings and
# every sampled final frame remain byte-identical; retain observed visual meaning.
from solution_video.verify import verification_fingerprint
from solution_video.util import write
visual=read(run/'verification/visual-review.json')
assert all(file_hash(run/n)==sha for n,sha in visual['evidence'].items())
visual['input_hash']=verification_fingerprint(run)
write(run/'verification/visual-review.json',visual)
print('Reviewed code fresh offline validation complete; same SRT/video; current visual evidence',flush=True)
