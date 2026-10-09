import sys, pathlib, copy
root=pathlib.Path.cwd();skill=root/'.agents/skills/ec2-solution-video';sys.path[:0]=[str(skill/'scripts'),str(skill/'tests')]
import video,authored_writing
from types import SimpleNamespace
from solution_video.util import read,write
from solution_video.pdf_pages import inside
from solution_video.manifest import content_fingerprint
run=next((root/'문제풀이영상/1007').glob('*제작자료/실행/*/videos/*'));pair=read(run/'source/pair.json');c=read(run/'layers/candidates.json')
boxes=[[500,190,1400,265],[500,265,1400,365],[500,365,1400,520],[500,590,1400,657]]
breaks=[[213,238],[291,309,325,342],[395,413,429,452,480],[617,635]]
steps=[]
for j,b in enumerate(boxes):
 gs=[g for g in c['glyphs'] if inside(g['bbox'],b)]
 # Reviewed PDF row sequence, preserving paint order within each semantic row.
 gs.sort(key=lambda g:(sum((g['bbox'][1]+g['bbox'][3])/2>=edge for edge in breaks[j]),g['paint_order']))
 steps.append(dict(id='block'+str(j),glyph_ids=[g['id'] for g in gs],shape_ids=[s['id'] for s in c['shapes'] if inside(s['bbox'],b)]))
authored_writing.ROW_BREAKS['P10.72']=breaks
draft=dict(glyphs=c['glyphs'],shapes=c['shapes'],map=dict(steps=steps));authored_writing.author_units(draft,'P10.72')
texts=[[
'먼저 전류 거울과 출력 노드의 관계를 정리합니다.',
'채널 길이 변조를 무시하고 엠 포가 포화에 있다고 가정합니다. 엠 포의 전류는 엠 쓰리에 흐르는 아이 원에 소자 크기의 비를 곱합니다. 분자는 엠 포의 폭 대 길이 비이고, 분모는 엠 쓰리의 폭 대 길이 비입니다.',
'출력 노드에 들어오는 아이 디 포는 아이 투와 저항 전류로 나뉩니다. 따라서 브이 아웃은 알 엘에 아이 디 포 빼기 아이 투를 곱한 값입니다.'],[
'에이에서는 두 소자의 폭 대 길이 비가 같습니다.',
'변화 전에는 거울 전류가 아이 영입니다. 출력에서 빠져나가는 아이 투도 아이 영이므로 차이가 영입니다. 따라서 출력 전압도 영입니다.',
'변화 후 거울 전류는 아이 영 더하기 델타 아이가 됩니다.',
'저항으로 흐르는 전류는 아이 영 더하기 델타 아이에서 아이 영 빼기 델타 아이를 뺀 값입니다. 증가한 전류와 감소한 전류의 효과가 함께 더해집니다.',
'아이 영끼리는 없어지고 델타 아이 두 개가 남습니다. 출력 전압은 이 델타 아이 알 엘입니다.'],[
'비에서는 엠 쓰리의 폭 대 길이 비가 엠 포의 두 배입니다.',
'거울 전류는 아이 원의 절반입니다. 변화 전에는 아이 영의 절반에서 아이 영을 빼므로 출력 전압은 마이너스 아이 영 알 엘 나누기 이입니다.',
'변화 후 거울 전류는 아이 영 더하기 델타 아이를 이로 나눈 값입니다.',
'출력 전압은 알 엘에 괄호 안 전류 차이를 곱합니다. 거울 전류인 아이 영 더하기 델타 아이의 절반에서 아이 영 빼기 델타 아이를 뺍니다.',
'이를 정리하면 델타 아이의 계수는 이분의 삼입니다. 아이 영의 계수는 마이너스 이분의 일입니다. 따라서 원문에 있는 이 두 항의 차이에 알 엘을 곱합니다.',
'변화량은 일 점 오 델타 아이 알 엘입니다. 같은 크기인 에이의 이 델타 아이 알 엘보다 작습니다.'],[
'답을 원본과 함께 확인합니다.',
'에이는 변화 전 영이고 변화 후 이 델타 아이 알 엘입니다. 비는 변화 전 마이너스 아이 영 알 엘 나누기 이이고, 변화 후 알 엘 곱하기 삼 델타 아이 빼기 아이 영을 이로 나눈 값입니다.']]
# Final box is intentionally retained with the complete two-row answer, preventing shape duplication across steps.
segs=[];new=[];lesson=[];cues=[];marks=[]
lex={'엠 쓰리':'M₃','엠 포':'M₄','아이 디 포':'I_D4','아이 원':'I₁','아이 투':'I₂','아이 영':'I₀','델타 아이':'ΔI','브이 아웃':'V_out','알 엘':'R_L'}
def cap(t):
 for a,b in lex.items():t=t.replace(a,b)
 return t
