"""Explicit local circuit render smoke; synthetic PCM, never a paid API."""
import argparse,copy,json
from pathlib import Path
from _util import ROOT,SKILL,pcm,write_circuit_review
from lib.cache import atomic_json,file_hash
from lib.theme import snapshot_theme
from lib.composition import stage_assets,assemble
from lib.timing import build_timeline,write_subtitles
from lib.render import probe_backends,render_parts,mux
from lib.verify import verify_media,verify_audio,verify_sync,check_sources
from lib.circuit import require_circuit_review

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--assets',required=True);p.add_argument('--hyperframes-entry',required=True);args=p.parse_args()
    run=Path(args.run).resolve();run.mkdir(parents=True,exist_ok=True)
    fixture=SKILL/'tests/fixtures/circuit-scene';m=json.loads((fixture/'manifest.json').read_text())
    m['scenes'].append(dict(m['scenes'][0],id='scene-review',template_kind='review'))
    m['segments'].append(dict(m['segments'][0],id='seg-review',scene_id='scene-review'))
    source=run/'source/inputs/src-note.md';source.parent.mkdir(parents=True,exist_ok=True)
    source.write_text('#ideal-mos\nSynthetic test: matched saturated MOS, ideal constant tail 100 μA, small differential signal, Δi=10 μA; branch currents 50±10 μA. Not a real lecture example.\n')
    m['sources'][0].update(path='source/inputs/src-note.md',sha256=file_hash(source),kind='note-md')
    atomic_json(run/'source/inputs.json',{'range':'1002','files':m['sources']})
    atomic_json(run/'manifest.json',m);fragments=run/'source/scene-fragments';fragments.mkdir(parents=True,exist_ok=True)
    for scene in m['scenes']:
        sid=scene['id'];segment=next(x for x in m['segments'] if x['scene_id']==sid)
        (fragments/(sid+'.html')).write_text((fixture/'scene.html').read_text().replace('scene-dm-',sid+'-'))
        motion=json.loads((fixture/'scene.motion.json').read_text())
        for item in motion:item['target']=item['target'].replace('scene-dm-',sid+'-');item['segment_id']=segment['id']
        atomic_json(fragments/(sid+'.motion.json'),motion)
    evidence=run/'source/numeric-states.json';atomic_json(evidence,{'tail_ua':100,'left_ua':60,'right_ua':40,'delta_ua':10,'pixel_per_ua':10,'final_widths':[600,400]})
    review=write_circuit_review(run,m);review['evidence']=[{'path':'source/numeric-states.json','sha256':file_hash(evidence)}]
    reasons={'model':'Synthetic ideal MOS small-signal current split, not a measured device simulation.','topology':'Bars explicitly labeled numeric display; no claim to show circuit wiring.','polarity':'Left +10 and right −10 μA preserve the defined input direction.','derivation':'Independent arithmetic: 50+10=60, 50−10=40, 60+40=100.','assumptions':'Matched saturated MOS, ideal constant tail and small differential input stated.','numeric-visual':'Initial widths 500 px times 1.2/.8 give 600/400 px; 10 px per μA matches 60/40.'}
    for scene in review['scenes']:
        for check in scene['checks']:check['reason']=reasons[check['domain']];check['locators']=['#ideal-mos']
    atomic_json(run/'source/circuit-review.json',review);require_circuit_review(run,m)
    audio=[]
    for s in m['segments']:
        path=pcm(run/'assets/voice'/(s['id']+'.wav'))
        audio.append({'id':s['id'],'path':path.relative_to(run).as_posix(),'samples':24000,'rate':24000,'sha256':file_hash(path)})
    atomic_json(run/'source/audio.json',{'voices':audio});t=build_timeline(m,audio);atomic_json(run/'source/timeline.json',t);write_subtitles(t,run)
    theme=snapshot_theme(ROOT/'.claude/skills/ec2-review-pack',run);stage_assets(Path(args.assets),run);parts=assemble(m,t,theme,run)
    backend=probe_backends(run);backend['hyperframes_entry']=args.hyperframes_entry
    rendered=render_parts(parts,run,backend);mux(rendered,audio,t,run/'review.mp4')
    results={'media':verify_media(run/'review.mp4',t),'audio':verify_audio(run,audio,t),'sync':verify_sync(run,audio,t),'source':check_sources(run,args.hyperframes_entry,timeout=180)}
    for name,result in results.items():atomic_json(run/('verification/'+name+'.json'),result)
    print(json.dumps({**{k:v['status'] for k,v in results.items()},'backend':backend},ensure_ascii=False,indent=2))
    return 0 if all(v['status']=='passed' for v in results.values()) else 1
if __name__=='__main__':raise SystemExit(main())
