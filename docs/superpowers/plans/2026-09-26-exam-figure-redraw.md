# 기출 회로도 다시 그리기 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 기출 4회차(2021-1 중간·기말, 2023-1 중간·기말) 문제 그림 18장을 schemdraw로 다시 그려 문제집 PDF에 넣는다. 원본과 배치·라벨 위치가 같고, 손글씨는 없다.

**Architecture:**
- 공통 스타일 모듈(`schem_style.py`)과 실행기(`draw_exam.py`)를 만든다. 실행기는 `figures/redrawn/fig-Q<n>.py`의 `draw()`를 불러 같은 폴더에 PNG를 쓴다.
- `verify_exam.py`는 짝과 최신 여부를 검사하고, 문제집 생성기는 redrawn PNG가 있으면 그것을 크롭과 같은 폭으로 넣는다.
- 도구는 한 브랜치에서 TDD로 만들어 병합한다. 그다음 파일럿 회차(2021 중간)로 스타일을 확정하고, 나머지 3회차를 worktree 3개에서 병렬로 그린다. PDF는 마지막에 한 번에 다시 만든다.

**Tech Stack:** Python 3.14 (Homebrew), schemdraw 0.23, matplotlib 3.11, Pillow(matplotlib 의존성으로 설치됨), PyYAML, PyMuPDF(`fitz`), 표준 `unittest`(pytest 없음), `workbook/build_workbook.py`(Playwright와 설치된 Chrome), Agent 도구(subagent, model `opus`).

**Spec:** `docs/superpowers/specs/2026-09-26-exam-figure-redraw-design.md`

## Global Constraints

- `MAIN` = `/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2`. 메인 checkout이고 브랜치는 `main`, 시작 시점은 `9ad339c`이다.
- `EXAMS` = `from_the_past/md`, `TOOLS` = `from_the_past/md/_tools` (저장소 루트 기준).
- **도구 브랜치:** Task 1–4는 `MAIN/.claude/worktrees/redraw-tools`(브랜치 `claude/redraw-tools`)에서 한다.
- **회차 worktree:** Task 5는 `redraw-2021-mid`, Task 6–8은 `redraw-2021-fin`, `redraw-2023-mid`, `redraw-2023-fin`에서 한다. Task 9는 `redraw-pdf`에서 한다. 모두 `MAIN/.claude/worktrees/` 아래에 있고, 브랜치 이름은 `claude/<같은 이름>`이다.
- `.claude/worktrees/sol-ch09`, `sol-ch10`, `sol-ch11`, `sol-exams`는 다른 세션의 것이다. 건드리지 않는다. 그중 `sol-exams`는 기출 md와 `workbook/pdf/2021-*`, `workbook/pdf/2023-*`를 고친다. 그래서 Task 5–8은 PDF를 커밋하지 않고, Task 9에서 한 번만 만든다.
- **의존성 설치 (한 번):** `pip3 install --user --break-system-packages schemdraw matplotlib`. 버전은 `schemdraw>=0.23`, `matplotlib>=3.11`이다.
- **파일 이름:** 다시 그린 그림은 `EXAMS/<회차>/figures/redrawn/fig-Q<n>.py`와 `fig-Q<n>.png`다. `<n>`과 id는 figures.yaml 키와 같다(`"Q2"`, `"Q2-2"`).
- **PNG:** 432 dpi, 흰 배경. `schem_style.save_png`로만 저장한다(메타데이터가 없어서 같은 코드면 같은 바이트가 나온다).
- **인쇄 크기:** 폭 = 크롭 PNG 폭(px) / figures.yaml dpi × 25.4 mm. 높이 = 폭 × 다시 그린 PNG의 높이/폭.
- **인쇄 라벨 글자 크기:** 7–11pt. `draw_exam.py`가 `WARN`으로 알린다. 회차 task는 `WARN`이 0개여야 끝난다.
- **그림 내용의 기준:** 연결은 md `## 회로 — Fig …` 절의 넷리스트, 모양은 `- 단자:`·`- 표시:`·`- 배치:` bullet을 따른다. `> 참고:` 줄의 손글씨 획은 그리지 않는다. md는 한 글자도 고치지 않는다.
- **git add:** 항상 경로를 명시한다. `git add -A`, `git add .`는 쓰지 않는다. `__pycache__`는 커밋하지 않는다.
- **커밋 메시지:** 마지막 줄은 빈 줄 뒤 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`이다.
- **push는 하지 않는다.** main 병합과 worktree 삭제는 그때마다 사용자에게 묻는다. 멈추는 지점은 Task 4 끝, Task 5 Step 3(스타일 확인)과 끝, Task 6·7·8 끝, Task 9 끝이다.
- **테스트 명령과 기대 개수**
  - 기출 도구: `python3 -m unittest discover -s from_the_past/md/_tools/tests`. 지금 71개 → Task 1 뒤 76 → Task 2 뒤 82 → Task 3 뒤 87.
  - 생성기: `python3 -m unittest discover -s workbook/tests`. 지금 97개 → Task 4 뒤 99.
- **서브에이전트:** `Agent`(subagent_type `general-purpose`, model `opus`)로 띄운다. worktree 하나에 작성자는 한 번에 한 명뿐이다.
- `SCRATCH` = 실행하는 세션의 scratchpad 경로다. 셸 상태가 유지되지 않으므로 셸 명령마다 `export SCRATCH=<경로>`를 앞에 붙인다.

## Review Focus

1. **FET 방향이 앞 요소를 따라 도는 문제:** `Line().up()` 뒤에 놓은 트랜지스터가 90° 돌아가면 안 된다. 게이트는 왼쪽(mirror면 오른쪽), 드레인(nmos)이나 소스(pmos)는 위에 와야 한다. schemdraw는 `.right()` 없이 진행 방향을 물려받는다. 이 문제는 프로토타입에서 실제로 났다. Task 1 `test_placed_after_vertical_line_keeps_orientation`이 검사한다.
2. **그림 코드 하나가 깨졌을 때:** 예외가 나거나 `draw()`가 없는 파일은 그 파일 이름과 이유를 `ERROR`로 알려야 하고, 나머지 그림은 계속 그려야 한다. Task 2의 `test_broken_figure_reported_others_drawn`과 `test_missing_draw_function`이 검사한다.
3. **코드만 고치고 PNG를 다시 만들지 않은 경우:** `verify_exam --redraw`가 잡아야 한다. Task 3 `test_redraw_detects_stale_png`가 검사한다.
4. **너무 넓거나 좁게 그려서 글자가 작게 또는 크게 찍히는 경우:** 문제집은 크롭 폭으로 찍으므로 그림 범위가 넓을수록 글자가 작아진다. 2021 기말 Q5는 폭이 167 mm라서 특히 위험하다. `WARN`으로 잡아야 한다. Task 2 `test_font_warning_when_crop_much_narrower`가 검사한다.
5. **크롭 없이 redrawn만 있는 경우:** 인쇄 폭의 기준이 없으므로 "그림 파일 없음" 오류가 나야 한다. 크롭 없이 조용히 넘어가면 안 된다. Task 4 `test_redrawn_needs_crop_for_size`가 검사한다.

## 공통 절차 (Task 5–8)

### 절차 R — 그림 하나 그리기
1. md `EXAMS/<회차>/Q<n>.md`의 `## 회로 — Fig Q<n>…` 절을 **모두** 읽는다. 넷리스트, 단자, 표시, 배치를 확인하고, 크롭 `figures/fig-Q<n>.png`를 Read로 연다.
2. `figures/redrawn/fig-Q<n>.py`를 쓴다. 규칙은 다음과 같다.
   - 첫 줄 docstring에 기준 절 이름을 적는다(예: `"""2021-1 중간 Q2 — 기준: Q2.md '회로 — Fig Q2(a)', '회로 — Fig Q2(b)'."""`).
   - 트랜지스터는 `schem_style.nmos`, `pmos`로만 놓는다. `at`과 `anchor`는 인자로 주고, add 뒤에 `.at()`을 부르지 않는다.
   - 게이트 단자는 `gate_terminal`로 만든다. 패널이 여럿이면 `panel_a(d, x0)`, `panel_b(d, x0)`처럼 함수로 나누고, 캡션은 `caption`으로 붙인다.
   - 아래로 그리는 소자(`.down()`)의 라벨은 `loc="bottom"`이면 오른쪽, `loc="top"`이면 왼쪽에 붙는다. `"left"`, `"right"`는 소자 양 끝에 붙으므로 쓰지 않는다.
   - BJT는 `elm.BjtNpn`/`elm.BjtPnp`(앵커 `base`, `collector`, `emitter`), op amp는 `elm.Opamp`(앵커 `in1`, `in2`, `out`), 전류원은 `elm.SourceI`, 굵은 전원 레일은 `elm.Line().linewidth(2.5)`로 그린다. Laser 상자처럼 전용 기호가 없는 것은 `elm.Rect`나 선과 `elm.Label`로 그린다.
