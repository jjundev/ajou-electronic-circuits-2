import pathlib,sys,copy
sys.path.insert(0,'.agents/skills/ec2-solution-video/scripts')
from solution_video.util import read,write,file_hash
from solution_video.state import finish_stage
from solution_video.media import probe
r=next(pathlib.Path.Path('문제풀이영상/1007').glob('*제작자료/실행/*/videos/*')) if False else next(pathlib.Path('문제풀이영상/1007').glob('*제작자료/실행/*/videos/*')).resolve();b=r.parents[1]/'caption-original'
a,z=read(b/'source/timeline.json'),read(r/'source/timeline.json')
for t in [a,z]:
 for s in t['segments']:s.pop('caption_text',None)
assert a==z,'non-caption timeline changed'
old,new=read(b/'source/manifest.json'),read(r/'source/manifest.json')
for m in [old,new]:
 for s in m['segments']:s.pop('caption_text',None)
assert old==new,'non-caption manifest changed'
assert read(b/'source/audio.json')==read(r/'source/audio.json'),'voice records changed'
for v in read(r/'source/audio.json')['voices']:assert file_hash(r/v['path'])==v['sha256']
master=r/'renders/master.mp4';before=read(b/'state.json')['stages']['render']['outputs']['renders/master.mp4'];assert file_hash(master)==before
stream=next(s for s in probe(master)['streams'] if s['codec_type']=='video');assert int(stream['nb_frames'])==z['total_frames']
write(r/'verification/master-reuse.json',dict(status='passed',reason='Only caption_text changed. Full original manifest/timeline excluding that field, voice records and every WAV hash, source layers and existing master output hash are preserved. Reuse the already rendered master for subtitle burn.',master_sha256=before,frames=z['total_frames'],paid_requests=0))
finish_stage(r,'render',[master]);print('master reuse verified; frames',z['total_frames'])
