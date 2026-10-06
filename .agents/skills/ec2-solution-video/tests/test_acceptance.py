from fixtures import *
class AcceptanceTests(Sandbox):
    def test_skill_is_discoverable_and_complete(self):
        skill=S/'SKILL.md'; self.assertTrue(skill.is_file()); text=skill.read_text(); self.assertIn('name: ec2-solution-video',text)
        self.assertIn('원본',text); self.assertTrue((S/'agents/openai.yaml').is_file())
    def test_fake_pcm_end_to_end_problem_batch(self):
        # Opt-in integration runner produces three sandbox videos, never fake live approval.
        import os
        target=os.environ.get('EC2_ACCEPTANCE_BATCH')
        if not target: self.skipTest('run tests/acceptance.py to render actual representative PDF cases')
        batch=Path(target); data=json.loads((batch/'acceptance.json').read_text())
        self.assertEqual(len(data['items']),3);self.assertEqual(data['paid_requests'],0)
        self.assertEqual(data['live_audio'],'unverified')
        for i in data['items']:
            self.assertTrue(i['media_passed']); self.assertEqual(i['pixel_diff'],0)
            self.assertEqual(i['final_sha256'],hashlib.sha256(Path(i['final']).read_bytes()).hexdigest())
