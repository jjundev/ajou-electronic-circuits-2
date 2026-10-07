"""Real frozen PDFs, synthetic PCM, scratch-only rendering; never approves publication."""
from pathlib import Path
from types import SimpleNamespace
import argparse,unicodedata
from fixtures import S,REPO,make_audio
from acceptance import author,IDS
import video
from solution_video.util import read,write,file_hash,digest
from solution_video.manifest import content_fingerprint
from solution_video.annotations import load_teaching
from solution_video.teaching import build_teaching_timeline
from solution_video.review_adapter import default_config
from solution_video.writing import load_writing
from solution_video.composition import assemble
from solution_video.media import render_master
from solution_video.subtitles import write_srt,burn_subtitles
from solution_video.verify import verify_run

# Authored after inspecting the native 1440x810 answer pages. Marks reference existing nodes.
DRAWINGS={
 'E10.11':dict(region=[828,60,1076,242],circle=[919,169,939,187],runs=[dict(text='v',origin=[998,177],font_size_pt=12),dict(text='P',origin=[1005,181],font_size_pt=8),dict(text=' = 0',origin=[1011,177],font_size_pt=12)],notes='P is the virtual ground under the original differential small-signal assumption.'),
 'E10.13':dict(region=[800,60,996,242],circle=[871,78,894,101],runs=[dict(text='v',origin=[1004,112],font_size_pt=12),dict(text='X',origin=[1011,116],font_size_pt=8),dict(text=' = 0',origin=[1017,112],font_size_pt=12)],notes='The original answer names X as the symmetric virtual ground.'),
 '2021-1_중간-Q3':dict(region=[720,60,1080,242],circle=[988,115,1012,137],runs=[dict(text='R',origin=[1090,144],font_size_pt=12),dict(text='P',origin=[1098,148],font_size_pt=8)],notes='Reference the existing RP label; its parallel loading is explained by the original answer.')}

def add_teaching(run,m,l):
 d=DRAWINGS[m['problem_id']];first=m['segments'][1];ref=first['source_refs'][0]
 m['segments'].insert(1,dict(id='figure_intro',kind='reason',step_id=first['step_id'],text={'E10.11':'상단 회로의 피 노드가 가상 접지임을 표시합니다.','E10.13':'상단 회로의 엑스 노드가 가상 접지임을 표시합니다.','2021-1_중간-Q3':'상단의 두 회로를 비교하고 알 피를 표시합니다.'}[m['problem_id']],source_refs=[ref]))
 m['segments'].insert(3,dict(id='figure_return',kind='check',step_id=first['step_id'],text='표시를 남긴 회로와 방금 쓴 풀이를 연결합니다.',source_refs=[ref]))
 focus=dict(schema_version=1,source_sha256=l['metadata']['source_sha256'],regions=[dict(id='circuit',bbox=d['region'])],cues=[dict(segment_id=s,target='circuit') for s in ['figure_intro','figure_return']])
 shared=dict(segment_id='figure_intro',region_id='circuit',source_refs=[ref],meaning_notes=d['notes'])
 annotations=dict(schema_version=1,source_sha256=focus['source_sha256'],items=[dict(shared,id='node_circle',kind='ellipse',geometry={'bbox':d['circle']}),dict(shared,id='node_label',kind='label',geometry={'runs':d['runs']})])
 for name,data in [('focus',focus),('annotations',annotations),('manifest',m)]:write(run/'source'/(name+'.json'),data)
 coverage=read(run/'source/coverage.json');review=read(run/'source/circuit-review.json');h=content_fingerprint(m,l,coverage);coverage['input_hash']=review['input_hash']=h
 write(run/'source/coverage.json',coverage);write(run/'source/circuit-review.json',review);video.run_stage('check',run,SimpleNamespace())
 return m

