from pathlib import Path
import copy,html,json,re,shutil,xml.etree.ElementTree as ET
from .util import S,write,file_hash,local
from .contracts import InputError
from .page_layout import page_layout

def camera_keys(manifest,layers,timeline):
    meta=layers['metadata']; full=[0,0,meta['width_pt'],meta['height_pt']]; glyphs={g['id']:g for g in layers['glyphs']}
    layout=page_layout(full[2],full[3]); screen_h=layout['height']; safe_fraction=900/screen_h
    final=timeline['segments'][-1]['end_sample']//800
    step_of={gid:step['id'] for step in layers['map']['steps'] for gid in step['glyph_ids']}
    base_heights={}; bounds={}
    for step in layers['map']['steps']:
        gs=[glyphs[g] for g in step['glyph_ids'] if not glyphs[g]['text'].isspace()]
        heights=sorted(g['bbox'][3]-g['bbox'][1] for g in gs if g['bbox'][3]-g['bbox'][1]>=2)
        if not heights: raise InputError('writing step has no measurable letter')
        # Thin operators, punctuation and proportional subscripts do not define text size.
        base_heights[step['id']]=heights[int((len(heights)-1)*.75)]
        bounds[step['id']]=[min(g['bbox'][0] for g in gs),min(g['bbox'][1] for g in gs),max(g['bbox'][2] for g in gs),max(g['bbox'][3] for g in gs)]
    if manifest.get('cameras'):
        keys=[copy.deepcopy(k) for k in manifest['cameras'] if k['at_frame']<final]
        if not keys or keys[0]['at_frame']!=0: keys.insert(0,dict(at_frame=0,viewbox=full))
        if any(k['at_frame']>=timeline['total_frames'] for k in manifest['cameras']): raise InputError('camera outside timeline')
    else:
        keys=[dict(at_frame=0,viewbox=full)]; current=None; active=None
        for event in timeline['events']:
            if event['kind']!='glyph': continue
            g=glyphs[event['id']]; b=g['bbox']; sid=step_of[g['id']]
            if g['text'].isspace(): continue
            height=base_heights[sid]; h=min(full[3],height*screen_h/28); w=h*1920/screen_h; safe_h=h*safe_fraction
            cx,cy=(b[0]+b[2])/2,(b[1]+b[3])/2
            if active!=sid:
                bound=bounds[sid]; cx=(bound[0]+bound[2])/2; cy=min((bound[1]+bound[3])/2,b[1]+safe_h/3)
            view=[max(0,min(max(0,full[2]-w),cx-w/2)),max(0,min(max(0,full[3]-safe_h),cy-safe_h/2)),w,h]
            if active!=sid or not(current[0]+8<=b[0] and b[2]<=current[0]+current[2]-8 and current[1]+8<=b[1] and b[3]<=current[1]+current[3]*safe_fraction-8):
                keys.append(dict(at_frame=event['frame'],viewbox=view)); current=view; active=sid
    if keys[-1]['at_frame']<final: keys.append(dict(at_frame=final,viewbox=full))
    for event in timeline['events']:
        if event['kind']!='glyph': continue
        g=glyphs[event['id']]; b=g['bbox']
        if g['text'].isspace(): continue
        view=next(k['viewbox'] for k in reversed(keys) if k['at_frame']<=event['frame'])
        scale=min(1920/view[2],screen_h/view[3])
        if base_heights[step_of[g['id']]]*scale<25.99: raise InputError('camera makes writing body too small: '+g['id'])
        left=(1920-view[2]*scale)/2;top=(screen_h-view[3]*scale)/2
        screen=[left+(b[0]-view[0])*scale,top+(b[1]-view[1])*scale,
                left+(b[2]-view[0])*scale,top+(b[3]-view[1])*scale]
        if not(0<=screen[0] and 0<=screen[1] and screen[2]<=1920 and screen[3]<=900): raise InputError('camera clips current writing glyph: '+g['id'])
    return keys

def _prefix(svg,prefix):
    # Separate document IDs, preserving all geometry and shared references.
    ids=re.findall(r'\bid="([^"]+)"',svg)
    for old in sorted(ids,key=len,reverse=True):
        svg=svg.replace('id="'+old+'"','id="'+prefix+old+'"').replace('href="#'+old+'"','href="#'+prefix+old+'"').replace('url(#'+old+')','url(#'+prefix+old+')')
    return svg

def assemble(pair,layers,manifest,timeline,run,runtime):
    import fitz
    run=Path(run).resolve(); runtime=Path(runtime)
    if runtime.is_dir(): runtime=runtime/'gsap.min.js'
    if not runtime.is_file(): raise InputError('local GSAP runtime missing')
    dest=run/'composition'; dest.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(runtime,dest/'gsap.min.js'); shutil.copyfile(S/'assets/player.js',dest/'player.js'); shutil.copyfile(S/'assets/layout.css',dest/'layout.css')
    ref=pair['problem']; path=Path(ref['snapshot']); path=path if path.is_absolute() else local(run,path)
    with fitz.open(path) as pdf: problem=pdf[ref['page_index']].get_svg_image(text_as_path=True)
    answer=Path(layers['animated_svg']).read_text(encoding='utf-8'); t=copy.deepcopy(timeline); t['cameras']=camera_keys(manifest,layers,t)
    write(dest/'timeline.json',t)
    encode=lambda x:json.dumps(x,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
    contents='''<!doctype html><html lang="ko"><head><meta charset="utf-8"><link rel="stylesheet" href="layout.css"><script src="gsap.min.js"></script></head><body>'''
    contents+=f'<div data-composition-id="solution" data-width="1920" data-height="1080" data-duration="{t["total_frames"]/30}" id="solution">'
    contents+='<div id="pdf-viewport"><div id="problem-page">'+_prefix(problem,'problem-')+'</div><div id="answer-page" data-layout-allow-overflow>'+answer+'</div><div id="cursor"></div></div><div id="caption-strip"></div></div>'
    layout=page_layout(layers['metadata']['width_pt'],layers['metadata']['height_pt'])
    contents+='<script>window.solutionLayout='+encode(layout)+';window.solutionTimeline='+encode(t)+';window.solutionGlyphs='+encode({g['id']:g for g in layers['glyphs']})+';</script><script>'+(dest/'player.js').read_text(encoding='utf-8')+'</script></body></html>'
    (dest/'index.html').write_text(contents,encoding='utf-8')
    write(dest/'hyperframes.json',{'width':1920,'height':1080,'fps':30})
    write(dest/'runtime.json',{'gsap_sha256':file_hash(dest/'gsap.min.js'),'player_sha256':file_hash(dest/'player.js'),'layout_sha256':file_hash(dest/'layout.css')})
    parts=[dict(entry='composition/index.html',first_frame=0,last_frame=t['total_frames'],key='solution')]; write(run/'source/parts.json',parts); return parts
