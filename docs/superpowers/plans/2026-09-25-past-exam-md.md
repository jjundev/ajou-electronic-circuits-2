# 기출문제 → MD 추출 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `from_the_past/`의 기출 시험 4개(21문제)를 교과서 FORMAT.md 형식의 md로 옮긴다. 문제 1개당 md 1개이고, 그 결과를 검사하는 시험 전용 도구도 만든다.

**Architecture:** 교과서 `check_md.check_file`의 본문 검사를 `check_body()`로 떼어 낸다. 동작은 바꾸지 않는다. `from_the_past/md/_tools/`에 도구 네 개를 새로 둔다. `crop_exam.py`는 그림마다 PDF 경로를 받아 크롭하고, `check_exam.py`는 frontmatter를 검사한 뒤 `check_body`를 부른다. `make_exam_index.py`는 시험별 README를 만들고, `verify_exam.py`는 시험 단위 검사를 하면서 `verify_chapter.check_structure`를 재사용한다. 도구가 준비되면 시험 4개를 묶음 A–D로 나눠 opus 작성·리뷰 파이프라인으로 변환한다.

**Tech Stack:** Python 3 (Homebrew), PyMuPDF (`import fitz`), PyYAML, 표준 라이브러리 `unittest` (pytest는 설치돼 있지 않음). 서브에이전트는 Claude Code Agent 도구(opus).

**Spec:** `docs/superpowers/specs/2026-09-25-past-exam-md-design.md`

## Global Constraints

- `MAIN` = `/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2` (메인 checkout)
- `WT` = `/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2-exams` (작업 worktree, 브랜치 `feat/past-exam-md`)
- Task 0 이후 모든 명령은 `WT`에서 실행한다. from_the_past의 PDF는 git이 추적하므로 worktree에 그대로 있다. 심볼릭 링크는 만들지 않는다.
- **git add:** 추적하지 않는 파일(`STT/`, `강의노트/`, `교과서/**/*.pdf`)은 절대 add하지 않는다. `git add -A`, `git add .`는 쓰지 않고 항상 경로를 명시한다.
- **커밋 메시지:** 마지막 줄은 빈 줄 뒤 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`이다.
- **push, main 병합, worktree 삭제**는 사용자에게 묻고 나서 한다.
- **도구 코드 스타일:** 기존 `교과서/마이크로전자회로/_tools/*.py`를 따른다. 모듈 docstring에 사용법을 적고, `main(argv)`가 exit code를 돌려주며(0 성공, 1 오류, 2 사용법), 메시지는 한국어다.
- **교과서 결과물:** ch09–ch11의 md, 그림, README는 수정하지 않는다. 교과서 도구에서 바꾸는 것은 Task 1의 동작을 유지하는 추출뿐이다.
- **교과서 테스트:** `python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests`. 지금 76개가 통과하고, Task 1 뒤에는 79개가 통과해야 한다.
- **기출 테스트:** `python3 -m unittest discover -s from_the_past/md/_tools/tests`
- **형식 기준:** 본문 형식은 `교과서/마이크로전자회로/FORMAT.md`, 기출만의 차이는 `from_the_past/md/FORMAT-EXAM.md`(Task 6)를 따른다.
- **범위:** 답 절과 `role: answer` 그림은 두지 않는다(결정 #8). 설계과제, 학생 풀이, `23-1.pdf`(2021 기말 사본)는 변환하지 않는다(결정 #5, #9).
- **서브에이전트:** 작성·리뷰 에이전트는 모두 opus다. 렌더링 검증(md → PNG)은 하지 않는다.

## Review Focus

1. **공백과 한글이 든 PDF 경로:** figures.yaml의 `pdf: "../../../2023-1/23-1 기말/기말고사.pdf"`처럼 공백과 한글이 있는 경로도 크롭돼야 한다. → Task 2 `test_crops_from_each_entry_pdf`
2. **두 자리 문제 번호의 정렬:** Q10은 Q2 뒤에 와야 한다(문자열 정렬이면 Q10이 Q2 앞에 옴). 검사와 인덱스 모두 해당한다. → Task 3 `test_md_files_numeric_order`, Task 4 `test_rows_numeric_order`
3. **잘못 적은 그림 항목:** 따옴표 없는 id(`1:`)나 `pdf` 키가 빠진 항목이 있으면 traceback 없이 한국어 오류 한 줄을 내야 한다. → Task 2 `test_unquoted_id_rejected`, `test_missing_pdf_key`, Task 5 `test_recrop_missing_pdf_is_error`
4. **시험 폴더에 섞인 엉뚱한 md:** `Q2 copy.md`나 `notes.md`를 조용히 무시하면 안 된다. `README.md` 말고는 오류로 알려야 한다. → Task 5 `test_stray_md_is_error`
5. **답이 섞여 들어온 경우:** 결정 #8에 따라 `## 답` 절이나 `role: answer` 그림은 오류여야 한다. → Task 3 `test_answer_role_rejected`, Task 5 `test_answer_section_rejected`

---

## File Structure

| 경로 | 상태 | 책임 |
|---|---|---|
| `교과서/마이크로전자회로/_tools/check_md.py` | 수정 | 본문 검사를 `check_body()`로 추출 (동작 유지) |
| `교과서/마이크로전자회로/_tools/tests/test_check_md.py` | 수정 | `check_body` 테스트 3개 |
| `from_the_past/md/_tools/crop_exam.py` | 새로 만듦 | 그림마다 PDF를 지정해 크롭. `FIG_ID_RE`, `figure_filename`, `crop_all` |
| `from_the_past/md/_tools/check_exam.py` | 새로 만듦 | 파일 단위 검사. `ID_RE`, `FILE_RE`, `exam_title`, `md_files`, `check_file` |
| `from_the_past/md/_tools/make_exam_index.py` | 새로 만듦 | 시험 README 생성. `build_exam_index` |
| `from_the_past/md/_tools/verify_exam.py` | 새로 만듦 | 시험 단위 검사. `verify` |
| `from_the_past/md/_tools/tests/exam_fixtures.py` | 새로 만듦 | 테스트 공용 픽스처 (`make_pdf`, `VALID_Q1`, `VALID_Q2`, `make_exam`) |
| `from_the_past/md/_tools/tests/test_*.py` | 새로 만듦 | 도구별 unittest |
| `from_the_past/md/FORMAT-EXAM.md` | 새로 만듦 | 교과서 FORMAT.md와 다른 점 |
| `from_the_past/md/README.md` | 새로 만듦 | 시험 목록과 제외한 파일 (손으로 씀) |
| `from_the_past/md/<시험>/exam.yaml` ×4 | 새로 만듦 | 시험지 머리, 원본, 메모 |
| `from_the_past/md/<시험>/figures/figures.yaml` ×4 | 새로 만듦 | 그림 bbox |
| `from_the_past/md/<시험>/Q<n>.md`, `README.md`, `figures/*.png` | 파이프라인이 만듦 | 문제 md, 인덱스, 크롭 그림 |
| `docs/superpowers/reports/exams/review-{A..D}.md` | 파이프라인이 만듦 | 묶음별 리뷰 보고서 |

---

### Task 0: worktree와 설계 문서

- [ ] **Step 1: 메인 checkout의 상태를 확인한다**

```bash
cd "/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2"
git status --short | grep -v '^??'
git status --short
```
Expected: 첫 줄은 출력이 없다. 둘째 줄에는 이 계획과 spec 두 파일만 `??`로 나온다.

- [ ] **Step 2: worktree를 만들고 설계 문서를 옮긴다**

```bash
MAIN="/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2"
WT="/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2-exams"
git -C "$MAIN" worktree add "$WT" -b feat/past-exam-md main
mv "$MAIN/docs/superpowers/specs/2026-09-25-past-exam-md-design.md" "$WT/docs/superpowers/specs/"
mv "$MAIN/docs/superpowers/plans/2026-09-25-past-exam-md.md" "$WT/docs/superpowers/plans/"
ls "$WT/from_the_past/2023-1/23-1 기말/기말고사.pdf"
```
Expected: 마지막 `ls`가 파일을 보여 준다(PDF가 추적되고 있다는 확인).

- [ ] **Step 3: 커밋한다**

```bash
cd "/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2-exams"
git add docs/superpowers/specs/2026-09-25-past-exam-md-design.md docs/superpowers/plans/2026-09-25-past-exam-md.md
git commit -m "docs: add past-exam md design and plan

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 1: 교과서 `check_md`에서 본문 검사 추출

**Files:**
- Modify: `교과서/마이크로전자회로/_tools/check_md.py:90-130` (본문 검사 부분)
- Test: `교과서/마이크로전자회로/_tools/tests/test_check_md.py`

**Interfaces:**
- Produces: `check_md.check_body(body: str, path: Path, kind: str) -> list[str]`. 절(조건, 구할 것, 회로), `## 회로 — 없음` 규칙, 예제 답 절, spice 블록 문법, 블록 뒤 bullet 3개, 이미지 링크(`path.parent` 기준)를 검사하고 오류 목록을 돌려준다. `kind == "예제"`일 때만 `## 답 (검증용)`을 요구한다.

- [ ] **Step 1: 실패하는 테스트를 쓴다**

`tests/test_check_md.py`의 import 줄을 바꾼다.
```python
from check_md import check_body, check_file, check_netlist_line, main  # noqa: E402
```
파일 끝(`if __name__` 블록이 있으면 그 앞)에 추가한다.
````python
BODY_NO_ANSWER = """# 기출 2021-1 중간 2 — 테스트

## 조건
- I_D = 1 mA

## 구할 것
- (1) R_out

## 회로 — 그림
```spice
M1  out  Vin  0  nmos
```
- 단자: Vin = 입력 (개방 원)
- 표시: 노드 라벨 Vin
- 배치: M1 하나
"""


class CheckBodyTest(unittest.TestCase):
    def test_exam_kind_needs_no_answer(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(check_body(BODY_NO_ANSWER, Path(t) / "Q2.md", "기출"), [])

    def test_example_kind_needs_answer(self):
        with tempfile.TemporaryDirectory() as t:
            errors = check_body(BODY_NO_ANSWER, Path(t) / "E9.01.md", "예제")
        self.assertIn("예제에 절 누락: ## 답 (검증용)", errors)

    def test_missing_bullet_reported(self):
        body = BODY_NO_ANSWER.replace("- 배치: M1 하나\n", "")
        with tempfile.TemporaryDirectory() as t:
            errors = check_body(body, Path(t) / "Q2.md", "기출")
        self.assertTrue(any("'- 배치:' bullet 없음" in e for e in errors), errors)
````

- [ ] **Step 2: 테스트가 실패하는지 확인한다**

Run: `python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests 2>&1 | tail -5`
Expected: `ImportError: cannot import name 'check_body'`

- [ ] **Step 3: `check_body`를 추출한다**

`check_md.py`에서 `check_file` 안의 `headings = [...]` 줄부터 `for link in IMAGE_RE.findall(body): …` 루프 끝까지를 잘라 내고, 그 자리에 다음 한 줄을 둔다.
```python
    errors += check_body(body, path, kind)
```
잘라 낸 코드는 `check_file` 바로 위에 새 함수로 둔다(내용은 그대로, 들여쓰기만 함수 본문으로).
```python
def check_body(body, path, kind):
    """본문 절, 넷리스트, bullet, 이미지 링크를 검사한다. 기출 검사기(from_the_past/md/_tools)도 이 함수를 쓴다."""
    errors = []
    headings = [l.strip() for l in body.splitlines() if l.startswith("## ")]
    for h in ("## 조건", "## 구할 것"):
        if h not in headings:
            errors.append(f"절 누락: {h}")
    circuit_headings = [h for h in headings if h.startswith("## 회로")]
    if not circuit_headings:
        errors.append("절 누락: ## 회로 …")
    for h in circuit_headings:
        if h.startswith(NO_CIRCUIT_PREFIX) and not NO_CIRCUIT_RE.match(h):
            errors.append(f"{h!r}: 그림 없음 제목은 이유를 괄호로 적음 (예: '## 회로 — 없음 (설계 문제)')")
    no_circuit = bool(circuit_headings) and all(h.startswith(NO_CIRCUIT_PREFIX) for h in circuit_headings)
    for sec in re.finditer(r"^## 회로 — 없음.*?(?=^## |\Z)", body, re.DOTALL | re.MULTILINE):
        if "```spice" in sec.group(0):
            errors.append("'## 회로 — 없음' 절 아래에 ```spice 블록이 있음 (넷리스트는 적지 않음)")
    if kind == "예제" and "## 답 (검증용)" not in headings:
        errors.append("예제에 절 누락: ## 답 (검증용)")

    blocks = list(SPICE_BLOCK_RE.finditer(body))
    if not blocks and not no_circuit:
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
    return errors
```
`check_file`에서 `errors += check_body(...)` 다음 줄은 원래대로 `figures = meta["figures"] or []`로 이어진다.

- [ ] **Step 4: 테스트와 교과서 결과물 검사를 돌린다**

```bash
python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests 2>&1 | tail -3
for c in 교과서/마이크로전자회로/ch*/; do python3 교과서/마이크로전자회로/_tools/check_md.py "$c" | tail -1; done
```
Expected: `Ran 79 tests` / `OK`. 장마다 `N개 파일, 오류 0개`가 나온다(ch09–ch11의 파일 수는 바뀌지 않는다).

- [ ] **Step 5: 커밋한다**

```bash
git add 교과서/마이크로전자회로/_tools/check_md.py 교과서/마이크로전자회로/_tools/tests/test_check_md.py
git commit -m "refactor: extract check_body from check_md for reuse

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: `crop_exam.py` — 그림마다 PDF를 지정하는 크롭

