"""Wrong motion intervals, overlap, or fallback would select the wrong worker count."""
from fixtures import *
import copy
from solution_video.util import write,file_hash
from solution_video.render_options import resolve_part_workers
from test_render_options import M5,AUTO,OPTIONS


def motion_fixture(run,**changes):
    t=dict(fps=30,rate=24000,total_frames=900,total_samples=720000,
           segments=[dict(kind='write',start_sample=0,end_sample=720000)],
           events=[],cameras=[dict(at_frame=0,viewbox=[0,0,100,100])],
           writing=dict(mode='pencil'),writing_spans=[])
    t.update(changes)
    p=run/'composition/index.html';p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text('<script>window.solutionTimeline='+json.dumps(t)+';window.solutionGlyphs={};</script>')
    write(p.parent/'timeline.json',t)
    return dict(entry='composition/index.html',key='solution',first_frame=0,last_frame=900)


def span(left,right,kind='draw',**extras):
    return dict(start_frame=left,end_frame=right,kind=kind,**extras)


class WorkloadTests(Sandbox):
    def choose(self,part):return resolve_part_workers(self.run,part,AUTO,hardware=M5)
    def test_pencil_static_and_dynamic_select_two_and_six(self):
        for end,want in [(18,2),(450,2),(451,6),(720,6)]:
            with self.subTest(end=end):
                part=motion_fixture(self.run,writing_spans=[span(0,end)])
                before={p:file_hash(p) for p in self.run.rglob('*') if p.is_file()}
                result=self.choose(part);self.assertEqual(result['workers'],want)
                self.assertAlmostEqual(result['motion_ratio'],end/900)
                self.assertEqual(before,{p:file_hash(p) for p in before})
    def test_overlap_union_camera_and_annotation_hide(self):
        part=motion_fixture(self.run,writing_spans=[span(0,300),span(100,400,'move')],
             cameras=[dict(at_frame=0,viewbox=[0,0,100,100]),dict(at_frame=390,transition_frames=80,viewbox=[0,0,50,50]),dict(at_frame=800,transition_frames=90,viewbox=[0,0,50,50])],
             teaching=dict(spans=[span(450,650,hide_frame=480)]))
        result=self.choose(part);self.assertEqual(result['workers'],6)
        self.assertEqual(result['animated_frames'],480)
    def test_part_window_clips_global_motion(self):
        part=motion_fixture(self.run,total_frames=1800,total_samples=1440000,segments=[],writing_spans=[span(800,1500)])
        part.update(first_frame=900,last_frame=1800)
        result=self.choose(part);self.assertEqual(result['workers'],6);self.assertEqual(result['animated_frames'],600)
    def test_typing_counts_only_active_reveal_cadence(self):
        part=motion_fixture(self.run,writing=dict(mode='typing'),events=[dict(frame=10),dict(frame=720)])
        result=self.choose(part);self.assertEqual(result['workers'],6);self.assertEqual(result['animated_frames'],721)
        part=motion_fixture(self.run,writing=dict(mode='typing'),events=[dict(frame=10),dict(frame=100)])
        self.assertEqual(self.choose(part)['workers'],2)
    def test_missing_typing_mode_is_legacy_typing(self):
        part=motion_fixture(self.run,writing=None,events=[dict(frame=10),dict(frame=720)])
        self.assertEqual(self.choose(part)['workers'],6)
    def test_short_host_and_explicit_override(self):
        part=motion_fixture(self.run,writing_spans=[span(0,720)])
        short=dict(part,last_frame=899);self.assertEqual(self.choose(short)['workers'],2)
        self.assertEqual(resolve_part_workers(self.run,part,AUTO,hardware={})['workers'],2)
        for workers in range(1,7):
            self.assertEqual(resolve_part_workers(self.run,part,dict(OPTIONS,workers=workers),hardware={})['workers'],workers)
    def test_missing_metadata_is_read_only_safe_fallback(self):
        part=motion_fixture(self.run);(self.run/'composition/timeline.json').unlink()
        self.assertEqual(self.choose(part)['reason'],'missing_motion_metadata')
        self.assertFalse((self.run/'composition/timeline.json').exists())
        part=motion_fixture(self.run);(self.run/'composition/index.html').write_text('legacy no embedded metadata')
        self.assertEqual(self.choose(part)['workers'],2)
    def test_corrupt_and_mismatched_metadata_fail(self):
        cases=[dict(total_frames=True),dict(total_samples=1),dict(fps=24),dict(writing_spans=None),dict(writing_spans=[span(0,901)]),dict(writing_spans=[span(0,2.5)]),dict(writing_spans=[span(2,1)]),dict(writing_spans=[span(0,10,'hold')]),dict(cameras=[dict(at_frame=0,viewbox=[0,0,float('nan'),100])]),dict(teaching=dict(spans=[span(0,10,hide_frame=901)])),dict(events=[dict(frame=901)])]
        for change in cases:
            with self.subTest(change=change):
                part=motion_fixture(self.run,**change)
                with self.assertRaises(ValueError):self.choose(part)
        part=motion_fixture(self.run);write(self.run/'composition/timeline.json',dict(fps=30))
        with self.assertRaises(ValueError):self.choose(part)
        part=motion_fixture(self.run);(self.run/'composition/timeline.json').write_text('{broken')
        (self.run/'composition/index.html').write_text('no metadata')
        with self.assertRaises(ValueError):self.choose(part)
    def test_outside_run_entry_is_rejected(self):
        part=motion_fixture(self.run);part['entry']='../index.html'
        with self.assertRaises(ValueError):self.choose(part)
    def test_annotation_spaces_are_valid_and_do_not_count_as_motion(self):
        part=motion_fixture(self.run,teaching=dict(spans=[span(0,720,'space',hide_frame=900)]))
        result=self.choose(part);self.assertEqual(result['workers'],2);self.assertEqual(result['animated_frames'],0)
    def test_missing_metadata_does_not_mask_present_corruption(self):
        part=motion_fixture(self.run);write(self.run/'composition/timeline.json',[])
        (self.run/'composition/index.html').write_text('legacy missing timeline')
        with self.assertRaises(ValueError):self.choose(part)
        for change in [dict(cameras=[dict(at_frame=-1,viewbox=[0,0,100,100])]),dict(teaching=dict(spans=[span(0,901,hide_frame=900)]))]:
            part=motion_fixture(self.run,**change)
            p=self.run/'composition/timeline.json';t=json.loads(p.read_text());del t['writing_spans'];write(p,t)
            (self.run/'composition/index.html').write_text('window.solutionTimeline='+json.dumps(t)+';')
            with self.subTest(change=change),self.assertRaises(ValueError):self.choose(part)
    def test_present_null_timeline_is_corruption(self):
        part=motion_fixture(self.run);write(self.run/'composition/timeline.json',None)
        with self.assertRaises(ValueError):self.choose(part)
        part=motion_fixture(self.run);(self.run/'composition/index.html').write_text('window.solutionTimeline=null;')
        with self.assertRaises(ValueError):self.choose(part)
