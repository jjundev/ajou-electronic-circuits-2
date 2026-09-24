# 9장 교과서 문제 MD 변환 — 샘플 라운드 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 스캔본 `9장.pdf`의 문제를 복원 가능한 md로 바꾸는 형식·도구를 만들고, 샘플 7문제(E9.01, X9.01, E9.16, P9.04, P9.10, P9.38, P9.59)를 작성·검증해 사용자 피드백을 받는다.

**Architecture:** 문제 1개 = md 1개(frontmatter + 조건/구할 것/회로/답). 회로는 SPICE식 넷리스트에 `단자`/`표시`/`배치` bullet을 붙여 텍스트만으로 복원 가능하게 하고, PDF에서 잘라낸 그림 PNG는 대조용으로 링크한다. `crop_figures.py`가 `figures.yaml`의 bbox로 그림을 자르고, `check_md.py`가 형식을 기계적으로 검사한다.

**Tech Stack:** Python 3 (Homebrew), PyMuPDF 1.27 (`import fitz`), PyYAML 6.0, 표준 라이브러리 `unittest` (pytest 미설치).

**Spec:** `docs/superpowers/specs/2026-09-24-textbook-problem-md-design.md`

## Global Constraints

- 모든 경로는 레포 루트 `/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2` 기준.
- 원본 PDF: `교과서/마이크로전자회로/9장.pdf`. **수정하지 말고, git에 add하지도 말 것.**
- 브랜치 `feat/ch09-problem-md`에서 작업. `git add`에는 항상 경로를 명시 (`git add -A` / `git add .` 금지).
- 커밋 메시지 마지막 줄: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`
- md 문장은 **한국어**, 기호·용어(R_out, β, Early voltage 등)는 영어.
- 교재 문장을 **그대로 옮기지 말고** 조건/구할 것으로 재구성. 수치·단위·소문항은 하나도 빠뜨리지 말 것.
- 그림 PNG는 **144 dpi**(스캔 원래 해상도). 파일명은 `fig<장>-<번호 두 자리>.png` (예: `fig9-02.png`).
- md 파일 위치: `교과서/마이크로전자회로/ch09/{예제,연습문제,장말문제}/{E,X,P}9.NN.md`.
- `$SCRATCH` = 실행 세션의 scratchpad 디렉터리 (없으면 `/private/tmp/ch09-check`). 확인용 이미지는 모두 여기에 저장하고 레포에 두지 않는다. 셸 상태가 유지되지 않으므로 `$SCRATCH`를 쓰는 **모든 Bash 호출 앞에** `export SCRATCH=<경로>; mkdir -p "$SCRATCH";`를 붙인다.
- **원본 확대 명령** (여러 Task에서 사용). PAGE는 PDF 페이지(1부터), 좌표는 PDF pt:
  ```bash
  python3 -c "import fitz,sys; d=fitz.open('교과서/마이크로전자회로/9장.pdf'); d[int(sys.argv[1])-1].get_pixmap(dpi=216, clip=fitz.Rect(*map(float, sys.argv[2:6]))).save(sys.argv[6])" PAGE X0 Y0 X1 Y1 OUT.png
  ```
- PDF 페이지 ↔ 교재 쪽: p.1 = 449쪽, p.2–18 = 두 쪽 펼침(p.n = (2n+446)–(2n+447)쪽), p.19–29 = 484–494쪽, p.30 = 495쪽 윗부분.
- **원본 대조 체크리스트** (모든 md 작성 Task의 검증 단계에서 사용):
  1. 소자 종류와 극성 (npn/pnp, nmos/pmos)
  2. 각 단자의 연결 (C/B/E, D/G/S가 넷리스트와 그림에서 같은 노드인지)
  3. 선이 접속한 곳(점)인지, 그냥 교차한 곳인지
  4. 전류원·전류 화살표 방향
  5. 라벨과 첨자 (Vb1 vs Vb2, Q1 vs Q2, A_E 배수)
  6. 수치와 단위 (지수, μ/m, V/mV)
  7. 빠진 소문항 없는지 ((a)(b)…)

---

## File Structure

| 파일 | 책임 |
|---|---|
| `교과서/마이크로전자회로/_tools/crop_figures.py` | `figures.yaml`을 읽어 PDF에서 그림 PNG 생성. `figure_filename()` 제공 |
| `교과서/마이크로전자회로/_tools/check_md.py` | 문제 md 형식 검사기 (frontmatter, 절, 넷리스트 문법, bullet, 이미지·그림 존재) |
| `교과서/마이크로전자회로/_tools/tests/test_crop_figures.py` | 크롭 도구 테스트 |
| `교과서/마이크로전자회로/_tools/tests/test_check_md.py` | 검사기 테스트 |
| `교과서/마이크로전자회로/FORMAT.md` | 형식 규칙 (사람·에이전트가 읽는 기준 문서, 다른 장에도 재사용) |
| `교과서/마이크로전자회로/ch09/figures/figures.yaml` | 그림 id → PDF 페이지·bbox |
| `교과서/마이크로전자회로/ch09/figures/fig9-*.png` | 크롭된 그림 7개 |
| `교과서/마이크로전자회로/ch09/예제/E9.01.md`, `E9.16.md` | 샘플 예제 |
| `교과서/마이크로전자회로/ch09/연습문제/X9.01.md` | 샘플 연습문제 |
| `교과서/마이크로전자회로/ch09/장말문제/P9.04.md`, `P9.10.md`, `P9.38.md`, `P9.59.md` | 샘플 장말문제 |
| `docs/superpowers/reports/2026-09-24-ch09-sample-round-1.md` | 검증 결과 보고서 (사용자 피드백용) |

---

### Task 1: 그림 크롭 도구 + 샘플용 그림 7개

**Files:**
- Create: `교과서/마이크로전자회로/_tools/crop_figures.py`
- Create: `교과서/마이크로전자회로/_tools/tests/test_crop_figures.py`
- Create: `교과서/마이크로전자회로/ch09/figures/figures.yaml`
- Create (생성물): `교과서/마이크로전자회로/ch09/figures/fig9-02.png`, `fig9-30.png`, `fig9-33.png`, `fig9-42.png`, `fig9-47.png`, `fig9-62.png`, `fig9-78.png`

**Interfaces:**
- Consumes: 없음
- Produces:
  - `figure_filename(fig_id: str) -> str` — `"9.2"` → `"fig9-02.png"`, `"9.42"` → `"fig9-42.png"`
  - `crop_all(ch_dir: pathlib.Path) -> list[pathlib.Path]` — `ch_dir/figures/figures.yaml`을 읽어 PNG를 저장하고 경로 목록 반환. bbox가 페이지 밖이거나 그림 id가 문자열이 아니면 `ValueError`
  - CLI: `python3 crop_figures.py <장 폴더>`

- [ ] **Step 1: 작업 브랜치 만들기**

```bash
git switch -c feat/ch09-problem-md
```
Expected: `Switched to a new branch 'feat/ch09-problem-md'`

- [ ] **Step 2: 실패하는 테스트 작성**

`교과서/마이크로전자회로/_tools/tests/test_crop_figures.py`:

```python
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
```

- [ ] **Step 3: 테스트가 실패하는지 확인**

Run: `python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests -p "test_crop_figures.py" -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'crop_figures'`

- [ ] **Step 4: 최소 구현 작성**

`교과서/마이크로전자회로/_tools/crop_figures.py`:

```python
#!/usr/bin/env python3
"""figures.yaml에 적힌 bbox로 PDF에서 그림을 잘라 PNG로 저장한다.

사용법: python3 crop_figures.py <장 폴더>    예) python3 crop_figures.py ../ch09
"""
import sys
from pathlib import Path

import fitz
import yaml


def figure_filename(fig_id: str) -> str:
    chapter, number = fig_id.split(".")
    return f"fig{chapter}-{int(number):02d}.png"


def crop_all(ch_dir: Path) -> list[Path]:
    fig_dir = ch_dir / "figures"
    spec = yaml.safe_load((fig_dir / "figures.yaml").read_text(encoding="utf-8"))
    pdf_path = (fig_dir / spec["pdf"]).resolve()
    dpi = spec.get("dpi", 144)
    written = []
    with fitz.open(pdf_path) as doc:
        for fig_id, fig in spec["figures"].items():
            if not isinstance(fig_id, str):
                raise ValueError(f"그림 id {fig_id!r} 는 따옴표로 감싼 문자열이어야 함 (예: \"9.30\")")
            page = doc[fig["pdf_page"] - 1]
            rect = fitz.Rect(*fig["bbox"])
            if not page.rect.contains(rect):
                raise ValueError(f"{fig_id}: bbox {fig['bbox']} 가 {fig['pdf_page']}쪽 범위 {tuple(page.rect)} 밖")
            out = fig_dir / figure_filename(fig_id)
            page.get_pixmap(dpi=dpi, clip=rect).save(out)
            written.append(out)
    return written


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("사용법: python3 crop_figures.py <장 폴더>", file=sys.stderr)
        return 2
    for path in crop_all(Path(argv[1])):
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

