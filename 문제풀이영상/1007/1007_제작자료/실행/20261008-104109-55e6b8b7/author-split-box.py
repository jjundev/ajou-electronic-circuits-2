import pathlib,sys,copy
r=next(pathlib.Path('문제풀이영상/1007').glob('*제작자료/실행/*/videos/*'));sys.path.insert(0,str(pathlib.Path('.agents/skills/ec2-solution-video/scripts')))
from solution_video.util import read,write
from solution_video.manifest import content_fingerprint
mp=read(r/'source/map.json');st=mp['steps'][-1];units=[]
for u in st['writing_units']:
 if u['chunk_id']=='chunk_3_1_1':
  print('split',u)
  a=copy.deepcopy(u);b=copy.deepcopy(u);a['band'][1]=1150;b['band'][0]=1150;b['id']+='b';b['chunk_id']='chunk_3_1_2';b['camera_break_before']=True;units.extend([a,b])
 else:units.append(u)
st['writing_units']=units;write(r/'source/map.json',mp)
import video
from types import SimpleNamespace
video.run_stage('extract',r.resolve(),SimpleNamespace())
l=read(r/'layers/layers.json');m=read(r/'source/manifest.json');cov=read(r/'source/coverage.json');rev=read(r/'source/circuit-review.json');h=content_fingerprint(m,l,cov);cov['input_hash']=rev['input_hash']=h
write(r/'source/coverage.json',cov);write(r/'source/circuit-review.json',rev)
video.run_stage('check',r.resolve(),SimpleNamespace())
