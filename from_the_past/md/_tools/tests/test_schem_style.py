import sys
import tempfile
import unittest
from pathlib import Path

import pymupdf as fitz
import matplotlib
import matplotlib.pyplot as plt
import schemdraw.elements as elm

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from schem_style import (  # noqa: E402
    DPI,
    INCHES_PER_UNIT,
    RAIL_LW,
    Resistor,
    caption,
    gate_terminal,
    new_drawing,
    nmos,
    pmos,
    rail,
    save_png,
)


class FetTest(unittest.TestCase):
    def test_nmos_gate_left_drain_up(self):
        m = nmos(new_drawing())
        self.assertLess(m.gate.x, m.drain.x)
        self.assertGreater(m.drain.y, m.source.y)

    def test_pmos_gate_left_source_up(self):
        m = pmos(new_drawing())
        self.assertLess(m.gate.x, m.source.x)
        self.assertGreater(m.source.y, m.drain.y)

    def test_mirror_puts_gate_right(self):
        d = new_drawing()
        self.assertGreater(nmos(d, mirror=True).gate.x, 0)
        self.assertGreater(pmos(d, mirror=True).gate.x, 0)

    def test_placed_after_vertical_line_keeps_orientation(self):
        d = new_drawing()
        d.add(elm.Line().up().length(1))
        dot = d.add(elm.Dot())
        m = nmos(d, at=dot.center, anchor="source")
        self.assertAlmostEqual(m.source.x, dot.center.x)
        self.assertAlmostEqual(m.source.y, dot.center.y)
        self.assertGreater(m.drain.y, m.source.y)
        self.assertLess(m.gate.x, m.source.x)


class CaptionTest(unittest.TestCase):
    def _placed(self, d, c):
        d.draw(show=False)
        seg = c.segments[0]
        return c.transform.transform(seg.xy)

    def test_position_independent_of_preceding_element_direction(self):
        d1 = new_drawing()
        d1.add(elm.Line().up())
        c1 = caption(d1, (0, -2), "(a)")

        d2 = new_drawing()
        d2.add(elm.Line().left())
        c2 = caption(d2, (0, -2), "(a)")

        self.assertEqual(self._placed(d1, c1), self._placed(d2, c2))


class SaveTest(unittest.TestCase):
    def test_same_code_same_bytes_white_background(self):
        def build():
            d = new_drawing()
            m = nmos(d, label="$M_1$")
            gate_terminal(d, m.gate, "$V_{in}$", open_=True)
            caption(d, (0, -2.5), "(a)")
            return d
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / "a.png", Path(tmp) / "b.png"
            save_png(build(), a)
            save_png(build(), b)
            self.assertEqual(a.read_bytes(), b.read_bytes())
            self.assertEqual(tuple(fitz.Pixmap(str(a)).pixel(0, 0))[:3], (255, 255, 255))

    def test_closes_figure_after_save(self):
        # 완전히 빈 드로잉은 schemdraw 0.23의 getfig()에서 bbox가 inf가 되어 예외가 난다
        # (실제 fig-Q*.py는 항상 요소를 하나 이상 그리므로 해당 없음). 요소를 하나 둔다.
        with tempfile.TemporaryDirectory() as tmp:
            d = new_drawing()
            d.add(elm.Line().right().length(1))
            before = len(plt.get_fignums())
            save_png(d, Path(tmp) / "a.png")
            self.assertEqual(len(plt.get_fignums()), before)

    def test_png_width_follows_inches_per_unit(self):
        d = new_drawing()
        d.add(elm.Line().right().length(5))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.png"
            save_png(d, path)
            width = fitz.Pixmap(str(path)).width
        expected = 5 * INCHES_PER_UNIT * DPI
        self.assertAlmostEqual(width, expected, delta=expected * 0.1)


class ResistorTest(unittest.TestCase):
    def test_resistor_is_short_and_narrow(self):
        r = Resistor()
        xs = [p[0] for p in r.segments[0].path]
        ys = [p[1] for p in r.segments[0].path]
        self.assertAlmostEqual(max(ys), 0.11, delta=1e-9)
        self.assertAlmostEqual(min(ys), -0.11, delta=1e-9)
        self.assertAlmostEqual(max(xs) - min(xs), 0.55, delta=1e-9)


class RailTest(unittest.TestCase):
    def test_rail_uses_rail_linewidth(self):
        d = new_drawing()
        e = rail(d, (0, 0), (2, 0))
        self.assertEqual(e._userparams["lw"], RAIL_LW)


class LabelFontTest(unittest.TestCase):
    def test_labels_use_arial_bold(self):
        self.assertEqual(matplotlib.rcParams["mathtext.it"], "Arial:bold:italic")
        self.assertEqual(matplotlib.rcParams["mathtext.rm"], "Arial:bold")


if __name__ == "__main__":
    unittest.main()
