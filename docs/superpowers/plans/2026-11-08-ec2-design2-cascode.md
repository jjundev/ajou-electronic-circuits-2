# 설계과제2 캐스코드 주파수 응답 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 설계과제2(전류 주입 캐스코드, |A0| = 10, 모든 극점 ≥ 1 GHz)의 손계산, ngspice 검증, LTspice 회로도, 보고서 md를 과제1과 같은 흐름으로 만든다.

**Architecture:** `sim/handcalc.py`가 설계값을 정해 `params.inc`와 `design.json`을 쓴다. ngspice가 `cascode.cir`로 op·ac·pz를 돌린다. `polemap.py`는 극점을 노드에 대응시키고, `post.py`는 그림과 비교표를 만든다. 보고서 md는 이 산출물의 수치만 옮긴다. 파싱은 `spice_io.py` 한 곳에서만 한다.

**Tech Stack:** Python 3 (numpy 2.5, matplotlib 3.11, unittest — pytest 없음), ngspice-47, LTspice(Wine, 회로도만), `scripts/ec2_report/check.py`.

**Spec:** `docs/superpowers/specs/2026-11-08-ec2-design2-cascode-design.md`

## Global Constraints

- 과제 값: VDD = 1 V, RS = 500 Ω, L = 0.18 µm, µnCox = 100 µA/V², µpCox = 50 µA/V², λn = 0.1, λp = 0.2 V⁻¹, VTHN = 0.4 V, VTHP = −0.4 V, P ≤ 0.5 mW, ID2 = |ID3|, |A0| = 10, 모든 극점 ≥ 1 GHz.
- 손계산 C 파라미터: Cox = 12 fF/µm², CGS = (2/3)WLCox + 0.3W, CGD = 0.3W, CDB = CSB = 0.4W (fF, W는 µm).
- 설계 입력: I1 = 400 µA, Vov1 = Vov2 = 0.15 V, |Vov3| = 0.30 V, VY = 0.30 V.
- SPICE 모델: `설계과제/과제1/sim/MOSFET_model.lib`를 수정 없이 쓴다(CMOSN/CMOSP). 모든 MOSFET에 AD = AS = 0.49u·W, PD = PS = W.
- 수치를 지어내지 않는다. 보고서의 모든 수치는 `설계과제/과제2/sim/` 산출물에서 온다.
- 보고서 본문에 AI 관련 언급을 쓰지 않는다. 이모지 기호도 쓰지 않는다(`양식.md` §4).
- 그림은 `report/figs/NN_<이름>.png` 한 폴더에 모은다. 01 회로, 02 설계 Bode, 03 회로도(사용자 캡처), 04 SPICE Bode.
- 학번·이름 표기: `202220953 신현준`.
- 테스트 실행: 저장소 루트에서 `python3 -m unittest tests.test_ec2_design2 -v`.
- 범위: 보고서 md(검사기 error 0)와 `cascode.asc`까지. 회로도 캡처는 사용자가 한다. 노션 업로드와 표지 병합은 하지 않는다.

## Review Focus

1. ngspice `show m`이 Level 1에서 `vdsat`을 0으로 보고할 수 있다. 포화 여유는 |VGS| − 0.4로 계산해야 한다(Task 6 `test_sat_rows_ignore_vdsat`).
2. 바이어스가 바뀌어 pz 극점이 켤레 복소수로 나와도 파서가 허수부를 잃지 않아야 한다. 대응은 |p| 기준이다(Task 3 `test_parse_pz_complex`).
3. 1 fF 섭동으로도 극점과 노드가 일대일로 대응되지 않으면 조용히 넘어가지 말고 ValueError로 멈춰야 한다(Task 5 `test_map_poles_ambiguous_raises`).
4. 경로에 한글과 공백이 있다. ngspice는 `cwd=sim`, 상대 `.include`로 돌아야 하고, 저장소 루트에서 실행한 테스트도 통과해야 한다(Task 4 통합 테스트).
5. 설계 입력을 바꿔도(예: I1 = 500 µA) RL 반복이 수렴해 |A0| = 10을 유지해야 하고, 사양을 깨는 입력은 `check`가 거부해야 한다(Task 2 `test_other_current_keeps_gain`, `test_check_rejects_slow_input_pole`).