3. `python3 TOOLS/draw_exam.py EXAMS/<회차>`를 실행하고 PNG를 Read로 연다. `ERROR`나 `WARN`이 없어지고 배치가 크롭과 같을 때까지 고친다. `WARN`이 나면 소자 간격을 줄이거나 늘려 그림 범위를 맞춘다. `FONT_SIZE`는 바꾸지 않는다.
4. 자가 점검표. 모두 맞아야 다음 그림으로 넘어간다.
   - 넷리스트의 소자가 모두 **한 번씩** 그려졌고, 라벨이 표시 bullet과 같다.
   - 넷리스트 줄마다 단자가 적힌 노드에 이어진다.
   - 배치 bullet의 "접속점" 목록과 점 개수가 같다. "교차"는 점 없이 지나간다.
   - 좌우 반전, 화살표 방향, 라벨 위치가 표시·배치 bullet과 같다.
   - `> 참고:` 줄에 적힌 손글씨 획은 하나도 없다.

### 절차 C — 대조 검토 (opus 리뷰어, 읽기 전용)
1. `python3 TOOLS/draw_exam.py EXAMS/<회차> --compare $SCRATCH/<회차>-sheet.png`를 실행하고 시트를 Read로 연다. 시트가 너무 길면 그림별 PNG와 크롭을 따로 연다.
2. 그림마다 md 넷리스트를 한 줄씩 따라가며, 소자 단자가 그림에서 적힌 노드에 닿는지 확인한다. 이어서 절차 R 4의 점검표를 다시 확인한다.
3. `.py`를 읽고 절차 R 2의 규칙을 어긴 곳이 있는지 본다.
4. 보고서 `docs/superpowers/reports/redraw/<회차>.md` 형식: `그림 | 항목 | 문제 | 제안` 표 한 개. 문제가 없으면 "지적 없음".

### 절차 V — 검증
```bash
cd <worktree>
python3 -m unittest discover -s from_the_past/md/_tools/tests        # 87개 OK
python3 from_the_past/md/_tools/draw_exam.py from_the_past/md/<회차>  # ERROR·WARN 줄 없음, 종료 코드 0
python3 from_the_past/md/_tools/verify_exam.py from_the_past/md/<회차> --recrop --redraw   # 오류 0개
python3 workbook/build_workbook.py <회차> 2>&1 | tail -5             # OVERFLOW·ERROR 없음, 종료 코드 0
git checkout -- workbook/pdf                                          # PDF는 Task 9에서만 커밋
```

---

### Task 1: 의존성과 `schem_style.py`

**Files:**
- Create: `from_the_past/md/_tools/schem_style.py`
- Test: `from_the_past/md/_tools/tests/test_schem_style.py`

**Interfaces:**
- Consumes: 없음
- Produces:
  - `DPI = 432`, `FONT_SIZE = 12`, `LW = 1.2`, `GATE_LEAD = 1.0`
  - `new_drawing() -> schemdraw.Drawing`
  - `nmos(d, at=None, anchor="drain", mirror=False, label=None, label_loc=None) -> Element`
  - `pmos(d, at=None, anchor="source", mirror=False, label=None, label_loc=None) -> Element`
  - `gate_terminal(d, gate, label, open_=False, right=False) -> Element`
  - `caption(d, xy, text) -> Element`
  - `save_png(drawing, path, dpi=DPI) -> None`

- [ ] **Step 1: worktree와 의존성**

```bash
MAIN=/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2
git -C "$MAIN" worktree add "$MAIN/.claude/worktrees/redraw-tools" -b claude/redraw-tools main
pip3 install --user --break-system-packages schemdraw matplotlib
python3 -c "import schemdraw, matplotlib; print(schemdraw.__version__, matplotlib.__version__)"   # 0.23 이상, 3.11 이상
```

- [ ] **Step 2: 실패하는 테스트 쓰기** — `from_the_past/md/_tools/tests/test_schem_style.py`

```python
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
```

- [ ] **Step 3: 실패 확인**

Run: `python3 -m unittest from_the_past/md/_tools/tests/test_schem_style.py`
Expected: `ModuleNotFoundError: No module named 'schem_style'`

- [ ] **Step 4: 구현** — `from_the_past/md/_tools/schem_style.py`

```python
"""기출 회로도 다시 그리기 공통 스타일 (Razavi 시험지 모양). 규칙은 FORMAT-EXAM.md '다시 그린 그림'."""
from pathlib import Path

import schemdraw
import schemdraw.elements as elm

schemdraw.use("matplotlib")
DPI = 432          # 크롭 144 dpi의 3배
FONT_SIZE = 12
LW = 1.2
GATE_LEAD = 1.0    # 게이트에서 단자까지 가로선 길이
schemdraw.config(fontsize=FONT_SIZE, lw=LW, font="DejaVu Sans")


def new_drawing():
    return schemdraw.Drawing(show=False, unit=2.0)


def _fet(d, cls, at, anchor, mirror, label, label_loc):
    # d.add 전에 방향·위치를 정한다. add 뒤의 .anchor().at()은 위치를 바꾸지 않는다.
    # .right()를 꼭 준다: 안 주면 앞 요소의 진행 방향(예: Line().up())을 물려받아 기호가 돈다.
    e = cls(offset_gate=False, source_arrow=True).right()
    if not mirror:
        e = e.reverse()
    if at is not None:
        e = e.anchor(anchor).at(at)
    if label:
        e = e.label(label, loc=label_loc or ("left" if mirror else "right"))
    return d.add(e)


def nmos(d, at=None, anchor="drain", mirror=False, label=None, label_loc=None):
    """게이트 왼쪽(mirror면 오른쪽), 드레인 위, 소스 아래, 소스 화살표 바깥. 벌크 없음."""
    return _fet(d, elm.AnalogNFet, at, anchor, mirror, label, label_loc)


def pmos(d, at=None, anchor="source", mirror=False, label=None, label_loc=None):
    """게이트 왼쪽(mirror면 오른쪽), 소스 위, 드레인 아래, 소스 화살표 안쪽. 벌크 없음."""
    return _fet(d, elm.AnalogPFet, at, anchor, mirror, label, label_loc)


def gate_terminal(d, gate, label, open_=False, right=False):
    """게이트에서 가로선을 긋고 끝에 단자(점, open_이면 개방 원)와 라벨을 단다."""
    line = elm.Line().at(gate).length(GATE_LEAD)
    d.add(line.right() if right else line.left())
    return d.add(elm.Dot(open=open_).label(label, "right" if right else "left"))


def caption(d, xy, text):
    """패널 캡션 (a), (b). 원본처럼 패널 아래 가운데에 둔다."""
    return d.add(elm.Label().at(xy).label(text))


def save_png(drawing, path, dpi=DPI):
    """흰 배경, 여백 최소, 메타데이터 없이 저장한다. Drawing.save()는 매번 다른 바이트를 내서 쓰지 않는다."""
    fig = drawing.draw(show=False)
    fig.fig.savefig(Path(path), dpi=dpi, facecolor="white", bbox_inches="tight",
                    pad_inches=0.05, metadata={"Software": None})
```

