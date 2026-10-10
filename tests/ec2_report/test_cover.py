import shutil
import tempfile
import unittest
from pathlib import Path

from _util import REPO
from scripts.ec2_report import config, cover
from scripts.ec2_report.check import AI_WORDS
from scripts.ec2_report.html2pdf import PdfError, resolve_chrome

INFO = config.load_course_info(REPO)


def chrome_available() -> bool:
    try:
        resolve_chrome(INFO["chrome"])
        return True
    except PdfError:
        return False


def make_root(d: Path, text: str | None = None) -> Path:
    (d / ".claude").mkdir()
    src = (REPO / ".claude" / "과목정보.md").read_text(encoding="utf-8")
    (d / ".claude" / "과목정보.md").write_text(text or src, encoding="utf-8")
    (d / "설계과제" / "과제1").mkdir(parents=True)
    return d


class CoverTests(unittest.TestCase):
    def test_cover_title(self):
        self.assertEqual(cover.cover_title(1), "설계과제 1 보고서")

    def test_render_fills_all_placeholders(self):
        html = cover.render_cover_html("설계과제 1 보고서", INFO, "2026.10.30")
        self.assertNotIn("{{", html)
        self.assertIn("202220953", html)
        self.assertIn("C024", html)
        self.assertIn("2026.10.30", html)
        self.assertNotIn("조</dt>", html)
        self.assertIn("윤리", html)
        self.assertIsNone(AI_WORDS.search(html))

    def test_render_rejects_leftover_placeholder(self):
        info = dict(INFO)
        with self.assertRaises(ValueError):
            cover.render_cover_html("{{X}}", info, "2026.10.30")

    def test_missing_identity_blocks_cover(self):
        src = (REPO / ".claude" / "과목정보.md").read_text(encoding="utf-8")
        text = src.replace('student_id: "202220953"', "student_id: ~")
        with tempfile.TemporaryDirectory() as d:
            root = make_root(Path(d), text)
            with self.assertRaisesRegex(ValueError, "student_id"):
                cover.make_cover(1, "2026.10.30", root)
            p = config.paths(1, root, config.load_course_info(root))
            self.assertFalse(p.cover_pdf.exists())

    @unittest.skipUnless(chrome_available(), "Chrome 없음")
    def test_make_cover_is_one_a4_page(self):
        from pypdf import PdfReader
        with tempfile.TemporaryDirectory() as d:
            root = make_root(Path(d))
            pdf = cover.make_cover(1, "2026.10.30", root)
            self.assertEqual(pdf.name, "설계과제1 표지.pdf")
            r = PdfReader(pdf)
            self.assertEqual(len(r.pages), 1)
            box = r.pages[0].mediabox
            w, h = float(box.width) * 25.4 / 72, float(box.height) * 25.4 / 72
            self.assertAlmostEqual(w, 210, delta=5)
            self.assertAlmostEqual(h, 297, delta=5)


if __name__ == "__main__":
    unittest.main()
