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

    def test_crop_suffix(self):
        self.assertEqual(figure_filename("10.16", "a"), "fig10-16-a.png")
        self.assertEqual(figure_filename("9.2", "abc"), "fig9-02-abc.png")


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

    def test_rejects_pdf_page_out_of_range(self):
        for page in (0, 2, -1):
            with self.subTest(pdf_page=page), tempfile.TemporaryDirectory() as t:
                ch = make_chapter(Path(t), (
                    "pdf: ../../book.pdf\n"
                    "figures:\n"
                    f'  "9.1": {{pdf_page: {page}, bbox: [0, 0, 72, 36]}}\n'
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


class CropsTest(unittest.TestCase):
    def crop(self, fig_line):
        with tempfile.TemporaryDirectory() as t:
            ch = make_chapter(Path(t), "pdf: ../../book.pdf\ndpi: 144\nfigures:\n" + fig_line + "\n")
            outs = crop_all(ch)
            return [(o.name, fitz.Pixmap(str(o)).width, fitz.Pixmap(str(o)).height) for o in outs]

    def test_crops_written_after_whole(self):
        got = self.crop('  "9.30": {pdf_page: 1, bbox: [0, 0, 72, 36], '
                        'crops: {a: [0, 0, 36, 36], bc: [36, 0, 72, 18]}}')
        self.assertEqual(got, [("fig9-30.png", 144, 72), ("fig9-30-a.png", 72, 72),
                               ("fig9-30-bc.png", 72, 36)])

    def test_rejects_bad_crop_name(self):
        for name in ("A", "a_b", "1"):          # "1"은 YAML에서 int가 된다
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "크롭 이름"):
                self.crop(f'  "9.30": {{pdf_page: 1, bbox: [0, 0, 72, 36], crops: {{{name}: [0, 0, 10, 10]}}}}')

    def test_rejects_crop_bbox_wrong_length(self):
        with self.assertRaisesRegex(ValueError, "bbox"):
            self.crop('  "9.30": {pdf_page: 1, bbox: [0, 0, 72, 36], crops: {a: [0, 0, 10]}}')

    def test_rejects_crop_bbox_outside_page(self):
        with self.assertRaisesRegex(ValueError, "범위 밖"):
            self.crop('  "9.30": {pdf_page: 1, bbox: [0, 0, 72, 36], crops: {a: [0, 0, 300, 50]}}')

    def test_rejects_crops_not_mapping(self):
        with self.assertRaisesRegex(ValueError, "crops"):
            self.crop('  "9.30": {pdf_page: 1, bbox: [0, 0, 72, 36], crops: [0, 0, 10, 10]}')


if __name__ == "__main__":
    unittest.main()