- [ ] **Step 5: 테스트 통과 확인**

Run: `python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests -p "test_crop_figures.py" -v`
Expected: `Ran 5 tests` … `OK`

- [ ] **Step 6: 샘플용 figures.yaml 작성**

`교과서/마이크로전자회로/ch09/figures/figures.yaml` (bbox는 계획 작성 시 실제로 잘라 보고 확인한 값):

```yaml
# 그림 id → PDF 페이지(1부터)와 bbox [x0, y0, x1, y1] (PDF pt, 왼쪽 위 원점)
# id 는 반드시 따옴표로 감싼다 ("9.30" 이 숫자 9.3 으로 바뀌는 것 방지)
pdf: ../../9장.pdf
dpi: 144
figures:
  "9.2":  {pdf_page: 2,  bbox: [850, 40, 1045, 138]}
  "9.30": {pdf_page: 14, bbox: [185, 290, 345, 435]}
  "9.33": {pdf_page: 15, bbox: [830, 40, 1015, 175]}
  "9.42": {pdf_page: 20, bbox: [25, 520, 465, 660]}
  "9.47": {pdf_page: 21, bbox: [310, 250, 465, 365]}
  "9.62": {pdf_page: 25, bbox: [285, 360, 475, 470]}
  "9.78": {pdf_page: 28, bbox: [280, 548, 465, 670]}
```

- [ ] **Step 7: 그림 크롭 실행**

Run: `python3 교과서/마이크로전자회로/_tools/crop_figures.py 교과서/마이크로전자회로/ch09`
Expected: `fig9-02.png` … `fig9-78.png` 경로 7줄 출력

- [ ] **Step 8: 크롭 결과 눈으로 확인**

```bash
python3 -c "
from PIL import Image; import glob, os
fs = sorted(glob.glob('교과서/마이크로전자회로/ch09/figures/fig9-*.png')); ims = [Image.open(f) for f in fs]
c = Image.new('RGB', (max(i.width for i in ims), sum(i.height + 10 for i in ims)), 'white'); y = 0
for i in ims: c.paste(i, (0, y)); y += i.height + 10
c.save(os.path.join(os.environ.get('SCRATCH', '/private/tmp/ch09-check'), 'figs.png'))"
```
`$SCRATCH/figs.png`를 Read로 열어 확인. Expected:
- 9.2: (a) Q1/Q2 적층 + (b) Q1·r_O2 등가회로. 위쪽 R_out 라벨까지 포함
- 9.30: I_REF 0.2 mA, 기준 소자 4개(4A_E), X, Q1(A_E), Q2(10A_E)
- 9.33: VCC 레일, P, Q_F, X, Q1, Q2
- 9.42: 패널 (a)–(d)와 "Figure 9.42" 라벨
- 9.47: VCC = 2.5 V, Q2, X, Q1, Circuit 상자, 0.5 mA
- 9.62: V_REF, R1, 연산증폭기, Q1, V1, Q2, I_X, 배터리
- 9.78: V_DD 라벨부터 M4–M1, V_out. 위쪽에 본문 텍스트가 섞이지 않을 것

그림이 잘렸거나 옆 텍스트가 섞였으면 해당 bbox를 5–10 pt씩 조정하고 Step 7부터 다시 한다.

- [ ] **Step 9: 커밋**

```bash
git add 교과서/마이크로전자회로/_tools/crop_figures.py 교과서/마이크로전자회로/_tools/tests/test_crop_figures.py 교과서/마이크로전자회로/ch09/figures/
git commit -m "feat: add figure crop tool and ch09 sample figures

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: 형식 검사기 + FORMAT.md

**Files:**
- Create: `교과서/마이크로전자회로/_tools/check_md.py`
- Create: `교과서/마이크로전자회로/_tools/tests/test_check_md.py`
- Create: `교과서/마이크로전자회로/FORMAT.md`

**Interfaces:**
- Consumes: `figure_filename(fig_id: str) -> str` (Task 1, `crop_figures.py`)
- Produces:
  - `check_netlist_line(line: str) -> str | None` — 문제가 없으면 `None`, 있으면 오류 문장
  - `check_file(path: Path, ch_dir: Path) -> tuple[list[str], list[str]]` — `(errors, warnings)`
  - `main(argv: list[str]) -> int` — 오류가 있으면 1, 없으면 0, 사용법 오류는 2
  - CLI: `python3 check_md.py <장 폴더>`

- [ ] **Step 1: 실패하는 테스트 작성**

`교과서/마이크로전자회로/_tools/tests/test_check_md.py`:

````python
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_md import check_file, check_netlist_line, main  # noqa: E402

VALID_MD = """---
id: E9.01
kind: 예제
number: "9.1"
section: "9.1.1 전류원으로서의 캐스코드"
book_page: 451
pdf_page: 2
source_lang: ko
figures:
  - {id: "9.2", role: problem, panels: [a]}
depends_on: []
refs: ["식 9.7"]
---
# 예제 9.1 — 테스트

## 조건
- I_C = 1 mA

## 구할 것
- R_out

## 회로 — Fig 9.2(a)
```spice
Q1  out  Vb1  n1  npn
Q2  n1   Vb2  0   npn
```
- 단자: Vb1, Vb2 = 이상적 DC 바이어스
- 표시: R_out 화살표
- 배치: 위→아래 Q1, Q2

![Fig 9.2](../figures/fig9-02.png)

## 답 (검증용)
- 328.9 kΩ
"""


def make_chapter(root: Path, files: dict, with_png: bool = True) -> Path:
    ch = root / "ch09"
    (ch / "figures").mkdir(parents=True)
    if with_png:
        (ch / "figures" / "fig9-02.png").write_bytes(b"\x89PNG")
    for rel, text in files.items():
        p = ch / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return ch


class NetlistLineTest(unittest.TestCase):
    def test_valid_lines(self):
        for line in [
            "Q1 out Vb1 n1 npn",
            "QR1 X X 0 npn area=4",
            "Q2 X Vb2 VCC pnp",
            "M4 n3 Vb3 VDD pmos W/L=20/0.18",
            "IREF VCC X 0.2mA",
            "RP Vb1 n1",
            "R1 VREF n1 {R_1}",
            "VB 0 n3",
            "X1 0 n1 V1 opamp",
            'X1 n1 0 box "Circuit"',
            "* 주석 줄",
            "Q1 a b c npn   ; 뒤 주석",
            "",
        ]:
            with self.subTest(line=line):
                self.assertIsNone(check_netlist_line(line))

    def test_invalid_lines(self):
        for line in ["Q1 a b npn", "M1 d g s nfet", "Z1 a b", "X1 a b opamp", "Q1 a b c npn area=x"]:
            with self.subTest(line=line):
                self.assertIsNotNone(check_netlist_line(line))


class CheckFileTest(unittest.TestCase):
    def run_check(self, text, rel="예제/E9.01.md", with_png=True):
        with tempfile.TemporaryDirectory() as t:
            ch = make_chapter(Path(t), {rel: text}, with_png=with_png)
            return check_file(ch / rel, ch)

    def test_valid_file_has_no_errors(self):
        self.assertEqual(self.run_check(VALID_MD), ([], []))

    def test_missing_frontmatter_key(self):
        errors, _ = self.run_check(VALID_MD.replace("pdf_page: 2\n", ""))
        self.assertTrue(any("pdf_page" in e for e in errors), errors)

    def test_filename_must_match_id(self):
        errors, _ = self.run_check(VALID_MD, rel="예제/E9.02.md")
        self.assertTrue(any("파일명" in e for e in errors), errors)

    def test_folder_must_match_kind(self):
        errors, _ = self.run_check(VALID_MD, rel="장말문제/E9.01.md")
        self.assertTrue(any("폴더" in e for e in errors), errors)

    def test_bad_netlist_line(self):
        errors, _ = self.run_check(VALID_MD.replace("Q2  n1   Vb2  0   npn", "Q2  n1   Vb2  npn"))
        self.assertTrue(any("넷리스트 문법 오류" in e for e in errors), errors)

    def test_missing_layout_bullet(self):
        errors, _ = self.run_check(VALID_MD.replace("- 배치: 위→아래 Q1, Q2\n", ""))
        self.assertTrue(any("- 배치:" in e for e in errors), errors)

    def test_missing_image_and_figure(self):
        errors, _ = self.run_check(VALID_MD, with_png=False)
        self.assertTrue(any("이미지 없음" in e for e in errors), errors)
        self.assertTrue(any("그림 파일 없음" in e for e in errors), errors)

    def test_example_needs_answer_section(self):
        errors, _ = self.run_check(VALID_MD.split("## 답 (검증용)")[0])
        self.assertTrue(any("## 답 (검증용)" in e for e in errors), errors)

    def test_problem_needs_difficulty_and_sol(self):
        text = VALID_MD.replace("id: E9.01", "id: P9.01").replace("kind: 예제", "kind: 장말문제")
        errors, _ = self.run_check(text, rel="장말문제/P9.01.md")
        self.assertTrue(any("difficulty" in e for e in errors), errors)

    def test_missing_dependency_is_only_warning(self):
        errors, warnings = self.run_check(VALID_MD.replace("depends_on: []", "depends_on: [E9.15]"))
        self.assertEqual(errors, [])
        self.assertTrue(any("E9.15" in w for w in warnings), warnings)


class MainTest(unittest.TestCase):
    def test_exit_codes(self):
        with tempfile.TemporaryDirectory() as t:
            ok = make_chapter(Path(t) / "ok", {"예제/E9.01.md": VALID_MD})
            bad = make_chapter(Path(t) / "bad", {"예제/E9.01.md": VALID_MD}, with_png=False)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(["check_md.py", str(ok)]), 0)
                self.assertEqual(main(["check_md.py", str(bad)]), 1)
                self.assertEqual(main(["check_md.py"]), 2)


if __name__ == "__main__":
    unittest.main()
````

- [ ] **Step 2: 테스트가 실패하는지 확인**

Run: `python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests -p "test_check_md.py" -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'check_md'`

- [ ] **Step 3: 검사기 구현**

`교과서/마이크로전자회로/_tools/check_md.py`:

```python
#!/usr/bin/env python3
"""교과서 문제 md 형식 검사기. 규칙은 ../FORMAT.md.

사용법: python3 check_md.py <장 폴더>    예) python3 check_md.py ../ch09
오류가 하나라도 있으면 종료 코드 1.
"""
import re
import sys
from pathlib import Path

