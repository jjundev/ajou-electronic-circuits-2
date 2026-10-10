from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import subprocess,time,json,re,hashlib,os,shutil,statistics,sys
ROOT=Path.cwd().resolve()
SOURCE=ROOT/'문제풀이영상/1007/1007_제작자료/실행/20261010-124459-semantic-caption-wrap/videos/problem-d885c8738da3'
CLI=Path('/Users/hyunjun_macbook_pro/.npm/_npx/702923228c2ce1e6/node_modules/hyperframes/dist/cli.js')
FFMPEG='/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg'
DEST=SOURCE.parents[3]/'성능시험'/datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y%m%d-%H%M%S')
DEST.mkdir(parents=True);(DEST/'renders').mkdir();(DEST/'logs').mkdir()
shutil.copy2(__file__,DEST/'benchmark.py')
COMP=DEST/'inputs/composition';shutil.copytree(SOURCE/'composition',COMP)
for name in ['narration.wav','captions.srt']:shutil.copy2(SOURCE/'renders'/name,DEST/'inputs'/name)
FONT=ROOT/'.agents/skills/ec2-review-video/assets/fonts/Pretendard-Bold.ttf'
(DEST/'inputs/fonts').mkdir();shutil.copy2(FONT,DEST/'inputs/fonts/Pretendard-Bold.ttf')
EXPECTED=json.loads((SOURCE/'source/timeline.json').read_text())['total_frames']
ENV=os.environ.copy();ENV['HYPERFRAMES_FFMPEG_PATH']=FFMPEG

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def inventory():
 paths=[p for sub in ['source','composition'] for p in (SOURCE/sub).rglob('*') if p.is_file()]
 paths += [SOURCE/'renders'/n for n in ['master.mp4','final.mp4','narration.wav','captions.srt']]
 return {str(p.relative_to(SOURCE)):sha(p) for p in paths}
FROZEN=inventory();(DEST/'source-hashes-before.json').write_text(json.dumps(FROZEN,indent=2,ensure_ascii=False))
RESULTS=[];PROGRESS=DEST/'progress.json'
def save():
 (DEST/'results.json').write_text(json.dumps(RESULTS,indent=2,ensure_ascii=False))
def probe(p):
 x=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)],text=True))
 return {'streams':[{k:s.get(k) for k in ['codec_type','codec_name','width','height','avg_frame_rate','nb_frames','duration','sample_rate','bit_rate']} for s in x['streams']],'size':p.stat().st_size}
def ps_tree(pid):
 s=subprocess.check_output(['ps','-axo','pid=,ppid=,rss=,%cpu='],text=True)
 rows={}
 for l in s.splitlines():
  a=l.split()
  if len(a)!=4:continue
  try:rows[int(a[0])]=(int(a[1]),int(a[2]),float(a[3]))
  except ValueError:continue
 selected={pid};prev=None
 while prev!=selected:
  prev=selected.copy();selected.update(p for p,(par,_,_) in rows.items() if par in selected)
 return sum(rows[p][1] for p in selected if p in rows)/1024,sum(rows[p][2] for p in selected if p in rows)
def timed(case,cmd,cwd=COMP):
 log=DEST/'logs'/f'{case}.log';resource_log=DEST/'logs'/f'{case}-resources.json'
 start=time.monotonic();samples=[]
 PROGRESS.write_text(json.dumps({'case':case,'state':'running','log':str(log),'started_at':datetime.now(ZoneInfo('Asia/Seoul')).isoformat()}))
 swap_before=subprocess.check_output(['sysctl','vm.swapusage'],text=True).strip()
 with log.open('w') as f:
  p=subprocess.Popen(['/usr/bin/time','-lp',*map(str,cmd)],cwd=cwd,env=ENV,stdout=f,stderr=subprocess.STDOUT)
  while p.poll() is None:
   try:rss,cpu=ps_tree(p.pid);samples.append({'at_s':round(time.monotonic()-start,2),'rss_mib':round(rss,2),'cpu_percent_ps':round(cpu,2)})
   except (ValueError,subprocess.CalledProcessError):pass
   time.sleep(1)
  rc=p.wait()
 elapsed=time.monotonic()-start
 resource_log.write_text(json.dumps(samples))
 txt=log.read_text();row={'case':case,'command':list(map(str,cmd)),'returncode':rc,'wall_s':round(elapsed,3),'log':str(log.relative_to(DEST)),'rss_tree_peak_mib':max((s['rss_mib'] for s in samples),default=0),'rss_tree_median_mib':statistics.median([s['rss_mib'] for s in samples]) if samples else 0,'swap_before':swap_before,'swap_after':subprocess.check_output(['sysctl','vm.swapusage'],text=True).strip()}
 for k in ['real','user','sys']:
  m=re.findall(r'^'+k+r'\s+([0-9.]+)',txt,re.M);row[k+'_s']=float(m[-1]) if m else None
 for l in txt.splitlines():
  if 'Render:trace' not in l:continue
  try:x=json.loads(l[l.index('{'):])
  except ValueError:continue
  if x.get('status')=='end' and x.get('phase') in ['capture_disk','encode','pipeline','compile']:
   row[x['phase']+'_s']=x.get('durationMs',0)/1000
  if x.get('message')=='artifact validated':row['render_pipeline_s']=x.get('totalElapsedMs',0)/1000
 row['cpu_seconds']=round((row.get('user_s') or 0)+(row.get('sys_s') or 0),3)
 RESULTS.append(row);save();PROGRESS.write_text(json.dumps({'case':case,'state':'done','result':row}))
 print(json.dumps({k:v for k,v in row.items() if k not in ['command','swap_before','swap_after']},ensure_ascii=False),flush=True)
 if rc:raise RuntimeError('case failed: '+case)
 return row

