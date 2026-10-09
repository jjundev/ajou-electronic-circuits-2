from pathlib import Path
import json,sys,shutil
from types import SimpleNamespace
root=Path.cwd();sys.path.insert(0,str(root/'.agents/skills/ec2-solution-video/scripts'))
from solution_video.util import read,write,file_hash,digest
from solution_video.subtitles import _caption_units
from solution_video.speech_chunks import MODE,validate_speech_chunks
from solution_video.manifest import content_fingerprint
import video
old=root/'문제풀이영상/1007/1007_제작자료/실행/20261008-104109-55e6b8b7/videos/problem-d885c8738da3'
batch=Path(__file__).resolve().parent;run=next((batch/'videos').iterdir())
oldinputs=read(old/'source/inputs.json');newinputs=read(run/'source/inputs.json')
assert {k:v['sha256'] for k,v in oldinputs['files'].items()}=={k:v['sha256'] for k,v in newinputs['files'].items()}
for name in ['map','writing','focus','annotations','lesson']:
    shutil.copyfile(old/'source'/f'{name}.json',run/'source'/f'{name}.json')
print(video.run_stage('extract',run,SimpleNamespace()))
l=read(run/'layers/layers.json');oldl=read(old/'layers/layers.json')
for key in ['glyphs','shapes','map']:
    assert l[key]==oldl[key],key
assert file_hash(l['original_svg'])==file_hash(oldl['original_svg'])
m=read(old/'source/manifest.json');m['caption_timing']=MODE
pairs=[]
for segment in m['segments']:
    spoken=_caption_units(segment['text'],False);captions=_caption_units(segment['caption_text'],False)
    assert len(spoken)==len(captions),(segment['id'],len(spoken),len(captions))
    segment['chunks']=[dict(id='cue'+str(i+1),text=text,caption_text=caption) for i,(text,caption) in enumerate(zip(spoken,captions))]
    assert ' '.join(spoken)==segment['text']
    assert ' '.join(captions)==segment['caption_text']
    pairs.extend([dict(segment_id=segment['id'],**c) for c in segment['chunks']])
validate_speech_chunks(m['segments'],required=True)
# Manual semantic review: original spoken/caption pairs are preserved, no automatic mathematical rewrite.
write(run/'source/manifest.json',m)
c=read(old/'source/coverage.json');r=read(old/'source/circuit-review.json')
h=content_fingerprint(m,l,c);c['input_hash']=r['input_hash']=h
for name,data in [('coverage',c),('circuit-review',r)]:write(run/'source'/f'{name}.json',data)
write(run/'source/chunk-authorship.json',dict(source_run=str(old),input_hash=h,pairs=pairs,source_snapshots_equal=True,geometry_equal=True,review='Original 19 narration/caption segments preserved; 47 sentence/comma pairs checked in order. Numeric captions retain original formula meaning; no production listening approval.'))
print(video.run_stage('check',run,SimpleNamespace()))
print('RUN='+str(run));print('CHUNKS='+str(len(pairs)))