---

### Task 1: 문제 정리와 과제2 폴더

**Files:**
- Create: `설계과제/과제2/설계과제2.md`
- Create: `설계과제/과제2/figures/fig1_cascode.png`, `설계과제/과제2/report/figs/01_cascode.png`
- Create: `설계과제/과제2/sim/MOSFET_model.lib` (과제1 파일을 바이트 그대로 복사)

**Interfaces:**
- Produces: Task 8이 그대로 옮길 문제 원문(`설계과제2.md`), 01 그림, Task 4가 include할 모델 파일.

- [ ] **Step 1: BB 공지 가져오기.** `ajou-bb` 스킬로 ECE305 전자회로2의 "설계과제#2" 공지(게시일, 마감, 첨부, 본문)를 읽는다. 첨부에 새 모델 라이브러리가 있으면 과제1 lib와 `diff`를 떠 보고, 다르면 진행을 멈추고 사용자에게 알린다.
- [ ] **Step 2: `설계과제2.md` 작성.** `설계과제/과제1/설계과제1.md`와 같은 구조로 쓴다. 출처 인용 → `## 공지 본문` → `## <설계과제 2>`(조건 LaTeX 목록, 그림, 회로 구성 목록: M1 NMOS CS, M2 NMOS CG(게이트 Vb1), M3 PMOS 전류원(게이트 Vb2, 드레인 Y), RL: VDD–Vout, RS: Vin–X) → `### 1) Design Problem`의 (a)–(d), `### 2) Spice Problem`의 (a)–(e)를 원문 그대로 → Capacitance Parameters 표.
- [ ] **Step 3: 그림 잘라 내기.** PDF 1쪽을 200 dpi로 렌더링하고 회로도 영역만 잘라 `figures/fig1_cascode.png`에 저장한 뒤 `report/figs/01_cascode.png`로 복사한다. 확인: 이미지를 열어 Vb2/M3, RL, Vout, Vb1/M2, Y, RS, Vin, X, M1 라벨이 모두 보인다.
- [ ] **Step 4: 모델 복사 확인.** Run: `cmp 설계과제/과제1/sim/MOSFET_model.lib 설계과제/과제2/sim/MOSFET_model.lib`. Expected: 출력 없음(종료 코드 0).
- [ ] **Step 5: Commit.** `git add` 위 파일들, 메시지 `docs(설계과제2): transcribe problem, figure, model lib`.

### Task 2: 손계산 `handcalc.py`

**Files:**
- Create: `설계과제/과제2/sim/handcalc.py`
- Test: `tests/test_ec2_design2.py` (새 파일, 클래스 `HandcalcTests`)

**Interfaces:**
- Produces:
  - `design(I1: float = 400e-6, vov1: float = 0.15, vov2: float = 0.15, vov3: float = 0.30, VY: float = 0.30, av: float = 10.0) -> dict` (SI 단위, C만 fF, W만 µm). 키:
    - 스칼라: `I1, I2, RL, Vout, VY, Rin2, RY, Gm, Rcas, Rout, A0`(음수), `AXY`(음수), `Vin, Vb1, Vb2, P`
    - 노드별 dict(`X/Y/out`): `R`(Ω), `C`(fF), `f`(Hz)
    - MOSFET별 dict(`M1/M2/M3`): `W`, `gm`, `ro`, `sat`(VDS − Vov, V), `caps`(각 값이 `{"CGS","CGD","CDB","CSB"}` fF)
  - `check(d: dict) -> None`: min(f) < 1.5e9, sat 중 하나라도 < 0.1, P > 0.5e-3, ||A0| − 10| > 1e-6 중 하나면 AssertionError.
  - `write_outputs(d: dict, sim_dir: Path) -> None`:
    - `params.inc` 한 줄: `.param W1=<W1>u W2=<W2>u W3=<W3>u RLV=<RL> VIN=<Vin> VB1=<Vb1> VB2=<Vb2> XJ=0.49u`
    - `design.json`: d 전체를 JSON으로
  - `__main__`: design() → check() → write_outputs(같은 폴더), 표 출력.