**Files:**
- Create: `from_the_past/md/_tools/crop_exam.py`
- Create: `from_the_past/md/_tools/tests/exam_fixtures.py`
- Test: `from_the_past/md/_tools/tests/test_crop_exam.py`

**Interfaces:**
- Produces:
  - `FIG_ID_RE = re.compile(r"^Q[1-9]\d*(-[2-9]|-[1-9]\d+)?$")` — `"Q2"`, `"Q2-2"`
  - `figure_filename(fig_id: str) -> str` — `"Q2"` → `"fig-Q2.png"`
  - `crop_all(exam_dir: Path) -> list[Path]` — `exam_dir/figures/figures.yaml`을 읽어 그림마다 `pdf`(figures 폴더 기준 상대 경로 또는 절대 경로), `pdf_page`(1부터), `bbox`로 잘라 `figures/fig-<id>.png`로 저장한다. 잘못된 항목은 `ValueError`(한국어 메시지)를 낸다.
  - `tests/exam_fixtures.make_pdf(path: Path, pages: int = 1) -> None` — 200×100 pt 빈 PDF

- [ ] **Step 1: 픽스처와 실패하는 테스트를 쓴다**

`from_the_past/md/_tools/tests/exam_fixtures.py`:
```python
"""기출 도구 테스트 공용 픽스처."""
from pathlib import Path

import fitz


def make_pdf(path: Path, pages: int = 1) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()
    for _ in range(pages):
        doc.new_page(width=200, height=100)
    doc.save(str(path))
```

`from_the_past/md/_tools/tests/test_crop_exam.py`:
```python
import sys
import tempfile
import unittest
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from crop_exam import crop_all, figure_filename  # noqa: E402
from exam_fixtures import make_pdf  # noqa: E402


def make_exam(root: Path, figures_yaml: str) -> Path:
    fig_dir = root / "md" / "2021-1_중간" / "figures"
    fig_dir.mkdir(parents=True)
    (fig_dir / "figures.yaml").write_text(figures_yaml, encoding="utf-8")
    return fig_dir.parent


class FigureFilenameTest(unittest.TestCase):
    def test_single(self):
        self.assertEqual(figure_filename("Q2"), "fig-Q2.png")

    def test_second_figure(self):
        self.assertEqual(figure_filename("Q2-2"), "fig-Q2-2.png")


class CropAllTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        make_pdf(self.root / "src" / "a.pdf")
        make_pdf(self.root / "23-1 기말" / "기말고사.pdf", pages=2)

    def tearDown(self):
        self.tmp.cleanup()

    def test_crops_from_each_entry_pdf(self):
        exam = make_exam(self.root, """dpi: 72
figures:
  "Q1": {pdf: ../../../src/a.pdf, pdf_page: 1, bbox: [0, 0, 100, 50]}
  "Q2": {pdf: "../../../23-1 기말/기말고사.pdf", pdf_page: 2, bbox: [0, 0, 50, 50]}
""")
        out = crop_all(exam)
        self.assertEqual([p.name for p in out], ["fig-Q1.png", "fig-Q2.png"])
        a, b = fitz.Pixmap(str(out[0])), fitz.Pixmap(str(out[1]))
        self.assertEqual((a.width, a.height), (100, 50))
        self.assertEqual((b.width, b.height), (50, 50))

    def test_empty_figures_is_noop(self):
        exam = make_exam(self.root, "dpi: 72\nfigures:\n")
        self.assertEqual(crop_all(exam), [])

    def test_unquoted_id_rejected(self):
        exam = make_exam(self.root, "figures:\n  1: {pdf: ../../../src/a.pdf, pdf_page: 1, bbox: [0, 0, 10, 10]}\n")
        with self.assertRaisesRegex(ValueError, "형식"):
            crop_all(exam)

    def test_missing_pdf_key(self):
        exam = make_exam(self.root, 'figures:\n  "Q1": {pdf_page: 1, bbox: [0, 0, 10, 10]}\n')
        with self.assertRaisesRegex(ValueError, "pdf 경로가 없음"):
            crop_all(exam)

    def test_missing_pdf_file(self):
        exam = make_exam(self.root, 'figures:\n  "Q1": {pdf: ../../../src/none.pdf, pdf_page: 1, bbox: [0, 0, 10, 10]}\n')
        with self.assertRaisesRegex(ValueError, "PDF 없음"):
            crop_all(exam)

    def test_page_out_of_range(self):
        exam = make_exam(self.root, 'figures:\n  "Q1": {pdf: ../../../src/a.pdf, pdf_page: 3, bbox: [0, 0, 10, 10]}\n')
        with self.assertRaisesRegex(ValueError, "범위 밖"):
            crop_all(exam)

    def test_bbox_outside_page(self):
        exam = make_exam(self.root, 'figures:\n  "Q1": {pdf: ../../../src/a.pdf, pdf_page: 1, bbox: [0, 0, 300, 50]}\n')
        with self.assertRaisesRegex(ValueError, "bbox"):
            crop_all(exam)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 테스트가 실패하는지 확인한다**

Run: `python3 -m unittest discover -s from_the_past/md/_tools/tests 2>&1 | tail -3`
Expected: `ModuleNotFoundError: No module named 'crop_exam'`

- [ ] **Step 3: `crop_exam.py`를 쓴다**

```python
#!/usr/bin/env python3
"""시험 폴더의 figures/figures.yaml에 적힌 bbox로 기출 PDF에서 그림을 잘라 PNG로 저장한다.

교과서 crop_figures.py와 달리 한 시험이 여러 PDF에 나뉘어 있어서 그림마다 pdf 경로를 적는다
(figures 폴더 기준 상대 경로).

사용법: python3 crop_exam.py <시험 폴더>    예) python3 crop_exam.py ../2021-1_중간
"""
import re
import sys
from pathlib import Path

import fitz
import yaml

FIG_ID_RE = re.compile(r"^Q[1-9]\d*(-[2-9]|-[1-9]\d+)?$")


def figure_filename(fig_id: str) -> str:
    return f"fig-{fig_id}.png"


def crop_all(exam_dir: Path) -> list[Path]:
    fig_dir = exam_dir / "figures"
    spec = yaml.safe_load((fig_dir / "figures.yaml").read_text(encoding="utf-8")) or {}
    dpi = spec.get("dpi", 144)
    written = []
    for fig_id, fig in (spec.get("figures") or {}).items():
        if not isinstance(fig_id, str) or not FIG_ID_RE.match(fig_id):
            raise ValueError(f'그림 id {fig_id!r} 형식 오류: 따옴표로 감싼 "Q<번호>" 또는 "Q<번호>-<n>" (예: "Q2")')
        if not isinstance(fig, dict) or "pdf" not in fig:
            raise ValueError(f"{fig_id}: pdf 경로가 없음 (figures 폴더 기준 상대 경로로 적음)")
        pdf_path = (fig_dir / fig["pdf"]).resolve()
        if not pdf_path.is_file():
            raise ValueError(f"{fig_id}: PDF 없음 ({fig['pdf']})")
        with fitz.open(pdf_path) as doc:
            pdf_page = fig.get("pdf_page")
            if not isinstance(pdf_page, int) or not 1 <= pdf_page <= len(doc):
                raise ValueError(f"{fig_id}: pdf_page {pdf_page!r} 가 1..{len(doc)} 범위 밖")
            page = doc[pdf_page - 1]
            rect = fitz.Rect(*fig["bbox"])
            if not page.rect.contains(rect):
                raise ValueError(f"{fig_id}: bbox {fig['bbox']} 가 {pdf_page}쪽 범위 {tuple(page.rect)} 밖")
            out = fig_dir / figure_filename(fig_id)
            page.get_pixmap(dpi=dpi, clip=rect).save(out)
        written.append(out)
    return written


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("사용법: python3 crop_exam.py <시험 폴더>", file=sys.stderr)
        return 2
    try:
        paths = crop_all(Path(argv[1]))
    except (OSError, ValueError, yaml.YAMLError) as e:
        print(f"ERROR {e}", file=sys.stderr)
        return 1
    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

- [ ] **Step 4: 테스트가 통과하는지 확인한다**

Run: `python3 -m unittest discover -s from_the_past/md/_tools/tests 2>&1 | tail -3`
Expected: `Ran 9 tests` / `OK`

- [ ] **Step 5: 커밋한다**

```bash
git add from_the_past/md/_tools/crop_exam.py from_the_past/md/_tools/tests/exam_fixtures.py from_the_past/md/_tools/tests/test_crop_exam.py
git commit -m "feat: add crop_exam for per-figure PDF cropping of past exams

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: `check_exam.py` — 파일 단위 형식 검사

**Files:**
- Create: `from_the_past/md/_tools/check_exam.py`
- Modify: `from_the_past/md/_tools/tests/exam_fixtures.py` (픽스처 추가)
- Test: `from_the_past/md/_tools/tests/test_check_exam.py`

**Interfaces:**
- Consumes: `check_md.check_body(body, path, kind)`, `check_md.split_frontmatter(text) -> (dict, str)` (Task 1). `crop_exam.FIG_ID_RE`, `crop_exam.figure_filename` (Task 2).
- Produces:
  - `TEXTBOOK_TOOLS: Path` — `<저장소>/교과서/마이크로전자회로/_tools`. import할 때 `sys.path`에 넣는다.
  - `KIND = "기출"`, `EXAM_DIR_RE`, `ID_RE = ^(<시험>)-Q(<n>)$` (group 1 = 시험 폴더 이름, group 2 = 번호 문자열), `FILE_RE = ^Q(<n>)\.md$`
  - `exam_title(dir_name: str) -> str` — `"2021-1_중간"` → `"2021-1 중간고사"`. 형식이 틀리면 `ValueError`
  - `md_files(exam_dir: Path) -> list[Path]` — `Q<n>.md`만 번호 순(숫자 기준)으로 돌려준다
  - `check_file(path: Path, exam_dir: Path) -> tuple[list[str], list[str]]` — (errors, warnings)
  - `split_frontmatter` 재노출(`from check_exam import split_frontmatter`)
  - 픽스처: `VALID_Q1`, `VALID_Q2` (str), `make_exam(root: Path, files: dict[str, str], with_png: bool = True) -> Path` — `root/src/a.pdf`(1쪽)와 `root/md/2021-1_중간/`을 만들고, `with_png`이면 `figures/fig-Q2.png`를 만든다

- [ ] **Step 1: 픽스처를 추가한다**

`tests/exam_fixtures.py` 끝에 추가한다.
````python
VALID_Q1 = """---
id: 2021-1_중간-Q1
kind: 기출
exam: "2021-1 중간고사"
number: "1"
points: 20
source: ../../src/a.pdf
pdf_page: 1
source_lang: ko
figures: []
textbook_chapters: [9]
depends_on: []
refs: []
---
# 기출 2021-1 중간 1 — 서술형

## 조건
- 주어진 값 없음

## 구할 것
- (1) 개념 설명

## 회로 — 없음 (서술형)
"""

VALID_Q2 = """---
id: 2021-1_중간-Q2
kind: 기출
exam: "2021-1 중간고사"
number: "2"
points: 20
source: ../../src/a.pdf
pdf_page: 1
source_lang: ko
figures:
  - {id: "Q2", role: problem, panels: [a]}
textbook_chapters: [9, 10]
depends_on: []
refs: []
---
# 기출 2021-1 중간 2 — 캐스코드 출력 저항

## 조건
- $I_D = 1$ mA

## 구할 것
- (1) 출력 저항

## 회로 — 그림 (a)
```spice
M1  out  Vin  0  nmos
```
- 단자: Vin = 입력 (개방 원)
- 표시: 노드 라벨 Vin
- 배치: M1 하나

![Q2](figures/fig-Q2.png)
"""


def make_exam(root: Path, files: dict, with_png: bool = True) -> Path:
    make_pdf(root / "src" / "a.pdf")
    exam = root / "md" / "2021-1_중간"
    (exam / "figures").mkdir(parents=True)
    if with_png:
        (exam / "figures" / "fig-Q2.png").write_bytes(b"\x89PNG")
    for name, text in files.items():
        (exam / name).write_text(text, encoding="utf-8")
    return exam
````

- [ ] **Step 2: 실패하는 테스트를 쓴다**

`tests/test_check_exam.py`:
```python
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_exam import check_file, exam_title, main, md_files  # noqa: E402
from exam_fixtures import VALID_Q1, VALID_Q2, make_exam  # noqa: E402


