from fixtures import *
from solution_video.state import finish_stage,recover_run,STAGES
from solution_video.util import write
class StateTests(Sandbox):
    def test_first_invalid_stage_and_voice_preservation(self):
        (self.run/'source').mkdir(); (self.run/'layers').mkdir(); write(self.run/'source/map.json',{'work_bbox':[1,2,3,4]}); write(self.run/'source/config.json',{'voice':'Aoede'})
        pub=self.run/'published.mp4';pub.write_bytes(b'published')
        from solution_video.util import file_hash
        write(self.run/'verification/publication.json',{'published':{str(pub):file_hash(pub)}})
        for stage in STAGES:
            out=self.run/(stage+'.txt'); out.write_text(stage); finish_stage(self.run,stage,[out])
        self.assertIsNone(recover_run(self.run))
        write(self.run/'source/config.json',{'voice':'Other'}); self.assertEqual(recover_run(self.run),'voice')
        write(self.run/'source/map.json',{'work_bbox':[1,2,30,40]}); self.assertEqual(recover_run(self.run),'layers'); self.assertEqual((self.run/'voice.txt').read_text(),'voice')