- [ ] **Step 1: 실패하는 테스트 작성**

```python
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
```

- [ ] **Step 2: 실패 확인.** Run: `python3 -m unittest tests.test_ec2_design2.HandcalcTests -v`. Expected: `ModuleNotFoundError: No module named 'handcalc'`.
- [ ] **Step 3: `handcalc.py` 구현.** 스펙 §핵심 식을 따른다.
  - ro = (1 + λ·VDS)/(λ·ID)
  - VDS: M1 = VY, M2 = Vout − VY, M3 = VDD − VY
  - RL 반복: RL ← RL·10/|A0|를 수렴할 때까지(최대 200회, 상대 변화 < 1e-12). 수렴 후 W를 반올림하고, 반올림한 W로 C와 f를 계산한다.
  - 바이어스: Vin = VTH + Vov1, Vb1 = VY + VTH + Vov2, Vb2 = VDD − VTH − Vov3
  - 모듈 docstring 첫 줄은 `"""설계과제2 손계산: ..."""`로 쓴다(과제1 스타일).
- [ ] **Step 4: 통과 확인.** 같은 명령. Expected: 8 tests OK.
- [ ] **Step 5: 산출물 생성.** Run: `cd 설계과제/과제2/sim && python3 handcalc.py`. Expected: `params.inc`, `design.json`이 생기고 표의 f_X ≈ 1.94 GHz.
- [ ] **Step 6: Commit.** `feat(설계과제2): hand calculation for cascode design`.

### Task 3: ngspice 출력 파서 `spice_io.py`

**Files:**
- Create: `설계과제/과제2/sim/spice_io.py`
- Test: `tests/test_ec2_design2.py` (클래스 `SpiceIoTests`)

**Interfaces:**
- Produces:
  - `parse_scalars(text: str) -> dict[str, float]`: `name = value` 줄을 읽는다(`v(y)`, `i(vdd)`, `a0`, `f3db` 등). 키는 소문자.
  - `parse_devices(text: str) -> dict[str, dict[str, float]]`: `show m` 블록 여러 개를 합친다. 장치 이름은 대문자(`M1`), `?????`는 nan.
  - `parse_pz(text: str) -> tuple[list[complex], list[complex]]`: `pole(n) = re,im`과 `zero(n) = re,im`을 읽는다. 단위 rad/s, 부호 유지.
  - `load_ac(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]`: wrdata 4열 파일에서 (f, dB, 위상[deg]) = 열 0, 1, 3.

- [ ] **Step 1: 실패하는 테스트 작성.** 픽스처는 스펙 타당성 검증 때 나온 출력 형식을 그대로 쓴다.

```python
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
        import spice_io; self.s = spice_io
    def test_parse_scalars(self):
        d = self.s.parse_scalars("v(y) = 2.997411e-01\ni(vdd) = -4.14127e-04\na0 = 2.03080e+01\n")
        self.assertAlmostEqual(d["v(y)"], 0.2997411); self.assertAlmostEqual(d["i(vdd)"], -4.14127e-4)
    def test_parse_devices(self):
        d = self.s.parse_devices(DEV + DEV.replace("m3", "m9"))
        self.assertAlmostEqual(d["M1"]["id"], 0.000414127)
        self.assertAlmostEqual(d["M2"]["cgs"], 4.45142e-14)
        self.assertIn("M9", d)
        self.assertNotEqual(d["M1"]["vth"], d["M1"]["vth"])  # nan
    def test_parse_pz(self):
        p, z = self.s.parse_pz("pole(1) = -4.67097e+10,0.000000e+00\npole(2) = -9.76058e+09,0.000000e+00\nzero(1) = 2.222905e+11,0.000000e+00\n")
        self.assertEqual(p, [complex(-4.67097e10, 0), complex(-9.76058e9, 0)])
        self.assertEqual(z, [complex(2.222905e11, 0)])
    def test_parse_pz_complex(self):
        p, _ = self.s.parse_pz("pole(1) = -1.0e+10,5.0e+09\npole(2) = -1.0e+10,-5.0e+09\n")
        self.assertEqual(p[0].imag, 5e9); self.assertEqual(p[1].imag, -5e9)
```

