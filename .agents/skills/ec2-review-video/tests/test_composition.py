import tempfile,unittest,json
from pathlib import Path
from _util import ROOT,minimal_manifest
from lib.theme import snapshot_theme
from lib.timing import build_timeline
from lib.composition import assemble

class CompositionTest(unittest.TestCase):
    def test_composition_and_invalid_target(self):
        with tempfile.TemporaryDirectory() as d:
            run=Path(d); m=minimal_manifest()
            import shutil
            pack=run/'pack'; shutil.copytree(ROOT/'.claude/skills/ec2-review-pack/assets',pack/'assets')
            shutil.copy2(pack/'assets/note-template.html',pack/'assets/review-template.html')
            theme=snapshot_theme(pack,run)
            p=run/'source/scene-fragments'; p.mkdir()
            (p/'scene-atp.html').write_text('<section class="topic"><h3 id="scene-atp-count">32 ATP</h3></section>',encoding='utf-8')
            motions=[{'target':'#scene-atp-count','segment_id':'seg-atp','kind':'count','from':{'textContent':0},'to':{'textContent':32},'duration_s':1}]
            (p/'scene-atp.motion.json').write_text(json.dumps(motions))
            t=build_timeline(m,[{'id':'seg-atp','samples':24000,'rate':24000,'path':'assets/voice/test.wav'}])
            parts=assemble(m,t,theme,run)
            page=(run/parts[0]['entry']).read_text(encoding='utf-8')
            self.assertIn('data-theme="dark"',page); self.assertIn('scene-atp-count',page)
            self.assertNotIn('class="clip video-caption"',page)
            self.assertIn('id="audio-seg-atp"',(run/'index.html').read_text(encoding='utf-8'))
            self.assertEqual(parts[0]['frames'],78)
            motions[0]['target']='#missing'
            (p/'scene-atp.motion.json').write_text(json.dumps(motions))
            with self.assertRaises(ValueError): assemble(m,t,theme,run)
    def test_rejects_executable_fragment(self):
        from lib.composition import validate_fragment
        for fragment in ('<img src="https://example.com/x">','<svg onload="alert(1)"></svg>','<script>bad()</script>'):
            with self.assertRaises(ValueError): validate_fragment(fragment,'scene-x')
    def test_math_needs_complete_local_assets(self):
        import shutil
        for missing in ['katex.min.js','katex.min.css','auto-render.min.js','fonts']:
            with self.subTest(missing=missing), tempfile.TemporaryDirectory() as d:
                run=Path(d);m=minimal_manifest();theme=snapshot_theme(ROOT/'.claude/skills/ec2-review-pack',run)
                frag=run/'source/scene-fragments';frag.mkdir()
                (frag/'scene-atp.html').write_text('<section class="topic"><h3 id="scene-atp-count">$g_m$</h3></section>')
                (frag/'scene-atp.motion.json').write_text(json.dumps([{'target':'#scene-atp-count','segment_id':'seg-atp','kind':'reveal','from':{'opacity':0},'to':{'opacity':1},'duration_s':.6}]))
                vendor=run/'assets/vendor/katex';vendor.mkdir(parents=True)
                for name in ['katex.min.js','katex.min.css','auto-render.min.js']:(vendor/name).write_text('asset')
                (vendor/'fonts').mkdir();(vendor/'fonts/test.woff2').write_bytes(b'font')
                p=vendor/missing
                if p.is_dir():shutil.rmtree(p)
                else:p.unlink()
                timeline=build_timeline(m,[{'id':'seg-atp','samples':24000,'rate':24000,'path':'voice.wav'}])
                with self.assertRaisesRegex(ValueError,'KaTeX'):assemble(m,timeline,theme,run)
    def test_circuit_state_coordinates_match_values(self):
        import xml.etree.ElementTree as ET
        from _util import SKILL
        f=SKILL/'tests/fixtures/circuit-scene'
        root=ET.fromstring((f/'scene.html').read_text())
        for id,current,width in [('scene-dm-left',60,600),('scene-dm-right',40,400)]:
            el=next(e for e in root.iter() if e.attrib.get('id')==id)
            factor=1.2 if id.endswith('left') else .8
            self.assertEqual(int(el.attrib['width'])*factor,width)
            self.assertEqual(int(el.attrib['data-current-ua']),current)
        motion=json.loads((f/'scene.motion.json').read_text())
        xs=[x['to']['scaleX'] for x in motion if x['kind']=='move']
        self.assertEqual(xs,[1.2,.8])
        self.assertEqual(60+40,100);self.assertEqual(60-50,10);self.assertEqual(50-40,10)

    def test_math_subcomposition_preserves_local_render_and_dark_tokens(self):
        import shutil
        from _util import SKILL
        from lib.composition import stage_assets
        with tempfile.TemporaryDirectory() as d:
            run=Path(d);f=SKILL/'tests/fixtures/circuit-scene';m=json.loads((f/'manifest.json').read_text())
            frag=run/'source/scene-fragments';frag.mkdir(parents=True)
            shutil.copyfile(f/'scene.html',frag/'scene-dm.html');shutil.copyfile(f/'scene.motion.json',frag/'scene-dm.motion.json')
            stage_assets(SKILL/'assets/runtime',run);theme=snapshot_theme(ROOT/'.claude/skills/ec2-review-pack',run)
            timeline=build_timeline(m,[{'id':'seg-dm','samples':24000,'rate':24000,'path':'voice.wav'}])
            parts=assemble(m,timeline,theme,run)
            # Exercise the generated standalone JS contract separately from dormant <template>.
            text=(run/'source/compositions/scene-dm.html').read_text()
            self.assertIn('renderMathInElement',text);self.assertIn('assets/vendor/katex/katex.min.js',text)
            self.assertIn('.video-scene{--bg:',text)