- [ ] **Step 5: 통과 확인**

Run: `python3 -m unittest discover -s from_the_past/md/_tools/tests`
Expected: `Ran 76 tests` … `OK`

- [ ] **Step 6: 커밋**

```bash
git add from_the_past/md/_tools/schem_style.py from_the_past/md/_tools/tests/test_schem_style.py
git commit -m "feat(exams): add schemdraw style helpers for redrawn figures

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

### Task 2: `draw_exam.py` — 실행기, 글자 크기 경고, 대조 시트

**Files:**
- Create: `from_the_past/md/_tools/draw_exam.py`
- Test: `from_the_past/md/_tools/tests/test_draw_exam.py`

**Interfaces:**
- Consumes: Task 1 `DPI`, `FONT_SIZE`, `save_png`
- Produces:
  - `REDRAWN = "redrawn"`, `FONT_PT_RANGE = (7.0, 11.0)`, `SHEET_WIDTH = 1200`
  - `sources(exam_dir) -> list[Path]` (`figures/redrawn/fig-*.py`, 정렬됨)
  - `load_draw(py: Path) -> Callable[[], schemdraw.Drawing]` (없으면 `ValueError("draw() 없음")`)
  - `printed_font_pt(crop_w_px, crop_dpi, redrawn_w_px, dpi=DPI) -> float`
  - `draw_all(exam_dir, out_dir=None) -> tuple[list[Path], list[str], list[str]]` (쓴 PNG, 오류, 경고)
  - `compare_sheet(exam_dir, out) -> Path`
  - `main(argv) -> int` (0 성공, 1 그림 오류, 2 사용법)

- [ ] **Step 1: 실패하는 테스트 쓰기** — `from_the_past/md/_tools/tests/test_draw_exam.py`

```python
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
```

- [ ] **Step 2: 실패 확인**

Run: `python3 -m unittest from_the_past/md/_tools/tests/test_draw_exam.py`
Expected: `ModuleNotFoundError: No module named 'draw_exam'`

- [ ] **Step 3: 구현** — `from_the_past/md/_tools/draw_exam.py`

```python
#!/usr/bin/env python3
"""시험 폴더의 figures/redrawn/fig-Q<n>.py를 실행해 다시 그린 회로도 PNG를 만든다.

그림 코드는 `def draw() -> schemdraw.Drawing` 하나를 둔다. 규칙은 FORMAT-EXAM.md '다시 그린 그림'.

사용법: python3 draw_exam.py <시험 폴더> [--compare <out.png>]
"""
import importlib.util
import struct
import sys
from pathlib import Path

import yaml
from PIL import Image, ImageDraw

from schem_style import DPI, FONT_SIZE, save_png

REDRAWN = "redrawn"
FONT_PT_RANGE = (7.0, 11.0)   # 문제집에 찍힐 라벨 글자 크기(pt) 허용 범위
SHEET_WIDTH = 1200            # 대조 시트 폭(px)
USAGE = "사용법: python3 draw_exam.py <시험 폴더> [--compare <out.png>]"


def png_size(path):
    return struct.unpack(">II", Path(path).read_bytes()[16:24])


def sources(exam_dir):
    return sorted((Path(exam_dir) / "figures" / REDRAWN).glob("fig-*.py"))


def load_draw(py):
    spec = importlib.util.spec_from_file_location("redrawn_" + py.stem.replace("-", "_"), py)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    draw = getattr(mod, "draw", None)
    if not callable(draw):
        raise ValueError("draw() 없음")
    return draw


def printed_font_pt(crop_w_px, crop_dpi, redrawn_w_px, dpi=DPI):
    """문제집은 다시 그린 그림을 크롭과 같은 폭으로 찍는다. 그때의 라벨 글자 크기(pt)."""
    return FONT_SIZE * (crop_w_px / crop_dpi) / (redrawn_w_px / dpi)


def crop_dpi(exam_dir):
    spec = yaml.safe_load((Path(exam_dir) / "figures" / "figures.yaml").read_text(encoding="utf-8")) or {}
    return spec.get("dpi", 144)


def draw_all(exam_dir, out_dir=None):
    """(쓴 PNG 목록, 오류 줄, 경고 줄). out_dir를 주면 PNG를 거기에 쓴다(verify_exam --redraw용)."""
    exam_dir = Path(exam_dir)
    fig_dir = exam_dir / "figures"
    written, errors, warnings = [], [], []
    for py in sources(exam_dir):
        out = Path(out_dir or py.parent) / (py.stem + ".png")
        try:
            save_png(load_draw(py)(), out)
        except Exception as e:  # 그림 하나가 틀려도 나머지는 그린다
            errors.append(f"{py.name}: {e}")
            continue
        written.append(out)
        crop = fig_dir / (py.stem + ".png")
        if crop.exists():
            pt = printed_font_pt(png_size(crop)[0], crop_dpi(exam_dir), png_size(out)[0])
            lo, hi = FONT_PT_RANGE
            if not lo <= pt <= hi:
                warnings.append(f"{out.name}: 인쇄 글자 {pt:.1f}pt (허용 {lo:g}–{hi:g}pt). 그림 폭을 조정")
    return written, errors, warnings


def compare_sheet(exam_dir, out):
    """크롭(위)과 다시 그린 그림(아래)을 같은 폭으로 쌓은 대조 시트."""
    fig_dir = Path(exam_dir) / "figures"
    tiles = []
    for png in sorted((fig_dir / REDRAWN).glob("fig-*.png")):
        for tag, path in (("crop", fig_dir / png.name), ("redrawn", png)):
            if not path.exists():
                continue
            img = Image.open(path).convert("RGB")
            img = img.resize((SHEET_WIDTH, round(img.height * SHEET_WIDTH / img.width)))
            label = Image.new("RGB", (SHEET_WIDTH, 28), "white")
            ImageDraw.Draw(label).text((6, 6), f"{png.stem} {tag}", fill="red")
            tiles += [label, img]
    if not tiles:
        raise ValueError("다시 그린 그림이 없음")
    sheet = Image.new("RGB", (SHEET_WIDTH, sum(t.height for t in tiles)), "white")
    y = 0
    for t in tiles:
        sheet.paste(t, (0, y))
        y += t.height
    sheet.save(out)
    return Path(out)


def main(argv):
    args = argv[1:]
    compare = None
    if "--compare" in args:
        i = args.index("--compare")
        if i + 1 >= len(args):
            print(USAGE, file=sys.stderr)
            return 2
        compare = args[i + 1]
        args = args[:i] + args[i + 2:]
    if len(args) != 1 or not Path(args[0]).is_dir():
        print(USAGE, file=sys.stderr)
        return 2
    exam_dir = Path(args[0])
    written, errors, warnings = draw_all(exam_dir)
    for path in written:
        print(path)
    for w in warnings:
        print(f"WARN {w}")
    for e in errors:
        print(f"ERROR {e}")
    if compare and not errors:
        print(compare_sheet(exam_dir, compare))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

- [ ] **Step 4: 통과 확인**

Run: `python3 -m unittest discover -s from_the_past/md/_tools/tests`
Expected: `Ran 82 tests` … `OK`

- [ ] **Step 5: 커밋**