- [ ] **Step 2: 실패 확인.** `python3 -m unittest tests.test_ec2_design2.SpiceIoTests -v` → ModuleNotFoundError.
- [ ] **Step 3: `spice_io.py` 구현.** 정규식과 `show` 표 행(첫 토큰이 행 이름, 나머지가 장치별 값)으로 파싱한다. `device` 행에서 장치 순서를 잡는다.
- [ ] **Step 4: 통과 확인.** Expected: 4 tests OK. 이어 Task 2 테스트까지 전체를 돌려 12 OK인지 본다.
- [ ] **Step 5: Commit.** `feat(설계과제2): ngspice output parsers`.

### Task 4: 넷리스트와 SPICE 실행

**Files:**
- Create: `설계과제/과제2/sim/core.inc`, `설계과제/과제2/sim/cascode.cir`
- Generated (커밋): `op.txt`, `ac.txt`, `meas.txt`, `pz.txt`
- Test: `tests/test_ec2_design2.py` (클래스 `SpiceRunTests`, `@unittest.skipUnless(shutil.which("ngspice"), ...)`)

**Interfaces:**
- Consumes: `params.inc`(Task 2), `spice_io.*`(Task 3), `MOSFET_model.lib`(Task 1).
- Produces:
  - 노드 이름: `vdd, in, x, y, out, vb1, vb2`. 장치 이름: `M1, M2, M3, RS, RL, Vin, Vb1, Vb2, VDD`.
  - `op.txt`: `=== NODES ===`(v(x) v(y) v(out) v(vb1) v(vb2) v(in), i(VDD)) 다음 `=== DEVICES ===`(`show m : id vgs vds vdsat gm gds cgs cgd cbd cbs`).
  - `meas.txt`: `a0`(dB, 1 MHz), `f3db`(Hz). `ac.txt`: `wrdata ac.txt vdb(out) ph`(ph = 180/pi·cph(v(out))). `pz.txt`: `pz in 0 out 0 vol pz` 뒤 `print all`.

- [ ] **Step 1: 실패하는 통합 테스트 작성**

```python
@unittest.skipUnless(shutil.which("ngspice"), "ngspice not installed")
class SpiceRunTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(["python3", "handcalc.py"], cwd=SIM, check=True)
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
```

- [ ] **Step 2: 실패 확인.** `python3 -m unittest tests.test_ec2_design2.SpiceRunTests -v` → `cascode.cir` 없음으로 CalledProcessError.
- [ ] **Step 3: `core.inc`와 `cascode.cir` 작성.**
  - `core.inc`: `.include MOSFET_model.lib`, `.include params.inc`, VDD 1 V, `Vin in 0 DC {VIN} AC 1`, `RS in x 500`, `RL vdd out {RLV}`
  - MOSFET 세 개, 각각 `AD={XJ*Wn} AS={XJ*Wn} PD={Wn} PS={Wn}`:
    - `M1 y x 0 0 CMOSN W={W1} L=0.18u`
    - `M2 out vb1 y 0 CMOSN W={W2} L=0.18u`
    - `M3 y vb2 vdd vdd CMOSP W={W3} L=0.18u`
  - `cascode.cir`: `.include core.inc`와 `.control` 블록(과제1 `diffamp.cir` 형식)만 둔다.
  - 모델의 `WD` unrecognized 경고는 무해하다(LTspice_작성메모에 적는다).
