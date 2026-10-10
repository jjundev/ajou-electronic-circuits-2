from pathlib import Path
import json,shutil,subprocess,time,sys
sys.path.insert(0,str(Path.cwd()/'.agents/skills/ec2-review-video/scripts'))
from lib.render import cpu_backend,render_parts
from lib.render_options import default_render_options
from lib.cache import atomic_json,file_hash
base=Path('/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/복습영상/1002/1002_제작자료/성능시험/20261010-review-policy-motion24')
dest=base/'fonts-ready-probe';dest.mkdir();entry=Path('/Users/hyunjun_macbook_pro/.npm/_npx/702923228c2ce1e6/node_modules/hyperframes/dist/cli.js');result=[]
for workers in [2,6]:
 run=dest/f'workers-{workers}';shutil.copytree(base/'fixture',run)
 for path in run.glob('scene-*.html'):
  text=path.read_text().replace('<script>(()=>{const tl=','<script>Promise.resolve().then(()=>document.fonts.ready).then(()=>{const tl=').replace('})();</script>','});</script>')
  path.write_text(text)
 options=default_render_options();options['workers']=workers;backend=cpu_backend(entry,options)
 parts=json.loads((run/'source/parts.json').read_text())['parts'][1:];start=time.monotonic();outputs=render_parts(parts,run,backend)
 frames=dest/f'workers-{workers}.framemd5';subprocess.run(['/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg','-y','-v','error','-i',str(outputs[0]),'-f','framemd5',str(frames)],check=True)
 row=dict(workers=workers,elapsed=time.monotonic()-start,video_sha256=file_hash(outputs[0]),framemd5_sha256=file_hash(frames));result.append(row);print(row,flush=True)
atomic_json(dest/'result.json',dict(runs=result,equal=result[0]['framemd5_sha256']==result[1]['framemd5_sha256']))
