"""Opt-in, zero-paid real-PDF acceptance. Produces scratch media, blocks live publication."""
from pathlib import Path
import argparse,sys,json,shutil
from types import SimpleNamespace
from fixtures import S,REPO,make_audio
sys.path.insert(0,str(S/'scripts'))
import video
from solution_video.util import read,write,file_hash,digest
from solution_video.sources import discover
from solution_video.pdf_pages import export_page,extract_layers,inside
from solution_video.manifest import content_fingerprint
from solution_video.reveal import build_timeline
from solution_video.review_adapter import default_config
from solution_video.media import render_master
from solution_video.subtitles import write_srt,burn_subtitles
from solution_video.composition import assemble
from solution_video.verify import verify_run,verification_fingerprint

IDS=['E10.11','E10.13','2021-1_중간-Q3']
# Bounds authored from native pages; Q3 is left1,left2,right3,right4,answer.
BOXES={1:[[301,260,815,340],[301,340,815,425],[301,425,815,525],[301,525,815,574]],2:[[301,180,747,256],[301,256,747,332],[301,332,747,412],[301,412,747,504],[301,504,747,574]],7:[[301,180,529,311],[301,311,529,513],[534,180,747,280],[534,280,747,513],[301,513,747,574]]}
TEXTS={
'E10.11':['차동 소신호에서 이미터 전류 변화가 상쇄됩니다.','접지된 베이스와 이미터의 pnp 부하를 확인합니다.','출력 저항의 병렬값으로 차동 이득을 씁니다.','음의 전압 이득을 답안과 대조합니다.'],
'E10.13':['대칭 때문에 P와 X가 가상 접지입니다.','pnp 부하는 컬렉터 출력 저항만 보입니다.','R1도 교류 접지로 가는 저항입니다.','세 저항의 병렬값에 음의 트랜스컨덕턴스를 곱합니다.','답안의 이득과 부호를 확인합니다.'],
'2021-1_중간-Q3':['전류로 각 소신호 파라미터를 계산합니다.','이미터 저항과 베이스 입력 저항의 병렬을 확인합니다.','차동 반회로의 전류와 파라미터를 확인합니다.','RP가 캐스코드 소자의 출력 저항과 병렬입니다.','단일 출력 저항과 차동 출력 저항을 구별합니다.']}
def author(run):
    pair=read(run/'source/pair.json');candidate=read(run/'layers/candidates.json'); idx=pair['answer']['page_index'];boxes=BOXES[idx]
    for s in candidate['shapes']:
        if s['kind']=='unclassified' and any(inside(s['bbox'],b) for b in boxes):s['kind']='answer_box'
    write(run/'layers/candidates.json',candidate);steps=[]
    for j,b in enumerate(boxes):
        gs=[g for g in candidate['glyphs'] if inside(g['bbox'],b)]
        # A spatial draft is reviewed below against the original PDF/MD; never used as generic auto authoring.
        gs.sort(key=lambda g:(round(g['bbox'][1]/8),g['bbox'][0]))
        steps.append(dict(id='answer' if j==len(boxes)-1 else 'step'+str(j+1),glyph_ids=[g['id'] for g in gs],shape_ids=[s['id'] for s in candidate['shapes'] if inside(s['bbox'],b)]))
    mp=dict(work_bbox=[301,boxes[0][1],boxes[-1][2],574],steps=steps,answer_step_id='answer');write(run/'source/map.json',mp)
    video.run_stage('extract',run,SimpleNamespace())
    layers=read(run/'layers/layers.json'); glyphs={g['id']:g for g in layers['glyphs']}
    md=(run/pair['md_snapshot']).read_text(encoding='utf-8').split('## 풀이',1)[-1];sections=md.split('### ')[1:]
    segs=[dict(id='intro',step_id='',text='원본 문제의 조건과 구할 것을 먼저 확인합니다.',source_refs=['problem:'+str(pair['problem']['page_index']+1)],kind='problem')]
    segs.extend(dict(id='write'+str(j),step_id=step['id'],text=TEXTS[pair['problem_id']][j],source_refs=['answer:'+str(idx+1),'md:풀이/'+str(j+1)],kind='write') for j,step in enumerate(steps))
    manifest=dict(schema_version=1,problem_id=pair['problem_id'],title={'E10.11':'pnp 부하 차동쌍의 이득','E10.13':'가상 접지와 세 저항의 병렬','2021-1_중간-Q3':'캐스코드 출력 저항과 차동 이득'}[pair['problem_id']],segments=segs,reveal_order=[g for step in steps for g in step['glyph_ids']],shape_anchors={sid:step['glyph_ids'][0] if next(s for s in layers['shapes'] if s['id']==sid)['kind']=='step_badge' else step['glyph_ids'][-1] for step in steps for sid in step['shape_ids']},cameras=[])
    rows=[dict(step_id=step['id'],source_refs=['answer:'+str(idx+1),'md:풀이/'+str(j+1)],pdf_text=''.join(glyphs[g]['text'] for g in step['glyph_ids']),md_text=sections[j],meaning_review='동결 답안 화면과 MD의 단계/식/부호/수치를 직접 대조; 렌더 검증용 로컬 PCM') for j,step in enumerate(steps)]
    coverage=dict(status='passed',pdf_md_agree=True,rows=rows)
    review=dict(status='passed',steps=[dict(step_id=step['id'],assumptions='문제의 바이어스 및 차동/단일 출력 정의 유지',equations=sections[j],units='이득 V/V, 저항 ohm, 전류 A, gm S',evidence='동결 PDF/MD 대조. Q3: gm=0.02/0.04 S, RE||rpi=2.5 kohm, Rout=500 kohm, Av=-20000; 차동 Rout=1 Mohm, Av=-10000. E10.11/13: 고정 pnp 부하 rO, R1은 X 교류 접지에 병렬.') for j,step in enumerate(steps)])
    h=content_fingerprint(manifest,layers,coverage);coverage['input_hash']=review['input_hash']=h
    for name,data in [('manifest',manifest),('coverage',coverage),('circuit-review',review)]:write(run/'source'/(name+'.json'),data)
    video.run_stage('check',run,SimpleNamespace());return manifest,layers

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--dest',required=True,type=Path);parser.add_argument('--hyperframes-entry',required=True,type=Path);args=parser.parse_args()
    args.dest.mkdir(parents=True,exist_ok=True); originals={str(p):file_hash(p) for p in REPO.rglob('*.pdf')}; oldskill={str(p):file_hash(p) for p in (S.parent/'ec2-review-video').rglob('*') if p.is_file() and '__pycache__' not in str(p)}
    # Create a separate source view without touching actual final output folders.
    for folder in ['복습노트','교과서','from_the_past']:
        source=next(p for p in REPO.iterdir() if __import__('unicodedata').normalize('NFC',p.name)==folder)
        target=args.dest/folder
        if not target.exists(): target.symlink_to(source,target_is_directory=True)
    batch=video.prepare_batch(args.dest,'1002',IDS,False); print('BATCH',batch,flush=True);results=[]
    for item in read(batch/'batch.json')['items']:
        run=batch/item['run'];m,l=author(run);audio=[make_audio(s['id'],24000,run) for s in m['segments']];write(run/'source/audio.json',{'voices':audio})
        t=build_timeline(m,l,audio,default_config());write(run/'source/timeline.json',t);parts=assemble(read(run/'source/pair.json'),l,m,t,run,S.parent/'ec2-review-video/assets/runtime/vendor/gsap.min.js')
        master=render_master(parts,t,audio,run,args.hyperframes_entry);srt=write_srt(t,run/'renders/captions.srt');final=burn_subtitles(master,srt,run/'renders/final.mp4',S.parent/'ec2-review-video/assets/fonts/Pretendard-Bold.ttf')
        report=verify_run(run,args.hyperframes_entry); technical=all(report['checks'][k]['status']=='passed' for k in ['content','original_svg','hyperframes','final_media','captions'])
        if not technical: raise RuntimeError(json.dumps(report,ensure_ascii=False))
        if report['complete'] or report['live_audio']!='unverified':raise RuntimeError('fake PCM wrongly approved for live production')
        r=dict(problem_id=item['id'],final=str(final),final_sha256=file_hash(final),pixel_diff=read(run/'verification/gate.json')['pixel_diff'],media_passed=technical,total_frames=t['total_frames']);results.append(r);print('DONE',r,flush=True)
    assert all(file_hash(p)==sha for p,sha in originals.items());assert all(file_hash(p)==sha for p,sha in oldskill.items())
    publish=video.publish_batch(batch);assert not publish['complete'] and not publish['published']
    write(batch/'acceptance.json',dict(items=results,paid_requests=0,live_audio='unverified',production_publish_blocked=True));print('ACCEPTANCE',batch,flush=True)
if __name__=='__main__':main()
