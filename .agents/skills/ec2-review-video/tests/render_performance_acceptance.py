"""Real, opt-in local benchmark. Synthetic PCM/circuit fixture, no paid TTS or approvals."""
from pathlib import Path
import argparse,array,copy,json,math,os,shutil,subprocess,sys,time,wave
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from lib.cache import atomic_json,file_hash
from lib.composition import assemble,stage_assets
from lib.theme import snapshot_theme
from lib.timing import build_timeline,write_subtitles
from lib.render import cpu_backend,render_parts,mux,mux_with_receipt,write_render_receipt,command
from lib.render_options import default_render_options,detect_hardware
from lib.verify import verify_media,verify_sync,check_sources
from lib.subtitles import burn_subtitles

SKILL=Path(__file__).resolve().parents[1]
REPO=SKILL.parents[2]
def inventory(run):
    return {p.relative_to(run).as_posix():file_hash(p) for p in run.rglob('*') if p.is_file()}
def checked(args,**kwargs):
    r=command(args,**kwargs)
    if r.returncode:raise RuntimeError(r.stderr[-1500:])
    return r

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination',required=True);parser.add_argument('--hyperframes-entry',required=True)
    parser.add_argument('--motion-duration',type=float,default=.6)
    parser.add_argument('--workers',type=int,nargs='+',choices=(1,2,6),default=(1,2,6))
    args=parser.parse_args()
    if 6 not in args.workers or len(set(args.workers))!=len(args.workers):parser.error('workers must include 6 and cannot repeat')
    dest=Path(args.destination).resolve();entry=Path(args.hyperframes_entry).resolve()
    if dest.exists():raise ValueError('fresh destination required')
    if not entry.is_file():raise ValueError('HyperFrames missing')
    dest.mkdir(parents=True);fixture=dest/'fixture';fixture.mkdir()
    f=SKILL/'tests/fixtures/circuit-scene';m=json.loads((f/'manifest.json').read_text())
    second=copy.deepcopy(m['scenes'][0]);second['id']='scene-dm-b';second['visual']+=' (재확인)';m['scenes'].append(second)
    seg=copy.deepcopy(m['segments'][0]);seg.update(id='seg-dm-b',scene_id='scene-dm-b');m['segments'].append(seg)
    m['coverage_reviews'][0]['segment_ids'].append('seg-dm-b')
    frag=fixture/'source/scene-fragments';frag.mkdir(parents=True);audio=[]
    for sid,segid in [('scene-dm','seg-dm'),('scene-dm-b','seg-dm-b')]:
        (frag/(sid+'.html')).write_text((f/'scene.html').read_text().replace('scene-dm',sid))
        motions=json.loads((f/'scene.motion.json').read_text().replace('scene-dm',sid).replace('seg-dm',segid))
        for motion in motions:motion['duration_s']=args.motion_duration
        atomic_json(frag/(sid+'.motion.json'),motions)
        path=fixture/'assets/voice'/(segid+'.wav');path.parent.mkdir(parents=True,exist_ok=True)
        samples=681600 # 28.4 seconds + scene intro/gap/tail 1.6 = 30 seconds.
        signal=array.array('h',(int(2500*math.sin(i*2*math.pi*220/24000)) for i in range(samples)))
        if sys.byteorder!='little':signal.byteswap()
        with wave.open(str(path),'wb') as w:w.setparams((1,2,24000,0,'NONE','not compressed'));w.writeframes(signal.tobytes())
        audio.append(dict(id=segid,path=path.relative_to(fixture).as_posix(),samples=samples,rate=24000,sha256=file_hash(path)))
    atomic_json(fixture/'manifest.json',m);atomic_json(fixture/'source/audio.json',{'voices':audio})
    stage_assets(SKILL/'assets/runtime',fixture);theme=snapshot_theme(REPO/'.claude/skills/ec2-review-pack',fixture)
    timeline=build_timeline(m,audio);assert timeline['total_frames']==1800
    atomic_json(fixture/'source/timeline.json',timeline);write_subtitles(timeline,fixture)
    parts=assemble(m,timeline,theme,fixture)
    before=inventory(fixture);atomic_json(dest/'source-hashes-before.json',before)
    result=dict(fixture='existing MOS differential pair fixture, two scenes, synthetic 220Hz PCM; not a production narration benchmark',
                motion_duration=args.motion_duration,hardware=detect_hardware(),hyperframes=checked(['node',entry,'--version']).stdout.strip(),
                ffmpeg=checked(['ffmpeg','-version']).stdout.splitlines()[0],frames=1800,seconds=60,runs=[])
    for workers in args.workers:
        run=dest/f'workers-{workers}';shutil.copytree(fixture,run)
        options=default_render_options();options['workers']=workers;atomic_json(run/'source/render-options.json',options)
        backend=cpu_backend(entry,options);start=time.monotonic()
        rendered=render_parts(parts,run,backend);render_seconds=time.monotonic()-start
        receipt=mux_with_receipt(rendered,audio,timeline,run/'review.mp4',backend)
        elapsed=time.monotonic()-start
        media=verify_media(run/'review.mp4',timeline);sync=verify_sync(run,audio,timeline)
        assert media['status']==sync['status']=='passed',(media,sync)
        atomic_json(run/'verification/media.json',media);atomic_json(run/'verification/sync.json',sync)
        framefile=dest/f'workers-{workers}.framemd5'
        checked(['ffmpeg','-y','-v','error','-i',run/'review.mp4','-map','0:v:0','-f','framemd5',framefile],timeout=300)
        frames=[l for l in framefile.read_text().splitlines() if l and not l.startswith('#')];assert len(frames)==1800
        aac=dest/f'workers-{workers}.aac';checked(['ffmpeg','-y','-v','error','-i',run/'review.mp4','-map','0:a:0','-c:a','copy',aac])
        row=dict(workers=workers,render_seconds=render_seconds,render_and_mux_seconds=elapsed,
                 master_sha256=file_hash(run/'review.mp4'),pcm_sha256=file_hash(run/'work/mux/narration.wav'),
                 aac_sha256=file_hash(aac),framemd5_sha256=file_hash(framefile),receipt_sha256=file_hash(receipt))
        result['runs'].append(row);atomic_json(dest/'result.json',result)
        print(json.dumps(row),flush=True)
    for key in ('master_sha256','pcm_sha256','aac_sha256','framemd5_sha256'):
        assert len({r[key] for r in result['runs']})==1,key
    assert inventory(fixture)==before,'fixture modified'
    atomic_json(dest/'source-hashes-after.json',inventory(fixture))
    by_worker={row['workers']:row for row in result['runs']}
    if 2 in by_worker and 6 in by_worker:
        two,six=by_worker[2],by_worker[6]
        result['reduction_percent']=100*(1-six['render_and_mux_seconds']/two['render_and_mux_seconds'])
        result['six_faster_than_two']=six['render_and_mux_seconds']<two['render_and_mux_seconds']
    else:result['reduction_percent']=None
    # Correct output is an acceptance gate; performance is a measurement, not a doctored pass criterion.
    run=dest/'workers-6';source=check_sources(run,entry);atomic_json(run/'verification/source.json',source)
    assert source['status']=='passed',source
    captioned=dest/'captioned-workers-6.mp4';burn_subtitles(run/'review.mp4',run/'narration.srt',captioned)
    assert verify_media(captioned,timeline)['status']=='passed'
    for at in (0,1,15,30,31,59):
        checked(['ffmpeg','-y','-v','error','-ss',str(at),'-i',captioned,'-frames:v','1',dest/f'frame-{at}.png'])
    result.update(status='passed',source_checks=source['status'],captioned_sha256=file_hash(captioned),source_file_count=len(before))
    atomic_json(dest/'result.json',result);print(json.dumps(dict(status='passed',reduction_percent=result['reduction_percent'])),flush=True)
if __name__=='__main__':main()
