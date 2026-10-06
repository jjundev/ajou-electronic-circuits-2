import math
from .contracts import InputError
from .review_adapter import validate_config

def build_timeline(manifest,layers,audio,config):
    validate_config(config); fps,rate=30,24000; per_frame=800
    voices={a['id']:a for a in audio}
    if len(voices)!=len(audio) or set(voices)!={s['id'] for s in manifest['segments']}: raise InputError('audio/segment mismatch')
    if any(a['rate']!=rate or type(a['samples']) is not int or a['samples']<=0 for a in audio): raise InputError('invalid measured PCM')
    interval=math.ceil(fps/float(config['chars_per_second'])); hold=math.ceil(float(config['read_hold_seconds'])*fps)
    steps={s['id']:s for s in layers['map']['steps']}; segs=[]; events=[]; frame=0
    for seg in manifest['segments']:
        n=math.ceil(voices[seg['id']]['samples']/per_frame)
        if seg['kind']=='write':
            step=steps[seg['step_id']]; count=len(step['glyph_ids']); n=max(n,count*interval)+hold
            for i,gid in enumerate(step['glyph_ids']):
                at=frame+(i+1)*interval; events.append(dict(id=gid,frame=at,kind='glyph'))
                events.extend(dict(id=sid,frame=at,kind='shape') for sid,anchor in manifest['shape_anchors'].items() if anchor==gid)
        segs.append(dict(seg,start_sample=frame*per_frame,end_sample=(frame+n)*per_frame,voice_samples=voices[seg['id']]['samples']))
        frame+=n
    # Dedicated finished full-page hold; all glyphs remain visible without swapping SVG.
    frame+=max(hold,30)
    return dict(fps=fps,rate=rate,total_samples=frame*per_frame,total_frames=frame,segments=segs,events=sorted(events,key=lambda e:e['frame']),cameras=manifest.get('cameras',[]))
def visible_ids(timeline,frame): return [e['id'] for e in timeline['events'] if e['kind']=='glyph' and e['frame']<=frame]
