from fixtures import *
from solution_video.verify import verify_run
class VerifyTests(Sandbox):
    def test_final_media_checked_after_burn(self):
        report=verify_run(self.run,Path('/missing/hyperframes'))
        self.assertFalse(report['complete']); self.assertIsNone(report['final_sha256'])
    def test_source_timeout_and_missing_reviews(self):
        report=verify_run(self.run,Path('/missing/hyperframes'))
        self.assertFalse(report['complete']); self.assertIn('unverified',str(report['checks']))
    def test_gate_evidence_tamper_is_rejected(self):
        from solution_video.util import write,digest,file_hash
        from solution_video.verify import gate_valid
        layer=dict(original_svg=str(self.run/'a.svg'),animated_svg=str(self.run/'b.svg'),reference_png=str(self.run/'native.png'))
        for p in [self.run/'a.svg',self.run/'b.svg',self.run/'native.png',self.run/'evidence.png']:p.write_bytes(b'original')
        g=dict(input_hash=digest(layer),pixel_diff=0,non_target_diff=0,hidden_leaks=0,evidence=['evidence.png'],evidence_hashes={'evidence.png':file_hash(self.run/'evidence.png')},source_hashes={k:file_hash(v) for k,v in layer.items()})
        self.assertTrue(gate_valid(self.run,layer,g));(self.run/'evidence.png').write_bytes(b'changed')
        self.assertFalse(gate_valid(self.run,layer,g))