- [ ] **Step 4: 통과 확인.** Expected: 3 tests OK. 참고 값(스펙 타당성 검증): a0 ≈ 20.3 dB, 최저 극점 ≈ 1.55 GHz. 전류 불일치가 1 %를 넘으면 스펙 결정 #9에 따라 `tune.cir`(Vin DC sweep)을 추가하고, 조정한 값을 `params.inc`가 아니라 `cascode.cir`의 `.param VIN=`으로 덮어쓴다.
- [ ] **Step 5: Commit.** 넷리스트와 산출 txt를 함께 커밋한다. `feat(설계과제2): ngspice op/ac/pz netlists and results`.

### Task 5: 극점–노드 대응 `polemap.py`

**Files:**
- Create: `설계과제/과제2/sim/polemap.py`; Generated (커밋): `polemap.json`
- Test: `tests/test_ec2_design2.py` (클래스 `PolemapTests`)

**Interfaces:**
- Consumes: `core.inc`(Task 4), `spice_io.parse_pz`.
- Produces:
  - `run_pz(node: str | None, c_probe: float = 1e-15) -> list[complex]`: `SIM/_pz_tmp.cir`에 `.include core.inc`, (node가 있으면) `Cprobe <node> 0 <c_probe>`, pz 제어 블록을 쓰고 `ngspice -b`(cwd = SIM)로 돌린다. stdout을 파싱한 뒤 임시 파일은 지운다.
  - `map_poles(base: list[complex], shifted: dict[str, list[complex]]) -> dict[str, int]`: 두 목록 모두 |p| 오름차순으로 정렬한 뒤, 노드마다 |Δp|/|p|가 가장 큰 인덱스를 고른다. 인덱스가 겹치면 ValueError.
  - `polemap.json`: `{"X": {"index": i, "f_hz": |p|/2π}, "Y": {...}, "out": {...}}`.

- [ ] **Step 1: 실패하는 테스트 작성**

```python
class PolemapTests(unittest.TestCase):
    def setUp(self):
        import polemap; self.m = polemap
    def test_map_poles_unique(self):
        base = [-1e10, -2e10, -4e10]
        sh = {"X": [-0.9e10, -2e10, -4e10], "Y": [-1e10, -1.8e10, -4e10], "out": [-1e10, -2e10, -3.7e10]}
        self.assertEqual(self.m.map_poles(base, sh), {"X": 0, "Y": 1, "out": 2})
    def test_map_poles_ambiguous_raises(self):
        base = [-1e10, -2e10, -4e10]
        sh = {"X": [-0.9e10, -2e10, -4e10], "Y": [-0.95e10, -2e10, -4e10], "out": [-1e10, -2e10, -3.7e10]}
        with self.assertRaises(ValueError):
            self.m.map_poles(base, sh)
    @unittest.skipUnless(shutil.which("ngspice"), "ngspice not installed")
    def test_real_map_x_is_dominant(self):
        subprocess.run(["python3", "polemap.py"], cwd=SIM, check=True)
        pm = json.loads((SIM / "polemap.json").read_text())
        self.assertEqual(set(pm), {"X", "Y", "out"})
        self.assertEqual(pm["X"]["index"], 0)
        self.assertGreaterEqual(min(v["f_hz"] for v in pm.values()), 1e9)
```

- [ ] **Step 2: 실패 확인.** `python3 -m unittest tests.test_ec2_design2.PolemapTests -v` → ModuleNotFoundError.
- [ ] **Step 3: `polemap.py` 구현.** 위 시그니처대로 만든다. `__main__`은 base 1회와 노드 3회 실행 → map_poles → json 쓰기 → 표 출력 순서다.
- [ ] **Step 4: 통과 확인.** Expected: 3 tests OK.
- [ ] **Step 5: Commit.** `feat(설계과제2): map pz poles to nodes by 1 fF perturbation`.

### Task 6: 그림과 비교표 `post.py`

**Files:**
- Create: `설계과제/과제2/sim/post.py`
- Generated (커밋): `설계과제/과제2/report/figs/02_bode_design.png`, `.../04_ac_bode.png`, `설계과제/과제2/report/sat_table.md`, `설계과제/과제2/report/compare.md`
- Test: `tests/test_ec2_design2.py` (클래스 `PostTests`)