```bash
git add from_the_past/md/_tools/draw_exam.py from_the_past/md/_tools/tests/test_draw_exam.py
git commit -m "feat(exams): add draw_exam runner with font-size warning and compare sheet

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

### Task 3: `verify_exam.py` — redrawn 짝·id 검사와 `--redraw`, FORMAT-EXAM 규칙

**Files:**
- Modify: `from_the_past/md/_tools/verify_exam.py` (docstring 4행, `verify` 166–184행, `main` 187–202행; 새 함수는 `verify` 앞에 넣음)
- Modify: `from_the_past/md/FORMAT-EXAM.md` (`## 텍스트 레이어 (2021)` 앞에 새 절, `## 검사` 명령 추가)
- Test: `from_the_past/md/_tools/tests/test_verify_exam.py`

**Interfaces:**
- Consumes: Task 2 `draw_all(exam_dir, out_dir=None)`, `crop_exam.figure_filename`
- Produces: `check_redrawn(exam_dir) -> list[str]`, `check_redraw(exam_dir) -> list[str]`, `verify(exam_dir, recrop=False, redraw=False) -> list[str]`. CLI 플래그는 `--redraw`다.

- [ ] **Step 1: 실패하는 테스트 쓰기.** `test_verify_exam.py`의 import 줄 `from verify_exam import main, verify  # noqa: E402` 바로 위에 `from draw_exam import draw_all  # noqa: E402`를 넣는다. 그다음 `class MainTest` 앞에 아래를 넣는다.

```python
SIMPLE_FIG = '''import schemdraw.elements as elm
from schem_style import new_drawing


def draw():
    d = new_drawing()
    d.add(elm.Resistor().right().label("$R$"))
    return d
'''


class RedrawnTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.exam = make_full_exam(Path(self.tmp.name))
        self.red = self.exam / "figures" / "redrawn"
        self.red.mkdir()
        (self.red / "fig-Q2.py").write_text(SIMPLE_FIG, encoding="utf-8")
        draw_all(self.exam)

    def tearDown(self):
        self.tmp.cleanup()

    def assertHas(self, errors, fragment):
        self.assertTrue(any(fragment in e for e in errors), errors)

    def test_valid_redrawn_passes(self):
        self.assertEqual(verify(self.exam, recrop=True, redraw=True), [])

    def test_png_without_py(self):
        (self.red / "fig-Q2.py").unlink()
        self.assertHas(verify(self.exam), "redrawn/fig-Q2.png: 짝이 되는 .py 없음")

    def test_py_without_png(self):
        (self.red / "fig-Q2.png").unlink()
        self.assertHas(verify(self.exam), "redrawn/fig-Q2.py: PNG 없음")

    def test_unknown_id_and_stray_file(self):
        (self.red / "fig-Q9.py").write_text(SIMPLE_FIG, encoding="utf-8")
        (self.red / "notes.txt").write_text("x", encoding="utf-8")
        errors = verify(self.exam)
        self.assertHas(errors, "redrawn/fig-Q9: figures.yaml에 없는 그림")
        self.assertHas(errors, "redrawn/notes.txt: 알 수 없는 파일")

    def test_redraw_detects_stale_png(self):
        (self.red / "fig-Q2.py").write_text(SIMPLE_FIG.replace('"$R$"', '"$R_2$"'), encoding="utf-8")
        self.assertHas(verify(self.exam, redraw=True), "redrawn/fig-Q2.png: 코드로 다시 그린 결과와 다름")
```

- [ ] **Step 2: 실패 확인**

Run: `python3 -m unittest from_the_past/md/_tools/tests/test_verify_exam.py`
Expected: `TypeError: verify() got an unexpected keyword argument 'redraw'`, 그리고 `test_png_without_py` 등 3개 FAIL

- [ ] **Step 3: 구현.** `verify_exam.py`의 `def verify(` 바로 앞에 넣는다.

```python
REDRAWN_RE = re.compile(r"^fig-(Q[1-9]\d*(?:-[2-9]|-[1-9]\d+)?)\.(py|png)$")


def check_redrawn(exam_dir):
    """figures/redrawn/: fig-<id>.py와 fig-<id>.png가 짝으로 있고 id가 figures.yaml에 있는지."""
    red = exam_dir / "figures" / "redrawn"
    if not red.is_dir():
        return []
    spec = yaml.safe_load((exam_dir / "figures" / "figures.yaml").read_text(encoding="utf-8")) or {}
    yaml_ids = {str(k) for k in (spec.get("figures") or {})}
    errors, found = [], {"py": set(), "png": set()}
    for path in sorted(red.iterdir()):
        if path.name == "__pycache__":
            continue
        m = REDRAWN_RE.match(path.name)
        if not m:
            errors.append(f"redrawn/{path.name}: 알 수 없는 파일 (fig-Q<n>.py와 fig-Q<n>.png만 둠)")
            continue
        found[m.group(2)].add(m.group(1))
    for i in sorted(found["png"] - found["py"]):
        errors.append(f"redrawn/{figure_filename(i)}: 짝이 되는 .py 없음")
    for i in sorted(found["py"] - found["png"]):
        errors.append(f"redrawn/fig-{i}.py: PNG 없음 (draw_exam.py 실행)")
    for i in sorted((found["py"] | found["png"]) - yaml_ids):
        errors.append(f"redrawn/fig-{i}: figures.yaml에 없는 그림")
    return errors


def check_redraw(exam_dir):
    """redrawn/*.py로 다시 그려 지금 PNG와 바이트가 같은지. schemdraw가 필요해서 여기서만 import한다."""
    from draw_exam import draw_all
    red = exam_dir / "figures" / "redrawn"
    errors = []
    with tempfile.TemporaryDirectory() as t:
        written, draw_errors, _ = draw_all(exam_dir, out_dir=t)
        errors += [f"다시 그리기 실패: {e}" for e in draw_errors]
        for out in written:
            current = red / out.name
            if current.exists() and current.read_bytes() != out.read_bytes():
                errors.append(f"redrawn/{out.name}: 코드로 다시 그린 결과와 다름 (draw_exam.py 다시 실행)")
    return errors
```

이어서 기존 코드를 이렇게 바꾼다.
- docstring 4행: `사용법: python3 verify_exam.py <시험 폴더> [--recrop] [--redraw]    예) python3 verify_exam.py ../2021-1_중간 --recrop --redraw`
- `def verify(exam_dir, recrop=False):` → `def verify(exam_dir, recrop=False, redraw=False):`
- checks 목록의 마지막 항목 `("check_readme", lambda: check_readme(exam_dir))]` → `("check_readme", lambda: check_readme(exam_dir)),` 다음 줄에 `("check_redrawn", lambda: check_redrawn(exam_dir))]`
- `if recrop:` 블록 바로 뒤에 넣는다.

```python
    if redraw:
        checks.append(("check_redraw", lambda: check_redraw(exam_dir)))
```

- `main`을 이렇게 바꾼다.

```python
def main(argv):
    flags = ("--recrop", "--redraw")
    args = [a for a in argv[1:] if a not in flags]
    if len(args) != 1:
        print("사용법: python3 verify_exam.py <시험 폴더> [--recrop] [--redraw]", file=sys.stderr)
        return 2
    exam_dir = Path(args[0]).resolve()
    if not exam_dir.is_dir():
        print(f"시험 폴더가 없음: {exam_dir}", file=sys.stderr)
        return 2
    errors = verify(exam_dir, recrop="--recrop" in argv[1:], redraw="--redraw" in argv[1:])
    for e in errors:
        print(f"ERROR {e}")
    print(f"{exam_dir}: 오류 {len(errors)}개")
    return 1 if errors else 0
```

- [ ] **Step 4: FORMAT-EXAM.md에 규칙 추가.** `## 텍스트 레이어 (2021)` 바로 앞에 넣는다.

