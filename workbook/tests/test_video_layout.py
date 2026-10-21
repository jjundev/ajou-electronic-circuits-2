"""The review PDF must fill a video frame without using its caption band."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

import fitz
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_workbook
from assemble import build_data, ids_selection
from render import inject, load_template, render_pdf


class VideoLayoutTests(unittest.TestCase):
    def test_dense_solution_preserves_previous_screen_text_size(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for layout in ['a4', 'video-16x9']:
                args=build_workbook.parse_args(['build_workbook.py','--ids','2021-1_중간-Q3',
                    '--name',layout,'--layout',layout,'--pdf-dir',str(root),'--build-dir',str(root/'build')])
                self.assertEqual(build_workbook.build_one(build_workbook.selections(args)[0],args),[])
            def sizes(layout):
                with fitz.open(root/(layout+'-답안.pdf')) as d:
                    return [round(s['size'],2) for b in d[0].get_text('dict')['blocks'] if b['type']==0
                        for l in b['lines'] for s in l['spans'] if '전류 변화' in s['text']]
            self.assertTrue(sizes('a4'))
            self.assertAlmostEqual(sizes('video-16x9')[0], 9.06, delta=.03)
    def test_review_directory_selects_video_layout_by_default(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            args = build_workbook.parse_args(['build_workbook.py', '--ids', 'E10.11',
                '--name', 'sample', '--json-only', '--pdf-dir', str(root/'복습노트/1002'),
                '--build-dir', str(root/'build')])
            build_workbook.build_one(build_workbook.selections(args)[0], args)
            data = json.loads((root/'build/sample-답안.json').read_text())
            self.assertEqual(data['meta'].get('layout'), 'video-16x9')

    def test_wide_pdf_keeps_all_text_out_of_caption_band(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            data = build_data(ids_selection(['E10.11', 'E10.13', '2021-1_중간-Q3'], 'wide'), 'answers')
            template = load_template('answers', layout='video-16x9')
            html = root/'wide.html'; html.write_text(inject(template, data))
            pdf = root/'wide.pdf'
            self.assertEqual(render_pdf(html, pdf), [])
            with fitz.open(pdf) as doc:
                self.assertGreaterEqual(len(doc), 3)
                for page in doc:
                    self.assertAlmostEqual(page.rect.width/page.rect.height, 16/9, delta=.002)
                    self.assertFalse(page.get_text(clip=fitz.Rect(0, page.rect.height*5/6,
                        page.rect.width, page.rect.height)).strip(), 'caption band contains PDF text')
                self.assertIn('출력', doc[2].get_text())
                body = [s for b in doc[0].get_text('dict')['blocks'] if b['type']==0
                    for l in b['lines'] for s in l['spans'] if '소자 값은' in s['text']]
                self.assertTrue(body)
                self.assertAlmostEqual(body[0]['size'], 11.34, delta=.03)


class PersonalizedVideoLayoutTests(unittest.TestCase):
    def test_personalized_core_svg_and_images_render_above_caption_band(self):
        from overlay_fixture import OverlayBundle
        from test_answer_overlay import _cli
        from playwright.sync_api import sync_playwright
        with tempfile.TemporaryDirectory() as td:
            bundle = OverlayBundle(Path(td))
            svg = ('<figure class="figure"><svg viewBox="0 0 240 80" role="img">'
                '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">'
                '<path d="M0 0 L8 4 L0 8 Z"/></marker></defs>'
                '<path class="fig-ink" d="M20 40 H180" marker-end="url(#arrow)"/>'
                '<circle class="fig-dot" cx="20" cy="40" r="4"/>'
                '<text class="fig-text" x="70" y="26">R_out</text></svg></figure>')
            bundle.overlay['problems'][0]['steps'][0]['html'] += svg
            bundle.sync()
            pdf_dir = bundle.build_dir/'pdf'
            pdf_dir.mkdir(parents=True)
            untouched = pdf_dir/'personal-문제.pdf'
            untouched.write_bytes(b'Existing problem PDF')
            before = (untouched.read_bytes(), untouched.stat().st_mtime_ns)
            result = _cli(bundle, '--mode','answers','--answer-overlay',str(bundle.path),'--layout','video-16x9')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((untouched.read_bytes(),untouched.stat().st_mtime_ns),before)
            pdf = pdf_dir/'personal-답안.pdf'
            with fitz.open(pdf) as doc:
                self.assertEqual(len(doc),2)
                self.assertIn('R_out',doc[0].get_text())
                for page in doc:
                    self.assertAlmostEqual(page.rect.width/page.rect.height,16/9,delta=.002)
                    self.assertFalse(page.get_text(clip=fitz.Rect(0,page.rect.height*5/6,page.rect.width,page.rect.height)).strip())
            with sync_playwright() as pw:
                browser = pw.chromium.launch(channel='chrome',headless=True)
                try:
                    page = browser.new_page(viewport={'width':1920,'height':1080})
                    page.goto((bundle.build_dir/'personal-답안.html').as_uri())
                    page.wait_for_selector('html[data-ready="true"]')
                    style = page.locator('.sol-step-body svg .fig-ink').first.evaluate('(n) => ({stroke:getComputedStyle(n).stroke, fill:getComputedStyle(n).fill, marker:getComputedStyle(n).markerEnd})')
                    self.assertNotEqual(style['stroke'],'none')
                    self.assertEqual(style['fill'],'none')
                    self.assertIn('#arrow',style['marker'])
                    marker = page.locator('.sol-step-body marker path').first.evaluate('(n) => getComputedStyle(n).fill')
                    self.assertNotEqual(marker,'none')
                    self.assertEqual(page.locator('.sol-step-label').first.inner_text(),'판단 & 계산')
                    self.assertTrue(page.locator('.sol-step-body img').first.evaluate('(n) => n.complete && n.naturalWidth > 0'))
                finally:
                    browser.close()


if __name__ == "__main__":
    unittest.main()
