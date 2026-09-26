import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from draw_exam import FONT_SIZE, draw_all, main, printed_font_pt  # noqa: E402

SIMPLE_FIG = '''import schemdraw.elements as elm
from schem_style import new_drawing


def draw():
    d = new_drawing()
    d.add(elm.Resistor().right().label("$R$"))
    return d
'''


def make_png(path, w, h):
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, w, h), False)
    pix.set_rect(pix.irect, (255, 255, 255))
    pix.save(str(path))


class DrawExamTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.exam = Path(self._tmp.name) / "2021-1_중간"
        self.red = self.exam / "figures" / "redrawn"
        self.red.mkdir(parents=True)
        (self.exam / "figures" / "figures.yaml").write_text("dpi: 144\nfigures: {}\n", encoding="utf-8")
        (self.red / "fig-Q2.py").write_text(SIMPLE_FIG, encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def test_draws_png(self):
        written, errors, _ = draw_all(self.exam)
        self.assertEqual(errors, [])
        self.assertEqual(written, [self.red / "fig-Q2.png"])
        self.assertEqual((self.red / "fig-Q2.png").read_bytes()[:8], b"\x89PNG\r\n\x1a\n")

    def test_broken_figure_reported_others_drawn(self):
        (self.red / "fig-Q1.py").write_text("def draw():\n    raise RuntimeError('boom')\n", encoding="utf-8")
        written, errors, _ = draw_all(self.exam)
        self.assertEqual(errors, ["fig-Q1.py: boom"])
        self.assertEqual(written, [self.red / "fig-Q2.png"])

    def test_missing_draw_function(self):
        (self.red / "fig-Q3.py").write_text("x = 1\n", encoding="utf-8")
        _, errors, _ = draw_all(self.exam)
        self.assertEqual(errors, ["fig-Q3.py: draw() 없음"])

    def test_printed_font_pt(self):
        # 크롭 1인치 폭, 다시 그린 그림 2인치 폭 → 글자는 절반 크기로 찍힌다
        self.assertAlmostEqual(printed_font_pt(144, 144, 864, dpi=432), FONT_SIZE / 2)

    def test_font_warning_when_crop_much_narrower(self):
        make_png(self.exam / "figures" / "fig-Q2.png", 20, 20)
        _, _, warnings = draw_all(self.exam)
        self.assertEqual(len(warnings), 1)
        self.assertIn("fig-Q2.png: 인쇄 글자", warnings[0])

    def test_main_exit_codes_and_compare(self):
        make_png(self.exam / "figures" / "fig-Q2.png", 200, 60)
        sheet = Path(self._tmp.name) / "sheet.png"
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(main(["draw_exam.py"]), 2)
            self.assertEqual(main(["draw_exam.py", str(self.exam), "--compare", str(sheet)]), 0)
        self.assertEqual(fitz.Pixmap(str(sheet)).width, 1200)
        (self.red / "fig-Q1.py").write_text("def draw():\n    raise RuntimeError('boom')\n", encoding="utf-8")
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(main(["draw_exam.py", str(self.exam)]), 1)
        self.assertIn("ERROR fig-Q1.py: boom", out.getvalue())


if __name__ == "__main__":
    unittest.main()
