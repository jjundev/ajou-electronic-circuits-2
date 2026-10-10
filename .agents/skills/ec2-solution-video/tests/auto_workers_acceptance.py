"""Real P10.72 static/dynamic windows via render_master, without voice generation.

Uses frozen existing composition/PCM. Fresh destination only; the windowed
player clock is a test adapter, while PDF geometry and global timeline remain
unchanged. Timings are single observations, not an optimization guarantee.
"""
import argparse
import json
import re
from pathlib import Path
import shutil
import sys
import time
import wave
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from solution_video.media import render_master,ffmpeg,probe
from solution_video.render_options import default_render_options,worker_capacity
from solution_video.subtitles import burn_subtitles,write_srt
from solution_video.util import read,write,file_hash,checked,local,S

WINDOWS=[('static',0,900,2),('dynamic',6269,7169,6)]


def hashes(root,inputs_only=False):
    return {p.relative_to(root).as_posix():file_hash(p) for p in root.rglob('*') if p.is_file()
            and (not inputs_only or p.relative_to(root).parts[0] in ('composition','source','assets'))}


def pcm(path):
    with wave.open(str(path),'rb') as w:
        assert (w.getnchannels(),w.getsampwidth(),w.getframerate())==(1,2,24000)
        return w.readframes(w.getnframes())


def save_pcm(path,raw):
    path.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(path),'wb') as w:
        w.setparams((1,2,24000,0,'NONE',''));w.writeframes(raw)


