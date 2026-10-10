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

    def tearDown(self):
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

    def test_merge_pages_metadata_and_delete(self):
        body = blank_pdf(self.dl / "전자회로2 설계과제1 보고서 v1.pdf", 3)
        r = self.run_merge(date="2026.10.30")
        self.assertEqual(r["pages"], 4)
        self.assertEqual(r["output"], self.paths.final_pdf)
        self.assertTrue(r["deleted"])
        self.assertFalse(body.exists())
        meta = PdfReader(r["output"]).metadata
        self.assertEqual(meta.title, "전자회로2 설계과제1 보고서")
        self.assertEqual(meta.author, "홍길동")
        self.assertEqual(set(meta.keys()), {"/Title", "/Author"})
        self.assertIsNone(AI_WORDS.search(" ".join(str(v) for v in meta.values())))

    def test_merge_keep_body(self):
        body = blank_pdf(self.dl / "전자회로2 설계과제1 보고서 v1.pdf", 2)
        r = self.run_merge(keep_body=True)
        self.assertTrue(body.exists())
        self.assertFalse(r["deleted"])

    def test_merge_explicit_body_zip_deletes_zip(self):
        z = self.root / "x.zip"
        with zipfile.ZipFile(z, "w") as zf:
            zf.writestr("body.pdf", pdf_bytes(2))
        r = self.run_merge(body=z)
        self.assertEqual(r["pages"], 3)
        self.assertEqual(r["body_origin"], z)
        self.assertFalse(z.exists())

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