import yaml

from crop_figures import figure_filename

KIND_BY_PREFIX = {"E": "예제", "X": "연습문제", "P": "장말문제"}
REQUIRED_KEYS = ["id", "kind", "number", "section", "book_page", "pdf_page",
                 "source_lang", "figures", "depends_on", "refs"]
FIGURE_ROLES = {"problem", "answer"}
ID_RE = re.compile(r"^([EXP])(\d+)\.(\d{2})$")

NODE = r"[A-Za-z0-9_]+"
NETLIST_RES = [
    re.compile(rf"^Q\w*\s+{NODE}\s+{NODE}\s+{NODE}\s+(npn|pnp)(\s+area=\d+(\.\d+)?)?$"),
    re.compile(rf"^M\w*\s+{NODE}\s+{NODE}\s+{NODE}\s+(nmos|pmos)(\s+W/L=[\d.]+/[\d.]+)?$"),
    re.compile(rf"^[RCLIV]\w*\s+{NODE}\s+{NODE}(\s+\S+)?$"),
    re.compile(rf"^X\w*\s+{NODE}\s+{NODE}\s+{NODE}\s+opamp$"),
    re.compile(rf'^X\w*(\s+{NODE})+\s+box\s+"[^"]+"$'),
]
SPICE_BLOCK_RE = re.compile(r"```spice\n(.*?)\n```", re.DOTALL)
IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)\)")
REQUIRED_BULLETS = ["- 단자:", "- 표시:", "- 배치:"]


def split_frontmatter(text):
    if not text.startswith("---\n"):
        raise ValueError("frontmatter(---)로 시작하지 않음")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError("frontmatter 닫는 --- 없음")
    return yaml.safe_load(text[4:end]) or {}, text[end + 5:]


def check_netlist_line(line):
    code = line.split(";", 1)[0].strip()
    if not code or code.startswith("*"):
        return None
    if any(r.match(code) for r in NETLIST_RES):
        return None
    return f"넷리스트 문법 오류: {code!r}"


def check_file(path, ch_dir):
    errors, warnings = [], []
    try:
        meta, body = split_frontmatter(path.read_text(encoding="utf-8"))
    except (ValueError, yaml.YAMLError) as e:
        return [str(e)], warnings

    missing = [k for k in REQUIRED_KEYS if k not in meta]
    if missing:
        return [f"frontmatter 키 누락: {', '.join(missing)}"], warnings

    m = ID_RE.match(str(meta["id"]))
    if not m:
        return [f"id 형식 오류: {meta['id']!r} (예: E9.01)"], warnings
    kind = KIND_BY_PREFIX[m.group(1)]
    if meta["kind"] != kind:
        errors.append(f"kind {meta['kind']!r} 가 id 접두어와 안 맞음 (기대: {kind})")
    if path.stem != meta["id"]:
        errors.append(f"파일명 {path.name} 이 id {meta['id']} 와 다름")
    if path.parent.name != kind:
        errors.append(f"폴더 {path.parent.name} 이 kind {kind} 와 다름")
    if kind == "장말문제":
        if meta.get("difficulty") not in (0, 1, 2):
            errors.append("장말문제 difficulty 는 0, 1, 2 중 하나")
        if not isinstance(meta.get("sol"), bool):
            errors.append("장말문제 sol 은 true/false")

    headings = [l.strip() for l in body.splitlines() if l.startswith("## ")]
    for h in ("## 조건", "## 구할 것"):
        if h not in headings:
            errors.append(f"절 누락: {h}")
    if not any(h.startswith("## 회로") for h in headings):
        errors.append("절 누락: ## 회로 …")
    if kind == "예제" and "## 답 (검증용)" not in headings:
        errors.append("예제에 절 누락: ## 답 (검증용)")

    blocks = list(SPICE_BLOCK_RE.finditer(body))
    if not blocks:
        errors.append("```spice 블록 없음")
    for b in blocks:
        lines = b.group(1).splitlines()
        for line in lines:
            err = check_netlist_line(line)
            if err:
                errors.append(err)
        after = body[b.end():]
        stop = re.search(r"\n(## |### |```)", after)
        tail = [l.strip() for l in (after[:stop.start()] if stop else after).splitlines()]
        for bullet in REQUIRED_BULLETS:
            if not any(l.startswith(bullet) for l in tail):
                first = lines[0].strip() if lines else ""
                errors.append(f"넷리스트 블록({first!r}…) 뒤에 '{bullet}' bullet 없음")

    for link in IMAGE_RE.findall(body):
        if not (path.parent / link).exists():
            errors.append(f"이미지 없음: {link}")

    for fig in meta["figures"] or []:
        fig_id = str(fig.get("id", ""))
        if "." not in fig_id:
            errors.append(f"그림 id 형식 오류: {fig_id!r}")
            continue
        if fig.get("role") not in FIGURE_ROLES:
            errors.append(f"그림 {fig_id} role 은 problem/answer")
        if not (ch_dir / "figures" / figure_filename(fig_id)).exists():
            errors.append(f"그림 파일 없음: figures/{figure_filename(fig_id)}")

    for dep in meta["depends_on"] or []:
        dm = ID_RE.match(str(dep))
        if not dm:
            errors.append(f"depends_on id 형식 오류: {dep!r}")
        elif not (ch_dir / KIND_BY_PREFIX[dm.group(1)] / f"{dep}.md").exists():
            warnings.append(f"depends_on {dep} 파일이 아직 없음")
    return errors, warnings


def md_files(ch_dir):
    return sorted(p for kind in KIND_BY_PREFIX.values() for p in (ch_dir / kind).glob("*.md"))


