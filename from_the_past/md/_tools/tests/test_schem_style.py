import sys
import tempfile
import unittest
from pathlib import Path

import fitz
import schemdraw.elements as elm

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from schem_style import caption, gate_terminal, new_drawing, nmos, pmos, save_png  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