```markdown
## 다시 그린 그림 (figures/redrawn)
- 문제집에는 크롭 대신 schemdraw로 다시 그린 그림을 넣는다. 크롭(`figures/fig-Q<n>.png`)은 지우지 않는다. 원본 기록이자 인쇄 폭의 기준이다.
- 파일: `figures/redrawn/fig-Q<n>.py`(`def draw() -> schemdraw.Drawing`)와 `draw_exam.py`가 만든 `fig-Q<n>.png`. id는 figures.yaml 키와 같다.
- 연결은 `## 회로` 넷리스트, 모양은 `- 단자:`·`- 표시:`·`- 배치:` bullet을 따른다. 크롭은 배치를 눈으로 참고할 때만 쓰고, `> 참고:` 줄의 손글씨 획은 그리지 않는다.
- 공통 기호와 저장은 `_tools/schem_style.py`로만 한다(`nmos`, `pmos`, `gate_terminal`, `caption`, `save_png`).
- 문제집은 다시 그린 그림을 크롭과 같은 폭으로 찍는다. 라벨 글자가 7–11pt를 벗어나면 `draw_exam.py`가 `WARN`을 낸다.
- md의 이미지 링크는 크롭을 그대로 가리킨다.
```

`## 검사` 코드 블록의 `verify_exam.py … --recrop` 줄을 아래 두 줄로 바꾼다.

```bash
python3 from_the_past/md/_tools/draw_exam.py from_the_past/md/2021-1_중간 [--compare /tmp/sheet.png]
python3 from_the_past/md/_tools/verify_exam.py from_the_past/md/2021-1_중간 --recrop --redraw
```

같은 파일 맨 위 폴더 트리의 `_tools/verify_exam.py` 줄 아래에 두 줄을 넣는다.

```
  _tools/schem_style.py       # 다시 그린 그림의 공통 기호·저장
  _tools/draw_exam.py         # figures/redrawn/*.py → PNG, --compare 대조 시트
```

그리고 `figures/figures.yaml, figures/fig-Q<n>.png` 줄 아래에 `    figures/redrawn/fig-Q<n>.py, fig-Q<n>.png   # 다시 그린 그림`을 넣는다.

- [ ] **Step 5: 통과 확인, 그리고 지금 main의 네 회차가 그대로 통과하는지 확인**

```bash
python3 -m unittest discover -s from_the_past/md/_tools/tests       # Ran 87 tests … OK
for e in 2021-1_중간 2021-1_기말 2023-1_중간 2023-1_기말; do python3 from_the_past/md/_tools/verify_exam.py from_the_past/md/$e --recrop --redraw | tail -1; done   # 모두 오류 0개
```

- [ ] **Step 6: 커밋**

```bash
git add from_the_past/md/_tools/verify_exam.py from_the_past/md/_tools/tests/test_verify_exam.py from_the_past/md/FORMAT-EXAM.md
git commit -m "feat(exams): verify redrawn figure pairs and freshness

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

### Task 4: 문제집 생성기가 redrawn 그림을 쓰게 하기, 그리고 도구 병합

**Files:**
- Modify: `workbook/problem.py:165-185` (`figures`)
- Modify: `workbook/README.md` (준비 절, 'md에서 PDF로 가는 것' 표의 그림 행)
- Test: `workbook/tests/test_problem.py` (`class TestExam`)

**Interfaces:**
- Consumes: 파일 규칙 `<시험>/figures/redrawn/fig-<id>.png` (Task 3)
- Produces: `figures(p)`는 기출에서 redrawn이 있으면 `src`에 그 PNG를 넣고, `w_mm`는 크롭 기준, `h_mm`는 `round(w_mm * rh / rw, 1)`로 준다.

- [ ] **Step 1: 실패하는 테스트 쓰기.** `test_problem.py`의 `TestExam`에서 `test_exam_crop_rejected` 뒤에 넣는다.

```python
    def test_redrawn_replaces_crop_at_crop_width(self):
        fig_dir = self.p.path.parent / "figures"
        crop_src = figures(self.p)[0]["src"]
        (fig_dir / "redrawn").mkdir()
        make_png(fig_dir / "redrawn" / "fig-Q1.png", 432, 288)
        figs = figures(self.p)
        self.assertEqual([(f["w_mm"], f["h_mm"]) for f in figs], [(25.4, 16.9)])
        self.assertNotEqual(figs[0]["src"], crop_src)

    def test_redrawn_needs_crop_for_size(self):
        fig_dir = self.p.path.parent / "figures"
        (fig_dir / "redrawn").mkdir()
        make_png(fig_dir / "redrawn" / "fig-Q1.png", 432, 288)
        (fig_dir / "fig-Q1.png").unlink()
        with self.assertRaisesRegex(ProblemError, "그림 파일 없음"):
            figures(self.p)
```

- [ ] **Step 2: 실패 확인**

Run: `python3 -m unittest workbook/tests/test_problem.py`
Expected: `test_redrawn_replaces_crop_at_crop_width` FAIL (`(25.4, 12.7)` != `(25.4, 16.9)`)

- [ ] **Step 3: 구현.** `figures()`의 반복문 끝부분을 바꾼다. 지금 코드:

```python
        data = png.read_bytes()
        w, h = png_size(data)
        out.append({"src": "data:image/png;base64," + base64.b64encode(data).decode("ascii"),
                    "w_mm": round(w / dpi * 25.4, 1), "h_mm": round(h / dpi * 25.4, 1)})
```

바꾼 코드:

```python
        data = png.read_bytes()
        w, h = png_size(data)
        w_mm, h_mm = round(w / dpi * 25.4, 1), round(h / dpi * 25.4, 1)
        redrawn = p.figures_dir / "redrawn" / png.name
        if p.is_exam and redrawn.exists():
            # 다시 그린 그림은 크롭과 같은 폭, 높이는 자기 비율 (FORMAT-EXAM.md '다시 그린 그림')
            data = redrawn.read_bytes()
            rw, rh = png_size(data)
            h_mm = round(w_mm * rh / rw, 1)
        out.append({"src": "data:image/png;base64," + base64.b64encode(data).decode("ascii"),
                    "w_mm": w_mm, "h_mm": h_mm})
```

docstring도 바꾼다: `"""문제 그림(role: problem)을 base64 data URI와 인쇄 크기(mm)로. mm = 픽셀 / dpi × 25.4. 기출에 figures/redrawn/ 그림이 있으면 그것을 크롭 폭으로 넣는다."""`

- [ ] **Step 4: README.** `workbook/README.md` '준비' 코드 블록의 pip 줄을 `pip3 install --user --break-system-packages playwright schemdraw matplotlib`로 바꾼다. 표의 그림 행은 이렇게 바꾼다.

```markdown
| 그림 | frontmatter `figures`의 `role: problem` 그림 (크기 = 픽셀 / dpi × 25.4 mm). 기출은 `figures/redrawn/fig-<id>.png`가 있으면 그것을 크롭과 같은 폭으로 넣는다 |
```

- [ ] **Step 5: 통과 확인**

```bash
python3 -m unittest discover -s workbook/tests                      # Ran 99 tests … OK
python3 -m unittest discover -s from_the_past/md/_tools/tests       # Ran 87 tests … OK
```

- [ ] **Step 6: 커밋**

```bash
git add workbook/problem.py workbook/tests/test_problem.py workbook/README.md
git commit -m "feat(workbook): use redrawn exam figures at crop width

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 7: 전체 리뷰 요청 후 병합 확인 (멈춤).** opus 리뷰어가 `git diff main...claude/redraw-tools`를 읽기 전용으로 검토한다. 사용자에게 `git log --oneline main..claude/redraw-tools`, 두 테스트 결과, 리뷰 요약을 보여 주고 병합 여부를 묻는다. 승인하면 아래를 실행한다.

```bash
git -C $MAIN/.claude/worktrees/redraw-tools rebase main
git -C $MAIN merge --ff-only claude/redraw-tools
git -C $MAIN worktree remove $MAIN/.claude/worktrees/redraw-tools && git -C $MAIN branch -d claude/redraw-tools
```