def main(argv):
    if len(argv) != 2:
        print("사용법: python3 check_md.py <장 폴더>", file=sys.stderr)
        return 2
    ch_dir = Path(argv[1])
    files = md_files(ch_dir)
    n_err = 0
    for path in files:
        errors, warnings = check_file(path, ch_dir)
        for e in errors:
            print(f"ERROR {path}: {e}")
        for w in warnings:
            print(f"WARN  {path}: {w}")
        n_err += len(errors)
    print(f"{len(files)}개 파일, 오류 {n_err}개")
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests -v`
Expected: `Ran 18 tests` … `OK` (crop 5개 + check_md 13개)

- [ ] **Step 5: 빈 장 폴더에 검사기 실행**

Run: `python3 교과서/마이크로전자회로/_tools/check_md.py 교과서/마이크로전자회로/ch09`
Expected: `0개 파일, 오류 0개`, 종료 코드 0

- [ ] **Step 6: FORMAT.md 작성**

`교과서/마이크로전자회로/FORMAT.md`:

````markdown
# 교과서 문제 MD 형식

목표: **md 파일 하나만 보고 원본 문제(조건, 질문, 회로도)를 그대로 복원**할 수 있게 한다.
그림 PNG는 대조용이다. md는 이미지 없이도 완결돼야 한다.

## 폴더와 파일 이름
```
교과서/마이크로전자회로/
  FORMAT.md
  _tools/crop_figures.py      # figures.yaml → 그림 PNG
  _tools/check_md.py          # 형식 검사
  ch<장>/
    예제/E<장>.<NN>.md        # 본문 예제
    연습문제/X<장>.<NN>.md    # 예제 <장>.<NN> 바로 뒤의 연습문제
    장말문제/P<장>.<NN>.md    # 장말 PROBLEMS
    figures/figures.yaml, figures/fig<장>-<NN>.png
```
번호는 두 자리로 채운다 (9.1 → `9.01`).

## frontmatter
```yaml
id: P9.04                 # E/X/P + 장.두자리
kind: 장말문제            # 예제 | 연습문제 | 장말문제 (id 접두어와 일치)
number: "9.4"             # 교재 표기 그대로
section: "9.1.1 전류원으로서의 캐스코드"
book_page: 485            # 교재 쪽
pdf_page: 20              # PDF 페이지(1부터)
difficulty: 1             # 장말문제만: * 개수 (0, 1, 2)
sol: false                # 장말문제만: SOL 마크 여부
source_lang: en           # 원문 언어 (ko | en)
figures:                  # 크롭 이미지가 있는 그림만
  - {id: "9.42", role: problem, panels: [a, b, c, d]}   # role: problem | answer
depends_on: []            # 전제로 하는 문제·예제 id (예: [E9.15])
refs: []                  # 참조하는 식·그림·장 (자유 문자열, 예: "식 9.88")
```

## 본문 절 (순서 고정)
1. `# <종류> <번호> — <짧은 제목>`
2. `## 조건` — 주어진 값, 가정, 회로 설명. 원문을 옮기지 않고 bullet로 재구성. 수치·단위는 빠짐없이
3. `## 구할 것` — 소문항 (a)(b)… 모두
4. `## 상속·참조` — (있을 때만) depends_on 문제의 조건, 참조 식(LaTeX), 공통 가정을 **이 파일 안에 풀어서** 적음
5. `## 회로 — Fig <번호>(<패널>)` — 패널마다 하나씩. 넷리스트 + bullet 3개. 마지막 패널 뒤에 이미지 링크
6. `## 답 (검증용)` — 예제만. 최종 답 1–2줄. 풀이에 설계 결과 회로가 있으면 `### 정답 회로 — Fig <번호>`로 넷리스트 + bullet 3개 + 이미지

## 넷리스트 (```spice 블록)
| 소자 | 형식 | 비고 |
|---|---|---|
| BJT | `Q<이름> C B E npn\|pnp [area=k]` | area = 이미터 면적 배수 (10A_E → `area=10`) |
| MOSFET | `M<이름> D G S nmos\|pmos [W/L=a/b]` | 그림에 바디 단자가 없으면 생략 |
| R / C / L | `R<이름> n1 n2 [값\|{기호}]` | 값이 기호뿐이면 중괄호 `{R_P}` |
| 전류원 | `I<이름> from to [값]` | **그림의 화살표가 from → to** (SPICE 규약과 같음) |
| 전압원·배터리 | `V<이름> + - [값]` | 첫 노드가 + 단자 |
| 블랙박스 | `X<이름> 노드… box "라벨"` | "Circuit", "Current Mirror", "?" 상자 |
| 연산증폭기 | `X<이름> in+ in- out opamp` | |

- 주석: 줄 앞 `*` 또는 줄 뒤 `; …`
- **노드 이름**
  - 그림에 라벨이 있으면 그대로, 첨자는 붙여 씀: `X`, `P`, `Vout`, `Vin`, `Vb1`, `VREF`, `V1`, `VCC`, `VDD`
  - 라벨 없는 내부 노드: `n1`, `n2`, …
  - 라벨 없는 측정 단자(R_out, I_copy, I_X 화살표가 붙은 개방 단자): `out` (여럿이면 `out1`, `out2`)
  - 접지: `0`
- 그림에 ⇒로 이어진 등가회로가 문제 그림 안에 있으면 별도 패널(`(a-eq)`)로 적는다.

## 넷리스트 뒤 bullet 3개 (필수)
- `- 단자:` 각 개방 단자의 의미 — 이상적 DC 바이어스 / 신호 입력 / 출력 / 전원 레일 값 / 플로팅
- `- 표시:` 그림 위의 표시 — R_out·전류 화살표와 방향, 노드 라벨, 수치 라벨, 면적 라벨, "?" (없으면 `없음`)
- `- 배치:` 그림 모양 — 위→아래 적층 순서, 좌우 위치, 레일·접지 위치, 선이 꺾이는 모양

## 풀이 그림
- 풀이 안의 그림(설계 결과)은 `role: answer`, `## 답 (검증용)`에만 둔다.
- 다른 문제가 그 그림을 문제 그림으로 쓰면, 그 문제에서는 `role: problem`이다 (예: E9.16의 Fig 9.30).

## 수식
- `$…$` / `$$…$$` LaTeX. 단위는 SI (μA, kΩ, V⁻¹ → `\text{V}^{-1}`).

## 검사
```bash
python3 교과서/마이크로전자회로/_tools/check_md.py 교과서/마이크로전자회로/ch09
```
````

- [ ] **Step 7: 커밋**

