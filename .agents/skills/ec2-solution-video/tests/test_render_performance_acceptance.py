"""Opt-in real P10.72 comparison through the production renderer (no TTS)."""
from fixtures import *
import os,shutil,time
from unittest.mock import patch
from solution_video.media import render_master,probe,ffmpeg
from solution_video.render_options import default_render_options
from solution_video.util import read,write,file_hash,checked,local


def acceptance_inputs():
    names=['EC2_RENDER_FIXTURE','EC2_RENDER_ACCEPTANCE_DEST','EC2_HYPERFRAMES_ENTRY']
    if any(not os.environ.get(n) for n in names):
        raise AssertionError('opt-in requires '+', '.join(names))
    fixture,dest,entry=(Path(os.environ[n]).resolve() for n in names)
    if not fixture.is_dir() or not entry.is_file():raise AssertionError('fixture or pinned CLI missing')
    if dest==fixture or dest.is_relative_to(fixture) or fixture.is_relative_to(dest):
        raise AssertionError('acceptance destination must be outside fixture')
    if dest.exists() and any(dest.iterdir()):raise AssertionError('destination must be new or empty')
    timeline=read(fixture/'source/timeline.json')
    if timeline['total_frames']!=7220:raise AssertionError('P10.72 fixture must contain 7,220 frames')
    return fixture,dest,entry


class AcceptanceInputTests(Sandbox):
    def test_opt_in_missing_inputs_fail_before_rendering(self):
        with patch.dict(os.environ,{'EC2_RENDER_ACCEPTANCE':'1'},clear=True),patch('test_render_performance_acceptance.render_master',side_effect=AssertionError('render launched')):
            with self.assertRaisesRegex(AssertionError,'opt-in requires'):acceptance_inputs()
    def test_destination_inside_fixture_is_rejected_before_writes(self):
        entry=self.run/'cli.js';entry.write_text('')
        with patch.dict(os.environ,dict(EC2_RENDER_FIXTURE=str(self.run),EC2_RENDER_ACCEPTANCE_DEST=str(self.run/'output'),EC2_HYPERFRAMES_ENTRY=str(entry))):
            with self.assertRaisesRegex(AssertionError,'outside fixture'):acceptance_inputs()
        self.assertFalse((self.run/'output').exists())


@unittest.skipUnless(os.environ.get('EC2_RENDER_ACCEPTANCE')=='1','real render requires EC2_RENDER_ACCEPTANCE=1 and frozen fixture/destination/pinned CLI')
class RenderPerformanceAcceptance(unittest.TestCase):
    def test_p1072_worker_change_preserves_every_frame_and_pcm(self):
        fixture,dest,entry=acceptance_inputs()
        before={p.relative_to(fixture).as_posix():file_hash(p) for p in fixture.rglob('*') if p.is_file()}
        parts=read(fixture/'source/parts.json');timeline=read(fixture/'source/timeline.json');audio=read(fixture/'source/audio.json')['voices']
        dest.mkdir(parents=True,exist_ok=True);write(dest/'source-hashes-before.json',before)
        metrics=[];frames=[];wav_hashes=[];aac_hashes=[]
        try:
            # These boundaries must never be reached by the media-only acceptance.
            with patch('solution_video.review_adapter.generate_voice',side_effect=AssertionError('paid voice invoked')),patch('solution_video.publication.publish_batch',side_effect=AssertionError('publish invoked')):
                for workers in [2,6]:
                    run=dest/f'workers-{workers}';run.mkdir()
                    shutil.copytree(fixture/'composition',run/'composition')
                    for name in ['parts','timeline','audio']:write(run/'source'/f'{name}.json',read(fixture/'source'/f'{name}.json'))
                    for a in audio:
                        source=local(fixture,a['path']);target=local(run,a['path']);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
                    options=default_render_options(dict(platform='unknown'));options['workers']=workers
                    write(run/'source/render-options.json',options)
                    print(f'rendering workers={workers}',flush=True);start=time.perf_counter()
                    master=render_master(parts,timeline,audio,run,entry,render_options=options)
                    elapsed=time.perf_counter()-start
                    streams=probe(master)['streams'];video=next(s for s in streams if s['codec_type']=='video');voice=next(s for s in streams if s['codec_type']=='audio')
                    self.assertEqual((video['width'],video['height'],video['r_frame_rate'],int(video['nb_frames'])),(1920,1080,'30/1',7220))
                    self.assertEqual((int(voice['sample_rate']),voice['channels']),(24000,1))
                    receipt=read(run/'verification/render-receipt.json');self.assertEqual(receipt['options'],options);self.assertEqual(receipt['master_sha256'],file_hash(master))
                    for part,row in zip(parts,receipt['parts'],strict=True):
                        self.assertEqual(row['frames'],part['last_frame']-part['first_frame'])
                        self.assertEqual(row['output_sha256'],file_hash(run/'renders'/(part['key']+'.mp4')))
                        args=row['command'];self.assertEqual(args[args.index('--workers')+1],str(workers));self.assertIn('--experimental-fast-capture=false',args);self.assertNotIn('--gpu',args)
                    framemd5=dest/f'workers-{workers}.framemd5'
                    checked([ffmpeg(),'-v','error','-i',master,'-map','0:v:0','-f','framemd5',framemd5],timeout=300)
                    rows=[r for r in framemd5.read_text().splitlines() if r and not r.startswith('#')]
                    self.assertEqual(len(rows),7220);frames.append(rows)
                    wav_hashes.append(file_hash(run/'renders/narration.wav'))
                    aac=dest/f'workers-{workers}.aac';checked([ffmpeg(),'-v','error','-i',master,'-map','0:a:0','-c','copy','-f','adts',aac],timeout=300);aac_hashes.append(file_hash(aac))
                    metrics.append(dict(workers=workers,elapsed_seconds=elapsed,part_seconds=sum(r['elapsed_seconds'] for r in receipt['parts']),master_sha256=file_hash(master),narration_sha256=wav_hashes[-1],aac_sha256=aac_hashes[-1],frames=7220))
                    write(dest/'progress.json',dict(metrics=metrics));print(f'workers={workers}: {elapsed:.2f}s',flush=True)
            self.assertEqual(frames[0],frames[1]);self.assertEqual(wav_hashes[0],wav_hashes[1]);self.assertEqual(aac_hashes[0],aac_hashes[1])
            self.assertEqual(wav_hashes[0],file_hash(fixture/'renders/narration.wav'))
            write(dest/'result.json',dict(metrics=metrics,ratio_6_over_2=metrics[1]['elapsed_seconds']/metrics[0]['elapsed_seconds'],all_frames_equal=True,pcm_equal=True,aac_equal=True,paid_requests=0,published=False))
        finally:
            after={p.relative_to(fixture).as_posix():file_hash(p) for p in fixture.rglob('*') if p.is_file()}
            write(dest/'source-hashes-after.json',after);self.assertEqual(before,after)
