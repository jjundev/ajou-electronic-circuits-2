import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from assemble import build_data, ids_selection  # noqa: E402
import paths  # noqa: E402
import vendor_route  # noqa: E402
from render import PLACEHOLDER, RenderError, inject, load_template, render_pdf  # noqa: E402

HAS_PLAYWRIGHT = importlib.util.find_spec("playwright") is not None
SMOKE_IDS = ["E9.01", "P9.05", "2023-1_기말-Q1"]


class TestInject(unittest.TestCase):
    def test_replaces_placeholder(self):
        out = inject(f'<script id="workbook-data">{PLACEHOLDER}</script>', {"a": 1})
        self.assertEqual(out, '<script id="workbook-data">{"a": 1}</script>')

    def test_script_end_in_data_is_escaped(self):
        data = {"html": "</script><!-- $a < b$"}
        out = inject(f"<script>{PLACEHOLDER}</script>", data)
        payload = out[len("<script>"):-len("</script>")]
        self.assertNotIn("<", payload)
        self.assertEqual(json.loads(payload), data)

    def test_template_without_placeholder_rejected(self):
        with self.assertRaisesRegex(RenderError, "자리표시자"):
            inject("<html></html>", {})

    def test_real_templates_accept_data(self):
        for mode in ("problems", "answers"):
            with self.subTest(mode=mode):
                self.assertNotIn(PLACEHOLDER, inject(load_template(mode), {"meta": {}, "problems": []}))


class TestRenderPdf(unittest.TestCase):
    def test_missing_playwright_message(self):
        with patch.dict(sys.modules, {"playwright": None, "playwright.sync_api": None}):
            with self.assertRaises(RenderError) as cm:
                render_pdf(Path("x.html"), Path("x.pdf"))
        self.assertIn("pip3 install", str(cm.exception))


CDN = "https://cdn.jsdelivr.net"


class TestVendorRoute(unittest.TestCase):
    """템플릿의 CDN 주소가 저장소 사본 파일로 바뀐다."""

    def test_template_urls_resolve(self):
        for mode in ("problems", "answers"):
            for url in __import__("re").findall(r'"(https://cdn\.jsdelivr\.net/[^"]+)"', load_template(mode)):
                with self.subTest(mode=mode, url=url):
                    target, reason = vendor_route.resolve(url)
                    self.assertIsNone(reason)
                    self.assertTrue(target.is_file())

    def test_font_and_alias_paths(self):
        target, _ = vendor_route.resolve(f"{CDN}/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css")
        self.assertEqual(target.name, "pretendard.css")
        target, _ = vendor_route.resolve(f"{CDN}/npm/katex@0.16.11/dist/fonts/KaTeX_Main-Regular.woff2?v=1")
        self.assertEqual(target.name, "KaTeX_Main-Regular.woff2")

    def test_unmatched_requests_are_refused(self):
        for url, why in [(f"{CDN}/npm/katex@0.16.10/dist/katex.min.js", "버전"),
                         (f"{CDN}/npm/katex@0.16.11/dist/nope.js", "사본에 없음"),
                         (f"{CDN}/npm/katex@0.16.11/dist/../../provenance.json", "사본에 없음"),
                         (f"{CDN}/npm/lodash@4/lodash.js", "매핑 밖")]:
            with self.subTest(url=url):
                target, reason = vendor_route.resolve(url)
                self.assertIsNone(target)
                self.assertIn(why, reason)

    def test_missing_vendor_is_reported(self):
        with tempfile.TemporaryDirectory() as td:
            target, reason = vendor_route.resolve(f"{CDN}/npm/katex@0.16.11/dist/katex.min.js", Path(td))
        self.assertIsNone(target)
        self.assertIn("사본 목록", reason)


@unittest.skipUnless(HAS_PLAYWRIGHT, "playwright 없음")
class TestRenderSmoke(unittest.TestCase):
    """교과서 예제·장말문제와 기출 하나를 실제 Chrome으로 그린다. KaTeX·글꼴은 저장소 사본에서 받는다."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def render(self, mode, edit=None):
        data = build_data(ids_selection(SMOKE_IDS, "스모크"), mode)
        if edit:
            edit(data)
        html_path = self.tmp / f"{mode}.html"
        html_path.write_text(inject(load_template(mode), data), encoding="utf-8")
        pdf_path = self.tmp / f"{mode}.pdf"
        return render_pdf(html_path, pdf_path), pdf_path, data

    def assert_pdf(self, mode):
        overflow, pdf_path, data = self.render(mode)
        self.assertEqual(overflow, [])
        # 문제 한 쪽씩. 답안지는 힌트가 있는 문제가 하나라도 있으면 끝에 Hint 쪽이 붙는다
        has_hint = any(p.get("hints") for p in data["problems"])
        pages = len(SMOKE_IDS) + (1 if mode == "answers" and has_hint else 0)
        with fitz.open(pdf_path) as doc:
            self.assertEqual(doc.page_count, pages)
            self.assertAlmostEqual(doc[0].rect.width, 841.89, delta=1)    # 297mm
            self.assertAlmostEqual(doc[0].rect.height, 595.28, delta=1)   # 210mm
            text = "".join(page.get_text() for page in doc)
        self.assertNotIn("$", text, "TeX 원문이 PDF에 남음")

    def test_problems_pdf(self):
        self.assert_pdf("problems")

    def test_answers_pdf(self):
        self.assert_pdf("answers")

    def test_missing_vendor_fails_loudly(self):
        with tempfile.TemporaryDirectory() as empty, patch.object(paths, "VENDOR", Path(empty)):
            with self.assertRaisesRegex(RenderError, "KaTeX를 불러오지 못함"):
                self.render("problems")
        self.assertFalse((self.tmp / "problems.pdf").exists())

    def test_tex_syntax_error_fails(self):
        def broken(data):
            data["problems"][0]["html"]["ask"] = "<ul><li>$\\notacommand x$</li></ul>"
        with self.assertRaisesRegex(RenderError, "TeX 문법 오류"):
            self.render("problems", broken)

    def test_unclosed_math_left_as_raw_tex_fails(self):
        def raw(data):
            data["problems"][0]["html"]["ask"] = "<ul><li>$\\frac{1}{$</li></ul>"
        with self.assertRaisesRegex(RenderError, "TeX 원문 남음"):
            self.render("problems", raw)


if __name__ == "__main__":
    unittest.main()