**Interfaces:**
- Consumes: `design.json`, `op.txt`, `ac.txt`, `meas.txt`, `pz.txt`, `polemap.json`, `spice_io.*`.
- Produces:
  - `sat_rows(dev: dict, order=("M1", "M2", "M3")) -> list[dict]`: 행마다 키 `name, id, vgs, vov, vds, margin, ok`. vov = |vgs| − 0.4, margin = |vds| − vov이며 vdsat은 쓰지 않는다.
  - `spice_node_R(dev: dict, RL: float, RS: float = 500.0) -> dict[str, float]`: X = RS, Y = ro1 ∥ ro3 ∥ Rin2, out = RL ∥ Rcas. ro = 1/gds이고 나머지는 스펙 식과 같다.
  - `node_caps(f: dict[str, float], R: dict[str, float]) -> dict[str, float]`: C = 1/(2π f R), 단위 fF.
  - `device_node_caps(dev: dict, axy: float) -> dict[str, float]`: SPICE 소자 C로 스펙의 C_X, C_Y, C_out 식을 계산한다(fF). M2 소스 쪽은 cbs, M1·M3 드레인 쪽은 cbd를 쓴다.
  - `err_pct(spice: float, design: float) -> float` = (spice − design)/design·100.
  - `compare.md`: 표 세 개(이득, 극점, 노드 C). 열은 `항목 | 설계 | SPICE | 오차 [%]`이고, 노드 C 표에는 SPICE 소자 C 열을 하나 더 둔다.
  - `sat_table.md`: 열은 `MOSFET | I_D [µA] | \lvert V_GS\rvert [V] | \lvert V_GS\rvert−V_TH [V] | \lvert V_DS\rvert [V] | margin [V] | region`, 순서 M1, M2, M3, region 값은 `saturation`(이모지 금지).

- [ ] **Step 1: 실패하는 테스트 작성**

```python
class PostTests(unittest.TestCase):
    def setUp(self):
        import post; self.p = post
    def test_sat_rows_ignore_vdsat(self):
        dev = {"M1": {"id": 4e-4, "vgs": 0.55, "vds": 0.30, "vdsat": 0.0},
               "M2": {"id": 2e-4, "vgs": 0.55, "vds": 0.314, "vdsat": 0.0},
               "M3": {"id": -2e-4, "vgs": -0.70, "vds": -0.70, "vdsat": 0.0}}
        r = {x["name"]: x for x in self.p.sat_rows(dev)}
        self.assertAlmostEqual(r["M1"]["margin"], 0.15); self.assertAlmostEqual(r["M3"]["margin"], 0.40)
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
    @unittest.skipUnless(shutil.which("ngspice"), "ngspice not installed")
    def test_outputs_written(self):
        subprocess.run(["python3", "post.py"], cwd=SIM, check=True)
        figs = SIM.parent / "report/figs"
        for f in ("02_bode_design.png", "04_ac_bode.png"):
            self.assertTrue((figs / f).stat().st_size > 10_000)
        self.assertIn("saturation", (SIM.parent / "report/sat_table.md").read_text())
        self.assertIn("오차", (SIM.parent / "report/compare.md").read_text())
```

- [ ] **Step 2: 실패 확인.** `python3 -m unittest tests.test_ec2_design2.PostTests -v` → ModuleNotFoundError.
- [ ] **Step 3: `post.py` 구현.** 그림 저장 경로는 `../report/figs`(과제1 `post.py:4`와 같다), matplotlib `Agg`.
  - 02: design.json의 A0와 f로 H(jω) 크기[dB]를 1 MHz–100 GHz 범위에 그린다. 세 극점에 세로 점선과 라벨 X/Y/out을 단다.
  - 04: ac.txt로 크기·위상 두 칸을 그리고, f−3dB와 polemap의 세 극점을 표시한다.
  - 함수는 모두 `__main__` 밖에 두어 import해도 부작용이 없게 한다.
