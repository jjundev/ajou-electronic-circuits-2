"""E10.13 source-grounded authored lesson; scratch acceptance only."""
from pathlib import Path
from types import SimpleNamespace
import copy
from acceptance import author
import video
from solution_video.util import read,write,file_hash
from solution_video.manifest import content_fingerprint

TEXTS = [['먼저 가상 접지 노드를 찾습니다.', '차동 입력에서는 피 노드가 가상 접지입니다. 따라서 큐 원은 이미터가 접지된 공통 이미터 증폭기로 볼 수 있습니다. 지 엠 원은 큐 원의 트랜스컨덕턴스이고, 알 오 원은 큐 원의 출력 저항입니다. 이 두 기호를 구별해 둡니다.', '이번에는 엑스 노드를 봅시다. 같은 저항 알 원과 알 투의 가운데이고, 양쪽 컬렉터 전압은 같은 크기로 반대 방향으로 변합니다. 그래서 가운데 엑스의 소신호 전압은 영이 됩니다. 이 가상 접지를 이용해 절반 회로를 해석합니다.'], ['다음은 큐 쓰리와 큐 포 부하입니다.', '엑스가 고정되면 큐 쓰리와 큐 포의 베이스가 움직이지 않습니다. 이미터도 전원 브이 씨 씨에 연결되어 소신호에서는 고정되어 있습니다. 베이스와 이미터가 모두 고정되므로 베이스 이미터 전압이 일정합니다.', '베이스 이미터 전압이 일정하므로 고정 바이어스 전류원 부하처럼 보입니다. 여기서 소자를 완전히 없애면 안 됩니다. 문제에서 얼리 전압은 유한하므로, 컬렉터에서 바라본 출력 저항 알 오 쓰리는 남습니다.'], ['이제 큐 원 컬렉터에서 본 저항을 모읍니다.', '알 원의 반대쪽 끝은 방금 가상 접지로 확인한 엑스입니다. 따라서 알 원도 컬렉터에서 교류 접지로 연결된 저항입니다. 회로의 가운데 저항을 빼먹지 않고, 출력 저항 계산에 포함해야 합니다.', '컬렉터에서 같은 교류 접지로 이어지는 저항은 세 개입니다. 큐 원의 알 오 원, 부하의 알 오 쓰리, 그리고 알 원입니다. 같은 두 노드 사이에 있으므로 세 저항을 병렬로 묶어 출력 저항을 씁니다.'], ['마지막으로 차동 전압 이득을 씁니다.', '이득은 마이너스 지 엠 원에 방금 구한 병렬 저항을 곱한 값입니다. 괄호 안에는 알 오 원, 알 오 쓰리, 알 원이 차례로 들어갑니다. 공통 이미터 증폭기의 반전 동작이므로 앞에 음의 부호를 붙입니다.', '원문에서 예제 십 점 십이와 같은 절반 회로라고 정리한 부분입니다.'], ['답을 확인합니다.', '구한 값은 차동 이득입니다.', '최종 식에서도 세 저항의 병렬과 앞의 음의 부호를 확인합니다. 알 원은 엑스의 가상 접지 때문에 포함되었고, 알 오 쓰리는 유한한 출력 저항 때문에 남았습니다.']]
REASONS = [
 '회로의 두 가지와 가운데 피, 엑스를 봅시다. 완벽한 대칭에서 차동 입력은 양쪽을 같은 크기로 반대 방향으로 움직입니다. 그래서 가운데 피와 엑스의 소신호 전압은 영입니다. 이 가상 접지가 절반 회로 해석의 출발점입니다.',
 '회로 위쪽의 큐 쓰리와 큐 포를 봅시다. 베이스는 방금 확인한 엑스에 연결되고, 이미터는 전원 브이 씨 씨에 연결됩니다. 두 단자가 모두 소신호에서 고정되므로 베이스 이미터 전압이 변하지 않습니다. 다만 얼리 전압이 유한해서 출력 저항은 남습니다.',
 '큐 원 컬렉터와 가운데 알 원의 연결을 따라갑니다. 알 원의 반대쪽 끝은 교류 접지인 엑스입니다. 따라서 출력에서 접지로 이어지는 저항에 알 원도 포함됩니다. 큐 원과 큐 쓰리의 출력 저항까지 같은 두 노드에 연결되므로 병렬입니다.',
 '큐 원의 입력과 컬렉터 출력을 봅시다. 이미터의 피 노드가 교류 접지이므로 공통 이미터 동작입니다. 따라서 이득은 음의 지 엠 원에 방금 구한 병렬 부하를 곱합니다. 음의 부호는 입력과 출력이 반대 방향으로 움직인다는 뜻입니다.'
]
# Native answer page is 1440x810pt. These are pointers, not invented current arrows.
MARKS = [
 [('x','ellipse',{'bbox':[872,80,890,100]}),('p','ellipse',{'bbox':[872,167,892,187]}),('zero','label',{'runs':[{'text':'vP = vX = 0','origin':[1006,150],'font_size_pt':12}]})],
 [('load','ellipse',{'bbox':[838,76,927,108]}),('supply','arrow',{'from':[961,71],'to':[910,73]}),('fixed','label',{'runs':[{'text':'VBE fixed','origin':[1006,112],'font_size_pt':12}]})],
 [('r1','ellipse',{'bbox':[858,100,879,129]}),('out','arrow',{'from':[821,138],'to':[856,136]}),('x','ellipse',{'bbox':[872,80,890,100]})],
 [('q1','ellipse',{'bbox':[838,141,878,170]}),('p','ellipse',{'bbox':[872,167,892,187]}),('out','arrow',{'from':[950,141],'to':[868,136]})]
]

