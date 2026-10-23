"""Real Chromium PDF regression for responsive problem/original pane mounting."""
from dataclasses import replace

import pymupdf
import pytest
from playwright.sync_api import expect

from test_sync import synthetic
from test_sync_browser import browser
from epe_render import build_explanation


@pytest.fixture(scope='module')
def print_stage(tmp_path_factory):
    root = tmp_path_factory.mktemp('explain-print')
    repo, pack, fragments = synthetic(root)
    problems = []
    for number, color in enumerate([(1, 0, 0), (0, 1, 0), (0, 0, 1)], 1):
        with pymupdf.open() as image_doc:
            image_page = image_doc.new_page(width=40 + number, height=20)
            image_page.draw_rect(image_page.rect, color=color, fill=color)
            png = image_page.get_pixmap().tobytes('png')
        uri = f'original-{number}.png'
        (pack.folder / uri).write_bytes(png)
        problems.append(replace(
            pack.problems[0], id=f'p{number}', number=number,
            original_html=f'<p>Original question {number} unique text.</p>'
                          f'<img src="{uri}" alt="Original circuit {number}">'))
    pack = replace(pack, problems=tuple(problems))
    authored = {p.id: fragments['p1'] for p in problems}
    return build_explanation(pack, authored, root/'stage', repo).html.as_uri()


@pytest.mark.parametrize('width,height', [(1280, 900), (1024, 900), (375, 812)])
@pytest.mark.parametrize('theme', ['light', 'dark'])
def test_real_pdf_preserves_every_original_and_restores_screen(
        browser, print_stage, width, height, theme):
    # A responsive remount during print must not collapse the source panes.
    context = browser.new_context(viewport={'width': width, 'height': height},
                                  color_scheme=theme)
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    try:
        page.goto(print_stage + '#p2', wait_until='networkidle')
        page.evaluate('document.fonts.ready')
        if width >= 1024:
            page.locator('#tab-original').click()
        else:
            page.locator('#p2 .problem-toggle').click()
        # Do not emulate print or dispatch synthetic beforeprint: printToPDF
        # must exercise the native paper-width/media event ordering.
        pdf = page.pdf(print_background=True)
        with pymupdf.open(stream=pdf, filetype='pdf') as doc:
            text = '\n'.join(p.get_text() for p in doc)
            for number in (1, 2, 3):
                assert f'Original question {number} unique text.' in text
                assert any(image['width'] == 40 + number
                           for p in doc for image in p.get_image_info())
        if width >= 1024:
            expect(page.locator('#tab-original')).to_have_attribute('aria-selected', 'true')
            expect(page.locator('#tabpanel-original [data-original-problem="p2"]')).to_be_visible()
            expect(page.locator('[data-original-problem="p1"]')).to_be_hidden()
            page.locator('#tab-problem').click()
            expect(page.locator('#tabpanel-problem [data-problem-for="p2"]')).to_be_visible()
        else:
            expect(page.locator('#p2 .problem-toggle')).to_have_attribute('aria-expanded', 'true')
            expect(page.locator('#p2 [data-problem-for="p2"]')).to_be_visible()
            expect(page.locator('#p1 [data-problem-for="p1"]')).to_be_hidden()
        page.locator('#pager-next').click()
        expect(page.locator('main #p3')).to_be_visible()
        page.set_viewport_size({'width': 375 if width >= 1024 else 1280, 'height': 900})
        if width >= 1024:
            expect(page.locator('#p3 .problem-toggle')).to_be_visible()
            expect(page.locator('#p3 [data-problem-for="p3"]')).to_be_hidden()
        else:
            expect(page.locator('#tabpanel-problem [data-problem-for="p3"]')).to_be_visible()
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        assert not errors
    finally:
        context.close()