def render(w,gpu=False,rep=1,fast=False):
 name=f'w{w}-'+('gpu' if gpu else 'cpu')+('-fast' if fast else '')+f'-r{rep}'
 out=DEST/'renders'/f'{name}.mp4'
 cmd=['node',CLI,'render','--composition','index.html','--quality','delivery','--workers',str(w),'--experimental-fast-capture='+str(fast).lower(),'--output',out]
 if gpu:cmd+=['--gpu']
 row=timed(name,cmd);row['workers']=w;row['gpu_requested']=gpu;row['fast_requested']=fast;row['video']=probe(out)
 v=next(s for s in row['video']['streams'] if s['codec_type']=='video')
 assert (v['width'],v['height'],v['avg_frame_rate'],int(v['nb_frames']))==(1920,1080,'30/1',EXPECTED)
 row['output']=str(out.relative_to(DEST));save();return row

try:
 meta={'source_run':str(SOURCE),'destination':str(DEST),'frames':EXPECTED,'fps':30,'duration_s':EXPECTED/30,'cli':str(CLI),'cli_version':json.loads((CLI.parent.parent/'package.json').read_text())['version'],'ffmpeg':FFMPEG,'ffmpeg_version':subprocess.check_output([FFMPEG,'-version'],text=True).splitlines()[0],'hardware':subprocess.check_output(['system_profiler','SPHardwareDataType','SPDisplaysDataType','-detailLevel','mini'],text=True),'starting_swap':subprocess.check_output(['sysctl','vm.swapusage'],text=True),'method':'same unmodified composition; sequential timed trials; resource sample 1s; baseline and fastest CPU configuration repeated; no TTS'}
 (DEST/'metadata.json').write_text(json.dumps(meta,indent=2,ensure_ascii=False));print('DEST '+str(DEST),flush=True)
 base=render(2);four=render(4);six=render(6);gpu=render(4,gpu=True)
 best=min([four,six],key=lambda r:r['real_s']);render(2,rep=2);repeat=render(best['workers'],rep=2)
 # Reuse unchanged measured audio; mux by stream copy, then compare subtitle encoding.
 winner=DEST/best['output'];master=DEST/'renders/test-master.mp4'
 row=timed('mux-audio',[FFMPEG,'-y','-v','error','-i',winner,'-i',DEST/'inputs/narration.wav','-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','128k','-movflags','+faststart',master],cwd=DEST/'inputs');row['video']=probe(master);save()
 style='WrapStyle=2,FontName=Pretendard,FontSize=14,Bold=1,Alignment=2,MarginV=14,Outline=0,Shadow=4,BorderStyle=4,PrimaryColour=&HFFFFFF&,OutlineColour=&H4D0E0B0B,BackColour=&H4D0E0B0B'
 filt="subtitles=captions.srt:fontsdir=fonts:force_style='"+style+"'"
 for name,args in [('captions-current',['-c:v','libx264','-crf','18']),('captions-fast',['-c:v','libx264','-crf','18','-preset','fast']),('captions-hardware',['-c:v','h264_videotoolbox','-allow_sw','0','-b:v','15M'])]:
  out=DEST/'renders'/f'{name}.mp4';row=timed(name,[FFMPEG,'-y','-v','error','-i',master,'-vf',filt,*args,'-pix_fmt','yuv420p','-c:a','copy',out],cwd=DEST/'inputs');row['video']=probe(out);row['output']=str(out.relative_to(DEST));save()
 after=inventory();(DEST/'source-hashes-after.json').write_text(json.dumps(after,indent=2,ensure_ascii=False));assert after==FROZEN,'source modified during test'
 PROGRESS.write_text(json.dumps({'state':'measured','best_cpu_case':best['case'],'source_unchanged':True,'destination':str(DEST)}));print('MEASUREMENTS COMPLETE '+str(DEST),flush=True)
except Exception as e:
 PROGRESS.write_text(json.dumps({'state':'failed','error':str(e),'destination':str(DEST)}));print('FAILED '+repr(e),flush=True);raise