### Task 5: 파일럿 — 2021-1 중간 (Q2, Q3, Q4, Q5)

**Files:**
- Create: `from_the_past/md/2021-1_중간/figures/redrawn/fig-Q{2,3,4,5}.py`, `fig-Q{2,3,4,5}.png`
- Create: `docs/superpowers/reports/redraw/2021-1_중간.md`
- Modify (스타일 확인에서 필요할 때만): `from_the_past/md/_tools/schem_style.py`

**Interfaces:**
- Consumes: Task 1 `schem_style`의 모든 함수, Task 2 `draw_exam.py`
- Produces: `verify_exam.py from_the_past/md/2021-1_중간 --recrop --redraw` 오류 0. 스타일을 확정한 `schem_style.py`(Task 6–8이 그대로 씀).

실행 방식: 작성자 subagent(opus)가 Step 1–2와 4–5를 한다. Step 3에서는 사용자가 스타일을 확인한다. 리뷰어 subagent(opus)는 Step 6을 한다.

- [ ] **Step 1: worktree**

```bash
git -C "$MAIN" worktree add "$MAIN/.claude/worktrees/redraw-2021-mid" -b claude/redraw-2021-mid main
```

- [ ] **Step 2: Q2 그리기.** 아래 코드를 `from_the_past/md/2021-1_중간/figures/redrawn/fig-Q2.py`로 쓴다. 이 코드는 프로토타입에서 렌더링해 크롭과 대조했다. 그다음 `draw_exam.py`를 돌려 절차 R 3–4를 확인한다.

```python
"""2021-1 중간 Q2 — 기준: Q2.md '회로 — Fig Q2(a)', '회로 — Fig Q2(b)'."""
import schemdraw.elements as elm

from schem_style import caption, gate_terminal, new_drawing, nmos, pmos


def panel_a(d, x0):
    # 한 세로줄 아래→위: 접지, M1, n1, M2, Vout, M3, M4, VDD
    m1 = nmos(d, at=(x0, 0), anchor="source", label="$M_1$")
    d.add(elm.Ground().at(m1.source))
    gate_terminal(d, m1.gate, "$V_{in}$", open_=True)
    d.add(elm.Line().up().at(m1.drain).length(0.4))
    n1 = d.add(elm.Dot())
    m2 = nmos(d, at=n1.center, anchor="source")
    gate_terminal(d, m2.gate, "$V_{b2}$")
    d.add(elm.Line().up().at(m2.drain).length(0.4))
    vout = d.add(elm.Dot())
    d.add(elm.Label().at((m2.drain.x - 0.35, vout.center.y - 0.35)).label("$M_2$"))
    m3 = pmos(d, at=vout.center, anchor="drain", label="$M_3$")
    gate_terminal(d, m3.gate, "$V_{b3}$")
    m4 = pmos(d, at=m3.source, anchor="drain", label="$M_4$")
    gate_terminal(d, m4.gate, "$V_{b4}$")
    d.add(elm.Vdd().at(m4.source).label("$V_{DD}$", "right"))
    # Vout → 두 번째 접속점 → Vout 원. 두 번째 접속점에서 R_P를 지나 n1로
    d.add(elm.Line().right().at(vout.center).length(0.8))
    tap = d.add(elm.Dot())
    d.add(elm.Line().right().length(0.8))
    d.add(elm.Dot(open=True).label("$V_{out}$", "right"))
    d.add(elm.Resistor().down().at(tap.center).toy(n1.center).label("$R_P$", "bottom"))
    d.add(elm.Line().left().tox(n1.center))
    caption(d, (x0, -1.3), "(a)")


def half_b(d, x, rail_y, mirror):
    """(b)의 한쪽 세로줄 위→아래: R_S, M3/M4, 출력 접속점, M1/M2, 소스 접속점, I_SS."""
    # 아래로 그리는 소자의 라벨: loc="bottom"이 오른쪽, "top"이 왼쪽에 붙는다
    side = "bottom" if mirror else "top"
    rs = d.add(elm.Resistor().down().at((x, rail_y)).length(1.2).label("$R_S$", side))
    mp = pmos(d, at=rs.end, anchor="source")
    d.add(elm.Line().down().at(mp.drain).length(0.4))
    out = d.add(elm.Dot())
    mn = nmos(d, at=out.center, anchor="drain", mirror=mirror,
              label="$M_2$" if mirror else "$M_1$")
    d.add(elm.Line().down().at(mn.source).length(0.3))
    src = d.add(elm.Dot())
    iss = d.add(elm.SourceI().down().at(src.center).length(1.4).label("$I_{SS}$", side))
    d.add(elm.Ground().at(iss.end))
    return mp, out, mn, src


def panel_b(d, x0):
    xl, xr, rail_y = x0, x0 + 3.6, 6.3
    d.add(elm.Line().right().at((xl - 0.3, rail_y)).to((xr + 0.3, rail_y)).linewidth(2.5))
    d.add(elm.Label().at((xr + 0.3, rail_y + 0.25)).label("$V_{DD}$", "right"))
    m3, out1, m1, n3 = half_b(d, xl, rail_y, mirror=False)
    m4, out2, m2, n4 = half_b(d, xr, rail_y, mirror=True)
    d.add(elm.Label().at((m3.gate.x - 0.1, m3.gate.y + 0.35)).label("$M_3$"))
    d.add(elm.Label().at((m4.gate.x - 0.1, m4.gate.y + 0.35)).label("$M_4$"))
    # V_b → M3 게이트, 같은 높이로 M4 게이트까지 (게이트 공통선)
    gate_terminal(d, m3.gate, "$V_b$")
    d.add(elm.Line().right().at(m3.gate).tox(m4.gate))
    # 출력: 두 원이 가운데에서 마주 보고 그 사이에 V_out
    d.add(elm.Line().right().at(out1.center).length(0.9))
    d.add(elm.Dot(open=True))
    d.add(elm.Line().left().at(out2.center).length(0.9))
    d.add(elm.Dot(open=True))
    d.add(elm.Label().at(((xl + xr) / 2, out1.center.y)).label("$V_{out}$"))
    gate_terminal(d, m1.gate, "$V_{in1}$", open_=True)
    gate_terminal(d, m2.gate, "$V_{in2}$", open_=True, right=True)
    d.add(elm.Resistor().right().at(n3.center).to(n4.center).label("$R_{SS}$", "bottom"))
    caption(d, ((xl + xr) / 2, -1.3), "(b)")


def draw():
    d = new_drawing()
    panel_a(d, 0)
    panel_b(d, 5.5)
    return d
```

```bash
cd $MAIN/.claude/worktrees/redraw-2021-mid
python3 from_the_past/md/_tools/draw_exam.py from_the_past/md/2021-1_중간 --compare $SCRATCH/2021-mid-Q2.png   # ERROR·WARN 없음
```

- [ ] **Step 3: 스타일 확인 (멈춤).** `$SCRATCH/2021-mid-Q2.png`를 사용자에게 보여 준다(SendUserFile). 선 굵기, 글자 크기, FET 기호, 레일 굵기 중 바꿀 것이 있는지 묻는다.
  - 바꿀 것이 있으면 `schem_style.py`의 상수(`LW`, `FONT_SIZE`, `GATE_LEAD`)나 `_fet`를 고친다.
  - 고친 뒤에는 기출 도구 테스트 87개를 다시 돌리고 Q2를 다시 그린다.
  - 확정하면 커밋한다.

