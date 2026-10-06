from pathlib import Path
import json,wave
from .util import digest,file_hash,read,write,command,local
from .media import probe,ffmpeg,source_checks
from .manifest import validate_manifest

def verification_fingerprint(run):
    run=Path(run)
    roots=['source','layers','composition','renders']
    files={p.relative_to(run).as_posix():file_hash(p) for root in roots for p in (run/root).rglob('*') if p.is_file() and p.suffix not in ('.log','.pending') and p.name!='config.env'}
    files['tool']=digest({p.name:file_hash(p) for p in (Path(__file__).parent).glob('*.py')})
    return digest(files)

def gate_valid(run,layers,g):
    try:
        return (g['input_hash']==digest(layers) and all(g[k]==0 for k in ['pixel_diff','non_target_diff','hidden_leaks'])
          and bool(g.get('evidence_hashes')) and set(g['evidence'])==set(g['evidence_hashes'])
          and all(local(run,p).is_file() and file_hash(local(run,p))==sha for p,sha in g['evidence_hashes'].items())
          and all(file_hash(Path(layers[k]))==g['source_hashes'][k] for k in ['original_svg','animated_svg','reference_png']))
    except (OSError,KeyError,ValueError): return False

def verify_run(run,hyperframes_entry):
    run=Path(run); checks={}; evidence=[]; final=run/'renders/final.mp4'; h=verification_fingerprint(run)
    def check(name,fn):
        try:
            ok=fn(); checks[name]={'status':'passed' if ok else 'unverified'}
        except Exception as ex: checks[name]={'status':'unverified','reason':str(ex)[:500]}
    def content():
        validate_manifest(read(run/'source/manifest.json'),read(run/'layers/layers.json'),read(run/'source/coverage.json'),read(run/'source/circuit-review.json')); return True
    check('content',content)
    def gate():
        return gate_valid(run,read(run/'layers/layers.json'),read(run/'verification/gate.json'))
    check('original_svg',gate)
    check('hyperframes',lambda:bool(source_checks(read(run/'source/parts.json'),run,hyperframes_entry)))
    def media():
        t=read(run/'source/timeline.json'); data=probe(final); streams=data['streams']; v=next(s for s in streams if s['codec_type']=='video'); a=next(s for s in streams if s['codec_type']=='audio')
        if (v['width'],v['height'],v['avg_frame_rate'],int(v['nb_frames']),int(a['sample_rate']))!=(1920,1080,'30/1',t['total_frames'],24000): return False
        if abs(float(v['duration'])-float(a['duration']))>1/30: return False
        if command([ffmpeg(),'-v','error','-i',final,'-f','null','-'],timeout=1800).returncode: return False
        for rec in read(run/'source/audio.json')['voices']:
            p=local(run,rec['path'])
            if file_hash(p)!=rec['sha256']: return False
            with wave.open(str(p),'rb') as f:
                if (f.getnchannels(),f.getsampwidth(),f.getframerate(),f.getnframes())!=(1,2,24000,rec['samples']): return False
        return True
    check('final_media',media)
    def captions():
        from PIL import Image,ImageChops
        import io
        t=read(run/'source/timeline.json'); srt=run/'renders/captions.srt'
        if not srt.is_file() or not (run/'renders/master.mp4').is_file(): return False
        # Compare captioned/master at each caption midpoint; lossy compression tolerance.
        import re,subprocess
        ranges=re.findall(r'(\d\d):(\d\d):(\d\d),(\d{3}) --> (\d\d):(\d\d):(\d\d),(\d{3})',srt.read_text())
        if not ranges: return False
        def sec(parts): return int(parts[0])*3600+int(parts[1])*60+int(parts[2])+int(parts[3])/1000
        for row in ranges:
            at=(sec(row[:4])+sec(row[4:]))/2; pics=[]
            for p in [run/'renders/master.mp4',final]:
                r=subprocess.run([ffmpeg(),'-v','error','-ss',str(at),'-i',str(p),'-frames:v','1','-f','image2pipe','-vcodec','png','-'],capture_output=True,timeout=60)
                if r.returncode: return False
                pics.append(Image.open(io.BytesIO(r.stdout)).convert('RGB'))
            diff=ImageChops.difference(*pics); bbox=diff.crop((0,900,1920,1080)).getbbox()
            if not bbox: return False
            # PDF pixels may differ slightly after CRF encoding; reject caption-sized dark blocks above strip.
            from PIL import ImageStat
            if max(ImageStat.Stat(diff.crop((0,0,1920,900))).mean)>3: return False
        return True
    check('captions',captions)
    for kind in ['audio','visual']:
        def review(k=kind):
            r=read(run/'verification'/f'{k}-review.json')
            if r.get('status')!='passed' or r.get('input_hash')!=h or not r.get('notes') or not r.get('evidence'): return False
            if k=='audio' and r.get('mode')!='live-listened': return False
            return all(local(run,p).is_file() and file_hash(local(run,p))==sha for p,sha in r['evidence'].items())
        check(kind+'_meaning',review)
    complete=all(v['status']=='passed' for v in checks.values())
    report=dict(complete=complete,input_hash=h,checks=checks,evidence=evidence,final_sha256=file_hash(final) if final.is_file() else None,review_hashes={p.relative_to(run).as_posix():file_hash(p) for p in (run/'verification').glob('*-review.json')},live_audio='verified' if checks['audio_meaning']['status']=='passed' else 'unverified')
    write(run/'verification/report.json',report); return report
