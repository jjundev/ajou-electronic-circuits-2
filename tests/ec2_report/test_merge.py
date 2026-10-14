import io
import os
import tempfile
import time
import unicodedata
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from pypdf import PdfReader, PdfWriter

from _util import make_root
from scripts.ec2_report import config, merge
from scripts.ec2_report.check import AI_WORDS


def blank_pdf(path: Path, pages: int) -> Path:
    w = PdfWriter()
    for _ in range(pages):
        w.add_blank_page(595, 842)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        w.write(f)
    return path


def pdf_bytes(pages: int) -> bytes:
    w = PdfWriter()
    for _ in range(pages):
        w.add_blank_page(595, 842)
    buf = io.BytesIO()
    w.write(buf)
    return buf.getvalue()


class MergeTestBase(unittest.TestCase):
    def setUp(self):
        self._d = tempfile.TemporaryDirectory()
        self.root = make_root(self._d.name)
        self.report = self.root / "설계과제" / "과제1" / "report"
        self.dl = self.root / "Downloads"
        self.dl.mkdir()
        self.paths = config.paths(1, self.root, config.load_course_info(self.root))
        self.trash = self.root / "Trash"
        self.trash.mkdir()
        self._trash_patch = mock.patch.object(merge, "TRASH", self.trash)
        self._trash_patch.start()

    def tearDown(self):
        self._trash_patch.stop()
        self._d.cleanup()

    def find(self):
        return merge.find_body(1, self.root, [self.report, self.dl])


class FindBodyTests(MergeTestBase):
    def test_find_body_picks_highest_version(self):
        blank_pdf(self.dl / "전자회로2 설계과제1 보고서 v1.pdf", 1)
        blank_pdf(self.dl / "전자회로2 설계과제1 보고서 v2.pdf", 1)
        self.assertEqual(self.find().path.name, "전자회로2 설계과제1 보고서 v2.pdf")

    def test_find_body_nfd_name(self):
        name = unicodedata.normalize("NFD", "전자회로2 설계과제1 보고서 v1.pdf")
        blank_pdf(self.dl / name, 1)
        self.assertTrue(self.find().path.exists())

    def test_find_body_duplicate_download_picks_newest(self):
        old = blank_pdf(self.dl / "전자회로2 설계과제1 보고서 v2.pdf", 1)
        new = blank_pdf(self.dl / "전자회로2 설계과제1 보고서 v2 (1).pdf", 1)
        t = time.time()
        os.utime(old, (t - 3600, t - 3600))
        os.utime(new, (t, t))
        self.assertEqual(self.find().path.name, new.name)

    def test_find_body_ignores_problem_pdf_and_final(self):
        blank_pdf(self.report.parent / "2026-2_전자회로2_설계과제1_v3.pdf", 1)
        blank_pdf(self.dl / "2026-2_전자회로2_설계과제1_v3.pdf", 1)
        blank_pdf(self.dl / self.paths.final_pdf.name, 1)
        blank_pdf(self.report / self.paths.cover_pdf.name, 1)
        with self.assertRaisesRegex(FileNotFoundError, "Downloads"):
            self.find()

    def test_find_body_notion_export_underscore_name(self):
        blank_pdf(self.dl / "599ef015-2a8c_전자회로2_설계과제1_보고서.pdf", 1)
        self.assertEqual(self.find().path.name, "599ef015-2a8c_전자회로2_설계과제1_보고서.pdf")

    def test_find_body_underscore_does_not_match_other_assignment(self):
        blank_pdf(self.dl / "x_전자회로2_설계과제11_보고서.pdf", 1)
        with self.assertRaises(FileNotFoundError):
            self.find()

    def test_find_body_other_assignment_ignored(self):
        blank_pdf(self.dl / "전자회로2 설계과제2 보고서 v5.pdf", 1)
        with self.assertRaises(FileNotFoundError):
            self.find()

    def test_find_body_zip_single_pdf(self):
        z = self.dl / "전자회로2 설계과제1 보고서 v3.zip"
        with zipfile.ZipFile(z, "w") as zf:
            zf.writestr("body.pdf", pdf_bytes(2))
        src = self.find()
        self.assertEqual(src.path.suffix, ".pdf")
        self.assertEqual(src.origin, z)
        self.assertEqual(len(PdfReader(src.path).pages), 2)

    def test_find_body_notion_export_zip_matches_inner_pdf(self):
        z = self.dl / "Export-1a2b3c4d.zip"
        with zipfile.ZipFile(z, "w") as zf:
            name = unicodedata.normalize("NFD", "전자회로2 설계과제1 보고서 v4 3f5b06d263bc80a8.pdf")
            zf.writestr(name, pdf_bytes(2))
            zf.writestr("__MACOSX/._" + name, b"x")
        blank_pdf(self.dl / "전자회로2 설계과제1 보고서 v3.pdf", 1)
        src = self.find()
        self.assertEqual(src.origin, z)
        self.assertEqual(len(PdfReader(src.path).pages), 2)

    def test_find_body_unrelated_zip_ignored(self):
        z = self.dl / "Export-ffff.zip"
        with zipfile.ZipFile(z, "w") as zf:
            zf.writestr("다른 문서.pdf", pdf_bytes(1))
        with self.assertRaises(FileNotFoundError):
            self.find()

    def test_find_body_zip_two_pdfs_rejected(self):
        z = self.dl / "전자회로2 설계과제1 보고서 v3.zip"
        with zipfile.ZipFile(z, "w") as zf:
            zf.writestr("a.pdf", pdf_bytes(1))
            zf.writestr("b.pdf", pdf_bytes(1))
        with self.assertRaises(ValueError):
            self.find()


