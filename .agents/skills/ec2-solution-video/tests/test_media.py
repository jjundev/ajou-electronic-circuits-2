from fixtures import *
from solution_video.subtitles import write_srt,burn_subtitles
from solution_video.util import checked
class MediaTests(Sandbox):
    def test_white_pdf_renders_and_captions_stay_outside(self):
        timeline=dict(rate=24000,segments=[dict(text='원본 풀이를 확인합니다.',start_sample=0,end_sample=24000,voice_samples=24000)])
        srt=write_srt(timeline,self.run/'caption.srt'); self.assertIn('원본 풀이',srt.read_text())
        master=self.run/'master.mp4'
        checked(['ffmpeg','-y','-v','error','-f','lavfi','-i','color=white:s=1920x1080:r=30','-t','1','-c:v','libx264','-pix_fmt','yuv420p',master])
        font=S.parent/'ec2-review-video/assets/fonts/Pretendard-Bold.ttf'
        final=burn_subtitles(master,srt,self.run/'최종.mp4',font)
        raw=checked(['ffmpeg','-v','error','-i',final,'-frames:v','1','-f','image2',self.run/'frame.png'])
        from PIL import Image,ImageChops
        image=Image.open(self.run/'frame.png').convert('RGB'); bbox=ImageChops.difference(image,Image.new('RGB',image.size,'white')).getbbox()
        self.assertIsNotNone(bbox); self.assertGreaterEqual(bbox[1],900)
