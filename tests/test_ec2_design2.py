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


DEV = """ Mos1: Level 1 MOSfet model with Meyer capacitance model
     device                    m3                    m2                    m1
      model                 cmosp                 cmosn                 cmosn
         id            0.00020668           0.000207447           0.000414127
        vdsat                     0                     0                     0
        cgs           1.94032e-14           4.45142e-14           8.91721e-14
        vth             ?????????             ?????????             ?????????
"""


class SpiceIoTests(unittest.TestCase):
    def setUp(self):
        import spice_io
        self.s = spice_io

    def test_parse_scalars(self):
        d = self.s.parse_scalars("v(y) = 2.997411e-01\ni(vdd) = -4.14127e-04\na0 = 2.03080e+01\n")
        self.assertAlmostEqual(d["v(y)"], 0.2997411)
        self.assertAlmostEqual(d["i(vdd)"], -4.14127e-4)

    def test_parse_devices(self):
        d = self.s.parse_devices(DEV + DEV.replace("m3", "m9"))
        self.assertAlmostEqual(d["M1"]["id"], 0.000414127)
        self.assertAlmostEqual(d["M2"]["cgs"], 4.45142e-14)
        self.assertIn("M9", d)
        self.assertNotEqual(d["M1"]["vth"], d["M1"]["vth"])  # nan

    def test_parse_pz(self):
        p, z = self.s.parse_pz("pole(1) = -4.67097e+10,0.000000e+00\npole(2) = -9.76058e+09,0.000000e+00\n"
                               "zero(1) = 2.222905e+11,0.000000e+00\n")
        self.assertEqual(p, [complex(-4.67097e10, 0), complex(-9.76058e9, 0)])
        self.assertEqual(z, [complex(2.222905e11, 0)])

    def test_parse_pz_complex(self):
        p, _ = self.s.parse_pz("pole(1) = -1.0e+10,5.0e+09\npole(2) = -1.0e+10,-5.0e+09\n")
        self.assertEqual(p[0].imag, 5e9)
        self.assertEqual(p[1].imag, -5e9)


@unittest.skipUnless(shutil.which("ngspice"), "ngspice not installed")
class SpiceRunTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(["python3", "handcalc.py"], cwd=SIM, check=True, capture_output=True)
        subprocess.run(["ngspice", "-b", "cascode.cir"], cwd=SIM, check=True, capture_output=True)
        import spice_io as s
        cls.op = (SIM / "op.txt").read_text()
        cls.dev = s.parse_devices(cls.op.split("=== DEVICES ===")[1])
        cls.meas = s.parse_scalars((SIM / "meas.txt").read_text())
        cls.poles, _ = s.parse_pz((SIM / "pz.txt").read_text())

    def test_currents_and_power(self):
        i2, i3 = self.dev["M2"]["id"], abs(self.dev["M3"]["id"])
        self.assertLess(abs(i2 - i3) / i3, 0.01)
        self.assertLessEqual(self.dev["M1"]["id"] * 1.0, 0.5e-3)

    def test_gain_near_ten(self):
        self.assertAlmostEqual(10 ** (self.meas["a0"] / 20), 10, delta=1.0)

    def test_all_poles_above_1ghz(self):
        self.assertEqual(len(self.poles), 3)
        self.assertGreaterEqual(min(abs(p) for p in self.poles) / 6.283185307, 1e9)


if __name__ == "__main__":
    unittest.main()