class ExamTitleTest(unittest.TestCase):
    def test_title(self):
        self.assertEqual(exam_title("2023-1_기말"), "2023-1 기말고사")

    def test_bad_name(self):
        with self.assertRaises(ValueError):
            exam_title("2023_기말")


class CheckFileTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def check(self, text, name="Q2.md"):
        exam = make_exam(self.root, {name: text})
        return check_file(exam / name, exam)

    def assertError(self, text, fragment, name="Q2.md"):
        errors, _ = self.check(text, name)
        self.assertTrue(any(fragment in e for e in errors), errors)

    def test_valid(self):
        self.assertEqual(self.check(VALID_Q2), ([], []))

    def test_valid_no_circuit(self):
        self.assertEqual(self.check(VALID_Q1, "Q1.md"), ([], []))

    def test_id_other_exam(self):
        self.assertError(VALID_Q2.replace("id: 2021-1_중간-Q2", "id: 2023-1_중간-Q2"), "폴더")

    def test_filename_mismatch(self):
        self.assertError(VALID_Q2, "파일명", name="Q3.md")

    def test_number_unquoted(self):
        self.assertError(VALID_Q2.replace('number: "2"', "number: 2"), "따옴표")

    def test_number_mismatch(self):
        self.assertError(VALID_Q2.replace('number: "2"', 'number: "3"'), "number")

    def test_kind(self):
        self.assertError(VALID_Q2.replace("kind: 기출", "kind: 예제"), "kind")

    def test_exam_title_mismatch(self):
        self.assertError(VALID_Q2.replace('exam: "2021-1 중간고사"', 'exam: "2021 중간"'), "exam")

    def test_points_not_int(self):
        self.assertError(VALID_Q2.replace("points: 20", 'points: "20점"'), "points")

    def test_source_missing(self):
        self.assertError(VALID_Q2.replace("../../src/a.pdf", "../../src/none.pdf"), "source PDF 없음")

    def test_pdf_page_out_of_range(self):
        self.assertError(VALID_Q2.replace("pdf_page: 1", "pdf_page: 2"), "범위 밖")

    def test_textbook_chapters_not_ints(self):
        self.assertError(VALID_Q2.replace("textbook_chapters: [9, 10]", 'textbook_chapters: ["9장"]'), "textbook_chapters")

    def test_answer_role_rejected(self):
        self.assertError(VALID_Q2.replace("role: problem", "role: answer"), "role")

    def test_figure_png_missing(self):
        exam = make_exam(self.root, {"Q2.md": VALID_Q2}, with_png=False)
        errors, _ = check_file(exam / "Q2.md", exam)
        self.assertIn("그림 파일 없음: figures/fig-Q2.png", errors)

    def test_depends_on_other_exam(self):
        self.assertError(VALID_Q2.replace("depends_on: []", "depends_on: [2023-1_중간-Q1]"), "다른 시험")

    def test_depends_on_missing_file_warns(self):
        errors, warnings = self.check(VALID_Q2.replace("depends_on: []", "depends_on: [2021-1_중간-Q1]"))
        self.assertEqual(errors, [])
        self.assertEqual(warnings, ["depends_on 2021-1_중간-Q1 파일이 아직 없음"])

    def test_body_checked(self):
        self.assertError(VALID_Q2.replace("- 배치: M1 하나\n", ""), "'- 배치:' bullet 없음")

    def test_missing_key(self):
        self.assertError(VALID_Q2.replace("points: 20\n", ""), "키 누락: points")


class MdFilesTest(unittest.TestCase):
    def test_md_files_numeric_order(self):
        with tempfile.TemporaryDirectory() as t:
            exam = make_exam(Path(t), {"Q10.md": "", "Q2.md": "", "README.md": "", "Q2 copy.md": ""})
            self.assertEqual([p.name for p in md_files(exam)], ["Q2.md", "Q10.md"])


class MainTest(unittest.TestCase):
    def run_main(self, exam):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(["check_exam.py", str(exam)])
        return code, out.getvalue()

    def test_ok(self):
        with tempfile.TemporaryDirectory() as t:
            exam = make_exam(Path(t), {"Q1.md": VALID_Q1, "Q2.md": VALID_Q2})
            code, out = self.run_main(exam)
        self.assertEqual(code, 0)
        self.assertIn("2개 파일, 오류 0개", out)

    def test_error(self):
        with tempfile.TemporaryDirectory() as t:
            exam = make_exam(Path(t), {"Q2.md": VALID_Q2.replace("kind: 기출", "kind: 예제")})
            code, out = self.run_main(exam)
        self.assertEqual(code, 1)

    def test_bad_folder_name(self):
        with tempfile.TemporaryDirectory() as t:
            bad = Path(t) / "midterm"
            bad.mkdir()
            code, _ = self.run_main(bad)
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: 테스트가 실패하는지 확인한다**

Run: `python3 -m unittest discover -s from_the_past/md/_tools/tests 2>&1 | tail -3`
Expected: `ModuleNotFoundError: No module named 'check_exam'`

- [ ] **Step 4: `check_exam.py`를 쓴다**

```python
#!/usr/bin/env python3
"""기출 문제 md 형식 검사기. 규칙은 ../FORMAT-EXAM.md (본문 절은 교과서 FORMAT.md).

사용법: python3 check_exam.py <시험 폴더>    예) python3 check_exam.py ../2021-1_중간
오류가 하나라도 있으면 종료 코드 1.
"""
import re
import sys
from pathlib import Path

import fitz
import yaml

TEXTBOOK_TOOLS = Path(__file__).resolve().parents[3] / "교과서" / "마이크로전자회로" / "_tools"
sys.path.insert(0, str(TEXTBOOK_TOOLS))
from check_md import check_body, split_frontmatter  # noqa: E402,F401  (split_frontmatter 재노출)
from crop_exam import FIG_ID_RE, figure_filename  # noqa: E402

KIND = "기출"
REQUIRED_KEYS = ["id", "kind", "exam", "number", "points", "source", "pdf_page", "source_lang",
                 "figures", "textbook_chapters", "depends_on", "refs"]
EXAM_DIR_RE = re.compile(r"^(\d{4})-([12])_(중간|기말)$")
ID_RE = re.compile(r"^(\d{4}-[12]_(?:중간|기말))-Q([1-9]\d*)$")
FILE_RE = re.compile(r"^Q([1-9]\d*)\.md$")
SOURCE_LANGS = {"ko", "en"}


def is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def exam_title(dir_name):
    m = EXAM_DIR_RE.match(dir_name)
    if not m:
        raise ValueError(f"시험 폴더 이름 형식 오류: {dir_name!r} (예: 2021-1_중간)")
    return f"{m.group(1)}-{m.group(2)} {m.group(3)}고사"


def md_files(exam_dir):
    return sorted((p for p in exam_dir.glob("Q*.md") if FILE_RE.match(p.name)),
                  key=lambda p: int(FILE_RE.match(p.name).group(1)))


def check_source(path, meta):
    source, pdf_page = meta["source"], meta["pdf_page"]
    if not isinstance(source, str) or not source.endswith(".pdf"):
        return [f"source {source!r} 는 md 기준 상대 경로의 .pdf"]
    pdf = (path.parent / source).resolve()
    if not pdf.is_file():
        return [f"source PDF 없음: {source}"]
    if not is_int(pdf_page):
        return [f"pdf_page {pdf_page!r} 는 정수"]
    with fitz.open(pdf) as doc:
        if not 1 <= pdf_page <= len(doc):
            return [f"pdf_page {pdf_page} 가 {Path(source).name} 의 1..{len(doc)} 범위 밖"]
    return []


def check_figures_meta(figures, exam_dir):
    figures = figures or []
    if not isinstance(figures, list):
        return [f"figures 는 목록이어야 함: {figures!r}"]
    errors = []
    for fig in figures:
        if not isinstance(fig, dict):
            errors.append(f"figures 항목은 {{id: ..., role: ...}} 형태여야 함: {fig!r}")
            continue
        fig_id = fig.get("id")
        if not isinstance(fig_id, str) or not FIG_ID_RE.match(fig_id):
            errors.append(f'그림 id {fig_id!r} 형식 오류 (따옴표로 감싼 "Q2" 또는 "Q2-2")')
            continue
        if fig.get("role") != "problem":
            errors.append(f"그림 {fig_id} role 은 problem (기출은 답 그림을 싣지 않음)")
        if not (exam_dir / "figures" / figure_filename(fig_id)).exists():
            errors.append(f"그림 파일 없음: figures/{figure_filename(fig_id)}")
    return errors


def check_file(path, exam_dir):
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
        return [f"id 형식 오류: {meta['id']!r} (예: 2021-1_중간-Q2)"], warnings
    exam, n = m.group(1), m.group(2)
    if exam != exam_dir.name:
        errors.append(f"id {meta['id']} 의 시험 {exam} 이 폴더 {exam_dir.name} 와 다름")
    if path.name != f"Q{n}.md":
        errors.append(f"파일명 {path.name} 이 id {meta['id']} 와 다름 (기대: Q{n}.md)")
    if not isinstance(meta["number"], str):
        errors.append(f'number {meta["number"]!r} 는 따옴표로 감싼 문자열이어야 함 (예: "{n}")')
    elif meta["number"] != n:
        errors.append(f"number {meta['number']!r} 가 id {meta['id']} 와 안 맞음 (기대: \"{n}\")")
    if meta["kind"] != KIND:
        errors.append(f"kind {meta['kind']!r} 는 {KIND} 이어야 함")
    try:
        title = exam_title(exam_dir.name)
        if meta["exam"] != title:
            errors.append(f"exam {meta['exam']!r} 가 폴더와 안 맞음 (기대: \"{title}\")")
    except ValueError as e:
        errors.append(str(e))
    if not is_int(meta["points"]) or meta["points"] <= 0:
        errors.append(f"points {meta['points']!r} 는 양의 정수 (원문 배점)")
    if meta["source_lang"] not in SOURCE_LANGS:
        errors.append(f"source_lang {meta['source_lang']!r} 는 ko 또는 en")
    errors += check_source(path, meta)
    chapters = meta["textbook_chapters"]
    if not isinstance(chapters, list) or not all(is_int(c) for c in chapters):
        errors.append(f"textbook_chapters {chapters!r} 는 정수 목록 (예: [9, 10])")
    errors += check_figures_meta(meta["figures"], exam_dir)

    for dep in meta["depends_on"] or []:
        dm = ID_RE.match(str(dep))
        if not dm:
            errors.append(f"depends_on id 형식 오류: {dep!r}")
        elif dm.group(1) != exam_dir.name:
            errors.append(f"depends_on {dep} 는 다른 시험 (같은 시험 id만 적고, 다른 시험은 refs에 적음)")
        elif not (exam_dir / f"Q{dm.group(2)}.md").exists():
            warnings.append(f"depends_on {dep} 파일이 아직 없음")

    errors += check_body(body, path, KIND)
    return errors, warnings


def main(argv):
    if len(argv) != 2:
        print("사용법: python3 check_exam.py <시험 폴더>", file=sys.stderr)
        return 2
    exam_dir = Path(argv[1]).resolve()   # "check_exam.py ." 로 불러도 폴더 이름이 나오게
    if not exam_dir.is_dir():
        print(f"시험 폴더가 없음: {exam_dir}", file=sys.stderr)
        return 2
    try:
        exam_title(exam_dir.name)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 2
    files = md_files(exam_dir)
    n_err = 0
    for path in files:
        try:
            errors, warnings = check_file(path, exam_dir)
        except Exception as e:  # 파일 하나가 깨져도 나머지는 계속 검사
            errors, warnings = [f"검사 중 예외 {e!r}"], []
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
`check_file`은 `exam_dir.name`을 쓰므로, 호출하는 쪽(`main`, `verify_exam.verify`)은 `.resolve()`한 경로를 넘긴다.

- [ ] **Step 5: 테스트가 통과하는지 확인한다**

Run: `python3 -m unittest discover -s from_the_past/md/_tools/tests 2>&1 | tail -3`
Expected: `Ran 33 tests` / `OK` (Task 2의 9개 + 24개)

- [ ] **Step 6: 커밋한다**

```bash
git add from_the_past/md/_tools/check_exam.py from_the_past/md/_tools/tests/exam_fixtures.py from_the_past/md/_tools/tests/test_check_exam.py
git commit -m "feat: add check_exam format checker for past-exam md

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: `make_exam_index.py` — 시험 README 생성