```bash
git add from_the_past/md/2021-1_중간/figures/redrawn/fig-Q2.py from_the_past/md/2021-1_중간/figures/redrawn/fig-Q2.png
git add from_the_past/md/_tools/schem_style.py      # 바꾼 경우에만
git commit -m "feat(2021-1 중간): redraw Q2 figure and settle schematic style

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 4: Q3, Q4, Q5 그리기.** 그림마다 절차 R을 적용한다. Q3와 Q5는 패널이 둘이므로(frontmatter `panels` 확인) `panel_a`, `panel_b`로 나눈다.
- [ ] **Step 5: 검증과 커밋.** 절차 V(`<회차>` = `2021-1_중간`)를 돌린다.

```bash
git add from_the_past/md/2021-1_중간/figures/redrawn/fig-Q3.py from_the_past/md/2021-1_중간/figures/redrawn/fig-Q3.png \
        from_the_past/md/2021-1_중간/figures/redrawn/fig-Q4.py from_the_past/md/2021-1_중간/figures/redrawn/fig-Q4.png \
        from_the_past/md/2021-1_중간/figures/redrawn/fig-Q5.py from_the_past/md/2021-1_중간/figures/redrawn/fig-Q5.png
git commit -m "feat(2021-1 중간): redraw Q3–Q5 figures

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 6: 리뷰.** 리뷰어(opus)가 네 그림 모두에 절차 C를 적용하고 `docs/superpowers/reports/redraw/2021-1_중간.md`를 쓴다. 작성자가 지적을 반영하고 절차 V를 다시 돌린 뒤 `fix(2021-1 중간): apply redraw review`로 커밋한다. 이 커밋에는 보고서, 고친 `.py`, 고친 `.png`를 넣는다.
- [ ] **Step 7: 병합 확인 (멈춤).** 사용자에게 `git log --oneline main..claude/redraw-2021-mid`, 절차 V 결과, 리뷰 요약, 대조 시트를 보여 주고 병합 여부를 묻는다. 승인하면 아래를 실행한다.

```bash
git -C $MAIN/.claude/worktrees/redraw-2021-mid rebase main
git -C $MAIN merge --ff-only claude/redraw-2021-mid
git -C $MAIN worktree remove $MAIN/.claude/worktrees/redraw-2021-mid && git -C $MAIN branch -d claude/redraw-2021-mid
```

### Task 6: 2021-1 기말 (Q1–Q6)

Task 5가 병합된 main에서 시작한다. Task 6·7·8은 서로 다른 worktree이므로 **동시에** 띄운다. 작성자는 opus subagent, 리뷰어는 별도 opus subagent다.

**Files:**
- Create: `from_the_past/md/2021-1_기말/figures/redrawn/fig-Q{1,2,3,4,5,6}.py`, `.png`
- Create: `docs/superpowers/reports/redraw/2021-1_기말.md`

**Interfaces:**
- Consumes: 확정된 `schem_style.py`(고치지 않음), `draw_exam.py`
- Produces: `verify_exam.py from_the_past/md/2021-1_기말 --recrop --redraw` 오류 0

- [ ] **Step 1:** `git -C "$MAIN" worktree add "$MAIN/.claude/worktrees/redraw-2021-fin" -b claude/redraw-2021-fin main`
- [ ] **Step 2:** Q1–Q6에 절차 R을 적용한다. Q5는 패널 두 개로 폭이 167 mm이므로, `WARN`이 없게 패널 사이 간격을 조정한다. `schem_style.py`는 고치지 않는다. 스타일 문제가 보이면 보고서에 적고 사용자에게 알린다.
- [ ] **Step 3:** 절차 V(`<회차>` = `2021-1_기말`)를 돌린 뒤 커밋한다.

```bash
git add from_the_past/md/2021-1_기말/figures/redrawn/fig-Q1.py from_the_past/md/2021-1_기말/figures/redrawn/fig-Q1.png \
        from_the_past/md/2021-1_기말/figures/redrawn/fig-Q2.py from_the_past/md/2021-1_기말/figures/redrawn/fig-Q2.png \
        from_the_past/md/2021-1_기말/figures/redrawn/fig-Q3.py from_the_past/md/2021-1_기말/figures/redrawn/fig-Q3.png \
        from_the_past/md/2021-1_기말/figures/redrawn/fig-Q4.py from_the_past/md/2021-1_기말/figures/redrawn/fig-Q4.png \
        from_the_past/md/2021-1_기말/figures/redrawn/fig-Q5.py from_the_past/md/2021-1_기말/figures/redrawn/fig-Q5.png \
        from_the_past/md/2021-1_기말/figures/redrawn/fig-Q6.py from_the_past/md/2021-1_기말/figures/redrawn/fig-Q6.png
git commit -m "feat(2021-1 기말): redraw Q1–Q6 figures

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 4:** 리뷰어(opus)가 절차 C를 적용하고 `docs/superpowers/reports/redraw/2021-1_기말.md`를 쓴다. 작성자가 반영하고 절차 V를 다시 돌린 뒤 `fix(2021-1 기말): apply redraw review`로 커밋한다. 커밋에는 보고서와 고친 파일을 넣는다.
- [ ] **Step 5 (멈춤):** 병합 여부를 묻는다. 승인하면 `rebase main` → `git -C $MAIN merge --ff-only claude/redraw-2021-fin` → `worktree remove`와 `branch -d`를 실행한다.

### Task 7: 2023-1 중간 (Q2, Q3, Q4)

**Files:**
- Create: `from_the_past/md/2023-1_중간/figures/redrawn/fig-Q{2,3,4}.py`, `.png`
- Create: `docs/superpowers/reports/redraw/2023-1_중간.md`

**Interfaces:**
- Consumes: 확정된 `schem_style.py`(고치지 않음), `draw_exam.py`
- Produces: `verify_exam.py from_the_past/md/2023-1_중간 --recrop --redraw` 오류 0

- [ ] **Step 1:** `git -C "$MAIN" worktree add "$MAIN/.claude/worktrees/redraw-2023-mid" -b claude/redraw-2023-mid main`
- [ ] **Step 2:** Q2, Q3, Q4에 절차 R을 적용한다. 이 회차는 손글씨가 겹친 스캔이라 다음을 지킨다.
  - 크롭보다 md 넷리스트와 배치 bullet을 우선한다. 예를 들어 Q3(a)의 M3·M4 위 X자 획, V_b1 둘레 세로 획, (a) 왼쪽에 손으로 그린 회로는 그리지 않는다.
  - Q2는 BJT 회로다(`elm.BjtNpn`, `elm.BjtPnp`). 배치 bullet의 ③번 접속점(Q_REF2 컬렉터 아래, 점 여부 판독 불가)에는 점을 찍는다.
- [ ] **Step 3:** 절차 V(`<회차>` = `2023-1_중간`)를 돌린 뒤 커밋한다.

```bash
git add from_the_past/md/2023-1_중간/figures/redrawn/fig-Q2.py from_the_past/md/2023-1_중간/figures/redrawn/fig-Q2.png \
        from_the_past/md/2023-1_중간/figures/redrawn/fig-Q3.py from_the_past/md/2023-1_중간/figures/redrawn/fig-Q3.png \
        from_the_past/md/2023-1_중간/figures/redrawn/fig-Q4.py from_the_past/md/2023-1_중간/figures/redrawn/fig-Q4.png
git commit -m "feat(2023-1 중간): redraw Q2–Q4 figures without answer-sheet handwriting

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 4:** 리뷰어(opus)가 절차 C를 적용한다. 추가로 각 md의 `> 참고:` 줄에 적힌 손글씨 항목을 하나씩 짚어, 그 획이 그림에 없는지 표에 적는다. 보고서는 `docs/superpowers/reports/redraw/2023-1_중간.md`다. 작성자가 반영하고 절차 V를 다시 돌린 뒤 `fix(2023-1 중간): apply redraw review`로 커밋한다.
- [ ] **Step 5 (멈춤):** 병합 여부를 묻는다. 승인하면 `rebase main` → `git -C $MAIN merge --ff-only claude/redraw-2023-mid` → `worktree remove`와 `branch -d`를 실행한다.

### Task 8: 2023-1 기말 (Q1–Q5)