```bash
git add 교과서/마이크로전자회로/_tools/check_md.py 교과서/마이크로전자회로/_tools/tests/test_check_md.py 교과서/마이크로전자회로/FORMAT.md
git commit -m "feat: add problem md format spec and checker

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: 샘플 E9.01 + X9.01 (예제와 그 변형 연습문제)

**Files:**
- Create: `교과서/마이크로전자회로/ch09/예제/E9.01.md`
- Create: `교과서/마이크로전자회로/ch09/연습문제/X9.01.md`

**Interfaces:**
- Consumes: `figures/fig9-02.png` (Task 1), `check_md.py` CLI (Task 2), FORMAT.md 규칙 (Task 2)
- Produces: `E9.01`, `X9.01` 파일 (X9.01의 `depends_on: [E9.01]`)

- [ ] **Step 1: E9.01.md 작성**

````markdown
---
id: E9.01
kind: 예제
number: "9.1"
section: "9.1.1 전류원으로서의 캐스코드"
book_page: 451
pdf_page: 2
source_lang: ko
figures:
  - {id: "9.2", role: problem, panels: [a]}
depends_on: []
refs: ["식 9.7", "식 9.10"]
---
# 예제 9.1 — 바이폴라 캐스코드 전류원의 출력 저항

## 조건
- 회로: Fig 9.2(a) 바이폴라 캐스코드 전류원
- $Q_1$, $Q_2$ 모두 컬렉터 전류 $I_C = 1\ \text{mA}$로 바이어스
- 두 트랜지스터 모두 $\beta = 100$, $V_A = 5\ \text{V}$

## 구할 것
- 출력 저항 $R_{out}$

## 상속·참조
- 식 (9.7): $R_{out} \approx g_{m1} r_{O1} \left( r_{O2} \parallel r_{\pi 1} \right)$

## 회로 — Fig 9.2(a)
```spice
Q1  out  Vb1  n1  npn
Q2  n1   Vb2  0   npn
```
- 단자: Vb1, Vb2 = 이상적 DC 바이어스(값 미지정) / out = 개방 출력 단자
- 표시: R_out = out을 위에서 아래로 들여다보는 화살표 / n1(Q1 이미터 = Q2 컬렉터)은 그림에 라벨 없음
- 배치: 위→아래 적층 Q1, Q2 / 두 베이스 단자는 왼쪽 / Q2 이미터 아래 접지 / 크롭 이미지 오른쪽의 (b)는 본문 등가회로라 이 문제와 무관

![Fig 9.2](../figures/fig9-02.png)

## 답 (검증용)
- $R_{out} \approx 328.9\ \text{k}\Omega$ ($V_T \approx 26\ \text{mV}$, 식 9.10)
````

- [ ] **Step 2: X9.01.md 작성**

````markdown
---
id: X9.01
kind: 연습문제
number: "9.1"
section: "9.1.1 전류원으로서의 캐스코드"
book_page: 452
pdf_page: 3
source_lang: ko
figures:
  - {id: "9.2", role: problem, panels: [a]}
depends_on: [E9.01]
refs: ["식 9.7"]
---
# 연습문제 9.1 — 목표 출력 저항에 필요한 Early 전압 (예제 9.1 변형)

## 조건
- 예제 9.1과 같은 회로·바이어스: Fig 9.2(a), $Q_1$, $Q_2$ 모두 $I_C = 1\ \text{mA}$, $\beta = 100$
- 바뀐 점: $V_A$가 미지수 (예제처럼 두 트랜지스터 동일), 목표 $R_{out} = 500\ \text{k}\Omega$

## 구할 것
- $R_{out} = 500\ \text{k}\Omega$이 되게 하는 $V_A$

## 상속·참조
- 예제 9.1 (E9.01): $V_A = 5\ \text{V}$일 때 $R_{out} \approx 328.9\ \text{k}\Omega$
- 식 (9.7): $R_{out} \approx g_{m1} r_{O1} \left( r_{O2} \parallel r_{\pi 1} \right)$

## 회로 — Fig 9.2(a)
```spice
Q1  out  Vb1  n1  npn
Q2  n1   Vb2  0   npn
```
- 단자: Vb1, Vb2 = 이상적 DC 바이어스(값 미지정) / out = 개방 출력 단자
- 표시: R_out = out을 위에서 아래로 들여다보는 화살표 / n1(Q1 이미터 = Q2 컬렉터)은 그림에 라벨 없음
- 배치: 위→아래 적층 Q1, Q2 / 두 베이스 단자는 왼쪽 / Q2 이미터 아래 접지 / 크롭 이미지 오른쪽의 (b)는 본문 등가회로라 이 문제와 무관

![Fig 9.2](../figures/fig9-02.png)
````

- [ ] **Step 3: 검사기 실행**

Run: `python3 교과서/마이크로전자회로/_tools/check_md.py 교과서/마이크로전자회로/ch09`
Expected: `2개 파일, 오류 0개`, WARN 없음

- [ ] **Step 4: 원본 대조**

```bash
python3 -c "import fitz,sys; d=fitz.open('교과서/마이크로전자회로/9장.pdf'); d[int(sys.argv[1])-1].get_pixmap(dpi=216, clip=fitz.Rect(*map(float, sys.argv[2:6]))).save(sys.argv[6])" 2 680 420 1191 694 "$SCRATCH/e901.png"
python3 -c "import fitz,sys; d=fitz.open('교과서/마이크로전자회로/9장.pdf'); d[int(sys.argv[1])-1].get_pixmap(dpi=216, clip=fitz.Rect(*map(float, sys.argv[2:6]))).save(sys.argv[6])" 3 0 120 500 180 "$SCRATCH/x901.png"
```
두 이미지와 `figures/fig9-02.png`를 Read로 열고 Global Constraints의 **원본 대조 체크리스트** 7항목을 확인한다. 틀린 곳이 있으면 md를 고치고 Step 3을 다시 실행한다.

- [ ] **Step 5: 커밋**

```bash
git add 교과서/마이크로전자회로/ch09/예제/E9.01.md 교과서/마이크로전자회로/ch09/연습문제/X9.01.md
git commit -m "docs: add ch09 samples E9.01 and X9.01

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: 샘플 E9.16 (앞 예제의 정답 그림을 문제로 쓰는 예제)

**Files:**
- Create: `교과서/마이크로전자회로/ch09/예제/E9.16.md`

**Interfaces:**
- Consumes: `figures/fig9-30.png`, `figures/fig9-33.png` (Task 1), `check_md.py` CLI (Task 2)
- Produces: `E9.16` 파일 (`depends_on: [E9.15]`, E9.15는 이번 라운드에 없음 → WARN 1개가 정상)

- [ ] **Step 1: E9.16.md 작성**

````markdown
---
id: E9.16
kind: 예제
number: "9.16"
section: "9.2.2 바이폴라 전류 거울"
book_page: 476
pdf_page: 15
source_lang: ko
figures:
  - {id: "9.30", role: problem, panels: []}
  - {id: "9.33", role: answer, panels: []}
depends_on: [E9.15]
refs: ["그림 9.32", "식 9.109", "식 9.110", "식 9.116", "식 9.117"]
---
# 예제 9.16 — 베이스 전류에 의한 복사 전류 오차와 이미터 폴로어

## 조건
- 회로: Fig 9.30 (예제 9.15의 설계 결과)
  - $I_{REF} = 0.2\ \text{mA}$
  - 기준 쪽: 단위 트랜지스터 4개 병렬, 총 면적 $4A_E$ (다이오드 연결)
  - $Q_1$ 면적 $A_E$ → 이상적이면 $I_{copy1} = 50\ \mu\text{A}$
  - $Q_2$ 면적 $10A_E$ → 이상적이면 $I_{copy2} = 500\ \mu\text{A}$
- 베이스 전류를 무시하지 않음: 모든 트랜지스터가 같은 유한한 $\beta$
- "폴로어를 붙인다" = 본문 Fig 9.32의 방법. 기준 트랜지스터들의 컬렉터 노드와 공통 베이스 노드 사이에 이미터 폴로어를 넣어 베이스 전류가 $I_{REF}$에서 빠지는 양을 줄임

## 구할 것
- 폴로어를 붙이기 전: $I_{copy1}$, $I_{copy2}$ (베이스 전류에 의한 오차가 드러나는 식)
- 폴로어를 붙인 후: $I_{copy1}$, $I_{copy2}$

## 상속·참조
- 예제 9.15 (E9.15): 200 μA 기준 전류로 50 μA와 500 μA 두 전류를 만드는 전류 거울 설계. 기준 쪽을 50 μA 단위 트랜지스터 4개로 만들고 $Q_1 = A_E$, $Q_2 = 10A_E$로 둔 결과가 Fig 9.30

## 회로 — Fig 9.30
```spice
IREF  VCC   X  0.2mA
QR1   X     X  0  npn  area=1
QR2   X     X  0  npn  area=1
QR3   X     X  0  npn  area=1
QR4   X     X  0  npn  area=1
Q1    out1  X  0  npn  area=1
Q2    out2  X  0  npn  area=10
```
- 단자: VCC = 전원 레일(값 미지정) / out1, out2 = 개방 컬렉터 단자(복사 전류 출력)
- 표시: 전류원 옆 "I_REF", "0.2 mA" / 기준 트랜지스터 4개 아래 중괄호 "4A_E" (개별 이름 라벨 없음) / 노드 X 라벨 / Q1 옆 "A_E", Q2 옆 "10A_E" / I_copy1 = out1로 들어가는 아래 화살표, I_copy2 = out2로 들어가는 아래 화살표
- 배치: 왼쪽 위 VCC와 I_REF(아래 방향) / 기준 트랜지스터 4개가 왼쪽에 가로로 나란히, 컬렉터 공통선이 오른쪽 끝에서 베이스 공통선과 만나 X / X 오른쪽에 Q1 / X에서 아래로 내려간 선이 오른쪽으로 꺾여 Q2 베이스로, Q2는 Q1 아래 / 모든 이미터 아래 접지

![Fig 9.30](../figures/fig9-30.png)

## 답 (검증용)
- 폴로어 전 (식 9.109–9.110): $I_{copy1} = \dfrac{I_{REF}}{4 + 15/\beta}$, $\quad I_{copy2} = \dfrac{10\, I_{REF}}{4 + 15/\beta}$
- 폴로어 후 (식 9.116–9.117): $I_{copy1} = \dfrac{I_{REF}}{4 + 15/\beta^2}$, $\quad I_{copy2} = \dfrac{10\, I_{REF}}{4 + 15/\beta^2}$ — 오차가 약 $\beta$배 줄어듦