**Files:**
- Create: `from_the_past/md/_tools/make_exam_index.py`
- Test: `from_the_past/md/_tools/tests/test_make_exam_index.py`

**Interfaces:**
- Consumes: `check_exam.md_files`, `check_exam.split_frontmatter`, `check_exam.TEXTBOOK_TOOLS` (Task 3)
- Produces: `build_exam_index(exam_dir: Path) -> str`. 입력은 `exam_dir/exam.yaml`(키: `exam` str, `header` str, `sources` list[str], `aux_sources` list[str] 선택, `notes` list[str] 선택)과 `Q<n>.md`의 frontmatter와 제목이다. 첫 줄은 `# <exam> — 문제 인덱스`다. 교과서 장 링크는 `ch<NN>/README.md`가 있을 때만 `[9장](../../../교과서/마이크로전자회로/ch09/README.md)`이고, 없으면 `12장`이다.

- [ ] **Step 1: 실패하는 테스트를 쓴다**

`tests/test_make_exam_index.py`:
```python
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from exam_fixtures import VALID_Q1, VALID_Q2, make_exam  # noqa: E402
from make_exam_index import build_exam_index, main  # noqa: E402

EXAM_YAML = """exam: "2021-1 중간고사"
header: "Closed book, 풀이과정 필수"
sources:
  - ../../src/a.pdf
aux_sources:
  - ../../src/b.pdf
notes:
  - "스캔 답안지라 손글씨가 겹침"
"""

Q10 = VALID_Q2.replace("2021-1_중간-Q2", "2021-1_중간-Q10").replace('number: "2"', 'number: "10"') \
    .replace("textbook_chapters: [9, 10]", "textbook_chapters: [99]") \
    .replace("depends_on: []", "depends_on: [2021-1_중간-Q2]") \
    .replace("# 기출 2021-1 중간 2 — 캐스코드 출력 저항", "# 기출 2021-1 중간 10 — 열 번째 | 문제")


class BuildExamIndexTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.exam = make_exam(Path(self.tmp.name), {
            "Q1.md": VALID_Q1, "Q2.md": VALID_Q2, "Q10.md": Q10, "exam.yaml": EXAM_YAML})
        self.text = build_exam_index(self.exam)

    def tearDown(self):
        self.tmp.cleanup()

    def test_header(self):
        lines = self.text.splitlines()
        self.assertEqual(lines[0], "# 2021-1 중간고사 — 문제 인덱스")
        self.assertIn("- 시험지 머리: Closed book, 풀이과정 필수", lines)
        self.assertIn("- 원본: `a.pdf`", lines)
        self.assertIn("- 보조 원본: `b.pdf`", lines)
        self.assertIn("- 문제 3개, 배점 합계 60점", lines)
        self.assertIn("- 스캔 답안지라 손글씨가 겹침", lines)

    def test_rows_numeric_order(self):
        rows = [l for l in self.text.splitlines() if l.startswith("| [Q")]
        self.assertEqual([r.split("]")[0] for r in rows], ["| [Q1", "| [Q2", "| [Q10"])

    def test_row_content(self):
        row = next(l for l in self.text.splitlines() if l.startswith("| [Q2]"))
        self.assertEqual(
            row,
            "| [Q2](Q2.md) | 캐스코드 출력 저항 | 20 | a.pdf | 1 | Q2(a) | "
            "[9장](../../../교과서/마이크로전자회로/ch09/README.md), "
            "[10장](../../../교과서/마이크로전자회로/ch10/README.md) | — |")

    def test_unknown_chapter_plain_and_escape_and_deps(self):
        row = next(l for l in self.text.splitlines() if l.startswith("| [Q10]"))
        self.assertIn("열 번째 \\| 문제", row)
        self.assertIn("| 99장 |", row)
        self.assertTrue(row.endswith("| [Q2](Q2.md) |"), row)

    def test_no_circuit_figures_dash(self):
        row = next(l for l in self.text.splitlines() if l.startswith("| [Q1]"))
        self.assertIn("| — |", row)


class MainTest(unittest.TestCase):
    def test_writes_readme(self):
        with tempfile.TemporaryDirectory() as t:
            exam = make_exam(Path(t), {"Q1.md": VALID_Q1, "exam.yaml": EXAM_YAML})
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(["make_exam_index.py", str(exam)]), 0)
            self.assertEqual((exam / "README.md").read_text(encoding="utf-8"), build_exam_index(exam))

    def test_missing_exam_yaml(self):
        with tempfile.TemporaryDirectory() as t:
            exam = make_exam(Path(t), {"Q1.md": VALID_Q1})
            with redirect_stderr(io.StringIO()):
                self.assertEqual(main(["make_exam_index.py", str(exam)]), 2)


if __name__ == "__main__":
    unittest.main()
```
`test_row_content`는 저장소에 커밋된 `교과서/마이크로전자회로/ch09/README.md`, `ch10/README.md`가 있다는 사실에 기대고 있다(main에 있음).

- [ ] **Step 2: 테스트가 실패하는지 확인한다**

Run: `python3 -m unittest discover -s from_the_past/md/_tools/tests 2>&1 | tail -3`
Expected: `ModuleNotFoundError: No module named 'make_exam_index'`

- [ ] **Step 3: `make_exam_index.py`를 쓴다**

```python
#!/usr/bin/env python3
"""시험 폴더의 문제 md frontmatter와 exam.yaml로 README.md(문제 인덱스)를 만든다.

사용법: python3 make_exam_index.py <시험 폴더>    예) python3 make_exam_index.py ../2021-1_중간
"""
import re
import sys
from pathlib import Path

import yaml

from check_exam import TEXTBOOK_TOOLS, md_files, split_frontmatter

TITLE_RE = re.compile(r"^# .*? — (.+)$", re.M)
TEXTBOOK_DIR = TEXTBOOK_TOOLS.parent
TEXTBOOK_LINK = "../../../교과서/마이크로전자회로"   # from_the_past/md/<시험>/ 기준


def esc(s):
    return str(s).replace("|", "\\|")


def figure_tag(fig):
    panels = fig.get("panels") or []
    return fig["id"] + (f"({','.join(panels)})" if panels else "")


def chapter_link(n):
    name = f"ch{n:02d}"
    if (TEXTBOOK_DIR / name / "README.md").exists():
        return f"[{n}장]({TEXTBOOK_LINK}/{name}/README.md)"
    return f"{n}장"


def build_exam_index(exam_dir):
    exam_dir = Path(exam_dir)
    meta = yaml.safe_load((exam_dir / "exam.yaml").read_text(encoding="utf-8")) or {}
    rows, total = [], 0
    for path in md_files(exam_dir):
        fm, body = split_frontmatter(path.read_text(encoding="utf-8"))
        m = TITLE_RE.search(body)
        q = path.stem
        total += fm["points"]
        figs = ", ".join(figure_tag(f) for f in fm.get("figures") or []) or "—"
        chapters = ", ".join(chapter_link(n) for n in fm.get("textbook_chapters") or []) or "—"
        deps = ", ".join(f"[{d.rsplit('-', 1)[1]}]({d.rsplit('-', 1)[1]}.md)"
                         for d in fm.get("depends_on") or []) or "—"
        row = [f"[{q}]({q}.md)", esc(m.group(1).strip() if m else ""), fm["points"],
               Path(fm["source"]).name, fm["pdf_page"], figs, chapters, deps]
        rows.append("| " + " | ".join(str(c) for c in row) + " |")

    exam = meta["exam"]
    lines = [
        f"# {exam} — 문제 인덱스",
        "",
        f"{exam} 문제를 md로 옮긴 파일의 목록이다. 형식은 [FORMAT-EXAM.md](../FORMAT-EXAM.md)를 따른다.",
        "이 표는 각 파일의 frontmatter와 `exam.yaml`에서 `_tools/make_exam_index.py`로 만들었다. "
        "PDF 열은 원본 PDF의 페이지(1부터)다.",
        "",
        f"- 시험지 머리: {meta['header']}",
        "- 원본: " + ", ".join(f"`{Path(s).name}`" for s in meta["sources"]),
    ]
    if meta.get("aux_sources"):
        lines.append("- 보조 원본: " + ", ".join(f"`{Path(s).name}`" for s in meta["aux_sources"]))
    lines.append(f"- 문제 {len(rows)}개, 배점 합계 {total}점")
    lines += [f"- {n}" for n in meta.get("notes") or []]
    lines += ["", "| 문제 | 제목 | 배점 | 원본 | PDF | 그림 | 교과서 | 전제 |",
              "|---|---|---|---|---|---|---|---|"]
    lines += rows
    lines.append("")
    return "\n".join(lines)


def main(argv):
    if len(argv) != 2:
        print("사용법: python3 make_exam_index.py <시험 폴더>", file=sys.stderr)
        return 2
    exam_dir = Path(argv[1])
    if not (exam_dir / "exam.yaml").is_file():
        print(f"exam.yaml 없음: {exam_dir}", file=sys.stderr)
        return 2
    out = exam_dir / "README.md"
    out.write_text(build_exam_index(exam_dir), encoding="utf-8")
    print(f"{out} 작성")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

- [ ] **Step 4: 테스트가 통과하는지 확인한다**

Run: `python3 -m unittest discover -s from_the_past/md/_tools/tests 2>&1 | tail -3`
Expected: `Ran 40 tests` / `OK`

- [ ] **Step 5: 커밋한다**

```bash
git add from_the_past/md/_tools/make_exam_index.py from_the_past/md/_tools/tests/test_make_exam_index.py
git commit -m "feat: add make_exam_index for past-exam README

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: `verify_exam.py` — 시험 단위 검사

**Files:**
- Create: `from_the_past/md/_tools/verify_exam.py`
- Test: `from_the_past/md/_tools/tests/test_verify_exam.py`