- [ ] **Step 4: 통과 확인.** Expected: 4 tests OK. 이어 전체 실행: `python3 -m unittest tests.test_ec2_design2 -v` → 모두 OK(ngspice가 있으면 skip 0).
- [ ] **Step 5: Commit.** `feat(설계과제2): bode plots, saturation and comparison tables`.

### Task 7: LTspice 회로도 `.asc`

**Files:**
- Create: `설계과제/과제2/sim/ltspice/make_asc.py`, generated `cascode.asc` (+ 배치 실행 산출물 `.log/.net/.raw`, 과제1처럼 커밋)
- Create: `설계과제/과제2/report/LTspice_작성메모.md`
- Test: `tests/test_ec2_design2.py` (클래스 `AscTests`)

**Interfaces:**
- Consumes: `params.inc` 값(make_asc.py가 `../params.inc`를 읽어 W·바이어스·RL을 채운다. 과제1처럼 상수로 박지 않는다), 템플릿 `설계과제/과제1/sim/ltspice/make_asc.py`의 `wire/flag/data/text/mos/vsrc` 도우미.
- Produces: `cascode.asc`. 내용:
  - 배치: M3·RL은 위, M2는 가운데, M1·RS·Vin은 아래(과제 그림 배치)
  - 심볼: M3는 3단자 `pmos`(소스 VDD), M1은 3단자 `nmos`(소스 GND), M2는 `nmos4`(body → GND)
  - 각 MOSFET에 `AD/AS/PD/PS`를 `SYMATTR Value2`로 넣는다
  - `DATAFLAG`: V(x), V(y), V(out), Id(M1), Id(M2), Id(M3)
  - `TEXT ;202220953 신현준`, `.include ../MOSFET_model.lib`, `.op`

- [ ] **Step 1: 실패하는 테스트 작성**

```python
class AscTests(unittest.TestCase):
    def test_asc_encoding_and_content(self):
        subprocess.run(["python3", "make_asc.py"], cwd=SIM / "ltspice", check=True)
        raw = (SIM / "ltspice/cascode.asc").read_bytes()
        self.assertFalse(raw.startswith(b"\xff\xfe"))           # BOM 금지
        txt = raw.decode("utf-16-le")
        for s in ("202220953 신현준", "CMOSN", "CMOSP", ".include ../MOSFET_model.lib", "\r\n"):
            self.assertIn(s, txt)
```

- [ ] **Step 2: 실패 확인.** `python3 -m unittest tests.test_ec2_design2.AscTests -v` → make_asc.py 없음.
- [ ] **Step 3: `make_asc.py` 구현.** 과제1 템플릿을 복사해 회로만 바꾼다. 인코딩은 `.claude/skills/ec2-write-design-report/references/LTspice.md` §인코딩을 따른다.
- [ ] **Step 4: 통과 확인.** Expected: 1 test OK.
- [ ] **Step 5: 배치 실행 검증.** LTspice.md §배치 실행의 Wine 명령으로 `cascode.asc`를 `-b -ascii` 실행한다. Expected: `cascode.log`에 floating·unconnected 경고가 없고, `.raw`의 V(y)·V(out)·Id(M1~M3)가 `op.txt`와 1 mV, 0.1 µA 안에서 같다. LTspice가 실행되지 않으면(Rosetta 등) 이 단계는 건너뛰고 사용자에게 알린다.
- [ ] **Step 6: `LTspice_작성메모.md` 작성.** 과제1 메모와 같은 구조로 쓴다(작성 순서, 시뮬레이션 파일 표, 실행 한 줄, 캡처 전 확인, `WD` 경고 설명, 배치 실행 결과 수치). 캡처는 `report/figs/03_schematic.png`로 저장한다고 적는다.
- [ ] **Step 7: Commit.** `feat(설계과제2): LTspice schematic generator`.

### Task 8: 보고서 본문 md

**Files:**
- Create: `설계과제/과제2/report/설계과제2_보고서.md`

