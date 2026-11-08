"""설계과제2(캐스코드 주파수 응답) 손계산·SPICE 파이프라인 테스트."""
import sys, json, shutil, subprocess, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIM = ROOT / "설계과제/과제2/sim"
sys.path.insert(0, str(SIM))


class HandcalcTests(unittest.TestCase):
    def setUp(self):
        import handcalc
        self.h, self.d = handcalc, handcalc.design()

    def test_gain_is_exactly_ten(self):
        self.assertAlmostEqual(self.d["A0"], -10.0, places=6)

    def test_power_and_current_split(self):
        self.assertAlmostEqual(self.d["P"], 0.4e-3, places=9)
        self.assertAlmostEqual(self.d["I2"], self.d["I1"] / 2)

    def test_operating_point_matches_spec(self):
        d = self.d
        self.assertAlmostEqual(d["RL"], 1930, delta=15)
        self.assertAlmostEqual(d["Vout"], 0.614, delta=0.003)
        for k, w in (("M1", 62.1), ("M2", 31.0), ("M3", 14.0)):
            self.assertAlmostEqual(d["W"][k], w, delta=0.2)
            self.assertEqual(round(d["W"][k], 2), d["W"][k])
        self.assertAlmostEqual(d["Vin"], 0.55)
        self.assertAlmostEqual(d["Vb1"], 0.85)
        self.assertAlmostEqual(d["Vb2"], 0.30)
        self.assertAlmostEqual(d["AXY"], -2.00, delta=0.05)

    def test_miller_poles(self):
        for k, f in (("X", 1.94e9), ("Y", 3.28e9), ("out", 3.80e9)):
            self.assertAlmostEqual(self.d["f"][k] / f, 1, delta=0.03)

    def test_saturation_margins(self):
        for k, m in (("M1", 0.15), ("M2", 0.164), ("M3", 0.40)):
            self.assertAlmostEqual(self.d["sat"][k], m, delta=0.005)

    def test_check_rejects_slow_input_pole(self):
        self.h.check(self.d)
        with self.assertRaises(AssertionError):
            self.h.check(self.h.design(I1=1e-3, vov1=0.10))

    def test_other_current_keeps_gain(self):
        d5 = self.h.design(I1=500e-6)
        self.assertAlmostEqual(d5["A0"], -10.0, places=6)
        self.assertLess(d5["f"]["X"], self.d["f"]["X"])

    def test_write_outputs(self):
        with tempfile.TemporaryDirectory() as t:
            self.h.write_outputs(self.d, Path(t))
            inc = (Path(t) / "params.inc").read_text()
            self.assertIn("XJ=0.49u", inc)
            self.assertIn(f"W1={self.d['W']['M1']}u", inc)
            self.assertIn("f", json.loads((Path(t) / "design.json").read_text()))


if __name__ == "__main__":
    unittest.main()
