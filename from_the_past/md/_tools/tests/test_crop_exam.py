import sys
import tempfile
import unittest
from pathlib import Path

import pymupdf as fitz

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from crop_exam import crop_all, figure_filename  # noqa: E402
from exam_fixtures import make_pdf  # noqa: E402


def make_exam(root: Path, figures_yaml: str) -> Path:
    fig_dir = root / "md" / "2021-1_중간" / "figures"
    fig_dir.mkdir(parents=True)
    (fig_dir / "figures.yaml").write_text(figures_yaml, encoding="utf-8")
    return fig_dir.parent


class FigureFilenameTest(unittest.TestCase):
    def test_single(self):
        self.assertEqual(figure_filename("Q2"), "fig-Q2.png")

    def test_second_figure(self):
        self.assertEqual(figure_filename("Q2-2"), "fig-Q2-2.png")


class CropAllTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        make_pdf(self.root / "src" / "a.pdf")
        make_pdf(self.root / "23-1 기말" / "기말고사.pdf", pages=2)

    def tearDown(self):
        self.tmp.cleanup()

    def test_crops_from_each_entry_pdf(self):
        exam = make_exam(self.root, """dpi: 72
figures:
  "Q1": {pdf: ../../../src/a.pdf, pdf_page: 1, bbox: [0, 0, 100, 50]}
  "Q2": {pdf: "../../../23-1 기말/기말고사.pdf", pdf_page: 2, bbox: [0, 0, 50, 50]}
""")
        out = crop_all(exam)
        self.assertEqual([p.name for p in out], ["fig-Q1.png", "fig-Q2.png"])
        a, b = fitz.Pixmap(str(out[0])), fitz.Pixmap(str(out[1]))
        self.assertEqual((a.width, a.height), (100, 50))
        self.assertEqual((b.width, b.height), (50, 50))

    def test_empty_figures_is_noop(self):
        exam = make_exam(self.root, "dpi: 72\nfigures:\n")
        self.assertEqual(crop_all(exam), [])

    def test_unquoted_id_rejected(self):
        exam = make_exam(self.root, "figures:\n  1: {pdf: ../../../src/a.pdf, pdf_page: 1, bbox: [0, 0, 10, 10]}\n")
        with self.assertRaisesRegex(ValueError, "형식"):
            crop_all(exam)

    def test_missing_pdf_key(self):
        exam = make_exam(self.root, 'figures:\n  "Q1": {pdf_page: 1, bbox: [0, 0, 10, 10]}\n')
        with self.assertRaisesRegex(ValueError, "pdf 경로가 없음"):
            crop_all(exam)

    def test_missing_pdf_file(self):
        exam = make_exam(self.root, 'figures:\n  "Q1": {pdf: ../../../src/none.pdf, pdf_page: 1, bbox: [0, 0, 10, 10]}\n')
        with self.assertRaisesRegex(ValueError, "PDF 없음"):
            crop_all(exam)

    def test_page_out_of_range(self):
        exam = make_exam(self.root, 'figures:\n  "Q1": {pdf: ../../../src/a.pdf, pdf_page: 3, bbox: [0, 0, 10, 10]}\n')
        with self.assertRaisesRegex(ValueError, "범위 밖"):
            crop_all(exam)

    def test_bbox_outside_page(self):
        exam = make_exam(self.root, 'figures:\n  "Q1": {pdf: ../../../src/a.pdf, pdf_page: 1, bbox: [0, 0, 300, 50]}\n')
        with self.assertRaisesRegex(ValueError, "bbox"):
            crop_all(exam)

    def test_missing_bbox(self):
        exam = make_exam(self.root, 'figures:\n  "Q1": {pdf: ../../../src/a.pdf, pdf_page: 1}\n')
        with self.assertRaisesRegex(ValueError, "bbox 는 \\[x0, y0, x1, y1\\] 숫자 4개"):
            crop_all(exam)

    def test_bbox_wrong_length(self):
        exam = make_exam(self.root, 'figures:\n  "Q1": {pdf: ../../../src/a.pdf, pdf_page: 1, bbox: [1, 2, 3]}\n')
        with self.assertRaisesRegex(ValueError, "bbox 는"):
            crop_all(exam)

    def test_pdf_null(self):
        exam = make_exam(self.root, 'figures:\n  "Q1": {pdf: null, pdf_page: 1, bbox: [0, 0, 10, 10]}\n')
        with self.assertRaisesRegex(ValueError, "pdf 경로가 없음"):
            crop_all(exam)

    def test_top_level_not_mapping(self):
        exam = make_exam(self.root, "- a\n- b\n")
        with self.assertRaisesRegex(ValueError, "최상위"):
            crop_all(exam)


if __name__ == "__main__":
    unittest.main()