**Interfaces:**
- Consumes: `check_exam.{FILE_RE, ID_RE, exam_title, md_files, split_frontmatter}`, `crop_exam.{FIG_ID_RE, crop_all, figure_filename}`, `make_exam_index.build_exam_index`, 교과서 `verify_chapter.check_structure(docs)` (docs = `{id: (path, fm, body)}`. id가 `E`로 시작하지 않으면 `## 답` 절을 오류로 본다)
- Produces: `verify(exam_dir: Path, recrop: bool = False) -> list[str]` (오류 목록). CLI는 `verify_exam.py <시험 폴더> [--recrop]`이고 exit 0/1/2다.

- [ ] **Step 1: 실패하는 테스트를 쓴다**

`tests/test_verify_exam.py`:
```python
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from crop_exam import crop_all  # noqa: E402
from exam_fixtures import VALID_Q1, VALID_Q2, make_exam  # noqa: E402
from make_exam_index import build_exam_index  # noqa: E402
from verify_exam import main, verify  # noqa: E402

FIGURES_YAML = """dpi: 72
figures:
  "Q2": {pdf: ../../../src/a.pdf, pdf_page: 1, bbox: [0, 0, 100, 50]}
"""
EXAM_YAML = """exam: "2021-1 중간고사"
header: "Closed book"
sources:
  - ../../src/a.pdf
"""


def make_full_exam(root: Path) -> Path:
    exam = make_exam(root, {"Q1.md": VALID_Q1, "Q2.md": VALID_Q2, "exam.yaml": EXAM_YAML}, with_png=False)
    (exam / "figures" / "figures.yaml").write_text(FIGURES_YAML, encoding="utf-8")
    crop_all(exam)
    (exam / "README.md").write_text(build_exam_index(exam), encoding="utf-8")
    return exam


class VerifyTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.exam = make_full_exam(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def assertHas(self, errors, fragment):
        self.assertTrue(any(fragment in e for e in errors), errors)

    def rebuild_readme(self):
        (self.exam / "README.md").write_text(build_exam_index(self.exam), encoding="utf-8")

    def test_valid_exam_passes(self):
        self.assertEqual(verify(self.exam, recrop=True), [])

    def test_empty_exam_is_error(self):
        empty = self.root / "md" / "2023-1_기말"
        empty.mkdir(parents=True)
        self.assertEqual(verify(empty), ["문제 md가 없음"])

    def test_missing_number(self):
        (self.exam / "Q1.md").unlink()
        self.rebuild_readme()
        self.assertHas(verify(self.exam), "번호가 빠짐: Q1")

    def test_stray_md_is_error(self):
        (self.exam / "Q2 copy.md").write_text(VALID_Q2, encoding="utf-8")
        self.assertHas(verify(self.exam), "알 수 없는 md 파일: Q2 copy.md")

    def test_unused_yaml_figure(self):
        (self.exam / "figures" / "figures.yaml").write_text(
            FIGURES_YAML + '  "Q3": {pdf: ../../../src/a.pdf, pdf_page: 1, bbox: [0, 0, 10, 10]}\n', encoding="utf-8")
        crop_all(self.exam)
        self.assertHas(verify(self.exam), "md가 쓰지 않는 그림: Q3")

    def test_extra_png(self):
        (self.exam / "figures" / "fig-Q9.png").write_bytes(b"\x89PNG")
        self.assertHas(verify(self.exam), "figures.yaml에 없는 PNG: fig-Q9.png")

    def test_image_link_missing(self):
        q2 = (self.exam / "Q2.md").read_text(encoding="utf-8").replace("![Q2](figures/fig-Q2.png)\n", "")
        (self.exam / "Q2.md").write_text(q2, encoding="utf-8")
        self.assertHas(verify(self.exam), "그림 Q2 이미지 링크 없음")

    def test_stale_readme(self):
        q1 = (self.exam / "Q1.md").read_text(encoding="utf-8").replace("— 서술형", "— 바뀐 제목")
        (self.exam / "Q1.md").write_text(q1, encoding="utf-8")
        self.assertHas(verify(self.exam), "README.md가 최신이 아님")

    def test_answer_section_rejected(self):
        with (self.exam / "Q1.md").open("a", encoding="utf-8") as f:
            f.write("\n## 답 (검증용)\n- 없음\n")
        self.assertHas(verify(self.exam), "'## 답' 절이 있음")

    def test_exam_yaml_mismatch(self):
        (self.exam / "exam.yaml").write_text(EXAM_YAML.replace("2021-1 중간고사", "2021-2 중간고사"), encoding="utf-8")
        self.assertHas(verify(self.exam), "exam.yaml")

    def test_exam_yaml_source_missing(self):
        (self.exam / "exam.yaml").write_text(EXAM_YAML.replace("a.pdf", "none.pdf"), encoding="utf-8")
        self.assertHas(verify(self.exam), "원본 없음: ../../src/none.pdf")

    def test_recrop_detects_changed_png(self):
        (self.exam / "figures" / "figures.yaml").write_text(FIGURES_YAML.replace("100, 50", "90, 50"), encoding="utf-8")
        self.assertHas(verify(self.exam, recrop=True), "다시 자른 결과와 다름")

    def test_recrop_missing_pdf_is_error(self):
        (self.root / "src" / "a.pdf").unlink()
        self.assertHas(verify(self.exam, recrop=True), "다시 자르기 실패")

    def test_broken_frontmatter_reported_not_raised(self):
        (self.exam / "Q1.md").write_text("frontmatter 없음\n", encoding="utf-8")
        self.assertHas(verify(self.exam), "Q1.md: frontmatter 읽기 실패")


class MainTest(unittest.TestCase):
    def test_ok_and_usage(self):
        with tempfile.TemporaryDirectory() as t:
            exam = make_full_exam(Path(t))
            with redirect_stdout(io.StringIO()) as out:
                self.assertEqual(main(["verify_exam.py", str(exam), "--recrop"]), 0)
            self.assertIn("오류 0개", out.getvalue())
            with redirect_stderr(io.StringIO()):
                self.assertEqual(main(["verify_exam.py"]), 2)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 테스트가 실패하는지 확인한다**

Run: `python3 -m unittest discover -s from_the_past/md/_tools/tests 2>&1 | tail -3`
Expected: `ModuleNotFoundError: No module named 'verify_exam'`

- [ ] **Step 3: `verify_exam.py`를 쓴다**

```python
#!/usr/bin/env python3
"""시험 폴더 전체의 정합성을 검사한다. check_exam.py가 파일 하나씩 보는 것을 시험 단위로 보완한다.

사용법: python3 verify_exam.py <시험 폴더> [--recrop]    예) python3 verify_exam.py ../2021-1_중간 --recrop
"""
import re
import sys
import tempfile
from pathlib import Path

import fitz
import yaml

from check_exam import FILE_RE, ID_RE, exam_title, md_files, split_frontmatter
from crop_exam import FIG_ID_RE, crop_all, figure_filename
from make_exam_index import build_exam_index
from verify_chapter import check_structure  # check_exam이 교과서 _tools를 sys.path에 넣음

IMG_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)\)")


def load_docs(exam_dir):
    docs, errors = {}, []
    for path in md_files(exam_dir):
        try:
            fm, body = split_frontmatter(path.read_text(encoding="utf-8"))
            docs[str(fm["id"])] = (path, fm, body)
        except Exception as e:  # 깨진 파일 하나가 나머지 검사를 막지 않게
            errors.append(f"{path.name}: frontmatter 읽기 실패 ({e})")
    return docs, errors


def check_stray_files(exam_dir):
    return [f"알 수 없는 md 파일: {p.name} (Q<번호>.md와 README.md만 둠)"
            for p in sorted(exam_dir.glob("*.md")) if p.name != "README.md" and not FILE_RE.match(p.name)]


def check_numbering(docs):
    nums = {int(m.group(2)) for i in docs if (m := ID_RE.match(i))}
    if not nums:
        return []
    missing = [f"Q{n}" for n in range(1, max(nums) + 1) if n not in nums]
    return [f"문제 번호가 빠짐: {', '.join(missing)}"] if missing else []


def check_figures(exam_dir, docs):
    fig_dir = exam_dir / "figures"
    yaml_path = fig_dir / "figures.yaml"
    if not yaml_path.exists():
        return ["figures/figures.yaml 없음"]
    try:
        spec = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        return [f"figures.yaml 읽기 실패 ({e})"]
    if not isinstance(spec, dict):
        return ["figures.yaml 최상위가 매핑(키: 값)이 아님"]
    figures = spec.get("figures") or {}
    if not isinstance(figures, dict):
        return ['figures.yaml의 figures가 매핑("Q2": {...})이 아님']
    errors, yaml_ids = [], set()
    for key, fig in figures.items():
        if not isinstance(key, str) or not FIG_ID_RE.match(key):
            errors.append(f'figures.yaml 그림 id {key!r} 형식 오류 (따옴표로 감싼 "Q2" 또는 "Q2-2")')
            continue
        yaml_ids.add(key)
        if not isinstance(fig, dict) or "pdf" not in fig:
            errors.append(f"figures.yaml {key}: pdf 경로가 없음")
    used = set()
    for i, (path, fm, body) in sorted(docs.items()):
        links = IMG_RE.findall(body)
        names = {Path(link).name for link in links}
        figs = fm.get("figures") or []
        if not isinstance(figs, list):
            errors.append(f"{i}: frontmatter figures가 목록이 아님")
            figs = []
        for fig in figs:
            fid = fig.get("id") if isinstance(fig, dict) else None
            if not isinstance(fid, str) or not FIG_ID_RE.match(fid):
                errors.append(f"{i}: figures 항목 {fig!r}에 올바른 id가 없음")
                continue
            used.add(fid)
            if figure_filename(fid) not in names:
                errors.append(f"{i}: 그림 {fid} 이미지 링크 없음")
        for link in links:
            if not (path.parent / link).exists():
                errors.append(f"{i}: 깨진 이미지 링크 {link}")
    if yaml_ids - used:
        errors.append(f"figures.yaml에만 있고 md가 쓰지 않는 그림: {', '.join(sorted(yaml_ids - used))}")
    if used - yaml_ids:
        errors.append(f"md가 쓰지만 figures.yaml에 없는 그림: {', '.join(sorted(used - yaml_ids))}")
    pngs = {p.name for p in fig_dir.glob("*.png")}
    expected = {figure_filename(i) for i in yaml_ids}
    if expected - pngs:
        errors.append(f"PNG 없음: {', '.join(sorted(expected - pngs))} (crop_exam.py 실행)")
    if pngs - expected:
        errors.append(f"figures.yaml에 없는 PNG: {', '.join(sorted(pngs - expected))}")
    return errors


def check_exam_yaml(exam_dir):
    path = exam_dir / "exam.yaml"
    if not path.exists():
        return ["exam.yaml 없음"]
    meta = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    errors = []
    title = exam_title(exam_dir.name)
    if meta.get("exam") != title:
        errors.append(f"exam.yaml exam {meta.get('exam')!r} 가 폴더와 안 맞음 (기대: \"{title}\")")
    if not isinstance(meta.get("header"), str) or not meta["header"]:
        errors.append("exam.yaml header(시험지 머리 문구) 없음")
    sources = meta.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append("exam.yaml sources 는 원본 PDF 경로 목록")
        sources = []
    for s in sources + list(meta.get("aux_sources") or []):
        if not (exam_dir / s).is_file():
            errors.append(f"exam.yaml 원본 없음: {s}")
    return errors


def check_readme(exam_dir):
    readme = exam_dir / "README.md"
    if not readme.exists():
        return ["README.md 없음 (make_exam_index.py 실행)"]
    try:
        fresh = build_exam_index(exam_dir)
    except Exception as e:  # 깨진 md나 exam.yaml — 그 원인은 다른 검사가 보고
        return [f"README.md 비교 실패 ({e})"]
    return [] if fresh == readme.read_text(encoding="utf-8") else ["README.md가 최신이 아님 (make_exam_index.py 다시 실행)"]


