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


@unittest.skipUnless(HAS_PLAYWRIGHT, "playwright 없음")
class TestRenderSmoke(unittest.TestCase):
    """교과서 예제·장말문제와 기출 하나를 실제 Chrome으로 그린다 (인터넷 필요)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def render(self, mode):
        data = build_data(ids_selection(SMOKE_IDS, "스모크"), mode)
        html_path = self.tmp / f"{mode}.html"
        html_path.write_text(inject(load_template(mode), data), encoding="utf-8")
        pdf_path = self.tmp / f"{mode}.pdf"
        return render_pdf(html_path, pdf_path), pdf_path

    def assert_pdf(self, mode):
        overflow, pdf_path = self.render(mode)
        self.assertEqual(overflow, [])
        with fitz.open(pdf_path) as doc:
            self.assertEqual(doc.page_count, 3)
            self.assertAlmostEqual(doc[0].rect.width, 841.89, delta=1)    # 297mm
            self.assertAlmostEqual(doc[0].rect.height, 595.28, delta=1)   # 210mm

    def test_problems_pdf(self):
        self.assert_pdf("problems")

    def test_answers_pdf(self):
        self.assert_pdf("answers")


if __name__ == "__main__":
    unittest.main()
