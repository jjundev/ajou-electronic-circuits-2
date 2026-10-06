from fixtures import *
import importlib.util
spec=importlib.util.spec_from_file_location('solution_cli',S/'scripts/video.py'); cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
class CLITests(Sandbox):
    def test_review_gate_and_zero_paid_prepare(self):
        self.assertEqual(cli.main(['prepare','0931','--repo',str(REPO)]),1)
        self.assertEqual(cli.main(['tts','--run',str(self.run)]),0)
        self.assertFalse((self.run/'assets/voice').exists())
    def test_stale_prerequisite_blocks_assemble(self):
        from unittest.mock import patch
        from test_manifest import example
        from types import SimpleNamespace
        m,l,c,r=example()
        for p in ['source/manifest.json','layers/layers.json','source/coverage.json','source/circuit-review.json']:
            (self.run/p).parent.mkdir(parents=True,exist_ok=True);(self.run/p).write_text('{}')
        (self.run/'state.json').write_text('{"stages":{}}')
        with patch.object(cli,'_load',return_value=(m,l,c,r)),patch.object(cli,'_gate'),patch.object(cli,'recover_run',return_value='voice'):
            with self.assertRaises(ValueError): cli.run_stage('assemble',self.run,SimpleNamespace(runtime='missing'))
    def test_batch_review_approval_is_current_and_paid_zero_until_approved(self):
        from unittest.mock import patch
        from test_manifest import example
        from types import SimpleNamespace
        from solution_video.util import write
        from solution_video.review_adapter import default_config
        batch=self.run/'batch';run=batch/'videos/one';run.mkdir(parents=True)
        m,l,c,r=example()
        for name,data in [('source/manifest.json',m),('layers/layers.json',l),('source/coverage.json',c),('source/circuit-review.json',r),('source/config.json',default_config()),('run.json',{'batch':str(batch),'review':True})]:write(run/name,data)
        write(batch/'videos/failed/source/prepare-error.json',{'reason':'unsupported'})
        write(batch/'batch.json',{'items':[{'id':m['problem_id'],'run':'videos/one'},{'id':'bad','run':'videos/failed','status':'failed'}]})
        args=SimpleNamespace(config=None,env_file=None,approve_review=False)
        with patch.object(cli,'_gate'),patch.object(cli,'generate_voice') as voice:
            result=cli.run_stage('tts',run,args);self.assertEqual(result['status'],'awaiting-review');voice.assert_not_called();self.assertEqual(result['paid_requests'],0)
        args.approve_review=True
        audio=[make_audio(s['id'],24000,run) for s in m['segments']];write(run/'source/audio.json',{'voices':audio})
        with patch.object(cli,'_gate'),patch.object(cli,'generate_voice',return_value=audio):
            result=cli.run_stage('tts',run,args,transport=lambda p:{});self.assertEqual(result['status'],'passed')
        args.approve_review=False;m['segments'][0]['text']='새로운 문제 설명';h=cli.content_fingerprint(m,l,c);c['input_hash']=r['input_hash']=h
        for name,data in [('manifest',m),('coverage',c),('circuit-review',r)]:write(run/'source'/(name+'.json'),data)
        # This test isolates review hash; stage invalidation is tested separately.
        with patch.object(cli,'_gate'),patch.object(cli,'recover_run',return_value='voice'),patch.object(cli,'generate_voice') as voice:
            result=cli.run_stage('tts',run,args);self.assertEqual(result['status'],'awaiting-review');voice.assert_not_called()
    def test_export_failure_preserves_other_prepared_items(self):
        from unittest.mock import patch
        from solution_video.contracts import ExtractionError
        from solution_video.sources import discover
        from solution_video.util import read
        pairs=discover(REPO,'1002',['E10.11','E10.13']); original=cli.export_page
        def export(pdf,index,dest):
            if index==1:raise ExtractionError('injected unsupported solution')
            return original(pdf,index,dest)
        with patch.object(cli,'discover',return_value=pairs),patch.object(cli,'export_page',side_effect=export):
            batch=cli.prepare_batch(self.run,'1002',None,False)
        data=read(batch/'batch.json');self.assertEqual(len(data['items']),2)
        self.assertEqual(data['items'][0]['status'],'failed');self.assertEqual(data['items'][1]['status'],'author-required')
        self.assertTrue((batch/data['items'][1]['run']/'layers/candidates.json').exists())
