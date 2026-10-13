"""Behavioral browser regression using the real offline template (skipped without Playwright)."""
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from _util import make_repo, fragment
from epe_render import build_explanation
from epe_source import load_source

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    sync_playwright = None


@unittest.skipIf(sync_playwright is None, 'playwright not installed')
class LayoutTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.repo = make_repo(self.tmp / 'repo')
        self.pack = load_source(self.repo / '복습노트' / '1007' / '.assets' / 'problems.txt', self.repo)

    def build(self, bodies=None, take=None):
        pack = self.pack if take is None else replace(self.pack, problems=self.pack.problems[take])
        bodies = bodies or {}
        return build_explanation(pack, {p.id: bodies.get(p.id, fragment(p)) for p in pack.problems},
                                 self.tmp / 'stage', self.repo)

    def test_summary_preserves_math_when_navigating_after_render(self):
        artifact = self.build()
        for width in (375, 1440):
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                page = browser.new_page(viewport={'width': width, 'height': 900}, color_scheme='dark')
                page.goto(artifact.html.as_uri(), wait_until='networkidle')
                for problem_id in ['p2', 'p1', 'p2']:
                    page.evaluate('(id)=>{location.hash=id}', problem_id)
                    page.wait_for_function('(id)=>document.querySelector("#"+id).hidden===false', arg=problem_id)
                    heading = page.locator(f'#{problem_id} h3')
                    summary = page.locator('#sum-for')
                    self.assertEqual(summary.locator('.katex').count(), heading.locator('.katex').count())
                    self.assertEqual(summary.inner_html(), heading.inner_html())
                self.assertEqual(page.locator('.katex-error').count(), 0)
                page.evaluate('location.hash="intro"')
                page.wait_for_function('document.querySelector("#sum-for").textContent==="전체 흐름"')
                self.assertEqual(page.locator('#sum-for .katex').count(), 0)
                browser.close()

    def test_short_math_and_layer_spacing_remain_readable(self):
        p = self.pack.problems[0]
        body = fragment(p).replace('$A=1$', '$(A^\\top)_{ij}=A_{ji}$')
        artifact = self.build({p.id: body}, take=slice(0, 1))
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': 375, 'height': 812})
            page.goto(artifact.html.as_uri(), wait_until='networkidle')
            page.locator('#pager-next').click()
            page.wait_for_timeout(100)
            inline = page.locator('#p1 [data-explanation="start"] .katex').first
            self.assertEqual(inline.evaluate('(e)=>getComputedStyle(e).overflowX'), 'visible')
            self.assertFalse(inline.evaluate('(e)=>e.classList.contains("math-block")'))
            for kind in ['understand', 'retry']:
                self.assertGreaterEqual(page.locator(f'#p1 [data-explanation="{kind}"]').evaluate(
                    '(e)=>parseFloat(getComputedStyle(e).marginTop)'), 24)
            self.assertTrue(page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
            self.assertEqual(page.locator('.katex-error').count(), 0)
            browser.close()

    def test_generated_question_has_top_spacing_before_ask_heading(self):
        artifact = self.build(take=slice(0, 1))
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page()
            page.set_content(artifact.html.read_text(encoding='utf-8'))
            page.evaluate("document.documentElement.classList.remove('js')")
            heading = page.locator('[data-source-problem="p1"] h4').filter(has_text='구할 것')
            self.assertEqual(heading.evaluate('(node) => getComputedStyle(node).marginTop'), '24px')
            browser.close()

    def test_long_formula_overflow_is_accessible_after_layout(self):
        p = self.pack.problems[0]
        long = '$' + '+'.join(f'a_{{{i}}}x_{{{i}}}' for i in range(40)) + '$'
        body = fragment(p).replace('$A=1$', long)
        artifact = self.build({p.id: body}, take=slice(0, 1))
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': 375, 'height': 812})
            page.goto(artifact.html.as_uri(), wait_until='networkidle')
            page.locator('#pager-next').click()
            page.wait_for_timeout(150)
            rows = page.locator('#p1 .math-row')
            self.assertGreater(rows.count(), 0)
            for row in rows.all():
                if row.evaluate('(e)=>e.scrollWidth>e.clientWidth+3'):
                    self.assertTrue(row.evaluate(
                        '(e)=>e.classList.contains("math-pan")&&getComputedStyle(e).scrollbarWidth==="none"'))
                    row.focus()
                    row.press('ArrowRight')
                    self.assertTrue(page.locator('#p1').is_visible())
            browser.close()


if __name__ == '__main__':
    unittest.main()