def run_acceptance(dest,entry,batch=None,selected=None,report_path=None):
 dest=Path(dest).resolve();dest.mkdir(parents=True,exist_ok=True);entry=Path(entry).resolve();selected=selected or IDS
 if not selected or not set(selected)<=set(IDS):raise ValueError('unknown acceptance problem')
 original={str(p):file_hash(p) for folder in ['복습노트','교과서','from_the_past'] for p in next(p for p in REPO.iterdir() if unicodedata.normalize('NFC',p.name)==folder).rglob('*.pdf')}
 for folder in ['복습노트','교과서','from_the_past']:
  source=next(p for p in REPO.iterdir() if unicodedata.normalize('NFC',p.name)==folder);target=dest/folder
  if not target.exists():target.symlink_to(source,target_is_directory=True)
 batch=Path(batch) if batch else video.prepare_batch(dest,'1002',IDS,False);print('BATCH',batch,flush=True);results=[]
 for item in read(batch/'batch.json')['items']:
  if item['id'] not in selected:continue
  run=batch/item['run']
  if not run.resolve().is_relative_to(dest):raise RuntimeError('acceptance run escapes scratch')
  for name in ['focus','annotations']:(run/'source'/(name+'.json')).unlink(missing_ok=True)
  m,l=author(run);m=add_teaching(run,m,l)
  audio=[make_audio(s['id'],24000,run) for s in m['segments']];write(run/'source/audio.json',{'voices':audio})
  t=build_teaching_timeline(m,l,audio,default_config(),load_writing(run,default_config()),load_teaching(run,m,l));write(run/'source/timeline.json',t)
  parts=assemble(read(run/'source/pair.json'),l,m,t,run,S.parent/'ec2-review-video/assets/runtime/vendor/gsap.min.js')
  print('RENDER',item['id'],t['total_frames'],flush=True)
  media_hash=digest({p.relative_to(run).as_posix():file_hash(p) for folder in ['composition','source'] for p in (run/folder).rglob('*') if p.is_file()})
  receipt=run/'renders/acceptance-input.json';final=run/'renders/final.mp4'
  if not receipt.is_file() or read(receipt).get('input_hash')!=media_hash or not final.is_file() or read(receipt).get('final_sha256')!=file_hash(final):
   master=render_master(parts,t,audio,run,entry);srt=write_srt(t,run/'renders/captions.srt');final=burn_subtitles(master,srt,final,S.parent/'ec2-review-video/assets/fonts/Pretendard-Bold.ttf')
   write(receipt,dict(input_hash=media_hash,final_sha256=file_hash(final)))
  report=verify_run(run,entry);technical=all(report['checks'][k]['status']=='passed' for k in ['content','original_svg','hyperframes','final_media','captions','writing_animation','teaching_animation','writing_flow'])
  if not technical:raise RuntimeError(str(report['checks']))
  if report['complete'] or report['live_audio']!='unverified':raise RuntimeError('fake voice approved')
  results.append(dict(problem_id=item['id'],run=str(run),final=str(final),final_sha256=file_hash(final),pixel_diff=read(run/'verification/gate.json')['pixel_diff'],media_passed=True,teaching_passed=True,writing_flow_passed=True,total_frames=t['total_frames']))
  print('DONE',item['id'],flush=True)
 if any(file_hash(p)!=sha for p,sha in original.items()):raise RuntimeError('source PDF changed')
 publication=video.publish_batch(batch)
 if publication['complete'] or publication['published']:raise RuntimeError('fake voice published')
 result=dict(items=results,selected_ids=selected,paid_requests=0,live_audio='unverified',production_publish_blocked=True);write(report_path or dest/'teaching-acceptance.json',result);return result

def main():
 p=argparse.ArgumentParser();p.add_argument('--dest',type=Path,required=True);p.add_argument('--hyperframes-entry',type=Path,required=True);p.add_argument('--batch',type=Path);p.add_argument('--problems');p.add_argument('--report',type=Path);a=p.parse_args();run_acceptance(a.dest,a.hyperframes_entry,a.batch,a.problems.split(',') if a.problems else None,a.report)
if __name__=='__main__':main()