### 정답 회로 — Fig 9.33
```spice
IREF  VCC   P  0.2mA
QF    VCC   P  X  npn
QR1   P     X  0  npn  area=1
QR2   P     X  0  npn  area=1
QR3   P     X  0  npn  area=1
QR4   P     X  0  npn  area=1
Q1    out1  X  0  npn  area=1
Q2    out2  X  0  npn  area=10
```
- 단자: VCC = 전원 레일(맨 위 가로선) / out1, out2 = 개방 컬렉터 단자
- 표시: 노드 P, X 라벨 / Q_F 라벨 / "0.2 mA", "4A_E"(중괄호), "A_E", "10A_E" / I_copy1, I_copy2 아래 화살표
- 배치: 맨 위 VCC 가로 레일에서 I_REF가 P로 내려옴 / P = 기준 트랜지스터 4개 컬렉터 공통선 / Q_F는 그 오른쪽, 컬렉터가 레일에 연결, 베이스가 P, 이미터가 아래로 X / X = 기준 트랜지스터 4개 베이스 공통선, 오른쪽으로 Q1 베이스, 아래로 Q2 베이스

![Fig 9.33](../figures/fig9-33.png)
````

- [ ] **Step 2: 검사기 실행**

Run: `python3 교과서/마이크로전자회로/_tools/check_md.py 교과서/마이크로전자회로/ch09`
Expected: `3개 파일, 오류 0개`, `WARN … E9.16.md: depends_on E9.15 파일이 아직 없음` 1줄

- [ ] **Step 3: 원본 대조**

```bash
python3 -c "import fitz,sys; d=fitz.open('교과서/마이크로전자회로/9장.pdf'); d[int(sys.argv[1])-1].get_pixmap(dpi=216, clip=fitz.Rect(*map(float, sys.argv[2:6]))).save(sys.argv[6])" 15 0 220 500 694 "$SCRATCH/e916.png"
python3 -c "import fitz,sys; d=fitz.open('교과서/마이크로전자회로/9장.pdf'); d[int(sys.argv[1])-1].get_pixmap(dpi=216, clip=fitz.Rect(*map(float, sys.argv[2:6]))).save(sys.argv[6])" 14 0 160 500 470 "$SCRATCH/e915.png"
python3 -c "import fitz,sys; d=fitz.open('교과서/마이크로전자회로/9장.pdf'); d[int(sys.argv[1])-1].get_pixmap(dpi=216, clip=fitz.Rect(*map(float, sys.argv[2:6]))).save(sys.argv[6])" 15 830 40 1015 175 "$SCRATCH/f933.png"
```
`e916.png`(예제 9.16 본문), `e915.png`(예제 9.15와 Fig 9.30), `f933.png`를 Read로 열고 **원본 대조 체크리스트** 7항목을 확인한다. 특히:
- Fig 9.30: 기준 트랜지스터의 컬렉터 공통선이 X(베이스 공통선)에 **점으로 접속**하는지 (다이오드 연결)
- Fig 9.33: Q_F 컬렉터가 VCC 레일, 베이스가 P, 이미터가 X인지

틀린 곳이 있으면 md를 고치고 Step 2를 다시 실행한다.

- [ ] **Step 4: 커밋**

```bash
git add 교과서/마이크로전자회로/ch09/예제/E9.16.md
git commit -m "docs: add ch09 sample E9.16

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: 샘플 P9.04 + P9.10 (다중 패널, pnp·블랙박스)

**Files:**
- Create: `교과서/마이크로전자회로/ch09/장말문제/P9.04.md`
- Create: `교과서/마이크로전자회로/ch09/장말문제/P9.10.md`

**Interfaces:**
- Consumes: `figures/fig9-42.png`, `figures/fig9-47.png` (Task 1), `check_md.py` CLI (Task 2)
- Produces: `P9.04`, `P9.10` 파일

- [ ] **Step 1: P9.04.md 작성**

````markdown
---
id: P9.04
kind: 장말문제
number: "9.4"
section: "9.1.1 전류원으로서의 캐스코드"
book_page: 485
pdf_page: 20
difficulty: 1
sol: false
source_lang: en
figures:
  - {id: "9.42", role: problem, panels: [a, b, c, d]}
depends_on: []
refs: []
---
# 장말문제 9.4 — 기생 저항 R_P가 생긴 캐스코드의 출력 저항

## 조건
- 제조 오류로 바이폴라 캐스코드 전류원에 기생 저항 $R_P$가 생김
- $R_P$가 붙은 위치는 Fig 9.42 (a)–(d)마다 다름
- 소자 값은 주어지지 않음 → $g_m$, $r_O$, $r_\pi$, $R_P$ 기호로 답함

## 구할 것
- (a)–(d) 각 회로의 출력 저항 $R_{out}$

## 회로 — Fig 9.42(a)
```spice
Q1  out  Vb1  n1  npn
Q2  n1   Vb2  0   npn
RP  Vb1  n1              ; Q1 베이스 ↔ Q1 이미터
```
- 단자: Vb1, Vb2 = 이상적 DC 바이어스(값 미지정) / out = 개방 출력 단자
- 표시: R_out = out을 위에서 아래로 들여다보는 화살표 / R_P 라벨
- 배치: 위→아래 적층 Q1, Q2 / Vb1 선이 왼쪽에서 들어와 점에서 갈라져 한쪽은 Q1 베이스, 다른 쪽은 아래로 내려가 가로로 놓인 R_P를 거쳐 n1에 닿음

## 회로 — Fig 9.42(b)
```spice
Q1  out  Vb1  n1  npn
Q2  n1   Vb2  0   npn
RP  out  n1              ; Q1 컬렉터 ↔ Q1 이미터
```
- 단자: Vb1, Vb2 = 이상적 DC 바이어스(값 미지정) / out = 개방 출력 단자
- 표시: R_out = out을 위에서 아래로 들여다보는 화살표 / R_P 라벨
- 배치: 위→아래 적층 Q1, Q2 / R_P는 Q1 오른쪽에 세로로, 위 끝은 out(점), 아래 끝은 n1(점)

## 회로 — Fig 9.42(c)
```spice
Q1  out  Vb1  n1  npn
Q2  n1   Vb2  0   npn
RP  n1   0               ; Q1 이미터 ↔ 접지
```
- 단자: Vb1, Vb2 = 이상적 DC 바이어스(값 미지정) / out = 개방 출력 단자
- 표시: R_out = out을 위에서 아래로 들여다보는 화살표 / R_P 라벨
- 배치: 위→아래 적층 Q1, Q2 / n1에서 오른쪽으로 나간 선이 세로 R_P를 거쳐 따로 그린 접지 기호로 (Q2 접지 오른쪽)

## 회로 — Fig 9.42(d)
```spice
Q1  out  Vb1  n1  npn
Q2  n1   Vb2  0   npn
RP  Vb2  n1              ; Q2 베이스 ↔ Q2 컬렉터
```
- 단자: Vb1, Vb2 = 이상적 DC 바이어스(값 미지정) / out = 개방 출력 단자
- 표시: R_out = out을 위에서 아래로 들여다보는 화살표 / R_P 라벨
- 배치: 위→아래 적층 Q1, Q2 / Vb2 선이 왼쪽에서 들어와 점에서 갈라져 한쪽은 Q2 베이스, 다른 쪽은 위로 올라가 Q2 위에 가로로 놓인 R_P를 거쳐 n1에 닿음

![Fig 9.42](../figures/fig9-42.png)
````

- [ ] **Step 2: P9.10.md 작성**

````markdown
---
id: P9.10
kind: 장말문제
number: "9.10"
section: "9.1.1 전류원으로서의 캐스코드"
book_page: 486
pdf_page: 21
difficulty: 1
sol: false
source_lang: en
figures:
  - {id: "9.47", role: problem, panels: []}
depends_on: []
refs: []
---
# 장말문제 9.10 — pnp 캐스코드 전류원의 바이어스 설계

## 조건
- Fig 9.47의 pnp 캐스코드가 어떤 회로("Circuit")에 바이어스 전류 0.5 mA를 공급해야 함
- $V_{CC} = 2.5\ \text{V}$
- $I_S = 10^{-16}\ \text{A}$, $\beta = 100$ (두 트랜지스터 동일)

## 구할 것
- (a) 필요한 $V_{b2}$
- (b) $V_X = V_{b1} + |V_{BE1}|$임을 이용해, $Q_2$의 베이스-컬렉터 순방향 바이어스가 200 mV를 넘지 않게 하는 $V_{b1}$의 최댓값

## 회로 — Fig 9.47
```spice
Q2  X   Vb2  VCC  pnp
Q1  n1  Vb1  X    pnp
X1  n1  0  box "Circuit"
```
- 단자: VCC = 2.5 V 전원 레일 / Vb1, Vb2 = 이상적 DC 바이어스(구할 값) / "Circuit" 상자는 한쪽이 Q1 컬렉터(n1), 다른 쪽이 접지
- 표시: 노드 X 라벨(Q2 컬렉터 = Q1 이미터) / Q1 컬렉터에서 Circuit 쪽으로 흐르는 전류 화살표 "0.5 mA"
- 배치: 위→아래 적층 VCC 레일, Q2, Q1 / 두 베이스 단자는 왼쪽 / Q1 컬렉터 선이 아래로 내려가 오른쪽으로 꺾여 Circuit 상자 왼쪽에 연결 / Circuit 상자 아래 접지

![Fig 9.47](../figures/fig9-47.png)
````

- [ ] **Step 3: 검사기 실행**

Run: `python3 교과서/마이크로전자회로/_tools/check_md.py 교과서/마이크로전자회로/ch09`
Expected: `5개 파일, 오류 0개` (WARN은 E9.16의 1줄만)

- [ ] **Step 4: 원본 대조**

```bash
python3 -c "import fitz,sys; d=fitz.open('교과서/마이크로전자회로/9장.pdf'); d[int(sys.argv[1])-1].get_pixmap(dpi=216, clip=fitz.Rect(*map(float, sys.argv[2:6]))).save(sys.argv[6])" 20 0 510 478 665 "$SCRATCH/f942.png"
python3 -c "import fitz,sys; d=fitz.open('교과서/마이크로전자회로/9장.pdf'); d[int(sys.argv[1])-1].get_pixmap(dpi=216, clip=fitz.Rect(*map(float, sys.argv[2:6]))).save(sys.argv[6])" 20 240 50 478 140 "$SCRATCH/p904.png"
python3 -c "import fitz,sys; d=fitz.open('교과서/마이크로전자회로/9장.pdf'); d[int(sys.argv[1])-1].get_pixmap(dpi=216, clip=fitz.Rect(*map(float, sys.argv[2:6]))).save(sys.argv[6])" 21 250 200 513 420 "$SCRATCH/p910a.png"
python3 -c "import fitz,sys; d=fitz.open('교과서/마이크로전자회로/9장.pdf'); d[int(sys.argv[1])-1].get_pixmap(dpi=216, clip=fitz.Rect(*map(float, sys.argv[2:6]))).save(sys.argv[6])" 22 0 0 260 110 "$SCRATCH/p910b.png"
```
Read로 열고 **원본 대조 체크리스트** 7항목을 확인한다. 특히:
- 9.42: 각 패널에서 R_P 양 끝이 어느 노드에 **점으로** 접속하는지
- 9.47: Q1, Q2 이미터 화살표가 **안쪽을 향하는지** (pnp), Q2 이미터가 VCC인지
- 9.10 (b) 문장이 p.22 윗부분까지 이어짐 — 200 mV 값 확인

틀린 곳이 있으면 md를 고치고 Step 3을 다시 실행한다.

- [ ] **Step 5: 커밋**

```bash
git add 교과서/마이크로전자회로/ch09/장말문제/P9.04.md 교과서/마이크로전자회로/ch09/장말문제/P9.10.md
git commit -m "docs: add ch09 samples P9.04 and P9.10

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: 샘플 P9.38 + P9.59 (연산증폭기·타 장 참조, Design Problems 공통 가정)

