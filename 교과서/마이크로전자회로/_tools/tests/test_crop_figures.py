import sys
import tempfile
import unittest
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from crop_figures import crop_all, figure_filename  # noqa: E402


class FigureFilenameTest(unittest.TestCase):
    def test_zero_pads_single_digit(self):
        self.assertEqual(figure_filename("9.2"), "fig9-02.png")

    def test_keeps_two_digits(self):
        self.assertEqual(figure_filename("9.42"), "fig9-42.png")


def make_chapter(root: Path, figures_yaml: str) -> Path:
    doc = fitz.open()
    doc.new_page(width=200, height=100)
    doc.save(str(root / "book.pdf"))
    fig_dir = root / "ch" / "figures"
    fig_dir.mkdir(parents=True)
    (fig_dir / "figures.yaml").write_text(figures_yaml, encoding="utf-8")
    return root / "ch"


class CropAllTest(unittest.TestCase):
    def test_crops_bbox_at_dpi(self):
        with tempfile.TemporaryDirectory() as t:
            ch = make_chapter(Path(t), (
                "pdf: ../../book.pdf\n"
                "dpi: 144\n"
                "figures:\n"
                '  "9.30": {pdf_page: 1, bbox: [0, 0, 72, 36]}\n'
            ))
            [out] = crop_all(ch)
            self.assertEqual(out.name, "fig9-30.png")
            pix = fitz.Pixmap(str(out))
            self.assertEqual((pix.width, pix.height), (144, 72))

    def test_rejects_bbox_outside_page(self):
        with tempfile.TemporaryDirectory() as t:
            ch = make_chapter(Path(t), (
                "pdf: ../../book.pdf\n"
                "figures:\n"
                '  "9.1": {pdf_page: 1, bbox: [0, 0, 300, 50]}\n'
            ))
            with self.assertRaises(ValueError):
                crop_all(ch)

    def test_rejects_unquoted_id(self):
        with tempfile.TemporaryDirectory() as t:
            ch = make_chapter(Path(t), (
                "pdf: ../../book.pdf\n"
                "figures:\n"
                "  9.30: {pdf_page: 1, bbox: [0, 0, 72, 36]}\n"
            ))
            with self.assertRaises(ValueError):
                crop_all(ch)


if __name__ == "__main__":
    unittest.main()
