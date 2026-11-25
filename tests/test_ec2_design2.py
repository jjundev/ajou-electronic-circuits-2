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

    def test_gain_matches_nodal_analysis(self):
        # Gm은 출력을 단락하고 구해야 한다: 3노드 소신호 회로를 직접 풀어 낸 이득과 같아야 한다
        self.assertAlmostEqual(self.d["nodal"]["A0"] / self.d["A0"], 1, delta=1e-6)

    def test_nodal_poles_with_table_caps(self):
        # 과제 표 C로 3노드 회로를 정확히 풀면 X·Y 극점이 Miller 값에서 서로 벌어진다
        for f, ref in zip(self.d["nodal"]["f"], (1.59e9, 3.78e9, 5.96e9)):
            self.assertAlmostEqual(f / ref, 1, delta=0.03)

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
        subprocess.run([sys.executable, "handcalc.py"], cwd=SIM, check=True, capture_output=True)
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


class PolemapTests(unittest.TestCase):
    def setUp(self):
        import polemap
        self.m = polemap

    def test_map_poles_unique(self):
        base = [-1e10, -2e10, -4e10]
        sh = {"X": [-0.9e10, -2e10, -4e10], "Y": [-1e10, -1.8e10, -4e10], "out": [-1e10, -2e10, -3.7e10]}
        self.assertEqual(self.m.map_poles(base, sh), {"X": 0, "Y": 1, "out": 2})

    def test_map_poles_ambiguous_raises(self):
        base = [-1e10, -2e10, -4e10]
        sh = {"X": [-0.9e10, -2e10, -4e10], "Y": [-0.9e10, -2e10, -4e10], "out": [-1e10, -2e10, -3.7e10]}
        with self.assertRaises(ValueError):
            self.m.map_poles(base, sh)

    def test_map_poles_coupled_pair_assigned_one_to_one(self):
        # 실제 회로 모양: X와 Y가 CGD1로 결합해 두 노드 모두 같은 극점을 가장 많이 움직인다
        base = [-1.0e10, -2.0e10, -4.0e10]
        sh = {"X": [-0.9964e10, -1.9988e10, -3.9802e10],
              "Y": [-0.9980e10, -1.9998e10, -3.9717e10],
              "out": [-0.9989e10, -1.9186e10, -3.9940e10]}
        self.assertEqual(self.m.map_poles(base, sh), {"X": 0, "Y": 2, "out": 1})

    def test_map_poles_near_tie_raises(self):
        # X와 Y가 두 극점을 거의 같은 비율로 움직이면 대응을 정할 수 없다 (정확히 같지 않아도)
        b = [-1e10, -2e10, -4e10]
        sh = {"X": [b[0] * 1.0040, b[1] * 1.0006, b[2] * 1.0041],
              "Y": [b[0] * 1.0038, b[1] * 1.0001, b[2] * 1.0040],
              "out": [b[0] * 1.001, b[1] * 1.04, b[2] * 1.001]}
        with self.assertRaises(ValueError):
            self.m.map_poles(b, sh)

    @unittest.skipUnless(shutil.which("ngspice"), "ngspice not installed")
    def test_real_map_x_is_dominant(self):
        subprocess.run([sys.executable, "polemap.py"], cwd=SIM, check=True, capture_output=True)
        pm = json.loads((SIM / "polemap.json").read_text())
        self.assertEqual(set(pm), {"X", "Y", "out"})
        self.assertEqual(pm["X"]["index"], 0)
        self.assertGreaterEqual(min(v["f_hz"] for v in pm.values()), 1e9)


def spice_io_devices():
    import spice_io
    return spice_io.parse_devices((SIM / "op.txt").read_text().split("=== DEVICES ===")[1])