class MergeTests(MergeTestBase):
    def fake_cover(self, n, submit_date=None, root=None):
        return blank_pdf(self.paths.cover_pdf, 1)

    def run_merge(self, **kw):
        with mock.patch.object(merge, "make_cover", side_effect=self.fake_cover), \
             mock.patch.object(merge, "_default_dirs", return_value=[self.report, self.dl]):
            return merge.merge(1, root=self.root, **kw)

    def test_merge_pages_metadata_and_trash(self):
        body = blank_pdf(self.dl / "전자회로2 설계과제1 보고서 v1.pdf", 3)
        r = self.run_merge(date="2026.10.30")
        self.assertEqual(r["pages"], 4)
        self.assertEqual(r["output"], self.paths.final_pdf)
        self.assertEqual(r["trashed"], self.trash / body.name)
        self.assertFalse(body.exists())
        self.assertTrue(r["trashed"].exists())
        meta = PdfReader(r["output"]).metadata
        self.assertEqual(meta.title, "전자회로2 설계과제1 보고서")
        self.assertEqual(meta.author, "홍길동")
        self.assertEqual(set(meta.keys()), {"/Title", "/Author"})
        self.assertIsNone(AI_WORDS.search(" ".join(str(v) for v in meta.values())))

    def test_merge_keep_body(self):
        body = blank_pdf(self.dl / "전자회로2 설계과제1 보고서 v1.pdf", 2)
        r = self.run_merge(keep_body=True)
        self.assertTrue(body.exists())
        self.assertIsNone(r["trashed"])
        self.assertEqual(list(self.trash.iterdir()), [])

    def test_merge_trash_name_collision_gets_number(self):
        name = "전자회로2 설계과제1 보고서.pdf"
        blank_pdf(self.trash / name, 1)
        blank_pdf(self.trash / "전자회로2 설계과제1 보고서 2.pdf", 1)
        blank_pdf(self.dl / name, 2)
        r = self.run_merge()
        self.assertEqual(r["trashed"], self.trash / "전자회로2 설계과제1 보고서 3.pdf")

    def test_merge_without_trash_keeps_body(self):
        body = blank_pdf(self.dl / "전자회로2 설계과제1 보고서.pdf", 2)
        with mock.patch.object(merge, "TRASH", self.root / "no-trash"):
            r = self.run_merge()
        self.assertTrue(body.exists())
        self.assertIsNone(r["trashed"])
        self.assertTrue(any("휴지통" in w for w in r["warnings"]))

    def test_merge_reports_body_warnings(self):
        blank_pdf(self.dl / "전자회로2 설계과제1 보고서.pdf", 2)
        self.p_md = self.paths.report_md
        self.p_md.write_text("![](figs/01_a.png)\n", encoding="utf-8")
        r = self.run_merge()
        self.assertTrue(any("그림" in w for w in r["warnings"]))

    def test_merge_explicit_body_zip_deletes_zip(self):
        z = self.root / "x.zip"
        with zipfile.ZipFile(z, "w") as zf:
            zf.writestr("body.pdf", pdf_bytes(2))
        r = self.run_merge(body=z)
        self.assertEqual(r["pages"], 3)
        self.assertEqual(r["body_origin"], z)
        self.assertFalse(z.exists())
        self.assertEqual(r["trashed"], self.trash / "x.zip")

    def test_lint_body_flags_version_title_images_and_old_refs(self):
        text = "전자회로2 설계과제1 보고서 v2\n설계 조건\n(1 % 차이는 2-(d) 에서 확인)\n"
        w = merge.lint_body(text, images=3, expected_images=4)
        self.assertEqual(len(w), 3)
        self.assertTrue(any("v2" in x for x in w))
        self.assertTrue(any("3장" in x and "4장" in x for x in w))
        self.assertTrue(any("2-(d)" in x for x in w))

    def test_lint_body_flags_emoji(self):
        w = merge.lint_body("M1 saturation ✔\nM2 saturation ✔\n▶ 조건은", images=4, expected_images=4)
        self.assertEqual(len(w), 1)
        self.assertIn("▶ ✔", w[0])

    def test_lint_body_clean(self):
        text = "전자회로2 설계과제1 보고서\n2(100 μ)/0.0736  V  (1+0.1×0.15) → ① −3 dB 180°\nSpice Problem (d)\n"
        self.assertEqual(merge.lint_body(text, images=4, expected_images=4), [])

    def test_verify_rejects_page_mismatch(self):
        p = blank_pdf(self.root / "m.pdf", 3)
        with self.assertRaises(ValueError):
            merge.verify_merged(p, 4)
        self.assertEqual(merge.verify_merged(p, 3)["pages"], 3)

    def test_verify_rejects_non_a4_first_page(self):
        w = PdfWriter()
        w.add_blank_page(612, 792)
        p = self.root / "letter.pdf"
        with open(p, "wb") as f:
            w.write(f)
        with self.assertRaises(ValueError):
            merge.verify_merged(p, 1)


if __name__ == "__main__":
    unittest.main()
