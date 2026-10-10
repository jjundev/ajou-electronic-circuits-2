"""Opt-in real auto-worker validation using previously frozen review fixtures."""
from pathlib import Path
import argparse,json,shutil,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from lib.cache import atomic_json,file_hash
from lib.render import cpu_backend,render_parts,mux,mux_with_receipt,command
from lib.render_options import default_render_options,resolve_scene_workers,detect_hardware
from lib.verify import verify_media,verify_sync,check_sources
from lib.subtitles import burn_subtitles

def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def inventory(run):return {p.relative_to(run).as_posix():file_hash(p) for p in run.rglob('*') if p.is_file()}
def checked(args):
    r=command(args,timeout=300)
    if r.returncode:raise RuntimeError(r.stderr[-1000:])
    return r

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source-root',required=True);parser.add_argument('--destination',required=True);parser.add_argument('--hyperframes-entry',required=True);args=parser.parse_args()
    source=Path(args.source_root).resolve();dest=Path(args.destination).resolve();entry=Path(args.hyperframes_entry).resolve()
    if dest.exists():raise ValueError('fresh destination required')
    sources=dict(static=source/'20261010-review-policy-static-final',dynamic=source/'20261010-review-policy-motion-safety-final')
    original={name:inventory(root/'fixture') for name,root in sources.items()}
    if not entry.is_file():raise ValueError('HyperFrames missing')
    dest.mkdir(parents=True);host=detect_hardware();result=dict(hardware=host,policy='authored motion union >50%, scene >=900frames, verified M5; otherwise2',cases=[])
    for name,expected in [('static',[2,2]),('dynamic',[6,6]),('mixed',[2,6])]:
        run=dest/name;fixture=sources['dynamic' if name=='dynamic' else 'static']/'fixture';shutil.copytree(fixture,run)
        parts=read(run/'source/parts.json')['parts']
        if name=='mixed':
            sid=parts[1]['id'];dynamic=sources['dynamic']/'fixture'
            for relative in [sid+'.html','source/compositions/'+sid+'.html','source/scene-fragments/'+sid+'.motion.json']:
                shutil.copyfile(dynamic/relative,run/relative)
            parts[1]=read(dynamic/'source/parts.json')['parts'][1];atomic_json(run/'source/parts.json',{'parts':parts})
        options=default_render_options();assert options['workers']=='auto';atomic_json(run/'source/render-options.json',options)
        before=inventory(run);atomic_json(dest/(name+'-source-hashes-before.json'),before)
        selections=[resolve_scene_workers(run,p,options,hardware=host) for p in parts]
        assert [s['workers'] for s in selections]==expected,selections
        backend=cpu_backend(entry,options);audio=read(run/'source/audio.json')['voices'];timeline=read(run/'source/timeline.json');start=time.monotonic()
        rendered=render_parts(parts,run,backend);receipt=mux_with_receipt(rendered,audio,timeline,run/'review.mp4',backend);elapsed=time.monotonic()-start
        records=read(receipt)['parts'];assert [r['worker_selection']['workers'] for r in records]==expected
        assert [int(r['args'][r['args'].index('--workers')+1]) for r in records]==expected
        media=verify_media(run/'review.mp4',timeline);sync=verify_sync(run,audio,timeline);assert media['status']==sync['status']=='passed'
        atomic_json(run/'verification/media.json',media);atomic_json(run/'verification/sync.json',sync)
        if name=='mixed':
            reference=dest/'mixed-reference';shutil.copytree(fixture,reference)
            reference_parts=[sources['static']/'workers-2/renders/parts'/ (parts[0]['id']+'.mp4'),sources['dynamic']/'workers-6/renders/parts'/(parts[1]['id']+'.mp4')]
            mux(reference_parts,audio,timeline,reference/'review.mp4');reference_video=reference/'review.mp4'
        else:reference_video=sources[name]/('workers-2/review.mp4' if name=='static' else 'workers-6/review.mp4')
        assert file_hash(run/'review.mp4')==file_hash(reference_video),'auto output differs from fixed reference'
        framefile=dest/(name+'.framemd5');checked(['ffmpeg','-y','-v','error','-i',run/'review.mp4','-map','0:v:0','-f','framemd5',framefile])
        assert len([l for l in framefile.read_text().splitlines() if l and not l.startswith('#')])==1800
        after={relative:file_hash(run/relative) for relative in before};assert before==after,'actual worker sources changed'
        atomic_json(dest/(name+'-source-hashes-after.json'),after)
        row=dict(case=name,workers=expected,selections=selections,elapsed_seconds=elapsed,master_sha256=file_hash(run/'review.mp4'),reference_sha256=file_hash(reference_video),pcm_sha256=file_hash(run/'work/mux/narration.wav'),frames=1800,source_files=len(before))
        result['cases'].append(row);atomic_json(dest/'result.json',result);print(json.dumps(row),flush=True)
    run=dest/'mixed';source_check=check_sources(run,entry);assert source_check['status']=='passed';atomic_json(run/'verification/source.json',source_check)
    captioned=dest/'mixed-captioned.mp4';burn_subtitles(run/'review.mp4',run/'narration.srt',captioned);assert verify_media(captioned,read(run/'source/timeline.json'))['status']=='passed'
    for at in [1,31,59]:checked(['ffmpeg','-y','-v','error','-ss',str(at),'-i',captioned,'-frames:v','1',dest/f'frame-{at}.png'])
    for name,hashes in original.items():assert inventory(sources[name]/'fixture')==hashes,'frozen fixture changed'
    result['status']='passed';atomic_json(dest/'result.json',result);print('AUTO ACCEPTANCE PASSED',flush=True)
if __name__=='__main__':main()