**Files:**
- Create: `교과서/마이크로전자회로/ch09/장말문제/P9.38.md`
- Create: `교과서/마이크로전자회로/ch09/장말문제/P9.59.md`

**Interfaces:**
- Consumes: `figures/fig9-62.png`, `figures/fig9-78.png` (Task 1), `check_md.py` CLI (Task 2)
- Produces: `P9.38`, `P9.59` 파일

- [ ] **Step 1: P9.38.md 작성**

````markdown
---
id: P9.38
kind: 장말문제
number: "9.38"
section: "9.2.2 바이폴라 전류 거울"
book_page: 490
pdf_page: 25
difficulty: 0
sol: false
source_lang: en
figures:
  - {id: "9.62", role: problem, panels: []}
depends_on: []
refs: ["그림 9.24(b)", "식 9.88", "8장 로그 증폭기"]
---
# 장말문제 9.38 — 로그 증폭기로 만든 전류 거울?

## 조건
- 한 학생이 Fig 9.24(b) 회로가 로그 함수를 만든다는 점을 배운 뒤, 8장의 로그 증폭기를 떠올려 Fig 9.62 회로를 만듦

## 구할 것
- Fig 9.62 회로에서 무슨 일이 일어나는지 설명

## 상속·참조
- Fig 9.24(b): $V_{CC}$에서 전류원 $I_{REF}$가 노드 $V_1$로 흘러 들어가고, $Q_{REF}$는 다이오드 연결 (컬렉터 = 베이스 = $V_1$, 이미터 = 접지)
- 식 (9.88): $V_1 = V_T \ln \dfrac{I_{REF}}{I_{S,REF}}$
- 8장 로그 증폭기 (이 PDF에는 없음): 반전 연산증폭기의 귀환 경로에 BJT를 넣어, 출력 전압이 입력 전압의 로그에 비례하게 만든 회로

## 회로 — Fig 9.62
```spice
R1  VREF  n1  {R_1}
X1  0     n1  V1  opamp     ; in+ = 접지, in- = n1
Q1  n1    0   V1  npn       ; 컬렉터 = n1(귀환 선), 베이스 = 접지, 이미터 = V1
Q2  out   V1  n2  npn
VB  0     n2                ; 배터리: + 단자 = 접지, − 단자 = Q2 이미터
```
- 단자: VREF = 입력 전압 단자(값 미지정) / out = Q2 컬렉터의 개방 단자 / 배터리 전압 값 미지정
- 표시: 노드 V1 라벨(연산증폭기 출력) / I_X = out으로 들어가는 아래 화살표 / 배터리 옆 "−"(위, Q2 쪽), "+"(아래, 접지 쪽) / 연산증폭기 입력 "−"(위), "+"(아래)
- 배치: 왼쪽→오른쪽 VREF, R1, 연산증폭기, V1, Q2 / 연산증폭기 + 입력은 아래로 접지 / Q1은 연산증폭기 위에 있고, n1에서 위로 올라간 선이 오른쪽으로 가서 Q1 컬렉터로 내려옴, Q1 이미터는 아래로 V1 / Q1 베이스 왼쪽에 접지 기호 / Q2 이미터 아래 배터리, 그 아래 접지

![Fig 9.62](../figures/fig9-62.png)
````

- [ ] **Step 2: P9.59.md 작성**

````markdown
---
id: P9.59
kind: 장말문제
number: "9.59"
section: "설계 문제 (Design Problems)"
book_page: 493
pdf_page: 28
difficulty: 0
sol: false
source_lang: en
figures:
  - {id: "9.78", role: problem, panels: []}
depends_on: []
refs: ["Design Problems 공통 가정"]
---
# 장말문제 9.59 — CMOS 캐스코드 증폭기 설계

## 조건
- 설계 대상: Fig 9.78의 CMOS 캐스코드 증폭기
- 목표 전압 이득 200, 전력 예산 2 mW, $V_{DD} = 1.8\ \text{V}$
- $(W/L)_1 = (W/L)_2 = (W/L)_3 = (W/L)_4 = 20/0.18$
- $\lambda_p = 2\lambda_n = 0.2\ \text{V}^{-1}$ (즉 $\lambda_n = 0.1\ \text{V}^{-1}$)
- 단순화를 위해 $V_{b1} = V_{b2} = 0.9\ \text{V}$

## 구할 것
- 필요한 $V_{in}$의 DC 레벨
- 필요한 $V_{b3}$

## 상속·참조
- Design Problems 공통 가정 (문제에 따로 적힌 값이 우선):
  - $I_{S,n} = I_{S,p} = 6 \times 10^{-16}\ \text{A}$
  - $V_{A,n} = V_{A,p} = 5\ \text{V}$
  - $\beta_n = 100$, $\beta_p = 50$
  - $\mu_n C_{ox} = 100\ \mu\text{A/V}^2$, $\mu_p C_{ox} = 50\ \mu\text{A/V}^2$
  - $V_{TH,n} = 0.4\ \text{V}$, $V_{TH,p} = -0.5\ \text{V}$
  - 첨자 n은 npn/NMOS, p는 pnp/PMOS