**Interfaces:**
- Consumes: `설계과제2.md`(문제 원문), `design.json`, `handcalc.py` 출력, `op.txt`, `meas.txt`, `polemap.json`, `sat_table.md`, `compare.md`, figs 01–04.

- [ ] **Step 1: 양식 읽기.** `ec2-write-design-report` 스킬을 연다(`/ec2-write-design-report 2` 절차). `양식.md`, `감점체크리스트.md`도 읽는다.
- [ ] **Step 2: 본문 작성.** 양식.md 구성 순서(제목, 목차 블록, `# 설계 조건`, `# Design Problem`, `# Spice Problem`, 소절 `## (a) …`, 원문 굵게, 여백 블록)를 따르고 다음 내용을 넣는다.
  - Design (a)
    - 회로 해석: I1 = 2·ID2
    - 전력식: 1 V × 400 µA = 0.4 mW ≤ 0.5 mW
    - Gm 정확식 유도와 Gm/gm1 값, R_in2·Rcas·Rout 유도, RL 결정(|A0| = 10.00)
    - 출력 강하 ≈ |A0|·Vov1/4 관계로 Vov1을 고른 이유, 헤드룸 표(VY, Vout)
    - 소신호 파라미터 표
  - Design (b): W 계산식 표(MOSFET · 식(숫자 대입) · W/L · W, 순서 M1, M2, M3), 요약 표, 바이어스 표(Vin,DC, Vb1, Vb2, RL), MOSFET마다 saturation 부등식.
  - Design (c): A_XY 유도(정확식과 강의 근사 −gm1/gm2 병기), 노드별 C 구성식(숫자 대입, 과제 표 값), f_X·f_Y·f_out과 1 GHz 판정.
  - Design (d): H(s) 식(숫자), RHP 영점 언급, `![](figs/02_bode_design.png)`.
  - Spice (a): `![LTspice 회로도 (.op 라벨, 학번·이름 표기)](figs/03_schematic.png)`, 노드 전압 표, 전류·전력(i(VDD)), 모델 KP = 103.6 µA/V² 차이.
  - Spice (b): `sat_table.md` 표를 그대로 옮기고 부등식을 쓴다.
  - Spice (c): `![](figs/04_ac_bode.png)`(크기·위상), 이득 비교와 오차 %.
  - Spice (d): pz 방법, 1 fF 대응 방법, 극점 비교표와 오차 %. Miller 근사와 정확한 극점의 차이(극점 상호작용, CGD 0.4 vs 0.3)를 번호 매겨 설명한다.
  - Spice (e): `compare.md`의 노드 C 표. 차이의 원인을 번호 매겨 쓴다(Cox 8.63 vs 12, CGSO/CGDO 0.4 vs 0.3, 접합 C의 바이어스 의존(MJ, PB), Miller 근사).
- [ ] **Step 3: 검사.** 저장소 루트에서 Run: `python3 -c "from scripts.ec2_report.check import check_markdown; [print(f) for f in check_markdown('설계과제/과제2/report/설계과제2_보고서.md')]"`. Expected: error 0. info 줄의 그림 목록이 `figs/01_cascode.png, figs/02_bode_design.png, figs/03_schematic.png, figs/04_ac_bode.png`와 같다.
- [ ] **Step 4: 감점 체크.** `감점체크리스트.md` 항목 1–9마다 본문 근거 위치를 ✔/✘ 표로 정리한다(#10 1 MHz 파형은 과제2에 해당 없음으로 표시). ✘가 있으면 고치고 Step 3으로 돌아간다. 수치 대조: 본문의 이득, 극점, 전류 값이 `meas.txt`·`polemap.json`·`op.txt`와 표시 자릿수까지 같은지 확인한다.
- [ ] **Step 5: Commit.** `docs(설계과제2): write design report body`.
- [ ] **Step 6: 사용자 안내.** 할 일 두 가지를 짧게 전한다. LTspice GUI 캡처를 `report/figs/03_schematic.png`로 저장하는 것(LTspice_작성메모.md 참고), 다음 단계 `ec2-sync-notion 2`.
