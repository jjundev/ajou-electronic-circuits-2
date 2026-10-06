from fixtures import *
from test_manifest import example
from solution_video.reveal import build_timeline,visible_ids
from solution_video.review_adapter import default_config
class RevealTests(Sandbox):
    def setUp(self):
        super().setUp(); self.m,self.l,_,_=example()
        self.l['glyphs']=[dict(id='g'+str(i),text='가',bbox=[100,100,110,110],svg_ids=['sv'+str(i)],paint_order=i) for i in range(70)]
        self.l['map']['steps'][0]['glyph_ids']=[g['id'] for g in self.l['glyphs'][:-1]]; self.l['map']['steps'][1]['glyph_ids']=['g69']; self.m['reveal_order']=[g['id'] for g in self.l['glyphs']]; self.m['shape_anchors']={'s1':'g69'}
        self.audio=[make_audio(s['id'],24000,self.run) for s in self.m['segments']]
    def test_short_pcm_extends_writing(self):
        t=build_timeline(self.m,self.l,self.audio,default_config())
        self.assertGreaterEqual(t['total_samples'],258000); self.assertEqual(t['total_frames']*800,t['total_samples'])
        self.assertEqual(visible_ids(t,t['total_frames']-1),self.m['reveal_order'])
        events=[e for e in t['events'] if e['kind']=='glyph']
        self.assertTrue(all(b['frame']-a['frame']>=5 for a,b in zip(events,events[1:])))
    def test_seek_is_pure(self):
        t=build_timeline(self.m,self.l,self.audio,default_config()); frames=[0,t['total_frames']-1,100,0]
        results=[visible_ids(t,f) for f in frames]; self.assertEqual(results[0],results[-1]); self.assertEqual(results[2],visible_ids(t,100))
