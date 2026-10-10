import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from _util import ROOT
from video import main

class CliTest(unittest.TestCase):
    def test_prepare_free_invalid_range_nonzero(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); p=root/'복습노트/0915'; p.mkdir(parents=True)
            (p/'정리노트_0915_test.md').write_text('수업 기준 32 ATP',encoding='utf-8')
            with patch('urllib.request.urlopen',side_effect=AssertionError('network forbidden')):
                self.assertEqual(main(['prepare','--repo',str(root),'0915']),0)
                self.assertNotEqual(main(['prepare','--repo',str(root),'0931']),0)
            runs=list((root/'복습영상/0915').iterdir())
            self.assertEqual(len(runs),1); self.assertTrue((runs[0]/'source/inputs.json').is_file())
    def test_resume_reports_next_step(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(main(['resume','--run',d]),0)
    def test_render_cannot_skip_changed_voice_stage(self):
        from _util import minimal_manifest
        from lib.cache import atomic_json
        from video import finish
        with tempfile.TemporaryDirectory() as d:
            run=Path(d)
            atomic_json(run/'manifest.json',minimal_manifest())
            atomic_json(run/'source/audio.json',{'voices':[]})
            atomic_json(run/'config.json',{'voice':'Aoede'})
            finish(run,'voice',[run/'source/audio.json'])
            atomic_json(run/'source/parts.json',{'parts':[]})
            finish(run,'composition',[run/'source/parts.json'])
            atomic_json(run/'config.json',{'voice':'Charon'})
            with patch('video.probe_backends',side_effect=AssertionError('stale render')):
                self.assertEqual(main(['render','--run',str(run),'--hyperframes-entry','unused']),1)

    def test_render_workers_is_render_and_revoice_only(self):
        from video import parser
        self.assertIn('--render-workers',parser()._subparsers._group_actions[0].choices['render'].format_help())
        for mode in ('render','revoice'):
            extra=['--source-run','old'] if mode=='revoice' else []
            self.assertEqual(parser().parse_args([mode,'--run','run','--render-workers','6',*extra]).render_workers,6)
        for argv in (['render','--run','r','--render-workers','7'],['tts','--run','r','--render-workers','2']):
            with self.assertRaises(SystemExit):parser().parse_args(argv)
    def test_render_saves_policy_before_recovery_without_changing_voice_config(self):
        import json
        from video import parser
        self.assertIn('--render-workers',parser()._subparsers._group_actions[0].choices['render'].format_help())
        from lib.state import RunStore
        with tempfile.TemporaryDirectory() as d:
            run=Path(d);seen=[]
            def recover(store):
                seen.append(json.loads((store.run/'source/render-options.json').read_text()))
            with patch.object(RunStore,'recover',recover):
                self.assertEqual(main(['render','--run',d,'--render-workers','3']),1)
            self.assertEqual(seen[0]['workers'],3)
            self.assertNotIn('render_workers',json.loads((run/'config.json').read_text()))

    def test_render_and_revoice_dispatch_cpu_policy_and_register_receipt(self):
        import json
        from _util import minimal_manifest
        from lib.cache import atomic_json
        from lib.timing import build_timeline
        from lib.state import RunStore
        for mode in ('render','revoice'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as d:
                run=Path(d)/'run';run.mkdir();old=Path(d)/'old';old.mkdir();m=minimal_manifest()
                audio=[dict(id='seg-atp',samples=24000,rate=24000,path='voice.wav')];timeline=build_timeline(m,audio)
                for base in (run,old):
                    atomic_json(base/'manifest.json',m);atomic_json(base/'source/theme.json',{})
                    atomic_json(base/'source/timeline.json',timeline);(base/'review.mp4').write_bytes(b'old')
                atomic_json(run/'source/audio.json',{'voices':audio});atomic_json(run/'source/parts.json',{'parts':[dict(id='scene-atp',entry='scene-atp.html',frames=78)]})
                capture=run/'renders/parts/scene-atp.mp4';capture.parent.mkdir(parents=True);capture.write_bytes(b'part')
                atomic_json(capture.with_suffix('.json'),{'args':['actual capture'],'frames':78})
                RunStore(run).save({'stages':{'composition':{'status':'passed'}}})
                seen=[]
                def render(parts,run,backend):seen.append(backend);return [capture]
                def fake_mux(parts,audio,t,destination):Path(destination).write_bytes(b'new-master')
                extra=['--source-run',str(old)] if mode=='revoice' else []
                with patch.object(RunStore,'recover',return_value='render'),patch('video.render_parts',side_effect=render),patch('lib.render.mux',side_effect=fake_mux),patch('video.probe_backends',side_effect=AssertionError('auto GPU probe forbidden')),patch('video.plan_revoice',return_value=[dict(scene_id='scene-atp',mode='rerender')]),patch('video.render_revoice',return_value=[capture]):
                    self.assertEqual(main([mode,'--run',str(run),'--hyperframes-entry','unused','--render-workers','6',*extra]),0)
                self.assertEqual(seen[0]['encoder'],'libx264');self.assertEqual(seen[0]['workers'],1);self.assertEqual(seen[0]['render_options']['workers'],6)
                state=RunStore(run).load();self.assertIn('verification/render-receipt.json',state['stages']['render']['output_hashes'])
                self.assertEqual(json.loads((run/'verification/render-receipt.json').read_text())['render_options']['workers'],6)

    def test_resume_legacy_run_does_not_create_options(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(main(['resume','--run',d]),0)
            self.assertFalse((Path(d)/'source/render-options.json').exists())

    def test_master_receipt_failure_preserves_previous_pair(self):
        from _util import minimal_manifest
        from lib.cache import atomic_json
        from lib.state import RunStore
        from lib.timing import build_timeline
        import lib.render as render
        with tempfile.TemporaryDirectory() as d:
            run=Path(d);m=minimal_manifest();audio=[dict(id='seg-atp',samples=24000,rate=24000,path='voice.wav')]
            atomic_json(run/'manifest.json',m);atomic_json(run/'source/audio.json',{'voices':audio});atomic_json(run/'source/parts.json',{'parts':[]})
            RunStore(run).save({'stages':{'composition':{'status':'passed'}}});(run/'review.mp4').write_bytes(b'old');atomic_json(run/'verification/render-receipt.json',{'old':True})
            def fake_mux(parts,audio,t,destination):Path(destination).write_bytes(b'new')
            with patch.object(RunStore,'recover',return_value='render'),patch('video.render_parts',return_value=[]),patch('lib.render.mux',side_effect=fake_mux),patch('video.mux',side_effect=fake_mux),patch('lib.render.atomic_json',side_effect=OSError('receipt failed')):
                self.assertEqual(main(['render','--run',str(run),'--hyperframes-entry','unused']),1)
            self.assertEqual((run/'review.mp4').read_bytes(),b'old');self.assertEqual(__import__('json').loads((run/'verification/render-receipt.json').read_text()),{'old':True})