def symbol_caption(text):
    # Explicit E10.13 lexicon; no runtime heuristic or changes to TTS text.
    substitutions={'알 오 쓰리':'r_O3','알 오 원':'r_O1','지 엠 원':'g_m1','알 원':'R₁','알 투':'R₂','큐 쓰리':'Q₃','큐 포':'Q₄','큐 원':'Q₁','브이 씨 씨':'V_CC','베이스 이미터 전압':'V_BE','엑스':'X','피 노드':'P 노드','가운데 피':'가운데 P','피와':'P와'}
    for spoken,symbol in substitutions.items():text=text.replace(spoken,symbol)
    return text

def author_guided(run:Path)->dict:
    run=Path(run)
    m,l=author(run)
    if m['problem_id']!='E10.13':raise ValueError('E10.13 only')
    pair=read(run/'source/pair.json')
    source_hashes={key:file_hash(run/pair[key]['snapshot']) for key in ['problem','answer']}
    old=l['map']['steps'];coverage=read(run/'source/coverage.json');review=read(run/'source/circuit-review.json')
    steps=[];rows=[];reviews=[];segments=[dict(m['segments'][0],caption_text=m['segments'][0]['text'])];lesson=[];cues=[];marks=[];core=[]
    for si,step in enumerate(old):
        lines=list(dict.fromkeys(u['line_id'] for u in step['writing_units']))
        if len(lines)!=len(TEXTS[si]):raise ValueError('source lines changed; review authored script')
        for ri,line in enumerate(lines):
            ident=f'part_{si}_{ri}';units=[u for u in step['writing_units'] if u['line_id']==line]
            gs={g for u in units for g in u['glyph_ids']};ss={s for u in units for s in u['shape_ids']}
            split=dict(id=ident,glyph_ids=[g for g in step['glyph_ids'] if g in gs],shape_ids=[s for s in step['shape_ids'] if s in ss],writing_units=units);steps.append(split)
            ref=m['segments'][si+1]['source_refs'];reason=f'reason_{si}';circuit=si<4 and ri==1
            if circuit:
                core.append(ident);segments.append(dict(id=reason,kind='reason',step_id=ident,text=REASONS[si],caption_text=symbol_caption(REASONS[si]),source_refs=ref));cues.append(dict(segment_id=reason,target='circuit'))
                ids=[]
                for short,kind,geometry in MARKS[si]:
                    mid=f'mark_{si}_{short}';ids.append(mid)
                    marks.append(dict(id=mid,kind=kind,geometry=geometry,segment_id=reason,region_id='circuit',source_refs=ref,meaning_notes=REASONS[si],hide_at={'segment_id':f'write_{si}_{ri}','offset_frames':0}))
            text=TEXTS[si][ri]
            segments.append(dict(id=f'write_{si}_{ri}',kind='write',step_id=ident,text=text,caption_text=symbol_caption(text),source_refs=ref))
            lesson.append(dict(step_id=ident,mode='circuit' if circuit else 'calculation',reason_segment_ids=[reason] if circuit else [],check_segment_ids=[],region_ids=['circuit'] if circuit else [],annotation_ids=ids if circuit else [],meaning_notes=review['steps'][si]['equations'],source_refs=ref,**({} if circuit else {'exemption_reason':'제목 또는 같은 논리 단계에서 이미 제시한 회로 근거의 후속 정리이며 원문 순서를 유지합니다.'})))
            row=copy.deepcopy(coverage['rows'][si]);row.update(step_id=ident,pdf_text=''.join(next(g['text'] for g in l['glyphs'] if g['id']==gid) for gid in split['glyph_ids']));rows.append(row)
            rev=copy.deepcopy(review['steps'][si]);rev['step_id']=ident;reviews.append(rev)
    mp=copy.deepcopy(l['map']);mp.update(steps=steps,answer_step_id=steps[-1]['id']);write(run/'source/map.json',mp)
    video.run_stage('extract',run,SimpleNamespace());l=read(run/'layers/layers.json')
    m.update(segments=segments,reveal_order=[g for s in steps for g in s['glyph_ids']],shape_anchors={sid:s['glyph_ids'][0] if next(o for o in l['shapes'] if o['id']==sid)['kind']=='step_badge' else s['glyph_ids'][-1] for s in steps for sid in s['shape_ids']})
    coverage['rows']=rows;review['steps']=reviews;coverage['input_hash']=review['input_hash']=content_fingerprint(m,l,coverage)
    sha=l['metadata']['source_sha256']
    focus=dict(schema_version=1,source_sha256=sha,regions=[dict(id='circuit',bbox=[800,60,996,242])],cues=cues)
    for name,data in [('manifest',m),('coverage',coverage),('circuit-review',review),('focus',focus),('annotations',dict(schema_version=1,source_sha256=sha,items=marks)),('lesson',dict(schema_version=1,steps=lesson))]:write(run/'source'/(name+'.json'),data)
    config=read(run/'source/config.json');config['max_attempts']=1;write(run/'source/config.json',config)
    video.run_stage('check',run,SimpleNamespace())
    return dict(problem_id=m['problem_id'],core_step_ids=core,source_hashes=source_hashes)