**Files:**
- Create: `from_the_past/md/2023-1_기말/figures/redrawn/fig-Q{1,2,3,4,5}.py`, `.png`
- Create: `docs/superpowers/reports/redraw/2023-1_기말.md`

**Interfaces:**
- Consumes: 확정된 `schem_style.py`(고치지 않음), `draw_exam.py`
- Produces: `verify_exam.py from_the_past/md/2023-1_기말 --recrop --redraw` 오류 0

- [ ] **Step 1:** `git -C "$MAIN" worktree add "$MAIN/.claude/worktrees/redraw-2023-fin" -b claude/redraw-2023-fin main`
- [ ] **Step 2: Q1(b) 대조용 원본 뽑기 (저장소에 넣지 않음).** hwp 안의 깨끗한 원본 그림을 `$SCRATCH`에 꺼낸다. `olefile`은 scratch에만 설치한다.

```bash
export SCRATCH=<scratchpad 경로>
pip3 install -q --target $SCRATCH/py olefile
PYTHONPATH=$SCRATCH/py python3 - <<'EOF'
import os, zlib, olefile
src = "from_the_past/2023-1/23-1 기말/2023 전회2 기말.hwp"
out = os.environ["SCRATCH"] + "/hwp"
os.makedirs(out, exist_ok=True)
o = olefile.OleFileIO(src)
for e in o.listdir():
    if e[0] == "BinData":
        data = o.openstream(e).read()
        try:
            data = zlib.decompress(data, -15)
        except zlib.error:
            pass
        open(f"{out}/{e[1]}", "wb").write(data)
        print(e[1], len(data))
EOF
```

`$SCRATCH/hwp/BIN0001.PNG` 오른쪽이 Q1(b)의 깨끗한 원본이다. 왼쪽의 붉은 글씨는 손글씨이므로 무시한다. `BIN0002.PNG`는 손으로 그린 노트라서 쓰지 않는다.
- [ ] **Step 3:** Q1–Q5에 절차 R을 적용한다. 이 회차도 손글씨가 겹친 스캔이므로 다음을 지킨다.
  - md 넷리스트와 배치 bullet을 우선한다.
  - Q1(a)에 손으로 쓴 C_GS·C_GD·C_SB·C_DB 커패시터와 라벨은 하나도 그리지 않는다.
  - Q3의 "open", R_L, M4 게이트 선 아래의 손으로 그린 저항과 접지도 그리지 않는다.
  - Q5의 -1 증폭기와 그것을 둘러싼 점선 원은 인쇄된 것인지 md 표시·배치 bullet으로 확인한다. 인쇄된 것만 그린다.
- [ ] **Step 4:** 절차 V(`<회차>` = `2023-1_기말`)를 돌린 뒤 커밋한다.

```bash
git add from_the_past/md/2023-1_기말/figures/redrawn/fig-Q1.py from_the_past/md/2023-1_기말/figures/redrawn/fig-Q1.png \
        from_the_past/md/2023-1_기말/figures/redrawn/fig-Q2.py from_the_past/md/2023-1_기말/figures/redrawn/fig-Q2.png \
        from_the_past/md/2023-1_기말/figures/redrawn/fig-Q3.py from_the_past/md/2023-1_기말/figures/redrawn/fig-Q3.png \
        from_the_past/md/2023-1_기말/figures/redrawn/fig-Q4.py from_the_past/md/2023-1_기말/figures/redrawn/fig-Q4.png \
        from_the_past/md/2023-1_기말/figures/redrawn/fig-Q5.py from_the_past/md/2023-1_기말/figures/redrawn/fig-Q5.png
git commit -m "feat(2023-1 기말): redraw Q1–Q5 figures without answer-sheet handwriting

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 5:** 리뷰어(opus)가 절차 C를 적용한다. 추가로 두 가지를 한다.
  - 각 md의 `> 참고:` 줄에 적힌 손글씨 항목이 그림에 없는지 하나씩 표에 적는다.
  - Q1(b)는 `$SCRATCH/hwp/BIN0001.PNG`와도 대조한다.

  보고서는 `docs/superpowers/reports/redraw/2023-1_기말.md`다. 작성자가 반영하고 절차 V를 다시 돌린 뒤 `fix(2023-1 기말): apply redraw review`로 커밋한다.
- [ ] **Step 6 (멈춤):** 병합 여부를 묻는다. 승인하면 `rebase main` → `git -C $MAIN merge --ff-only claude/redraw-2023-fin` → `worktree remove`와 `branch -d`를 실행한다.

### Task 9: 기출 PDF 다시 만들기 (Task 5–8이 모두 병합된 뒤)

**Files:**
- Modify: `workbook/pdf/2021-1_중간-문제.pdf`, `2021-1_중간-답안.pdf`, `2021-1_기말-문제.pdf`, `2021-1_기말-답안.pdf`, `2023-1_중간-문제.pdf`, `2023-1_중간-답안.pdf`, `2023-1_기말-문제.pdf`, `2023-1_기말-답안.pdf`

**Interfaces:**
- Consumes: 네 회차의 `figures/redrawn/*.png`, Task 4의 `figures()`
- Produces: 다시 그린 그림이 들어간 기출 PDF 8개

- [ ] **Step 1: 시점 확인 (멈춤).** `git -C $MAIN worktree list`로 `sol-exams`가 아직 있는지 본다. 있으면 사용자에게 두 가지 중 하나를 묻는다.
  - (1) 지금 만들고, `sol-exams`가 병합된 뒤 PDF를 한 번 더 만든다.
  - (2) `sol-exams` 병합을 기다린다.
- [ ] **Step 2: worktree와 빌드**

```bash
git -C "$MAIN" worktree add "$MAIN/.claude/worktrees/redraw-pdf" -b claude/redraw-pdf main
cd $MAIN/.claude/worktrees/redraw-pdf
for e in 2021-1_중간 2021-1_기말 2023-1_중간 2023-1_기말; do
  python3 from_the_past/md/_tools/verify_exam.py from_the_past/md/$e --recrop --redraw | tail -1   # 오류 0개
  python3 workbook/build_workbook.py $e 2>&1 | tail -3                                            # OVERFLOW·ERROR 없음
done
```

- [ ] **Step 3: 눈으로 확인.** 문제지 PDF 네 개에서 그림이 있는 쪽을 `fitz`로 `$SCRATCH`에 렌더링하고 Read로 연다. 확인할 것은 다음과 같다.
  - 크롭이 아니라 다시 그린 그림이 들어갔다.
  - 그림이 찌그러지지 않았다.
  - 글자가 읽힌다.

```bash
python3 - <<'EOF'
import os, fitz
for e in ["2021-1_중간", "2021-1_기말", "2023-1_중간", "2023-1_기말"]:
    doc = fitz.open(f"workbook/pdf/{e}-문제.pdf")
    for i, page in enumerate(doc):
        if page.get_images():
            page.get_pixmap(dpi=110).save(f"{os.environ['SCRATCH']}/{e}-p{i + 1}.png")
EOF
```

- [ ] **Step 4: 커밋**

```bash
git add workbook/pdf/2021-1_중간-문제.pdf workbook/pdf/2021-1_중간-답안.pdf \
        workbook/pdf/2021-1_기말-문제.pdf workbook/pdf/2021-1_기말-답안.pdf \
        workbook/pdf/2023-1_중간-문제.pdf workbook/pdf/2023-1_중간-답안.pdf \
        workbook/pdf/2023-1_기말-문제.pdf workbook/pdf/2023-1_기말-답안.pdf
git commit -m "build: regenerate exam pdfs with redrawn figures

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 5 (멈춤):** 렌더링한 쪽 몇 장을 사용자에게 보여 주고 병합 여부를 묻는다. 승인하면 `rebase main` → `git -C $MAIN merge --ff-only claude/redraw-pdf` → `worktree remove`와 `branch -d`를 실행한다.