## 회로 — Fig 9.78
```spice
M4  n3    Vb3  VDD  pmos  W/L=20/0.18
M3  Vout  Vb2  n3   pmos  W/L=20/0.18
M2  Vout  Vb1  n2   nmos  W/L=20/0.18
M1  n2    Vin  0    nmos  W/L=20/0.18
```
- 단자: VDD = 1.8 V 전원 레일 / Vb1, Vb2, Vb3 = 이상적 DC 바이어스 (점 단자) / Vin = 신호 입력 (개방 원 단자) / Vout = 출력 (개방 원 단자)
- 표시: 없음
- 배치: 위→아래 적층 VDD 레일, M4, M3, Vout 노드(오른쪽으로 인출), M2, M1, 접지 / 모든 게이트 단자는 왼쪽

![Fig 9.78](../figures/fig9-78.png)
````

- [ ] **Step 3: 검사기 실행**

Run: `python3 교과서/마이크로전자회로/_tools/check_md.py 교과서/마이크로전자회로/ch09`
Expected: `7개 파일, 오류 0개` (WARN은 E9.16의 1줄만)

- [ ] **Step 4: 원본 대조**

```bash
python3 -c "import fitz,sys; d=fitz.open('교과서/마이크로전자회로/9장.pdf'); d[int(sys.argv[1])-1].get_pixmap(dpi=216, clip=fitz.Rect(*map(float, sys.argv[2:6]))).save(sys.argv[6])" 25 250 280 520 470 "$SCRATCH/p938.png"
python3 -c "import fitz,sys; d=fitz.open('교과서/마이크로전자회로/9장.pdf'); d[int(sys.argv[1])-1].get_pixmap(dpi=216, clip=fitz.Rect(*map(float, sys.argv[2:6]))).save(sys.argv[6])" 28 0 30 250 170 "$SCRATCH/design_hdr.png"
python3 -c "import fitz,sys; d=fitz.open('교과서/마이크로전자회로/9장.pdf'); d[int(sys.argv[1])-1].get_pixmap(dpi=216, clip=fitz.Rect(*map(float, sys.argv[2:6]))).save(sys.argv[6])" 28 250 440 488 670 "$SCRATCH/p959.png"
```
Read로 열고 **원본 대조 체크리스트** 7항목을 확인한다. 특히:
- 9.62: Q1 베이스가 접지, 컬렉터가 귀환 선, 이미터가 V1인지 / 배터리 −·+ 방향
- 9.78: M4, M3가 PMOS(소스 쪽 화살표가 안쪽), M2, M1이 NMOS인지 / Vb1이 M2, Vb2가 M3에 붙는지
- 공통 가정의 지수 $6 \times 10^{-16}$과 $V_{TH,p} = -0.5$ V

틀린 곳이 있으면 md를 고치고 Step 3을 다시 실행한다.

- [ ] **Step 5: 커밋**

```bash
git add 교과서/마이크로전자회로/ch09/장말문제/P9.38.md 교과서/마이크로전자회로/ch09/장말문제/P9.59.md
git commit -m "docs: add ch09 samples P9.38 and P9.59

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: 블라인드 복원 테스트 + 검증 보고서

**Files:**
- Create: `docs/superpowers/reports/2026-09-24-ch09-sample-round-1.md`

**Interfaces:**
- Consumes: 샘플 md 7개 (Task 3–6), `FORMAT.md` (Task 2), 그림 PNG (Task 1)
- Produces: 사용자 피드백용 보고서

- [ ] **Step 1: 블라인드 복원 서브에이전트 실행**

Agent 도구로 `general-purpose` 서브에이전트 1개를 실행한다. 프롬프트 (그대로 사용):

```
당신은 전자회로 문제 복원 검증자다. 작업 디렉터리: /Users/hyunjun_macbook_pro/Documents/Univ/전자회로2

읽어도 되는 파일은 아래 8개뿐이다:
- 교과서/마이크로전자회로/FORMAT.md
- 교과서/마이크로전자회로/ch09/예제/E9.01.md
- 교과서/마이크로전자회로/ch09/연습문제/X9.01.md
- 교과서/마이크로전자회로/ch09/예제/E9.16.md
- 교과서/마이크로전자회로/ch09/장말문제/P9.04.md
- 교과서/마이크로전자회로/ch09/장말문제/P9.10.md
- 교과서/마이크로전자회로/ch09/장말문제/P9.38.md
- 교과서/마이크로전자회로/ch09/장말문제/P9.59.md

figures/ 폴더의 PNG, 9장.pdf, 그 밖의 파일은 절대 열지 마라 (Read, Bash 모두 금지).
md 속 이미지 링크도 따라가지 마라. 텍스트만으로 복원할 수 있는지 시험하는 것이다.

각 md 파일마다 아래 4개를 써라:
1. 복원한 문제: 이 md만 보고 교재 문제를 다시 쓴다면 어떤 문제인지 한 단락
2. 회로 스케치: 각 회로(패널)를 ASCII 회로도로 다시 그려라. 모든 소자, 연결, 노드 라벨, 화살표, 수치 라벨을 포함하고, 배치 bullet이 말하는 위치대로 그려라
3. 모호한 곳: 넷리스트나 bullet 중 두 가지 이상으로 읽히거나 정보가 모자란 부분. 해당 줄을 인용하고 이유를 한 줄로
4. FORMAT 위반: FORMAT.md 규칙과 어긋나는 부분

출력은 파일별로 "## <id>" 제목 아래 1–4를 적은 markdown 하나.
```

- [ ] **Step 2: 복원 결과를 원본과 대조**

서브에이전트의 ASCII 스케치를 파일별로 원본 이미지와 비교한다. 원본 이미지는 Task 3–6의 원본 대조 단계에서 `$SCRATCH`에 만든 PNG와 `ch09/figures/*.png`를 쓴다. 파일별로 기록할 것:
- 복원 일치 여부 (일치 / 부분 일치 / 불일치)
- 어긋난 점 (소자, 연결, 라벨, 배치)
- 원인: `md 오류`(md 내용이 틀림) 또는 `형식 모호`(md는 맞지만 형식이 여러 가지로 읽힘)

`md 오류`는 해당 md를 바로 고치고 검사기를 다시 실행한다:
Run: `python3 교과서/마이크로전자회로/_tools/check_md.py 교과서/마이크로전자회로/ch09`
Expected: `7개 파일, 오류 0개`

`형식 모호`는 고치지 말고 보고서의 "FORMAT 개선 제안"에 넣는다. 형식 변경은 사용자 확인 후에 한다.

- [ ] **Step 3: 보고서 작성**

`docs/superpowers/reports/2026-09-24-ch09-sample-round-1.md`를 아래 구조로 쓴다. 모든 칸은 Task 3–6의 원본 대조 결과와 Step 2 결과로 채운다:

```markdown
# 9장 샘플 라운드 1 — 검증 결과

## 요약
- 샘플 7개, 검사기 오류 0개
- 원본 대조에서 고친 곳: N곳 (파일별로 아래 표)
- 블라인드 복원: 일치 N / 부분 일치 N / 불일치 N

## 원본 대조
| 파일 | 고친 곳 (체크리스트 항목 번호: 내용) |
|---|---|
| E9.01 | … 또는 "없음" |

## 블라인드 복원 테스트
| 파일 | 결과 | 어긋난 점 | 원인 | 조치 |
|---|---|---|---|---|

## FORMAT 개선 제안
- (형식 모호로 분류된 항목마다: 문제 상황 → 제안하는 규칙 변경)

## 사용자 확인 필요
- 샘플 7개 파일 경로 목록
- 위 FORMAT 개선 제안 채택 여부
```

- [ ] **Step 4: 커밋**

```bash
git add docs/superpowers/reports/2026-09-24-ch09-sample-round-1.md docs/superpowers/specs/2026-09-24-textbook-problem-md-design.md docs/superpowers/plans/2026-09-24-textbook-problem-md.md
git add 교과서/마이크로전자회로/ch09/예제/ 교과서/마이크로전자회로/ch09/연습문제/ 교과서/마이크로전자회로/ch09/장말문제/
git commit -m "docs: add ch09 sample round 1 verification report

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 5: 사용자에게 보고하고 멈춤**

보고서 요약, 샘플 7개 경로, FORMAT 개선 제안을 사용자에게 전하고 **수정사항을 기다린다.** 나머지 103문제 변환은 사용자가 형식을 확정한 뒤 별도 계획으로 진행한다.