def check_recrop(exam_dir):
    fig_dir = exam_dir / "figures"
    errors = []
    try:
        spec = yaml.safe_load((fig_dir / "figures.yaml").read_text(encoding="utf-8")) or {}
        for fig in (spec.get("figures") or {}).values():
            fig["pdf"] = str((fig_dir / fig["pdf"]).resolve())
        with tempfile.TemporaryDirectory() as t:
            tmp_exam = Path(t) / exam_dir.name
            (tmp_exam / "figures").mkdir(parents=True)
            (tmp_exam / "figures" / "figures.yaml").write_text(
                yaml.safe_dump(spec, allow_unicode=True), encoding="utf-8")
            for out in crop_all(tmp_exam):
                current = fig_dir / out.name
                if not current.exists():
                    continue  # PNG 없음은 check_figures가 보고
                a, b = fitz.Pixmap(str(current)), fitz.Pixmap(str(out))
                if (a.width, a.height, a.samples) != (b.width, b.height, b.samples):
                    errors.append(f"{out.name}: figures.yaml로 다시 자른 결과와 다름 (crop_exam.py 다시 실행)")
    except Exception as e:  # PDF 없음, bbox 오류, pdf 키 누락
        errors.append(f"다시 자르기 실패 ({e})")
    return errors


def verify(exam_dir, recrop=False):
    exam_dir = Path(exam_dir).resolve()
    docs, errors = load_docs(exam_dir)
    if not docs and not errors:
        return ["문제 md가 없음"]
    checks = [("check_stray_files", lambda: check_stray_files(exam_dir)),
              ("check_numbering", lambda: check_numbering(docs)),
              ("check_figures", lambda: check_figures(exam_dir, docs)),
              ("check_structure", lambda: check_structure(docs)),
              ("check_exam_yaml", lambda: check_exam_yaml(exam_dir)),
              ("check_readme", lambda: check_readme(exam_dir))]
    if recrop:
        checks.append(("check_recrop", lambda: check_recrop(exam_dir)))
    for name, run in checks:
        try:  # 예상 못 한 입력 하나가 traceback으로 나머지 보고를 막지 않게
            errors += run()
        except Exception as e:
            errors.append(f"{name} 실패 ({e!r})")
    return errors


def main(argv):
    args = [a for a in argv[1:] if a != "--recrop"]
    if len(args) != 1:
        print("사용법: python3 verify_exam.py <시험 폴더> [--recrop]", file=sys.stderr)
        return 2
    exam_dir = Path(args[0])
    if not exam_dir.is_dir():
        print(f"시험 폴더가 없음: {exam_dir}", file=sys.stderr)
        return 2
    errors = verify(exam_dir, recrop="--recrop" in argv[1:])
    for e in errors:
        print(f"ERROR {e}")
    print(f"{exam_dir}: 오류 {len(errors)}개")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```
참고: `test_empty_exam_is_error`는 빈 폴더에 stray 검사 등이 돌기 전에 `["문제 md가 없음"]`만 돌려주는지 확인한다(위 코드가 그렇게 한다).

- [ ] **Step 4: 테스트가 통과하는지 확인한다**

Run: `python3 -m unittest discover -s from_the_past/md/_tools/tests 2>&1 | tail -3`
Expected: `Ran 55 tests` / `OK`

- [ ] **Step 5: 커밋한다**

```bash
git add from_the_past/md/_tools/verify_exam.py from_the_past/md/_tools/tests/test_verify_exam.py
git commit -m "feat: add verify_exam exam-level consistency checker

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: FORMAT-EXAM, exam.yaml, figures.yaml 머리, 최상위 README

**Files:**
- Create: `from_the_past/md/FORMAT-EXAM.md`, `from_the_past/md/README.md`
- Create: `from_the_past/md/{2021-1_중간,2021-1_기말,2023-1_중간,2023-1_기말}/exam.yaml`
- Create: `from_the_past/md/{…}/figures/figures.yaml`

- [ ] **Step 1: `FORMAT-EXAM.md`를 쓴다**

````markdown
# 기출문제 MD 형식

본문 형식(조건, 구할 것, 상속·참조, 회로 절, 넷리스트, bullet 3개, 수식, 원문에 없는 보충, 원문 오식)은
[교과서 FORMAT.md](../../교과서/마이크로전자회로/FORMAT.md)를 **그대로** 따른다. 이 문서는 기출만 다른 점을 적는다.

## 폴더와 파일 이름
```
from_the_past/md/
  FORMAT-EXAM.md, README.md
  _tools/crop_exam.py         # figures.yaml → 그림 PNG (그림마다 pdf 경로)
  _tools/check_exam.py        # 파일 단위 형식 검사
  _tools/make_exam_index.py   # frontmatter + exam.yaml → <시험>/README.md
  _tools/verify_exam.py       # 시험 단위 검사 (번호, 그림, 절 순서, exam.yaml, README, --recrop)
  <YYYY>-<학기>_<중간|기말>/
    exam.yaml                 # 시험지 머리 문구, 원본 PDF, 메모
    README.md                 # make_exam_index.py로 생성, 손으로 고치지 않음
    Q<n>.md                   # 문제 번호 그대로 (Q1, Q2, … Q10), 앞에 0을 채우지 않음
    figures/figures.yaml, figures/fig-Q<n>.png
```

## frontmatter
```yaml
id: 2021-1_중간-Q2        # <시험 폴더>-Q<n>
kind: 기출
exam: "2021-1 중간고사"   # 폴더에서 정해짐: <YYYY>-<학기> <중간|기말>고사
number: "2"               # 반드시 따옴표
points: 20                # 원문 배점 (정수)
source: ../../2021중간_기말/중간/Midterm0422_1p_rev.pdf   # md 기준 상대 경로. 문제 문장이 시작하는 PDF
pdf_page: 1               # 그 PDF의 페이지(1부터)
source_lang: ko
figures:                  # 크롭 그림. id 는 반드시 따옴표. role 은 problem 만
  - {id: "Q2", role: problem, panels: [a, b]}
textbook_chapters: [9, 10]   # 관련 교과서 장 (작성자 판단). 없으면 []
depends_on: []            # 같은 시험 안의 id만 (예: [2021-1_중간-Q2])
refs: []                  # 다른 시험·교과서 문제·식 (자유 문자열, 예: "교과서 P9.04", "2021-1_기말-Q3과 같은 회로")
```
- `textbook_chapters`는 문제가 다루는 내용이 교과서 몇 장인지를 적는다. 교과서 문제 md가 아직 없는 장(12장 이후)도 번호로 적는다.

## 본문 절 — 교과서와 다른 점
- 제목: `# 기출 2021-1 중간 2 — <짧은 제목>`
- `## 조건`: 모든 소문항에 공통인 값을 먼저 적고, 소문항 하나에만 붙은 값은 `- (1) 전용: …` bullet으로 적는다. 원문 줄바꿈 위치가 아니라 **어느 소문항에 인쇄돼 있는지**로 나눈다.
- `## 구할 것`: 원문 소문항 번호 (1)(2)…를 그대로 쓴다. 회로 패널 (a)(b)와 헷갈리지 않게 한다. 배점은 적지 않는다(frontmatter `points`).
- 서술형 문제(회로 없음): `## 회로 — 없음 (서술형)`. 소문항 중 일부만 회로를 쓰면 회로 절을 두고, 서술형 소문항은 구할 것에만 적는다.
- `## 답` 절은 두지 않는다(풀이는 이번 범위 밖).
- 시험지 머리 문구("Closed book, 풀이과정 필수 …")는 문제 md가 아니라 `exam.yaml`의 header에 적는다.

## 그림 (figures.yaml)
```yaml
dpi: 144
figures:
  "Q2": {pdf: ../../../2021중간_기말/중간/Midterm0422_1p_rev.pdf, pdf_page: 1, bbox: [x0, y0, x1, y1]}
```
- `pdf`는 **figures 폴더 기준** 상대 경로다(md의 `source`보다 `../`가 하나 많다). 공백이 있는 경로는 따옴표로 감싼다.
- 문제 하나에 그림 한 장이 원칙이다. 패널 (a)(b)가 한 영역에 있으면 bbox 하나로 자르고 `panels: [a, b]`를 둔다. 두 영역이 멀리 떨어져 한 bbox에 다른 문제의 글이 섞이면 `"Q2"`, `"Q2-2"`로 나눈다.
- 이미지 링크는 md와 같은 폴더 기준 `![Q2](figures/fig-Q2.png)`이다.

## 스캔 답안지 (2023)
- 인쇄된 문제 위에 손글씨가 겹친다. 문제는 **인쇄된 글자만** 옮긴다. 손글씨(풀이, 채점 표시, 동그라미)는 옮기지 않는다.
- 손글씨에 가려 읽을 수 없는 글자는 `[판독 불가]`로 적고, 짐작한 값은 별도 줄에 `… 로 보임 (원문에 없음)`으로 적는다.
- 크롭 그림에 손글씨가 들어가면 이미지 링크 아래에 `> 참고: 답안지 손글씨가 겹침 (…위치…)`를 적는다. 넷리스트와 bullet에는 손글씨로 그린 선·라벨을 넣지 않는다.
- 2023 기말은 가려진 곳에 한해 `23-1 기말고사 문제 및 답.pdf`(손정리 노트)를 보조로 쓴다. 그 줄 끝에 `(보조 출처: 손정리 노트)`를 붙인다.

## 텍스트 레이어 (2021)
2021 PDF는 텍스트를 추출할 수 있지만 그리스 문자(μ, λ, Ω, β)와 일부 기호가 빠진다. 판독은 렌더링한 이미지를 기준으로 하고, pdftotext는 보조로만 쓴다.

## 검사
```bash
python3 from_the_past/md/_tools/crop_exam.py from_the_past/md/2021-1_중간
python3 from_the_past/md/_tools/check_exam.py from_the_past/md/2021-1_중간
python3 from_the_past/md/_tools/make_exam_index.py from_the_past/md/2021-1_중간
python3 from_the_past/md/_tools/verify_exam.py from_the_past/md/2021-1_중간 --recrop
python3 -m unittest discover -s from_the_past/md/_tools/tests
```
````

- [ ] **Step 2: `exam.yaml` 네 개를 쓴다**

header 문구는 원본 첫 쪽 머리를 옮긴 값이다. 작성 에이전트가 묶음을 시작할 때 원본과 대조해 고친다(writer 프롬프트 2단계 1).

`from_the_past/md/2021-1_중간/exam.yaml`:
```yaml
exam: "2021-1 중간고사"
header: "Closed book, 풀이과정 필수 (풀이과정이 없으면 점수 미부여), 계산결과 필수 (근사계산 가능)"
sources:
  - ../../2021중간_기말/중간/Midterm0422_1p_rev.pdf
  - ../../2021중간_기말/중간/Midterm0422_2p_rev.pdf
  - ../../2021중간_기말/중간/Midterm0422_3p_rev.pdf
notes:
  - "원본은 1쪽짜리 PDF 3개다 (Q1–Q2, Q3–Q4, Q5)."
```
`from_the_past/md/2021-1_기말/exam.yaml`:
```yaml
exam: "2021-1 기말고사"
header: "Closed book, 풀이과정 필수 (풀이과정이 없으면 점수 미부여)"
sources:
  - ../../2021중간_기말/기말/Final0617_1p_rev.pdf
  - ../../2021중간_기말/기말/Final0617_2p_rev.pdf
  - ../../2021중간_기말/기말/Final0617_3p_rev.pdf
notes:
  - "원본은 1쪽짜리 PDF 3개다 (Q1–Q3, Q4–Q5, Q6–Q7)."
  - "`2023-1/23-1 기말/23-1.pdf`는 이 시험과 세 쪽 모두 같은 사본이라 쓰지 않았다."
```
`from_the_past/md/2023-1_중간/exam.yaml`:
```yaml
exam: "2023-1 중간고사"
header: "Closed book, 풀이과정 필수 (식과 풀이과정이 없으면 점수 미부여), 계산결과 필수 (근사계산 가능)"
sources:
  - ../../2023-1/중간고사.pdf
notes:
  - "원본은 채점된 답안지 스캔이다. 인쇄된 문제 위에 손글씨가 겹친다 (FORMAT-EXAM.md의 스캔 답안지 규칙)."
```
`from_the_past/md/2023-1_기말/exam.yaml`:
```yaml
exam: "2023-1 기말고사"
header: "Closed book, 풀이과정 필수 (식과 풀이과정이 없으면 점수 미부여), 부정행위 최저학점 부여"
sources:
  - "../../2023-1/23-1 기말/기말고사.pdf"
aux_sources:
  - "../../2023-1/23-1 기말/23-1 기말고사 문제 및 답.pdf"
notes:
  - "원본은 채점된 답안지 스캔이다. 인쇄된 문제 위에 손글씨가 겹친다 (FORMAT-EXAM.md의 스캔 답안지 규칙)."
  - "가려진 곳은 보조 원본(손정리 노트)으로 확인했다."
```

