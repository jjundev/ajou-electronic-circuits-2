"""The review PDF must fill a video frame without using its caption band."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

import pymupdf as fitz
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_workbook
from assemble import build_data, ids_selection
from render import inject, load_template, measure_typography, render_pdf
import vendor_route


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


    def test_problem_figures_scale_with_video_page_width(self):
        from playwright.sync_api import sync_playwright
        a4_px = 297 * 96 / 25.4
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            data = build_data(ids_selection(['E11.16'], 'fig'), 'problems')
            w_mm = data['problems'][0]['figures'][0]['w_mm']
            with sync_playwright() as pw:
                browser = pw.chromium.launch(channel='chrome', headless=True)
                try:
                    for layout, cap, frac in [('a4', 1.5, '.40'), ('video-16x9', 1.5 * 1920 / a4_px, '.40')]:
                        html = root/(layout+'.html'); html.write_text(inject(load_template('problems', layout=layout), data))
                        page = browser.new_page(viewport={'width':1400,'height':1000})
                        vendor_route.install(page)
                        page.goto(html.as_uri())
                        page.wait_for_function('document.documentElement.dataset.ready')
                        got = page.evaluate("""() => { const f=document.querySelector('.fig-band .fig');
                            return [f.style.getPropertyValue('--w-cap'),
                                getComputedStyle(f.closest('.fig-band')).getPropertyValue('--fig-frac').trim()]; }""")
                        self.assertAlmostEqual(float(got[0].removesuffix('mm')), w_mm * cap, places=3, msg=layout)
                        self.assertEqual(got[1], frac, layout)
                        page.close()
                finally:
                    browser.close()

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
            bundle.overlay['problems'][0]['steps'][0]['html'] += svg + r'<p>$g_m=\sqrt{3}$</p>'
            # Answer blocks accept the same reviewed figure contract as steps.
            bundle.overlay['problems'][1]['answers'][0]['html'] += svg + r'<p>$A=\sqrt{N}$</p>'
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
                    vendor_route.install(page)
                    page.goto((bundle.build_dir/'personal-답안.html').as_uri())
                    page.wait_for_selector('html[data-ready="true"]')
                    style = page.locator('.sol-step-body svg .fig-ink').first.evaluate('(n) => ({stroke:getComputedStyle(n).stroke, fill:getComputedStyle(n).fill, marker:getComputedStyle(n).markerEnd})')
                    # Radical SVGs must retain a visible height, not collapse under figure sizing.
                    for scope in ('.sol-step-body', '.sol-answer'):
                        radical = page.locator(scope + ' .sqrt svg').first.bounding_box()
                        self.assertGreater(radical['height'], 5, 'KaTeX radical collapsed by figure CSS')
                    answer_style = page.locator('.sol-answer svg .fig-ink').first.evaluate('(n) => ({stroke:getComputedStyle(n).stroke, fill:getComputedStyle(n).fill})')
                    self.assertNotEqual(answer_style['stroke'], 'none')
                    self.assertEqual(answer_style['fill'], 'none')
                    self.assertNotEqual(style['stroke'],'none')
                    self.assertEqual(style['fill'],'none')
                    self.assertIn('#arrow',style['marker'])
                    marker = page.locator('.sol-step-body marker path').first.evaluate('(n) => getComputedStyle(n).fill')
                    self.assertNotEqual(marker,'none')
                    self.assertEqual(page.locator('.sol-step-label').first.inner_text(),'판단 & 계산')
                    self.assertTrue(page.locator('.sol-step-body img').first.evaluate('(n) => n.complete && n.naturalWidth > 0'))
                finally:
                    browser.close()

class DenseFigureTests(unittest.TestCase):
    def test_dense_figure_keeps_cap_width_and_paginates(self):
        from playwright.sync_api import sync_playwright
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            data = build_data(ids_selection(['E11.16'], 'dense'), 'answers')
            prob = data['problems'][0]
            prob['figures'] = prob['figures'][:1]
            prob['figures'][0].update(w_mm=84.7, h_mm=71.6)
            steps = prob['solution']['steps']
            prob['solution']['steps'] = (steps * 8)[:8]
            prob['solution']['paginate'] = True
            data['meta']['layout'] = 'video-16x9'
            baseline = root/'baseline.html'
            baseline.write_text(inject(load_template('answers'), data))
            data['meta']['typography'] = measure_typography(baseline)
            html = root/'dense.html'
            html.write_text(inject(load_template('answers', layout='video-16x9'), data))
            with sync_playwright() as pw:
                browser = pw.chromium.launch(channel='chrome', headless=True)
                try:
                    page = browser.new_page(viewport={'width': 1920, 'height': 1080})
                    vendor_route.install(page)
                    page.goto(html.as_uri())
                    page.wait_for_selector('html[data-ready]')
                    got = page.evaluate("""() => ({
                        width: document.querySelector('.fig-band .fig').offsetWidth,
                        overflow: document.querySelectorAll('.page[data-overflow]').length,
                        pages: document.querySelectorAll('.page').length})""")
                finally:
                    browser.close()
            self.assertGreaterEqual(got['width'], 0.98 * 84.7 * 1.5 * 96 / 25.4)
            self.assertEqual(got['overflow'], 0)
            self.assertGreaterEqual(got['pages'], 2)


class StepFigureTests(unittest.TestCase):
    """P12.24: 그림 네 장(교재 Fig 12.85–12.88)이 한 띠에서 0.4배로 줄어 라벨을 못 읽던 문제."""
    LABELS = ['판정 기준과 묶음별 첫 줄', '그림 12.85 차동쌍 입력 여섯 회로', '그림 12.86 CG 입력 네 회로',
              '그림 12.87 전류 입력 네 회로', '그림 12.88 저항 귀환 두 회로']

    def _data(self, labels):
        from answer_overlay import match_step_figures
        data = build_data(ids_selection(['P12.24'], 'stepfig'), 'answers')
        data['meta']['layout'] = 'video-16x9'
        prob = data['problems'][0]
        prob['hints'] = []
        prob['solution'] = {'paginate': True, 'answer': '<p>FinalAnswer</p>',
                            'steps': [{'label': l, 'html': f'<p>단계 {i} 설명</p>'} for i, l in enumerate(labels)]}
        per_step = match_step_figures(prob['figures'], labels)
        if per_step is not None:
            for step, figs in zip(prob['solution']['steps'], per_step):
                if figs:
                    step['figures'] = figs
            prob['figures'] = []
        return data

    def _render(self, data, extra_css=''):
        from playwright.sync_api import sync_playwright
        with tempfile.TemporaryDirectory() as td:
            html = Path(td)/'stepfig.html'
            markup = inject(load_template('answers', layout='video-16x9'), data)
            html.write_text(markup.replace('</head>', f'<style>{extra_css}</style></head>', 1))
            with sync_playwright() as pw:
                browser = pw.chromium.launch(channel='chrome', headless=True)
                try:
                    page = browser.new_page(viewport={'width': 1920, 'height': 1080})
                    vendor_route.install(page)
                    page.goto(html.as_uri())
                    page.wait_for_selector('html[data-ready="true"]')
                    return page.evaluate("""() => ({
                        overflow: document.body.dataset.overflow,
                        figs: [...document.querySelectorAll('img.fig, img.step-fig')].map(f => ({
                            cls: f.className, dense: f.hasAttribute('data-dense'),
                            scale: f.offsetWidth / f.naturalWidth, top: Math.round(f.getBoundingClientRect().top),
                            page: f.closest('.page').id}))})""")
                finally:
                    browser.close()

    def test_each_figure_sits_in_its_step_at_full_size(self):
        got = self._render(self._data(self.LABELS))
        self.assertEqual(got['overflow'], '')
        self.assertEqual([f['cls'] for f in got['figs']], ['step-fig'] * 4)
        for f in got['figs']:
            self.assertGreaterEqual(f['scale'], 0.98, f)

    def test_unmatched_band_wraps_and_keeps_dense_figures_readable(self):
        got = self._render(self._data(['기준', '여섯 회로', '네 회로', '네 회로', '두 회로']))
        self.assertEqual([f['cls'] for f in got['figs']], ['fig'] * 4)
        self.assertGreater(len({f['top'] for f in got['figs']}), 1)        # 한 줄에 몰지 않고 줄을 바꾼다
        dense = [f for f in got['figs'] if f['dense']]
        self.assertTrue(dense)
        for f in dense:
            self.assertGreaterEqual(f['scale'], 0.8, f)
        self.assertNotIn('fig-scale', got['overflow'])

    def test_high_resolution_dense_figure_can_fill_its_print_width(self):
        data = build_data(ids_selection(['2018-2_중간-Q1'], 'dense-exam'), 'answers')
        data['meta']['layout'] = 'video-16x9'
        problem = data['problems'][0]
        problem['solution'] = {'paginate': True, 'answer': '<p>FinalAnswer</p>',
                               'steps': [{'label': '풀이', 'html': '<p>회로를 읽어요.</p>'}]}
        got = self._render(data)
        figure, = got['figs']
        self.assertTrue(figure['dense'])
        self.assertLess(figure['scale'], 0.8)
        self.assertEqual(got['overflow'], '')

    def test_shrunk_dense_figure_is_reported(self):
        got = self._render(self._data(self.LABELS), '.step-figs { width: 100px; }')
        self.assertIn('fig-scale=', got['overflow'])


if __name__ == "__main__":
    unittest.main()