def prepare_run(fixture,run,windows,workers):
    parts=[];segments=[];voices=[];offset=0;all_raw=b''
    original=pcm(fixture/'renders/narration.wav')
    for name,first,last,want in windows:
        parent=run/'composition'/name;shutil.copytree(fixture/'composition',parent)
        html=parent/'index.html';text=html.read_text();duration=(last-first)/30
        old=read(parent/'timeline.json')['total_frames']/30
        replacements=[(f'data-duration="{old}"',f'data-duration="{duration}"'),
                      ('const clock={frame:0};',f'const clock={{frame:{first}}};'),
                      ('{frame:0},{frame:T.total_frames,duration:T.total_frames/30',f'{{frame:{first}}},{{frame:{last},duration:{duration}'),
                      ('window.renderSolutionFrame(0);',f'window.renderSolutionFrame({first});')]
        for old_text,new_text in replacements:
            assert text.count(old_text)==1,(name,old_text)
            text=text.replace(old_text,new_text)
        html.write_text(text)
        parts.append(dict(key=name,entry=html.relative_to(run).as_posix(),first_frame=first,last_frame=last))
        raw=original[first*800*2:last*800*2];assert len(raw)==(last-first)*800*2
        all_raw+=raw;p=run/'assets/voice'/f'{name}.wav';save_pcm(p,raw)
        samples=len(raw)//2
        voices.append(dict(id=name,path=p.relative_to(run).as_posix(),samples=samples,rate=24000,sha256=file_hash(p)))
        segments.append(dict(id=name,start_sample=offset,end_sample=offset+samples))
        offset+=samples
    timeline=dict(rate=24000,fps=30,total_samples=offset,total_frames=offset//800,segments=segments)
    options=dict(default_render_options(),workers=workers)
    for name,value in [('parts',parts),('timeline',timeline),('audio',dict(voices=voices)),('render-options',options)]:
        write(run/'source'/f'{name}.json',value)
    return parts,timeline,voices,options,all_raw


def frame_hashes(master,dest):
    checked([ffmpeg(),'-v','error','-i',master,'-map','0:v:0','-f','framemd5',dest],timeout=300)
    return [row.rsplit(',',1)[1].strip() for row in dest.read_text().splitlines() if row and not row.startswith('#')]


def assert_media(path,frames):
    streams=probe(path)['streams']
    video=next(s for s in streams if s['codec_type']=='video')
    voice=next(s for s in streams if s['codec_type']=='audio')
    assert (video['width'],video['height'],video['r_frame_rate'],int(video['nb_frames']))==(1920,1080,'30/1',frames)
    assert (int(voice['sample_rate']),voice['channels'])==(24000,1)
    assert abs(float(video['duration'])-float(voice['duration']))<=1/30


def render_case(fixture,dest,entry,name,windows,workers):
    run=dest/name;parts,timeline,audio,options,expected_pcm=prepare_run(fixture,run,windows,workers)
    before=hashes(run,True);write(dest/(name+'-inputs-before.json'),before)
    print('rendering '+name,flush=True);start=time.perf_counter()
    master=render_master(parts,timeline,audio,run,entry,render_options=options)
    elapsed=time.perf_counter()-start
    after=hashes(run,True);write(dest/(name+'-inputs-after.json'),after);assert before==after
    receipt=read(run/'verification/render-receipt.json');assert receipt['options']==options
    assert receipt['master_sha256']==file_hash(master)
    selections=[]
    for part,row,window in zip(parts,receipt['parts'],windows,strict=True):
        want=window[3] if workers=='auto' else workers;selection=row['worker_selection'];selections.append(selection)
        assert selection['workers']==want
        args=row['command'];assert args[args.index('--workers')+1]==str(want)
        assert '--experimental-fast-capture=false' in args and '--gpu' not in args
        assert row['frames']==900 and row['output_sha256']==file_hash(run/'renders'/(part['key']+'.mp4'))
        log=(run/'renders'/(part['key']+'.log')).read_text()
        logged_workers=re.findall(r'workerCount[\"\s:]+(\d+)',log)
        assert logged_workers and set(logged_workers)=={str(want)},logged_workers
        assert 'Metal' in log
    assert pcm(run/'renders/narration.wav')==expected_pcm
    assert_media(master,timeline['total_frames'])
    decoded=frame_hashes(master,dest/(name+'.framemd5'));assert len(decoded)==timeline['total_frames']
    aac=dest/(name+'.aac');checked([ffmpeg(),'-v','error','-i',master,'-map','0:a:0','-c','copy','-f','adts',aac],timeout=300)
    row=dict(case=name,elapsed_seconds=elapsed,part_seconds=sum(p['elapsed_seconds'] for p in receipt['parts']),workers=[s['workers'] for s in selections],selections=selections,frames=len(decoded),master_sha256=file_hash(master),pcm_sha256=file_hash(run/'renders/narration.wav'),aac_sha256=file_hash(aac),inputs_unchanged=True)
    print(name+f': {elapsed:.2f}s workers='+str(row['workers']),flush=True)
    return row,decoded


def run_acceptance(fixture,dest,entry):
    assert fixture.is_dir() and entry.is_file()
    assert dest!=fixture and not dest.is_relative_to(fixture) and not fixture.is_relative_to(dest)
    assert not dest.exists(),'destination must be fresh'
    assert worker_capacity()==6,'this acceptance requires verified M5 host'
    assert read(fixture/'composition/timeline.json')['total_frames']==7220
    dest.mkdir(parents=True);before=hashes(fixture);write(dest/'fixture-before.json',before)
    results=[];decoded={}
    try:
        with patch('solution_video.review_adapter.generate_voice',side_effect=AssertionError('paid request forbidden')),patch('solution_video.publication.publish_batch',side_effect=AssertionError('production publication forbidden')):
            for window in WINDOWS:
                group=[]
                for workers in [2,6,'auto']:
                    name=window[0]+'-'+str(workers)
                    row,frames=render_case(fixture,dest,entry,name,[window],workers)
                    results.append(row);group.append(row);decoded[name]=frames
                    write(dest/'progress.json',dict(results=results))
                assert decoded[group[0]['case']]==decoded[group[1]['case']]==decoded[group[2]['case']]
                for key in ['master_sha256','pcm_sha256','aac_sha256']:
                    assert len({r[key] for r in group})==1,(window[0],key)
            row,frames=render_case(fixture,dest,entry,'mixed-auto',WINDOWS,'auto');results.append(row)
            assert frames==decoded['static-2']+decoded['dynamic-6']
            # Independent mux of the fixed controls gives the mixed reference.
            ref=dest/'mixed-reference';ref.mkdir()
            for index,name in enumerate(['static-2','dynamic-6']):shutil.copyfile(dest/name/'renders'/('static.mp4' if index==0 else 'dynamic.mp4'),ref/f'part-{index}.mp4')
            (ref/'concat.txt').write_text("file 'part-0.mp4'\nfile 'part-1.mp4'")
            save_pcm(ref/'narration.wav',pcm(dest/'static-2/renders/narration.wav')+pcm(dest/'dynamic-6/renders/narration.wav'))
            checked([ffmpeg(),'-y','-v','error','-f','concat','-safe','1','-i','concat.txt','-i','narration.wav','-c:v','copy','-c:a','aac','-b:a','128k','-movflags','+faststart',ref/'master.mp4'],cwd=ref,timeout=300)
            assert file_hash(ref/'master.mp4')==row['master_sha256']
            # Reuse original caption text, redistributing it inside clipped test windows.
            source=read(fixture/'source/timeline.json');caption_segments=[];offset=0
            for _,first,last,_ in WINDOWS:
                for segment in source['segments']:
                    left=max(first*800,segment['start_sample']);right=min(last*800,segment['start_sample']+segment['voice_samples'])
                    if right>left:caption_segments.append(dict(segment,start_sample=offset+left-first*800,end_sample=offset+right-first*800,voice_samples=right-left))
                offset+=(last-first)*800
            srt=write_srt(dict(rate=24000,segments=caption_segments),dest/'mixed-captions.srt')
            final=burn_subtitles(dest/'mixed-auto/renders/master.mp4',srt,dest/'mixed-captioned.mp4',S.parent/'ec2-review-video/assets/fonts/Pretendard-Bold.ttf')
            assert_media(final,1800)
            checked([ffmpeg(),'-v','error','-i',final,'-f','null','-'],timeout=300)
            for at in [2,45,59]:checked([ffmpeg(),'-v','error','-ss',str(at),'-i',final,'-frames:v','1',dest/f'frame-{at}.png'],timeout=60)
            write(dest/'result.json',dict(status='passed',results=results,all_frames_equal=True,pcm_equal=True,aac_equal=True,mixed_master_equal=True,captioned_decode_passed=True,paid_requests=0,published=False))
    finally:
        after=hashes(fixture);write(dest/'fixture-after.json',after);assert before==after,'frozen fixture changed'


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--fixture',type=Path,required=True);parser.add_argument('--destination',type=Path,required=True);parser.add_argument('--hyperframes-entry',type=Path,required=True)
    args=parser.parse_args();run_acceptance(args.fixture.resolve(),args.destination.resolve(),args.hyperframes_entry.resolve())