- [ ] **Step 3: `figures/figures.yaml` 머리 네 개를 쓴다**

네 시험 폴더에 모두 같은 내용으로 둔다.
```yaml
# 그림 id → 원본 PDF(이 figures 폴더 기준 상대 경로), 페이지(1부터), bbox [x0, y0, x1, y1] (PDF pt, 왼쪽 위 원점)
# id 는 반드시 따옴표로 감싼다 ("Q2", 한 문제에 영역이 둘이면 "Q2-2")
dpi: 144
figures:
```

- [ ] **Step 4: 최상위 `README.md`를 쓴다**

```markdown
# 전자회로2 기출문제 (md)

기출 시험지를 문제 1개당 md 1개로 옮겼다. 형식은 [FORMAT-EXAM.md](FORMAT-EXAM.md)
(본문은 [교과서 FORMAT.md](../../교과서/마이크로전자회로/FORMAT.md))를 따른다.

| 시험 | 인덱스 | 원본 |
|---|---|---|
| 2021-1 중간고사 | [2021-1_중간](2021-1_중간/README.md) | `2021중간_기말/중간/Midterm0422_{1,2,3}p_rev.pdf` |
| 2021-1 기말고사 | [2021-1_기말](2021-1_기말/README.md) | `2021중간_기말/기말/Final0617_{1,2,3}p_rev.pdf` |
| 2023-1 중간고사 | [2023-1_중간](2023-1_중간/README.md) | `2023-1/중간고사.pdf` (답안지 스캔) |
| 2023-1 기말고사 | [2023-1_기말](2023-1_기말/README.md) | `2023-1/23-1 기말/기말고사.pdf` (답안지 스캔) |

## 옮기지 않은 파일
- `2023-1/23-1 기말/23-1.pdf` — 2021-1 기말고사와 세 쪽 모두 같은 사본
- 설계과제: `2025-1_설계과제1_v2.pdf`, `설계+과제+1.pdf`, `설계2_리트라이.pdf`, `설계2_2트.hwp`, `*.xlsx`, `감점요인.png` — 시험 기출이 아님
- 학생 풀이: `2021중간_기말/기말/내풀이.pdf`, `2021중간_기말/중간/21솔루션 내가푼것.pdf`, `전회2 중간답안제출.pdf`, `201620690_김동영.pdf` — 풀이는 이번 범위 밖
- 풀이·답 절은 두지 않았다. 2023 답안지의 손글씨 풀이도 옮기지 않았다.
```

- [ ] **Step 5: 도구가 머리 파일을 받아들이는지 확인한다**

```bash
for e in 2021-1_중간 2021-1_기말 2023-1_중간 2023-1_기말; do
  python3 from_the_past/md/_tools/crop_exam.py from_the_past/md/$e; echo "crop $e exit $?"
  python3 -c "import sys; sys.path.insert(0,'from_the_past/md/_tools'); from verify_exam import check_exam_yaml; from pathlib import Path; print('$e', check_exam_yaml(Path('from_the_past/md/$e').resolve()))"
done
```
Expected: `crop … exit 0`(출력 없음)이 네 번, `check_exam_yaml` 결과가 네 번 모두 `[]`

- [ ] **Step 6: 커밋한다**

```bash
git add from_the_past/md/FORMAT-EXAM.md from_the_past/md/README.md \
  from_the_past/md/2021-1_중간/exam.yaml from_the_past/md/2021-1_기말/exam.yaml \
  from_the_past/md/2023-1_중간/exam.yaml from_the_past/md/2023-1_기말/exam.yaml \
  from_the_past/md/2021-1_중간/figures/figures.yaml from_the_past/md/2021-1_기말/figures/figures.yaml \
  from_the_past/md/2023-1_중간/figures/figures.yaml from_the_past/md/2023-1_기말/figures/figures.yaml
git commit -m "docs: add past-exam format notes, exam metadata, and figure specs

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: 에이전트 프롬프트 파일

세션 scratchpad 절대 경로를 `SCRATCH`라 한다. 아래 세 파일을 `SCRATCH/`에 쓴다(저장소에는 넣지 않는다). 형식은 교과서 스킬의 `.claude/skills/textbook-to-md/references/{common,writer,reviewer}.md`를 기출에 맞춘 것이다.

- [ ] **Step 1: `SCRATCH/EXAM-COMMON.md`를 쓴다** (`<<SCRATCH>>`는 실제 경로로 바꿔 쓴다)

````markdown
# 공통 지침 — 기출문제 → MD 변환

- 작업 루트: `/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2-exams` (경로는 모두 여기 기준이고, 셸 명령은 이 폴더에서 실행한다)
- 임시 파일은 `<<SCRATCH>>/` 아래에만 둔다. 저장소 안에 임시 파일을 만들지 않는다.

## 반드시 먼저 읽을 것
1. `교과서/마이크로전자회로/FORMAT.md` **전체**. 본문 형식과 판독 관례의 기준이다.
2. `from_the_past/md/FORMAT-EXAM.md` **전체**. 기출만 다른 점이다. FORMAT.md와 부딪히면 이쪽을 따른다.
3. 교과서 완성 파일 중 비슷한 것(`교과서/마이크로전자회로/` 기준):
   - 여러 패널 그림: `ch09/장말문제/P9.04.md`, `ch09/장말문제/P9.11.md`
   - 그림 없는 문제: `ch09/장말문제/P9.35.md`
   - 연산증폭기, 피드백 회로: `ch11/` 안에서 `opamp`로 검색한 파일
   - 원문 오식: `ch09/장말문제/P9.26.md`
4. 이번 시험 폴더의 `exam.yaml`, `figures/figures.yaml`

## 묶음과 원본
| 묶음 | 시험 폴더 | 대상 | 원본 PDF (저장소 루트 기준) | 문제 위치 |
|---|---|---|---|---|
| A | `from_the_past/md/2021-1_중간` | Q1–Q5 | `from_the_past/2021중간_기말/중간/Midterm0422_{1,2,3}p_rev.pdf` | 1p: Q1–Q2, 2p: Q3–Q4, 3p: Q5 |
| B | `from_the_past/md/2021-1_기말` | Q1–Q7 | `from_the_past/2021중간_기말/기말/Final0617_{1,2,3}p_rev.pdf` | 1p: Q1–Q3, 2p: Q4–Q5, 3p: Q6–Q7 |
| C | `from_the_past/md/2023-1_중간` | Q1–Q4 | `from_the_past/2023-1/중간고사.pdf` | p1–p4에 한 문제씩 |
| D | `from_the_past/md/2023-1_기말` | Q1–Q5 | `from_the_past/2023-1/23-1 기말/기말고사.pdf` (보조: `23-1 기말고사 문제 및 답.pdf`) | p1–p5에 한 문제씩 |

모든 PDF의 쪽 크기는 약 595×842 pt다. 2021 PDF는 그림이 JPEG로 삽입돼 있다. 2023 PDF는 답안지 스캔이다.

## 도구
```bash
# 원본 확대 (PAGE 1부터, 좌표 PDF pt, 왼쪽 위 원점). 216–300 dpi
python3 -c "import fitz,sys; d=fitz.open(sys.argv[1]); d[int(sys.argv[2])-1].get_pixmap(dpi=int(sys.argv[8]), clip=fitz.Rect(*map(float, sys.argv[3:7]))).save(sys.argv[7])" PDF PAGE X0 Y0 X1 Y1 <<SCRATCH>>/OUT.png DPI
# 보조: 텍스트 레이어 (2021만. 그리스 문자가 빠지니 이미지로 확인)
pdftotext -layout PDF -
# 그림 크롭, 형식 검사, 시험 단위 검사 (README는 마지막에 만들므로 작성 중에는 README 오류가 정상)
python3 from_the_past/md/_tools/crop_exam.py <시험 폴더>
python3 from_the_past/md/_tools/check_exam.py <시험 폴더>
python3 from_the_past/md/_tools/verify_exam.py <시험 폴더>
python3 -m unittest discover -s from_the_past/md/_tools/tests
```

## 핵심 규칙
- 문제 1개 = md 1개. md 텍스트만으로 원본 문제(조건, 구할 것, 회로도)를 복원할 수 있어야 한다.
- 한국어로 재구성하고, 원문을 그대로 옮기지 않는다. 수치, 단위, 지수, 소문항, 가정("$g_m r_o \gg 1$", "베이스 전류는 무시")을 하나도 빠뜨리지 않는다. 원문에 없는 보충은 줄 끝에 `(원문에 없음)`을 붙인다.
- 풀이, 답, 손글씨는 옮기지 않는다.
- `textbook_chapters`는 Razavi 마이크로전자회로(Fundamentals of Microelectronics)의 장 번호로 적는다. 9장 캐스코드·전류 거울, 10장 차동 증폭기, 11장 주파수 응답, 12장 피드백, 13장 출력단과 전력 증폭기, 14장 아날로그 필터. 9–11장은 `교과서/마이크로전자회로/ch09–ch11/README.md`의 절 목록과 대조한다. 한 문제가 여러 장에 걸치면 모두 적는다.
- YAML 그림 id는 반드시 따옴표로 감싼다 (`"Q2"`).

## 원본 대조 체크리스트
1. 소자 종류와 극성 (npn/pnp, nmos/pmos). 좌우 반전된 소자는 화살표 방향으로 확인한다
2. 모든 단자의 연결
3. 점으로 접속한 곳인지, 그냥 교차한 곳인지
4. 화살표 방향과 모양, 그리고 이름이 인쇄돼 있는지
5. 라벨, 첨자, W/L, 면적 배수
6. 수치, 단위, 지수 (μA/V², V⁻¹, kΩ)
7. 소문항 누락, 소문항별 조건이 붙은 위치
8. 배점(points), 시험지 머리(exam.yaml header), 손글씨를 인쇄 글자로 잘못 옮기지 않았는지

## git 규칙 (엄수)
- 현재 브랜치는 `feat/past-exam-md`다. 브랜치 전환, rebase, reset, merge, push는 하지 않는다.
- 추적하지 않는 파일(`STT/`, `강의노트/`, `교과서/**/*.pdf`)은 절대 add하지 않는다. `git add -A`, `git add .`는 쓰지 않고 항상 경로를 명시한다.
- 커밋 메시지는 빈 줄 뒤 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`로 끝낸다.
````

- [ ] **Step 2: `SCRATCH/exam-writer.md` 템플릿을 쓴다**

````markdown
# 작성 지시 — 기출 묶음 <<BATCH>>

당신은 기출문제 → md 변환의 작성 에이전트다. 먼저 `<<SCRATCH>>/EXAM-COMMON.md`를 읽고 그 지침을 그대로 따른다.

지금 다른 리뷰 에이전트가 다음 파일을 읽고 있으니 수정하지 않는다: <<BUSY_FILES>>

## 1단계: 리뷰 반영 (`<<PREV_REVIEW>>`가 "없음"이면 건너뛴다)
1. 리뷰 보고서 `<<PREV_REVIEW>>`를 읽는다 (묶음 <<PREV_BATCH>>: <<PREV_EXAM>>).
2. 지적마다 원본을 직접 확대해 확인하고, 사실인 것만 반영한다. 선택 제안은 원문에서 멀어지지 않을 때만 반영한다.
3. 그 시험 폴더의 `check_exam.py`가 오류 0, WARN 0인지 확인한다.
4. 보고서 파일과 고친 파일을 경로를 명시해 add하고 커밋한다.
   - 고친 파일이 있으면: `docs: apply review fixes to exam batch <<PREV_BATCH>> (<<PREV_EXAM>>)`
   - 고친 것 없이 보고서만 있으면: `docs: record review of exam batch <<PREV_BATCH>> (no fixes)`