class PostTests(unittest.TestCase):
    def setUp(self):
        import post
        self.p = post

    def test_sat_rows_ignore_vdsat(self):
        dev = {"M1": {"id": 4e-4, "vgs": 0.55, "vds": 0.30, "vdsat": 0.0},
               "M2": {"id": 2e-4, "vgs": 0.55, "vds": 0.314, "vdsat": 0.0},
               "M3": {"id": -2e-4, "vgs": -0.70, "vds": -0.70, "vdsat": 0.0}}
        r = {x["name"]: x for x in self.p.sat_rows(dev)}
        self.assertAlmostEqual(r["M1"]["margin"], 0.15)
        self.assertAlmostEqual(r["M3"]["margin"], 0.40)
        self.assertTrue(all(x["ok"] for x in r.values()))

    def test_node_caps_roundtrip(self):
        c = self.p.node_caps({"X": 1 / (2 * 3.141592653589793 * 500 * 164e-15)}, {"X": 500})
        self.assertAlmostEqual(c["X"], 164, places=6)

    def test_spice_node_R_matches_design(self):
        d = json.loads((SIM / "design.json").read_text())
        dev = {"M1": {"gm": d["gm"]["M1"], "gds": 1 / d["ro"]["M1"]},
               "M2": {"gm": d["gm"]["M2"], "gds": 1 / d["ro"]["M2"]},
               "M3": {"gm": d["gm"]["M3"], "gds": 1 / d["ro"]["M3"]}}
        R = self.p.spice_node_R(dev, d["RL"])
        for k in ("X", "Y", "out"):
            self.assertAlmostEqual(R[k] / d["R"][k], 1, delta=0.01)

    def test_spice_gain_matches_design_formula(self):
        d = json.loads((SIM / "design.json").read_text())
        dev = {k: {"gm": d["gm"][k], "gds": 1 / d["ro"][k]} for k in ("M1", "M2", "M3")}
        self.assertAlmostEqual(self.p.spice_gain(dev, d["RL"]) / d["nodal"]["A0"], 1, delta=1e-6)

    def test_spice_nodal_with_design_values_equals_design_nodal(self):
        d = json.loads((SIM / "design.json").read_text())
        dev = {k: {"gm": d["gm"][k], "gds": 1 / d["ro"][k], "cgs": c["CGS"] * 1e-15, "cgd": c["CGD"] * 1e-15,
                   "cbd": c["CDB"] * 1e-15, "cbs": c["CSB"] * 1e-15} for k, c in d["caps"].items()}
        n = self.p.spice_nodal(dev, d["RL"])
        self.assertAlmostEqual(n["A0"], d["nodal"]["A0"], places=9)
        for a, b in zip(n["f"], d["nodal"]["f"]):
            self.assertAlmostEqual(a / b, 1, places=9)

    def test_label_nodal_poles_by_perturbation(self):
        import handcalc
        lab = self.p.label_nodal(handcalc.design())
        for k, ref in (("X", 1.590e9), ("Y", 5.959e9), ("out", 3.786e9)):
            self.assertAlmostEqual(lab[k] / ref, 1, delta=0.005)

    def test_label_nodal_poles_when_y_and_out_swap_order(self):
        # vov2 = 0.2에서는 정확해의 Y 극점이 out 극점보다 낮다: |p| 순서로 붙이면 둘이 바뀐다
        import handcalc
        lab = self.p.label_nodal(handcalc.design(vov2=0.2))
        self.assertAlmostEqual(lab["Y"] / 5.711e9, 1, delta=0.005)
        self.assertAlmostEqual(lab["out"] / 7.551e9, 1, delta=0.005)

    def test_sensitivity_rows_one_at_a_time(self):
        # 표 C 정확해에서 한 가지씩 SPICE 값으로 바꿔 어떤 차이가 극점을 움직였는지 본다
        d = json.loads((SIM / "design.json").read_text())
        dev = spice_io_devices()
        rows = dict(self.p.sensitivity_rows(d, dev))
        ref = {"기준 (표 C 정확해)": (1.590, 5.959), "C_GD1 = 0 (X-Y 결합 제거)": (2.944, 4.946),
               "C_GD1만 SPICE 값": (1.412, 6.143), "C_GS1만 SPICE 값": (1.704, 6.450),
               "Y 노드 C만 SPICE 값": (1.628, 6.483), "gm, gds만 SPICE 값": (1.601, 6.119),
               "모두 SPICE 값": (1.552, 7.431)}
        self.assertEqual(list(rows), list(ref))
        for k, (fx, fy) in ref.items():
            self.assertAlmostEqual(rows[k]["X"] / 1e9, fx, delta=0.002)
            self.assertAlmostEqual(rows[k]["Y"] / 1e9, fy, delta=0.002)

    def test_device_node_caps_matches_design_with_table_caps(self):
        d = json.loads((SIM / "design.json").read_text())
        dev = {k: {"cgs": c["CGS"] * 1e-15, "cgd": c["CGD"] * 1e-15,
                   "cbd": c["CDB"] * 1e-15, "cbs": c["CSB"] * 1e-15} for k, c in d["caps"].items()}
        c = self.p.device_node_caps(dev, d["AXY"])
        for k in ("X", "Y", "out"):
            self.assertAlmostEqual(c[k], d["C"][k], places=6)

    def test_err_pct(self):
        self.assertAlmostEqual(self.p.err_pct(11.0, 10.0), 10.0)

    @unittest.skipUnless(shutil.which("ngspice"), "ngspice not installed")
    def test_outputs_written(self):
        subprocess.run([sys.executable, "post.py"], cwd=SIM, check=True, capture_output=True)
        figs = SIM.parent / "report/figs"
        for f in ("02_bode_design.png", "04_ac_bode.png"):
            self.assertTrue((figs / f).stat().st_size > 10_000)
        self.assertIn("saturation", (SIM.parent / "report/sat_table.md").read_text())
        self.assertIn("오차", (SIM.parent / "report/compare.md").read_text())


class AscTests(unittest.TestCase):
    def test_asc_encoding_and_content(self):
        subprocess.run([sys.executable, "make_asc.py"], cwd=SIM / "ltspice", check=True, capture_output=True)
        raw = (SIM / "ltspice/cascode.asc").read_bytes()
        self.assertFalse(raw.startswith(b"\xff\xfe"))           # BOM 금지
        txt = raw.decode("utf-16-le")
        for s in ("202220953 신현준", "CMOSN", "CMOSP", ".include ../MOSFET_model.lib", "\r\n"):
            self.assertIn(s, txt)

    def test_asc_mos_label_short_junction_params_hidden(self):
        # 화면에 보이는 Value2는 l, w만 (길면 RL 값과 .op 라벨을 덮는다). ad/as/pd/ps는 SpiceLine으로
        subprocess.run([sys.executable, "make_asc.py"], cwd=SIM / "ltspice", check=True, capture_output=True)
        txt = (SIM / "ltspice/cascode.asc").read_bytes().decode("utf-16-le")
        v2 = [l for l in txt.splitlines() if l.startswith("SYMATTR Value2")]
        sl = [l for l in txt.splitlines() if l.startswith("SYMATTR SpiceLine")]
        self.assertEqual(len(v2), 3)
        self.assertEqual(len(sl), 3)
        for l in v2:
            self.assertRegex(l, r"^SYMATTR Value2 l=0\.18u w=[\d.]+u$")
        for l in sl:
            self.assertRegex(l, r"ad=[\d.]+p as=[\d.]+p pd=[\d.]+u ps=[\d.]+u")


if __name__ == "__main__":
    unittest.main()
