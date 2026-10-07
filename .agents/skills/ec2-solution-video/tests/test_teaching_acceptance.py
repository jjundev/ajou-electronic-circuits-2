from fixtures import *
import os
class TeachingAcceptanceTests(Sandbox):
 def test_fake_voice_cannot_publish(self):
  from solution_video.publication import publish_batch
  from solution_video.util import write
  write(self.run/'batch.json',dict(selector='1002',items=[dict(id='fixture',run='videos/fixture',filename='fixture.mp4')]))
  write(self.run/'videos/fixture/verification/report.json',dict(complete=False,live_audio='unverified'))
  r=publish_batch(self.run);self.assertFalse(r['complete']);self.assertEqual(r['published'],[])
  import teaching_acceptance
  self.assertTrue(hasattr(teaching_acceptance,'run_acceptance'),'teaching acceptance runner missing')
 @unittest.skipUnless(os.environ.get('EC2_TEACHING_ACCEPTANCE_REPORT'),'opt-in real media report')
 def test_current_report_media_hash_and_teaching_checks(self):
  from solution_video.util import read,file_hash
  data=read(os.environ['EC2_TEACHING_ACCEPTANCE_REPORT']);self.assertEqual(data['paid_requests'],0);self.assertEqual(data['live_audio'],'unverified');self.assertTrue(data['production_publish_blocked'])
  self.assertEqual([i['problem_id'] for i in data['items']],['E10.11','E10.13','2021-1_중간-Q3'])
  for item in data['items']:
   self.assertEqual(file_hash(item['final']),item['final_sha256']);self.assertTrue(item['media_passed']);self.assertEqual(item['pixel_diff'],0);self.assertTrue(item['teaching_passed']);self.assertTrue(item['writing_flow_passed'])