## 2단계: 묶음 <<BATCH>> 작성 (대상이 "없음"이면 건너뛴다)
시험 폴더: `<<EXAM_DIR>>`, 대상: <<TARGETS>>, 원본: EXAM-COMMON.md의 묶음 표 <<BATCH>> 행

1. 원본 첫 쪽 머리를 확대해 읽고, `exam.yaml`의 header가 인쇄된 문구와 한 글자까지 같은지 확인한다. 다르면 고친다.
2. 쪽마다 저해상도로 훑어 문제 위치를 잡고, 216–300 dpi로 확대해 꼼꼼히 읽는다.
3. 그림을 등록하고 자른다.
   - 문제 그림을 `figures/figures.yaml`에 `pdf`(figures 폴더 기준 상대 경로), `pdf_page`, `bbox`로 추가한다.
   - `crop_exam.py`를 실행한다.
   - 새 PNG를 **Read로 열어** 라벨, 화살표, 패널 글자가 잘리지 않았는지, 문제 글이나 다른 그림이 들어오지 않았는지 확인한다. 잘렸으면 bbox를 고쳐 다시 자른다.
4. md를 번호 순으로 쓴다.
5. 결과가 `<<EXPECTED_TOTAL>>개 파일, 오류 0개`, WARN 0이 될 때까지 고친다. `verify_exam.py`는 README 오류 말고는 0이어야 한다. 도구 테스트 통과도 확인한다.
6. 새 md, `figures.yaml`, 새 PNG, (고쳤다면) `exam.yaml`을 경로를 명시해 add하고 커밋한다. 메시지: `docs: add <<EXAM_LABEL>> problems <<TARGETS>>`

## 보고 (최종 메시지)
- **1단계:** 반영한 것, 반영하지 않은 것과 그 이유, 커밋 해시
- **2단계:** 파일 목록(원본 PDF, 페이지, points, textbook_chapters), 그림 id와 bbox, add 커밋 해시, check_exam 결과 줄
- **판독이 애매했던 곳:** 그림, 위치, 무엇이 애매했고 어떻게 적었는지를 구체적으로 적는다. 손글씨에 가려진 곳은 모두 적는다. 리뷰어가 이 목록을 그대로 받아 집중 확인한다
- **FORMAT-EXAM으로 정하기 애매했던 결정**
````

- [ ] **Step 3: `SCRATCH/exam-reviewer.md` 템플릿을 쓴다**

````markdown
# 리뷰 지시 — 기출 묶음 <<BATCH>>

당신은 리뷰 에이전트다. 먼저 `<<SCRATCH>>/EXAM-COMMON.md`, FORMAT.md 전체, FORMAT-EXAM.md 전체를 읽는다.

- 대상: `<<EXAM_DIR>>` <<TARGETS>> (커밋 <<COMMIT>>)
- 작성자가 판독이 애매했다고 보고한 곳 (특히 독립적으로 확인할 것):
<<FLAGS>>
- 앞 묶음 리뷰 반영 커밋: <<PREV_FIX_COMMIT>>. "없음"이 아니면 `git show`로 반영 내용이 원본과 맞는지 빠르게 확인한다.

## 원칙
- **추적되는 파일을 수정하지 않고, git 상태도 바꾸지 않는다.** 만드는 파일은 보고서 `<<REPORT>>` 하나뿐이다(필요하면 폴더를 만든다). 커밋은 다음 작성 에이전트가 한다.
- 보고서는 먼저 `<<REPORT>>.part`에 쓰고, 리뷰를 모두 마친 마지막에 `mv <<REPORT>>.part <<REPORT>>`로 이름을 바꾼다.
- md를 먼저 믿지 않는다. 원본을 216–300 dpi로 **직접 확대해** 독립적으로 판독한 뒤 md와 대조한다.
- 크롭 PNG(`<<EXAM_DIR>>/figures/*.png`)를 Read로 열어 잘림과 침범을 확인한다.
- 파일마다 원본 대조 체크리스트 8항목을 모두 확인한다. 추가로 확인할 것:
  - 소문항별 조건이 맞는 소문항에 붙었는지 (`- (1) 전용:`)
  - frontmatter (source, pdf_page, points, textbook_chapters, figures의 panels)
  - `exam.yaml` header가 인쇄 문구와 같은지
  - 손글씨가 인쇄 글자로 섞여 들어오지 않았는지 (2023)
  - 원문에 없는 보충인데 `(원문에 없음)`이 빠진 곳
- `check_exam.py`를 한 번 돌린다.

## 보고서 (`<<REPORT>>`에 저장하고, 최종 메시지에 요약)
```
# 리뷰 <<BATCH>> — 커밋 <<COMMIT>> (<<EXAM_DIR>> <<TARGETS>>)

방법: <렌더링 dpi, 본 페이지, 크롭 확인 결과, 형식 검사 결과>

## 작성자가 애매하다고 한 곳 — 독립 판독 결과
- <항목>: 맞음 | 다름 (<원본 판독>)

### <id> — OK | 수정 필요
- [높음|중간|낮음] <체크 항목>: md는 "…" / 원본은 "…" (근거: <PDF> p.N, 위치) → 고칠 내용
```
사실 오류(원본과 다름)와 형식·표현 제안을 구분한다. 확신이 없는 지적은 "불확실"로 표시한다.
````

---

### Task 8: 변환 파이프라인 (묶음 A–D)

**자리표시자 값**

| 묶음 | `<<EXAM_DIR>>` | `<<TARGETS>>` | `<<EXAM_LABEL>>` | `<<EXPECTED_TOTAL>>` |
|---|---|---|---|---|
| A | `from_the_past/md/2021-1_중간` | Q1–Q5 | 2021-1 midterm | 5 |
| B | `from_the_past/md/2021-1_기말` | Q1–Q7 | 2021-1 final | 7 |
| C | `from_the_past/md/2023-1_중간` | Q1–Q4 | 2023-1 midterm | 4 |
| D | `from_the_past/md/2023-1_기말` | Q1–Q5 | 2023-1 final | 5 |

`<<REPORT>>` = `docs/superpowers/reports/exams/review-<묶음>.md`. `<<PREV_EXAM>>`는 앞 묶음의 시험 폴더 이름이다. `<<BUSY_FILES>>`에는 그때 리뷰 중인 시험 폴더의 `Q*.md`를 적는다.

에이전트는 모두 `model: opus`, 백그라운드로 띄운다. 프롬프트는 템플릿을 채운 파일을 `SCRATCH/`에 쓰고 "이 파일을 읽고 그대로 따르라"로 준다. **작성 에이전트(반영 포함)는 한 번에 하나만 돌린다.** 묶음마다 사용자에게 한 줄씩 알린다(작성 커밋, 리뷰의 사실 오류 수, 반영 커밋).

- [ ] **Step 1: 작성 A** — PREV_REVIEW "없음", BUSY_FILES "없음"
- [ ] **Step 2: 작성 A가 끝나면 리뷰 A와 작성 B를 동시에 띄운다** — 리뷰 A의 FLAGS는 작성 A의 "판독이 애매했던 곳", PREV_FIX_COMMIT "없음". 작성 B는 PREV_REVIEW "없음", BUSY_FILES = `2021-1_중간/Q*.md`
- [ ] **Step 3: 작성 B와 리뷰 A가 모두 끝나면 리뷰 B와 작성 C를 동시에 띄운다** — 작성 C의 1단계는 리뷰 A 반영(PREV_BATCH A, PREV_EXAM 2021-1_중간), BUSY_FILES = `2021-1_기말/Q*.md`
- [ ] **Step 4: 작성 C와 리뷰 B가 모두 끝나면 리뷰 C와 작성 D를 동시에 띄운다** — 리뷰 C의 PREV_FIX_COMMIT은 작성 C의 1단계 커밋. 작성 D의 1단계는 리뷰 B 반영, BUSY_FILES = `2023-1_중간/Q*.md`
- [ ] **Step 5: 작성 D와 리뷰 C가 모두 끝나면 리뷰 D와 반영 C를 동시에 띄운다** — 반영 C는 writer 템플릿에서 TARGETS "없음", PREV_BATCH C, BUSY_FILES = `2023-1_기말/Q*.md`로 채운다. 리뷰 D의 PREV_FIX_COMMIT은 작성 D의 1단계 커밋
- [ ] **Step 6: 리뷰 D와 반영 C가 끝나면 반영 D를 띄운다** — TARGETS "없음", PREV_BATCH D, BUSY_FILES "없음"
- [ ] **Step 7: 반영 기록을 확인한다**

```bash
ls docs/superpowers/reports/exams/
git log --oneline main.. --grep="apply review fixes\|record review"
```
Expected: `review-A.md`부터 `review-D.md`까지 네 개가 있고, 반영 또는 기록 커밋이 네 개 있다.

멈추고 묻는 경우: FORMAT-EXAM이 다루지 않는 그림 유형(예: 표나 그래프만 있는 문제)이 나오면 표기 방법을 제안하고, 확인을 받은 뒤 FORMAT-EXAM.md에 먼저 추가해 커밋한다.

---

### Task 9: 인덱스, 전체 검증, 보고

- [ ] **Step 1: 시험별 README를 만들고 커밋한다**

```bash
for e in 2021-1_중간 2021-1_기말 2023-1_중간 2023-1_기말; do
  python3 from_the_past/md/_tools/make_exam_index.py from_the_past/md/$e
done
git add from_the_past/md/2021-1_중간/README.md from_the_past/md/2021-1_기말/README.md \
  from_the_past/md/2023-1_중간/README.md from_the_past/md/2023-1_기말/README.md
git commit -m "docs: add past-exam problem index READMEs

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 2: 전체를 검증한다**

```bash
for e in 2021-1_중간 2021-1_기말 2023-1_중간 2023-1_기말; do
  python3 from_the_past/md/_tools/check_exam.py from_the_past/md/$e | tail -1
  python3 from_the_past/md/_tools/check_exam.py from_the_past/md/$e | grep -c WARN
  python3 from_the_past/md/_tools/verify_exam.py from_the_past/md/$e --recrop | tail -1
done
python3 -m unittest discover -s from_the_past/md/_tools/tests 2>&1 | tail -2
python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests 2>&1 | tail -2
for c in 교과서/마이크로전자회로/ch*/; do python3 교과서/마이크로전자회로/_tools/check_md.py "$c" | tail -1; done
git status --short | grep -v '^??'
```
Expected:
- check_exam: `5개 파일, 오류 0개`, `7개 …`, `4개 …`, `5개 …`이고 WARN은 각각 0
- verify_exam: 네 시험 모두 `오류 0개`
- 기출 테스트 `Ran 55 tests OK`, 교과서 테스트 `Ran 79 tests OK`
- 교과서 ch09–ch11: 오류 0개
- 커밋 안 된 추적 파일 없음

하나라도 실패하면 완료를 선언하지 않고, 오류 목록을 사용자에게 보여 준다.

- [ ] **Step 3: 보고하고 병합을 묻는다**

| 항목 | 결과 |
|---|---|
| 파일 수 | 시험별 문제 수, 합계 21 |
| 형식 검사 | 시험별 `N개 파일, 오류 0개`, WARN 0 |
| 시험 단위 검사 | 오류 0, 다시 크롭 일치 |
| 그림 | 등록 수 |
| 리뷰 | 묶음 4개, 사실 오류 수와 반영 내용, 반영하지 않은 제안과 이유 |
| 판독 불가 | `[판독 불가]`로 남긴 곳 목록 (2023) |
| 원문 오식 | 인쇄대로 적은 곳 목록 |
| 브랜치 | `WT`, main 대비 커밋 수, push 안 함 |

병합을 고르면 먼저 `git -C MAIN branch --show-current`가 `main`인지 확인한다. `main`이면 `git -C MAIN merge --ff-only feat/past-exam-md`로 한다. main이 앞서 있으면 `WT`에서 `git rebase main`을 한 뒤 fast-forward한다. push와 worktree 삭제(`git worktree remove`)는 따로 묻는다.
