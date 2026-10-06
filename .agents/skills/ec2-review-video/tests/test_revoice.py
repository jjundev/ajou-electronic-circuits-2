import unittest
from _util import ROOT
from lib.revoice import plan_revoice

class RevoiceTest(unittest.TestCase):
    def test_extreme_zero_and_hash(self):
        old={'fps':30,'windows':[{'id':'a-1','scene_id':'a','first_frame':0,'last_frame':30}]}
        for finish in (0,90):
            new={'fps':30,'windows':[{'id':'a-1','scene_id':'a','first_frame':0,'last_frame':finish}]}
            self.assertEqual(plan_revoice(old,new,'hash',{'a'})[0]['mode'],'rerender')
        a=plan_revoice(old,old,'a',{'a'}); b=plan_revoice(old,old,'b',{'a'})
        self.assertNotEqual(a[0]['key'],b[0]['key'])
    def test_mismatch_and_overlap(self):
        old={'fps':30,'windows':[{'id':'a','scene_id':'a','first_frame':0,'last_frame':30}]}
        with self.assertRaises(ValueError): plan_revoice(old,{'fps':30,'windows':[]},'a',{'a'})
    def test_picture_dependency_change_invalidates_retime(self):
        import tempfile
        from pathlib import Path
        from lib.revoice import picture_fingerprint
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); p=root/'assets/diagram.svg'; p.parent.mkdir()
            p.write_text('<svg/>')
            a=picture_fingerprint(root,'scene-a')
            p.write_text('<svg><rect/></svg>')
            self.assertNotEqual(a,picture_fingerprint(root,'scene-a'))
    def test_revoice_prepare_preserves_original_and_snapshots(self):
        import tempfile,json
        from pathlib import Path
        from video import main
        from _util import minimal_manifest,write_circuit_review,pcm
        from lib.cache import atomic_json,file_hash
        from lib.circuit import require_circuit_review
        with tempfile.TemporaryDirectory() as d:
            repo=Path(d);old=repo/'old';old.mkdir();m=minimal_manifest()
            atomic_json(old/'manifest.json',m);atomic_json(old/'source/inputs.json',{'range':'0915','files':[]})
            pcm(old/'assets/voice/old.wav');(old/'review.mp4').write_bytes(b'old-master')
            write_circuit_review(old,m);h=file_hash(old/'review.mp4')
            self.assertEqual(main(['prepare','--repo',d,'--from-run',str(old),'--voice','Charon']),0)
            new=next((repo/'복습영상/0915').iterdir())
            require_circuit_review(new,m)
            self.assertEqual(file_hash(old/'review.mp4'),h)
            self.assertEqual((new/'source/circuit-review.json').read_bytes(),(old/'source/circuit-review.json').read_bytes())
            self.assertEqual(json.loads((new/'config.json').read_text())['voice'],'Charon')
    def test_revoice_from_batch_is_an_independent_checked_run(self):
        import tempfile,json
        from pathlib import Path
        from video import main
        from lib.cache import file_hash
        from lib.batch import prepare_set,budget_path
        from test_selection import fixture,verified_fixture,read_batch
        with tempfile.TemporaryDirectory() as d:
            repo=Path(d);_,plan=fixture(repo,1);batch=prepare_set(repo,'1001',plan,{})
            old=batch/read_batch(batch)['clips'][0]['run'];verified_fixture(old,plan,plan['clips'][0]);before=file_hash(old/'review.mp4')
            from _util import pcm
            pcm(old/'assets/voice/old.wav')
            self.assertEqual(main(['prepare','--repo',d,'--from-run',str(old),'--voice','Charon']),0)
            new=next(p for p in (repo/'복습영상/1001').iterdir() if p.name!='1001_제작자료')
            self.assertEqual(main(['check','--run',str(new)]),0)
            self.assertEqual(budget_path(new),new.resolve()/'cost-ledger.json')
            self.assertEqual(file_hash(old/'review.mp4'),before)
            self.assertTrue((new/'source/selection.json').exists())