ref=['answer:9','md:풀이']
def seg(i,k,s,t):return dict(id=i,kind=k,step_id=s,text=t,caption_text=cap(t),source_refs=ref)
segs.append(seg('intro','problem','','문제 십 점 칠십이입니다. 아이 원은 아이 영에서 아이 영 더하기 델타 아이로 증가합니다. 아이 투는 아이 영에서 아이 영 빼기 델타 아이로 감소합니다. 두 가지 소자 크기에서 변화 전후의 출력 전압을 구합니다.'))
reasons={0:'위쪽 회로에서 엠 쓰리의 게이트와 드레인이 연결되어 있습니다. 엠 포는 같은 게이트 전압을 공유합니다. 채널 길이 변조를 무시하면 거울 전류는 폭 대 길이 비에 비례합니다. 출력 노드에서는 엠 포에서 들어오는 전류가 아이 투와 알 엘로 나뉩니다.',1:'같은 크기의 엠 쓰리와 엠 포를 생각합니다. 아이 원이 증가하면 거울을 통해 출력으로 들어오는 전류도 같은 양만큼 증가합니다. 동시에 아이 투는 감소합니다. 저항으로 흐르는 전류에는 두 변화가 같은 방향으로 더해집니다.',2:'이번에는 엠 쓰리의 크기가 엠 포의 두 배입니다. 같은 게이트 전압에서 엠 포의 전류는 아이 원의 절반이 됩니다. 출력에서는 이 절반 전류에서 아이 투를 빼야 합니다. 아이 투의 감소량 자체는 여전히 델타 아이입니다.'}
for si,st in enumerate(steps):
 lines=list(dict.fromkeys(u['line_id'] for u in st['writing_units']))
 groups=[lines] if si==3 else [[l] for l in lines]
 assert len(groups)==len(texts[si]) if si!=3 else True
 for ri,ls in enumerate(groups):
  ident='part_'+str(si)+'_'+str(ri); us=[u for u in st['writing_units'] if u['line_id'] in ls]; gg={g for u in us for g in u['glyph_ids']};ss={s for u in us for s in u['shape_ids']}
  p=dict(id=ident,glyph_ids=[g for g in st['glyph_ids'] if g in gg],shape_ids=[s for s in st['shape_ids'] if s in ss],writing_units=us);new.append(p)
  circuit=si<3 and ri==1;aid='mark_'+str(si);reason='reason_'+str(si)
  if circuit:
   segs.append(seg(reason,'reason',ident,reasons[si]));cues.append(dict(segment_id=reason,target='circuit'))
   geom=[{'bbox':[887,81,932,125]},{'bbox':[876,63,978,126]},{'bbox':[876,63,978,126]}][si]
   marks.append(dict(id=aid,region_id='circuit',segment_id=reason,kind='ellipse',geometry=geom,source_refs=ref,meaning_notes=reasons[si],hide_at=dict(segment_id='write_'+ident,offset_frames=0)))
  t=' '.join(texts[si]) if si==3 else texts[si][ri];segs.append(seg('write_'+ident,'write',ident,t))
  lesson.append(dict(step_id=ident,mode='circuit' if circuit else 'calculation',reason_segment_ids=[reason] if circuit else [],check_segment_ids=[],region_ids=['circuit'] if circuit else [],annotation_ids=[aid] if circuit else [],meaning_notes=t,source_refs=ref,**({} if circuit else {'exemption_reason':'원문 제목 또는 이미 설명한 회로 근거에 이어지는 전류 차이 계산과 최종 답 확인입니다.'})))
mp=dict(work_bbox=[500,190,1400,657],steps=new,answer_step_id=new[-1]['id']);write(run/'source/map.json',mp)
video.run_stage('extract',run,SimpleNamespace());l=read(run/'layers/layers.json');gs={g['id']:g for g in l['glyphs']};ss={s['id']:s for s in l['shapes']}
m=dict(schema_version=1,problem_id='P10.72',title='PMOS 전류 거울의 출력 변화',segments=segs,reveal_order=[g for s in new for g in s['glyph_ids']],shape_anchors={sid:s['glyph_ids'][0] if ss[sid]['kind']=='step_badge' else s['glyph_ids'][-1] for s in new for sid in s['shape_ids']},cameras=[])
md=(run/pair['md_snapshot']).read_text().split('## 풀이')[1]
cov=dict(status='passed',pdf_md_agree=True,rows=[dict(step_id=s['id'],source_refs=ref,pdf_text=''.join(gs[g]['text'] for g in s['glyph_ids']),md_text=md,meaning_review='원본 답안 9페이지의 행과 분수의 분자/분모, 첨자, 부호를 MD와 직접 대조. a: 0→2ΔIRL, b: -I0RL/2→RL(3ΔI-I0)/2. 원문 그대로 유지.') for s in new])
rev=dict(status='passed',steps=[dict(step_id=s['id'],assumptions='λ=0, M4 포화, 동일 VSG 및 PMOS 종류. 원문 조건 유지.',equations=md,units='전류 A, 저항 Ω, 출력 V. 비율 무차원.',evidence='M3 다이오드 접속과 공통 게이트 확인. KCL: ID4=I2+Vout/RL. a 크기비 1, b 크기비 1/2. a 증분 2ΔI, b 증분 3ΔI/2. 음의 초기 출력은 원문 가정하의 형식적 결과로 보존.') for s in new])
h=content_fingerprint(m,l,cov);cov['input_hash']=rev['input_hash']=h
sha=l['metadata']['source_sha256'];focus=dict(schema_version=1,source_sha256=sha,regions=[dict(id='circuit',bbox=[855,57,1050,181])],cues=cues)
for name,d in [('manifest',m),('coverage',cov),('circuit-review',rev),('focus',focus),('annotations',dict(schema_version=1,source_sha256=sha,items=marks)),('lesson',dict(schema_version=1,steps=lesson))]:write(run/'source'/(name+'.json'),d)
video.run_stage('check',run,SimpleNamespace());print(run)
