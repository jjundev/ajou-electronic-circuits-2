from fixtures import *
from test_manifest import example
from solution_video.pdf_pages import export_page,extract_layers
from solution_video.reveal import build_timeline
from solution_video.review_adapter import default_config
from solution_video.composition import assemble
from solution_video.util import browser
class CompositionTests(Sandbox):
    def test_parts_have_exact_frame_coverage(self):
        p=math_pdf(self.run/'a.pdf'); candidate=export_page(p,0,self.run/'layers'); mp=mapping(candidate); layers=extract_layers(candidate,mp)
        m,_,_,_=example(); m['segments']=m['segments'][:2]; m['segments'][1]['step_id']='solution'; m['reveal_order']=mp['steps'][0]['glyph_ids']; m['shape_anchors']={s['id']:m['reveal_order'][-1] for s in layers['shapes']}
        audio=[make_audio(s['id'],2400,self.run) for s in m['segments']]; t=build_timeline(m,layers,audio,default_config()); pair={'problem':{'snapshot':'a.pdf','page_index':0}}
        parts=assemble(pair,layers,m,t,self.run,S.parent/'ec2-review-video/assets/runtime/vendor/gsap.min.js')
        self.assertEqual(parts[0]['first_frame'],0); self.assertEqual(parts[-1]['last_frame'],t['total_frames'])
        html=(self.run/parts[0]['entry']).read_text(); self.assertNotIn('katex',html.lower()); self.assertIn('data-composition-id',html); self.assertIn("window.__timelines['solution']",html)
        r=browser(['--mode','timeline','--entry',str(self.run/parts[0]['entry'])]); self.assertTrue(r['seek_equal']); self.assertEqual(r['final_cursor'],'0'); self.assertEqual(r['viewport']['height'],900)
    def test_default_camera_keeps_readable_line_context(self):
        from solution_video.composition import camera_keys
        from test_manifest import example
        m,l,_,_=example();l['metadata']={'width_pt':842,'height_pt':595}
        l['glyphs']=[dict(id='g'+str(i),text='가' if i<8 else '=',bbox=[300+i*12,250,307+i*12,257 if i<8 else 252],svg_ids=[],paint_order=i) for i in range(10)]
        l['map']['steps']=[dict(id='s',glyph_ids=[g['id'] for g in l['glyphs']],shape_ids=[])];l['map']['answer_step_id']='s'
        t=dict(total_frames=120,segments=[dict(start_sample=0,end_sample=80000)],events=[dict(id=g['id'],frame=i*5+1,kind='glyph') for i,g in enumerate(l['glyphs'])])
        keys=camera_keys(m,l,t)
        self.assertLess(max(900/k['viewbox'][3] for k in keys),6)
    def test_explicit_final_zoom_cannot_crop_finished_answer(self):
        from solution_video.composition import camera_keys
        from test_manifest import example
        m,l,_,_=example();l['metadata']={'width_pt':842,'height_pt':595}
        m['cameras']=[dict(at_frame=0,viewbox=[50,50,200,150]),dict(at_frame=100,viewbox=[60,60,180,100]),dict(at_frame=120,viewbox=[60,60,180,100])]
        t=dict(total_frames=130,segments=[dict(start_sample=0,end_sample=80000)],events=[dict(id='g1',frame=5,kind='glyph'),dict(id='g2',frame=50,kind='glyph')])
        keys=camera_keys(m,l,t);self.assertEqual(keys[-1],dict(at_frame=100,viewbox=[0,0,842,595]))
