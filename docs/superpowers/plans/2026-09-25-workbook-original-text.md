# 문제 원문 옮기기 (`## 원문` 채우기) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 교과서 377문제와 기출 22문제의 md에 인쇄된 문제 문장을 `## 원문`으로 옮긴다. 그 결과 문제지 PDF에 원문 블록이 나오게 하고, 쪽 넘침 없이 PDF 14개를 다시 만들어 커밋한다.

**Architecture:** 코드 작업은 둘이다. `check_md.py`에 원문 내용 검사를 추가하고, 원본 페이지를 찾아 그리는 도구 `workbook/source_pages.py`를 새로 만든다. 나머지는 내용 작업이다. opus 작성자와 독립 리뷰어가 10문제씩 배치로 옮긴다. ch09 워크트리에서 도구와 파일럿을 먼저 끝내 main에 병합한다. 그 뒤 ch09, ch10, ch11, 기출 워크트리 4개를 병렬로 돌리고, 마지막에 ch09 브랜치로 모아 PDF를 다시 만든다.

**Tech Stack:** Python 3.14 (Homebrew), PyYAML, PyMuPDF(`fitz` 1.27), 표준 라이브러리 `unittest`(pytest 없음), 기존 생성기 `workbook/build_workbook.py`(Playwright + 설치된 Chrome), Agent 도구(subagent, model `opus`).

**Spec:** `docs/superpowers/specs/2026-09-25-workbook-original-text-design.md`

## Global Constraints

- `MAIN` = `/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2` (메인 checkout, 브랜치 `main`, 시작 시점 `969cd6f`)
- 워크트리 `WT09`, `WT10`, `WT11`, `WTEX` = `$MAIN/.claude/worktrees/original-{ch09,ch10,ch11,exams}`, 브랜치 `claude/original-{ch09,ch10,ch11,exams}`. `.claude/worktrees/`는 `.git/info/exclude`에 들어 있다.
- 다른 세션의 워크트리 `.claude/worktrees/past-exam-tool-minor-fixes-04332f`는 건드리지 않는다.
- **원본 PDF:** `교과서/마이크로전자회로/{9,10,11}장.pdf`는 git이 추적한다(`git ls-files`로 확인함, 커밋 `9895209`). 그래서 워크트리에 그대로 있고 심볼릭 링크는 필요 없다. 핸드오프의 "추적하지 않음"은 틀린 정보다. 기출 원본 PDF도 추적된다.
- `SCRATCH` = 실행하는 세션의 scratchpad 경로. 페이지 이미지는 `$SCRATCH/pages/<ch09|ch10|ch11|exams>/<배치>/`에 둔다. 저장소 안에는 두지 않는다. 셸 명령마다 앞에 `export SCRATCH=<경로>`를 붙인다(셸 상태가 유지되지 않음). `WT09` 같은 변수도 마찬가지로 매번 정의한다.
- **tesseract나 OCR은 쓰지 않는다.** PNG를 Read로 열어 보고 옮긴다.
- **git add:** 항상 경로를 명시한다. `git add -A`, `git add .`는 쓰지 않는다.
- **커밋 메시지:** 마지막 줄은 빈 줄 뒤 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`이다.
- **push는 하지 않는다.** main 병합과 워크트리 삭제는 그때마다 사용자에게 묻는다.
- **PDF:** Task 8 전까지 `workbook/pdf/*.pdf`를 다시 만들거나 커밋하지 않는다. 워크트리에서 빌드할 때는 항상 `--pdf-dir workbook/build/pdf`를 준다(`workbook/build/`는 gitignore).
- **원문 규칙**(스펙 '원문 규칙'과 같음)
  - 넣는 범위: 예제는 "풀이" 앞의 문제 문장, 연습문제는 그 문장, 장말문제는 번호를 뺀 본문과 (a)(b)…, 기출은 문항 번호·배점을 뺀 본문과 (1)(2)….
  - 넣지 않는 것: 그림 캡션, 그림 안 글자, 풀이, 손글씨.
  - 표기: 문단은 빈 줄로 나눈다. 기호·수치는 `## 조건`과 같은 LaTeX(`$R_{out}$`, `$I_C = 1\ \text{mA}$`)로 쓴다. 굵게는 인쇄물이 굵을 때만 쓰고, 기울임은 표시하지 않는다.
  - 오식은 인쇄된 그대로 두고, 오식 메모는 `## 조건`에 적는다.
  - 원문 안에는 작성자 표시(`원문에 없음`, `(원문의 …`, `보조 출처`), `*기울임*`, `###`, 이미지 줄을 쓰지 않는다.
  - 기출 손글씨에 가려 읽을 수 없으면 `[판독 불가]`로 적는다.
- **위치:** `## 원문`은 H1 줄 바로 다음(빈 줄 하나 뒤), 기존 `## 조건` 앞에 넣는다. md의 다른 부분은 고치지 않는다. 리뷰에서 조건 값 오류가 나오면 고칠 수 있다.
- **테스트 명령과 기대 개수**
  - 교과서 도구 `python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests`: 지금 95개, Task 1 뒤 99개.
  - 기출 도구 `python3 -m unittest discover -s from_the_past/md/_tools/tests`: 65개, 변하지 않는다.
  - 생성기 `python3 -m unittest discover -s workbook/tests`: 지금 69개, Task 2 뒤 77개, Task 8에서 템플릿을 고치면 78개.
- **서브에이전트:** 작성자와 리뷰어 모두 `Agent`(subagent_type `general-purpose`, model `opus`)로 띄운다. 워크트리 하나에 작성자는 한 번에 한 명뿐이다. 같은 git index와 같은 장의 파일을 쓰기 때문이다.

## Review Focus

1. **원문에 작성자 표시가 섞임:** 원문 절은 `strip_markers`를 거치지 않는다(`problem.py:141-143`). 그래서 `(원문에 없음)`이 PDF에 그대로 찍힌다. `check_md`가 막아야 한다. → Task 1 `test_original_author_marker_rejected`
2. **정상 원문이 오판으로 막힘:** `**굵게**`, 수식 속 `$V^*$`, `$a * b$`는 기울임 검사에 걸리면 안 된다. → Task 1 `test_original_bold_and_math_star_allowed`
3. **다음 쪽까지 이어지는 문제와 마지막 쪽:** P9.18처럼 문제가 다음 쪽으로 넘어가면 `pdf_page+1`도 그려야 한다. PDF의 마지막 쪽이면 다음 쪽 없이 조용히 넘어가야 한다. → Task 2 `test_textbook_page_and_next`, `test_last_page_has_no_next`
4. **폴더 이름 오타로 거짓 완료:** `missing ch99`가 "0개 남음, 종료 코드 0"을 내면 완료로 착각한다. 없는 폴더는 오류여야 한다. → Task 2 `test_missing_folder_raises`
5. **원본 PDF가 없음:** traceback이 아니라 `ERROR 원본 PDF 없음: …` 한 줄과 종료 코드 1이어야 한다. → Task 2 `test_missing_pdf_is_error_line`

---

## 절차 B — 배치 반복 (Task 3–7에서 오케스트레이터가 실행)

오케스트레이터는 이 계획을 실행하는 메인 세션이다. 워크트리 `WT`, 폴더 `F`(예: `교과서/마이크로전자회로/ch10`), 보고서 폴더 `R`(예: `docs/superpowers/reports/ch10`), 배치 글자(A, B, C…)를 가지고 아래를 반복한다.

1. `cd WT && python3 workbook/source_pages.py next F --size 10`으로 다음 배치의 md 경로 목록을 얻는다. 목록이 비었으면 6으로 간다.
2. 반영하지 않은 리뷰 보고서가 있으면 목록을 모은다. 대상은 `R/original-<글자>.md` 가운데 끝난 것(`.part`가 아닌 것)이고, 아직 반영 커밋이 없는 것이다.
3. **부록 W**의 작성자 지시에 값을 채워 작성자 subagent를 띄운다. 이 단계는 foreground로 돌리고, 끝나면 커밋 해시와 판독이 애매했던 곳 목록을 받는다.
4. **부록 R**의 리뷰어 지시에 3의 커밋과 애매한 곳 목록을 넣어 리뷰어 subagent를 띄운다. 이 단계는 background로 돌린다.
5. 배치 글자를 하나 올리고 1로 돌아간다. 리뷰가 끝나기를 기다리지 않는다.
6. 모든 리뷰어가 끝날 때까지 기다린다. 반영하지 않은 보고서가 남았으면 부록 W를 "반영만" 모드(대상 목록 없음)로 한 번 더 띄운다.
7. **완료 검사 C**를 돌린다.

### 완료 검사 C (교과서 장 `chNN`)
```bash
cd WT
python3 workbook/source_pages.py missing 교과서/마이크로전자회로/chNN            # 종료 코드 0, "원문 없음: 0개"
python3 교과서/마이크로전자회로/_tools/check_md.py 교과서/마이크로전자회로/chNN   # 오류 0
python3 교과서/마이크로전자회로/_tools/verify_chapter.py 교과서/마이크로전자회로/chNN --recrop
python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests
python3 -m unittest discover -s from_the_past/md/_tools/tests
python3 -m unittest discover -s workbook/tests
python3 workbook/build_workbook.py chNN --pdf-dir workbook/build/pdf 2> $SCRATCH/overflow-chNN.txt; grep OVERFLOW $SCRATCH/overflow-chNN.txt
```
- 앞의 여섯 명령은 모두 성공해야 한다.
- 마지막 명령의 OVERFLOW 줄은 실패로 보지 않는다. Task 8에서 처리하므로 목록만 오케스트레이터 메모에 남긴다.
- 기출은 `chNN` 자리에 네 시험 폴더를 넣어 `missing`을 돌리고, 검사는 `check_exam.py <폴더>`와 `verify_exam.py <폴더> --recrop`로 바꾼다. 빌드는 `build_workbook.py <시험 폴더 이름>`이다.

---

### Task 0: 준비 — ch09 워크트리와 설계 문서

**Files:**
- Move: `$MAIN/docs/superpowers/specs/2026-09-25-workbook-original-text-design.md`, `$MAIN/docs/superpowers/plans/2026-09-25-workbook-original-text.md` → `WT09`의 같은 경로. 두 파일은 지금 MAIN에서 추적되지 않는 상태다.

- [ ] **Step 1: 워크트리 만들기**

```bash
cd /Users/hyunjun_macbook_pro/Documents/Univ/전자회로2
git status --short                      # 설계 문서 두 개(??)만 보여야 한다
git worktree add .claude/worktrees/original-ch09 -b claude/original-ch09 main
```

- [ ] **Step 2: 설계 문서를 워크트리로 옮겨 커밋**

```bash
MAIN=/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2; WT09=$MAIN/.claude/worktrees/original-ch09
mv "$MAIN/docs/superpowers/specs/2026-09-25-workbook-original-text-design.md" "$WT09/docs/superpowers/specs/"
mv "$MAIN/docs/superpowers/plans/2026-09-25-workbook-original-text.md" "$WT09/docs/superpowers/plans/"
cd "$WT09"
git add docs/superpowers/specs/2026-09-25-workbook-original-text-design.md docs/superpowers/plans/2026-09-25-workbook-original-text.md
git commit -m "docs: add workbook original-text design and plan

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 3: 기준 테스트 확인**

```bash
cd "$WT09"
python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests 2>&1 | tail -1   # OK (95)
python3 -m unittest discover -s from_the_past/md/_tools/tests 2>&1 | tail -1          # OK (65)
python3 -m unittest discover -s workbook/tests 2>&1 | tail -1                         # OK (69)
ls -la 교과서/마이크로전자회로/9장.pdf                                                # 일반 파일
```

---

### Task 1: `check_md`에 원문 내용 검사 추가

**Files:**
- Modify: `교과서/마이크로전자회로/_tools/check_md.py:40-42` (정규식 추가), `:80-116` (`check_workbook_sections`에서 호출)
- Modify: `교과서/마이크로전자회로/FORMAT.md:165` 뒤 (규칙 두 줄)
- Modify: `from_the_past/md/FORMAT-EXAM.md:45`
- Test: `교과서/마이크로전자회로/_tools/tests/test_check_md.py` (`TestWorkbookSections` 클래스 끝, `:397` 뒤)

**Interfaces:**
- Produces: `check_original(text: str) -> list[str]`. 오류 메시지는 모두 `"## 원문: "`으로 시작한다. `check_workbook_sections`가 원문이 비어 있지 않을 때 이 함수를 부른다. `check_exam.py`는 `check_body`를 거쳐 같은 검사를 받는다.

- [ ] **Step 1: 실패하는 테스트 작성** — `TestWorkbookSections`의 `test_check_body_reports_workbook_errors` 뒤에 추가한다.

```python
    def test_original_author_marker_rejected(self):
        body = wb_body().replace("Repeat Example 9.1.", "Repeat Example 9.1 (원문에 없음).")
        self.assert_error(body, "작성자 표시")

    def test_original_single_emphasis_rejected(self):
        self.assert_error(wb_body().replace("Repeat Example 9.1.", "a *higher* gain"), "기울임")

    def test_original_bold_and_math_star_allowed(self):
        body = wb_body().replace("Repeat Example 9.1.", "a **higher** gain with $V^*$ and $a * b$.")
        self.assertEqual(check_workbook_sections(body), [])

    def test_original_subsection_and_image_rejected(self):
        body = wb_body().replace("Repeat Example 9.1.", "Text.\n![Fig](a.png)\n### (a)\nMore.")
        errors = check_workbook_sections(body)
        self.assertTrue(any("이미지" in e for e in errors), errors)
        self.assertTrue(any("### 소절" in e for e in errors), errors)
```

- [ ] **Step 2: 실패 확인**

Run: `python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests -k original 2>&1 | tail -3`
Expected: FAIL 3개(`author_marker`, `single_emphasis`, `subsection_and_image`)가 나온다. `bold_and_math_star_allowed`는 지금도 통과한다. 검사가 없으니 오류도 없기 때문이다.

- [ ] **Step 3: 구현** — `check_md.py`의 `WORKBOOK_TAIL = ("힌트", "풀이")` 줄 바로 아래에 추가한다.

```python
# 원문 절은 PDF에 그대로 나온다(작성자 표시를 지우지 않음). 수식을 가린 뒤 검사한다.
ORIGINAL_MATH_RE = re.compile(r"\$\$.+?\$\$|\$[^$]+?\$", re.DOTALL)
ORIGINAL_MARKER_RE = re.compile(r"원문에 없음|\(원문의 |보조 출처")
SINGLE_EMPHASIS_RE = re.compile(r"(?<![*\\])\*(?![*\s])[^*\n]+?(?<![*\s])\*(?!\*)")
```

`def check_workbook_sections(body):` 바로 위에 추가한다.

```python
def check_original(text):
    """## 원문 내용: 인쇄된 문장만. 작성자 표시·*기울임*·### 소절·이미지 줄은 쓰지 않는다."""
    errors = []
    plain = ORIGINAL_MATH_RE.sub("", text)
    if ORIGINAL_MARKER_RE.search(plain):
        errors.append("## 원문: 작성자 표시(원문에 없음, (원문의 …, 보조 출처)는 넣지 않음 — ## 조건에 적음")
    if SINGLE_EMPHASIS_RE.search(plain):
        errors.append("## 원문: *기울임* 강조는 쓰지 않음 (PDF에 별표가 그대로 나옴)")
    lines = text.splitlines()
    if any(line.startswith("### ") for line in lines):
        errors.append("## 원문: ### 소절을 두지 않음")
    if any(line.lstrip().startswith("![") for line in lines):
        errors.append("## 원문: 이미지 줄을 두지 않음")
    return errors
```

`check_workbook_sections` 안의 빈 절 검사 루프 바로 다음, `for name in WORKBOOK_TAIL:` 앞에 추가한다.

```python
    if content.get("원문", "").strip():
        errors += check_original(content["원문"])
```

- [ ] **Step 4: 통과 확인**

Run: `python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests 2>&1 | tail -1` → `OK` (99)
Run: `python3 -m unittest discover -s from_the_past/md/_tools/tests 2>&1 | tail -1` → `OK` (65)
Run: `python3 -m unittest discover -s workbook/tests 2>&1 | tail -1` → `OK` (69)
Run: `for c in ch09 ch10 ch11; do python3 교과서/마이크로전자회로/_tools/check_md.py 교과서/마이크로전자회로/$c | tail -1; done` → 세 장 모두 기존처럼 오류 0

- [ ] **Step 5: 문서** — `FORMAT.md`의 "PDF에서는 `## 조건`의 `- 회로:` 줄…" bullet 바로 아래에 두 줄을 넣는다.

```markdown
- `## 원문`에는 인쇄된 문제 문장만 둔다. 예제는 "풀이" 앞 문장, 연습문제는 그 문장, 장말문제는 번호를 뺀 본문과 소문항이다. 그림 캡션과 그림 안 글자는 넣지 않는다. 원문 오식은 그대로 두고, 오식 메모는 `## 조건`에 적는다.
- `## 원문` 안에는 작성자 표시(`원문에 없음`, `(원문의 …`, `보조 출처`), `*기울임*`, `###` 소절, 이미지 줄을 쓰지 않는다. 원문은 PDF에 그대로 나오기 때문이다(`check_md.py`가 막는다). 굵게는 인쇄물이 굵을 때만 쓴다.
```

`FORMAT-EXAM.md:45` 줄 끝에 이어 쓴다.

```markdown
 원문은 인쇄된 글자만 옮기고(손글씨 제외), 가려서 읽을 수 없는 글자는 `[판독 불가]`로 적는다. 2023-1 기말은 `2023 전회2 기말.hwp`(PDF로 바꿔서)를 글자 기준으로, 스캔은 배치 확인용으로 쓴다.
```

- [ ] **Step 6: 커밋**

```bash
git add 교과서/마이크로전자회로/_tools/check_md.py 교과서/마이크로전자회로/_tools/tests/test_check_md.py 교과서/마이크로전자회로/FORMAT.md from_the_past/md/FORMAT-EXAM.md
git commit -m "feat: reject author markers, italics, subsections and images in 원문

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: 원본 페이지 도구 `workbook/source_pages.py`

**Files:**
- Create: `workbook/source_pages.py`
- Test: `workbook/tests/test_source_pages.py`
- Modify: `workbook/README.md` (끝에 '원문 옮기기 도구' 절)

**Interfaces:**
- Consumes: `check_md.split_frontmatter(text) -> (meta: dict, body: str)`, `check_md.split_sections(body) -> [(제목, 내용)]`. `import paths`로 가져올 수 있다.
- Produces:
  - `pending(folder) -> list[Path]`: 원문이 없는 md를 (source, pdf_page, id) 순으로 돌려준다. 폴더가 없으면 `SourceError`.
  - `source_pdf(md: Path, meta: dict) -> Path`
  - `render(mds, out, dpi=200) -> list[Path]`
  - `main(argv) -> int`
  - CLI: `next <폴더> [--size N]`, `missing <폴더>`(남은 것이 있으면 1), `render <md…> --out <폴더> [--dpi N]`. 오류는 `ERROR …` 한 줄, 종료 코드 1이다.

- [ ] **Step 1: 실패하는 테스트 작성** — `workbook/tests/test_source_pages.py`

```python
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from source_pages import SourceError, main, pending, render, source_pdf  # noqa: E402


def write_md(path, pid, kind, page, original=False, extra=""):
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "# 장말문제 9.1 — 제목\n\n" + ("## 원문\nText.\n\n" if original else "") + "## 조건\n- a\n"
    path.write_text(f"---\nid: {pid}\nkind: {kind}\npdf_page: {page}\n{extra}---\n{body}", encoding="utf-8")
    return path


def write_pdf(path, pages=3, text_pages=(1, 2)):
    doc = fitz.open()
    for i in range(1, pages + 1):
        page = doc.new_page()
        if i in text_pages:
            page.insert_text((72, 72), f"Problem statement on page {i}, long enough.")
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(path)
    doc.close()
    return path


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(["source_pages.py"] + argv)
    return code, out.getvalue(), err.getvalue()


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.ch = self.root / "ch09"
        self.out = self.root / "out"

    def tearDown(self):
        self._tmp.cleanup()


class TestPending(Base):
    def test_sorted_by_page_then_id_and_skips_done(self):
        write_md(self.ch / "장말문제/P9.02.md", "P9.02", "장말문제", 1)
        write_md(self.ch / "장말문제/P9.01.md", "P9.01", "장말문제", 1, original=True)
        write_md(self.ch / "연습문제/X9.01.md", "X9.01", "연습문제", 2)
        write_md(self.ch / "예제/E9.01.md", "E9.01", "예제", 2)
        (self.ch / "README.md").write_text("# 9장\n", encoding="utf-8")
        self.assertEqual([p.name for p in pending(self.ch)], ["P9.02.md", "E9.01.md", "X9.01.md"])

    def test_missing_folder_raises(self):
        with self.assertRaises(SourceError):
            pending(self.root / "ch99")

    def test_main_missing_exit_code(self):
        write_md(self.ch / "예제/E9.01.md", "E9.01", "예제", 2)
        code, out, err = run(["missing", str(self.ch)])
        self.assertEqual(code, 1)
        self.assertIn("E9.01.md", out)
        self.assertIn("원문 없음: 1개", err)
        write_md(self.ch / "예제/E9.01.md", "E9.01", "예제", 2, original=True)
        self.assertEqual(run(["missing", str(self.ch)])[0], 0)

    def test_main_next_size(self):
        for i in range(1, 4):
            write_md(self.ch / f"장말문제/P9.0{i}.md", f"P9.0{i}", "장말문제", i)
        code, out, _ = run(["next", str(self.ch), "--size", "2"])
        self.assertEqual(code, 0)
        self.assertEqual([Path(line).name for line in out.splitlines()], ["P9.01.md", "P9.02.md"])


class TestRender(Base):
    def test_textbook_page_and_next(self):
        write_pdf(self.root / "9장.pdf")
        md = write_md(self.ch / "장말문제/P9.18.md", "P9.18", "장말문제", 2)
        self.assertEqual(source_pdf(md, {"kind": "장말문제"}), self.root / "9장.pdf")
        names = sorted(p.name for p in render([md], self.out, dpi=50))
        self.assertEqual(names, ["P9.18-p2.png", "P9.18-p2.txt", "P9.18-p3.png"])
        self.assertIn("page 2", (self.out / "P9.18-p2.txt").read_text(encoding="utf-8"))

    def test_last_page_has_no_next(self):
        write_pdf(self.root / "9장.pdf")
        md = write_md(self.ch / "장말문제/P9.68.md", "P9.68", "장말문제", 3)
        self.assertEqual([p.name for p in render([md], self.out, dpi=50)], ["P9.68-p3.png"])

    def test_exam_source_relative_to_md(self):
        write_pdf(self.root / "src/exam.pdf", pages=1, text_pages=(1,))
        md = write_md(self.root / "md/2023-1_기말/Q1.md", "2023-1_기말-Q1", "기출", 1,
                      extra='source: "../../src/exam.pdf"\n')
        names = sorted(p.name for p in render([md], self.out, dpi=50))
        self.assertEqual(names, ["2023-1_기말-Q1-p1.png", "2023-1_기말-Q1-p1.txt"])

    def test_missing_pdf_is_error_line(self):
        md = write_md(self.ch / "예제/E9.01.md", "E9.01", "예제", 1)
        code, _, err = run(["render", str(md), "--out", str(self.out)])
        self.assertEqual(code, 1)
        self.assertIn("ERROR 원본 PDF 없음", err)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 실패 확인**

Run: `python3 -m unittest workbook/tests/test_source_pages.py 2>&1 | tail -3`
Expected: `ModuleNotFoundError: No module named 'source_pages'`

- [ ] **Step 3: 구현** — `workbook/source_pages.py`

```python
#!/usr/bin/env python3
"""원문 옮기기용 원본 페이지 도구. md frontmatter의 pdf_page로 원본 PDF 쪽을 찾는다.

사용법:
  python3 workbook/source_pages.py next <폴더> [--size 10]   원문 없는 md를 (원본, pdf_page, id) 순으로 N개
  python3 workbook/source_pages.py missing <폴더>            원문 없는 md 목록. 하나라도 있으면 종료 코드 1
  python3 workbook/source_pages.py render <md…> --out <폴더> [--dpi 200]
      pdf_page와 다음 쪽을 <id>-p<쪽>.png로. 글자 층이 있으면 <id>-p<쪽>.txt도.
<폴더>는 장 폴더(교과서/마이크로전자회로/ch09)나 시험 폴더(from_the_past/md/2023-1_기말).
원본 PDF: 교과서는 장 폴더 옆 <장 번호>장.pdf, 기출은 frontmatter source(md 기준 상대 경로).
"""
import argparse
import re
import sys
from pathlib import Path

import fitz

import paths  # noqa: F401  (기존 도구 import 경로 설정)
from check_md import split_frontmatter, split_sections

CHAPTER_RE = re.compile(r"^ch(\d+)$")
TEXT_MIN = 20       # 이보다 짧은 글자 층은 스캔 잡음으로 보고 버린다


class SourceError(Exception):
    pass


def problem_mds(folder):
    folder = Path(folder)
    if not folder.is_dir():
        raise SourceError(f"폴더 없음: {folder}")
    return sorted(p for p in folder.rglob("*.md") if p.name != "README.md")


def read_md(md):
    try:
        return split_frontmatter(Path(md).read_text(encoding="utf-8"))
    except ValueError as e:
        raise SourceError(f"{md}: {e}") from e


def pending(folder):
    """원문이 없는 md를 (source, pdf_page, id) 순으로. 같은 쪽의 예제·연습문제가 이어진다."""
    keyed = []
    for md in problem_mds(folder):
        meta, body = read_md(md)
        if any(title == "원문" for title, _ in split_sections(body)):
            continue
        keyed.append(((str(meta.get("source", "")), int(meta["pdf_page"]), str(meta["id"])), md))
    return [md for _, md in sorted(keyed)]


def source_pdf(md, meta):
    md = Path(md)
    if meta.get("kind") == "기출":
        return md.parent / str(meta["source"])
    chapter = md.parent.parent
    m = CHAPTER_RE.match(chapter.name)
    if not m:
        raise SourceError(f"장 폴더를 알 수 없음: {md}")
    return chapter.parent / f"{int(m.group(1))}장.pdf"


def render(mds, out, dpi=200):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for md in mds:
        meta, _ = read_md(md)
        pdf = source_pdf(md, meta)
        if not pdf.exists():
            raise SourceError(f"원본 PDF 없음: {pdf}")
        first = int(meta["pdf_page"])
        with fitz.open(pdf) as doc:
            for page_no in (first, first + 1):
                if page_no > doc.page_count:
                    continue
                page = doc[page_no - 1]
                stem = out / f"{meta['id']}-p{page_no}"
                png = stem.with_name(stem.name + ".png")
                page.get_pixmap(dpi=dpi).save(str(png))
                written.append(png)
                text = page.get_text().strip()
                if len(text) >= TEXT_MIN:
                    txt = stem.with_name(stem.name + ".txt")
                    txt.write_text(text + "\n", encoding="utf-8")
                    written.append(txt)
    return written


def parse_args(argv):
    ap = argparse.ArgumentParser(prog="source_pages.py", description="원문 옮기기용 원본 페이지 도구")
    sub = ap.add_subparsers(dest="cmd", required=True)
    nxt = sub.add_parser("next", help="원문 없는 md를 N개")
    nxt.add_argument("folder", type=Path)
    nxt.add_argument("--size", type=int, default=10)
    mis = sub.add_parser("missing", help="원문 없는 md 전부 (있으면 종료 코드 1)")
    mis.add_argument("folder", type=Path)
    ren = sub.add_parser("render", help="pdf_page와 다음 쪽을 PNG로")
    ren.add_argument("mds", nargs="+", type=Path)
    ren.add_argument("--out", type=Path, required=True)
    ren.add_argument("--dpi", type=int, default=200)
    return ap.parse_args(argv[1:])


def main(argv):
    args = parse_args(argv)
    try:
        if args.cmd == "next":
            for md in pending(args.folder)[:args.size]:
                print(md)
        elif args.cmd == "missing":
            left = pending(args.folder)
            for md in left:
                print(md)
            print(f"원문 없음: {len(left)}개", file=sys.stderr)
            return 1 if left else 0
        else:
            for f in render(args.mds, args.out, args.dpi):
                print(f)
    except (SourceError, KeyError, OSError) as e:
        msg = e.args[0] if isinstance(e, SourceError) else f"{type(e).__name__}: {e}"
        print(f"ERROR {msg}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

- [ ] **Step 4: 통과 확인**

Run: `python3 -m unittest discover -s workbook/tests 2>&1 | tail -1` → `OK` (77)
Run: `python3 workbook/source_pages.py missing 교과서/마이크로전자회로/ch09 > /dev/null; echo $?` → stderr `원문 없음: 110개`, 종료 코드 `1`
Run: `python3 workbook/source_pages.py render 교과서/마이크로전자회로/ch09/장말문제/P9.18.md --out $SCRATCH/pages/smoke` → `P9.18-p22.png`, `P9.18-p23.png`(스캔이라 `.txt` 없음). PNG 하나를 Read로 열어 P9.18이 보이는지 확인한다.
Run: `python3 workbook/source_pages.py render from_the_past/md/2021-1_중간/Q1.md --out $SCRATCH/pages/smoke` → `.png`와 `.txt`가 함께 나온다.

- [ ] **Step 5: README** — `workbook/README.md` 끝에 추가한다.

````markdown
## 원문 옮기기 도구
`source_pages.py`는 md frontmatter의 `pdf_page`로 원본 PDF 쪽을 찾는다. 규칙은 `교과서/마이크로전자회로/FORMAT.md` '문제집용 절'.
```bash
python3 workbook/source_pages.py next 교과서/마이크로전자회로/ch10 --size 10   # 다음 배치 (원문 없는 md)
python3 workbook/source_pages.py missing from_the_past/md/2023-1_기말           # 남은 것 (있으면 종료 코드 1)
python3 workbook/source_pages.py render <md…> --out /tmp/pages                  # pdf_page·다음 쪽 PNG (+ 글자 층 .txt)
```
````

- [ ] **Step 6: 커밋**

```bash
git add workbook/source_pages.py workbook/tests/test_source_pages.py workbook/README.md
git commit -m "feat(workbook): add source_pages tool for original-text transcription

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: 파일럿 — ch09 15문제, main 병합

**Files:**
- Modify (원문 추가): `교과서/마이크로전자회로/ch09/장말문제/P9.01.md` … `P9.10.md`, `교과서/마이크로전자회로/ch09/예제/E9.01.md` … `E9.05.md`
- Create: `docs/superpowers/reports/ch09/original-A.md` (리뷰 보고서)

**Interfaces:**
- Consumes: Task 1의 `check_original`(check_md에서 호출됨), Task 2의 `source_pages.py render`
- Produces: main에 병합된 도구와 파일럿 결과. Task 4–7 워크트리는 이 main에서 만든다.

- [ ] **Step 1: 작성자 파견** — 부록 W를 채워 foreground로 띄운다. WT=`WT09`, 배치=`A`, 대상=위 15개 경로(`next`를 쓰지 않고 직접 준다), 반영할 보고서=없음, PAGES=`$SCRATCH/pages/ch09/A`. 커밋 해시와 애매한 곳 목록을 받는다.
- [ ] **Step 2: 리뷰어 파견** — 부록 R을 채워 **foreground**로 띄운다. 파일럿에서는 기다린다. 보고서는 `docs/superpowers/reports/ch09/original-A.md`다.
- [ ] **Step 3: 반영** — 부록 W를 "반영만" 모드로 띄운다(대상 없음, 반영할 보고서=`original-A.md`).
- [ ] **Step 4: 형식 검사와 빌드**

```bash
cd "$WT09"
python3 교과서/마이크로전자회로/_tools/check_md.py 교과서/마이크로전자회로/ch09
python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests 2>&1 | tail -1   # OK (99)
python3 -m unittest discover -s workbook/tests 2>&1 | tail -1                         # OK (77)
python3 workbook/build_workbook.py --ids P9.01,P9.02,P9.03,P9.04,P9.05,P9.06,P9.07,P9.08,P9.09,P9.10,E9.01,E9.02,E9.03,E9.04,E9.05 --name 원문-파일럿 --pdf-dir workbook/build/pdf 2>&1 | tail -5
```
Expected: 검사 오류가 0이다. OVERFLOW 줄이 있으면 쪽 id를 기록한다. 실패로 보지 않는다.

- [ ] **Step 5: 눈으로 확인** — 빌드된 문제지를 PNG로 그려 원문 블록을 본다.

```bash
python3 - <<'EOF'
import fitz, os
out = os.environ.get("SCRATCH", "/tmp") + "/pilot"
os.makedirs(out, exist_ok=True)
with fitz.open("workbook/build/pdf/원문-파일럿-문제.pdf") as d:
    for i in range(d.page_count):
        d[i].get_pixmap(dpi=80).save(f"{out}/p{i+1:02d}.png")
print(out)
EOF
```
PNG를 Read로 열어 다섯 가지를 확인한다.
1. 원문 블록이 조건 위에 있다.
2. 영어 장말문제의 줄바꿈과 하이픈 넣기가 자연스럽다.
3. 한국어 예제가 `lang=ko` 글꼴로 나온다.
4. 수식이 KaTeX로 그려졌다.
5. OVERFLOW 쪽에 빨간 표시가 있다.

**파일 이름 확인:** `--name`이 NFC로 바뀌지 않는 문제(미뤄 둔 사소한 문제 3번)가 있다. PDF 이름이 다르면 `ls workbook/build/pdf`로 실제 이름을 찾는다.

- [ ] **Step 6: 사용자 확인** — 다음을 보여 준다.
  - 샘플 PNG 두 장: 영어 장말문제 하나, 한국어 예제 하나.
  - 리뷰 A의 지적 수와 주요 유형.
  - OVERFLOW 목록.

  그리고 두 가지를 묻는다: "`claude/original-ch09`를 main에 ff-merge할까요? 병합 뒤 ch10·ch11·기출 워크트리를 열어 병렬 진행합니다." 사용자가 규칙 변경을 요청하면 Global Constraints의 원문 규칙과 FORMAT.md를 먼저 고치고, 파일럿을 다시 검토한다.
- [ ] **Step 7: 병합** (사용자가 승인한 뒤)

```bash
git -C /Users/hyunjun_macbook_pro/Documents/Univ/전자회로2 merge --ff-only claude/original-ch09
```

---

### Task 4: ch09 나머지 95문제

**Files:**
- Modify: `교과서/마이크로전자회로/ch09/{예제,연습문제,장말문제}/*.md` 가운데 원문이 없는 것
- Create: `docs/superpowers/reports/ch09/original-B.md`, `original-C.md`, …

**Interfaces:**
- Consumes: Task 2의 `source_pages.py next/missing/render`. main에 병합된 Task 3.
- Produces: `claude/original-ch09`에 ch09 110개의 원문. Task 8이 이 브랜치로 모은다.

- [ ] **Step 1:** `WT09`에서 절차 B를 돌린다. F=`교과서/마이크로전자회로/ch09`, R=`docs/superpowers/reports/ch09`, 첫 배치 글자는 `B`다. 약 10배치다.
- [ ] **Step 2:** 완료 검사 C(ch09)를 통과시키고, OVERFLOW 목록을 기록한다.

### Task 5: ch10 151문제

**Files:**
- Modify: `교과서/마이크로전자회로/ch10/{예제,연습문제,장말문제}/*.md`
- Create: `docs/superpowers/reports/ch10/original-A.md` …

**Interfaces:**
- Consumes: main(Task 3 병합 뒤)의 `source_pages.py`, `check_md.check_original`
- Produces: `claude/original-ch10`

- [ ] **Step 1: 워크트리**

```bash
cd /Users/hyunjun_macbook_pro/Documents/Univ/전자회로2
git worktree add .claude/worktrees/original-ch10 -b claude/original-ch10 main
```
- [ ] **Step 2:** `WT10`에서 절차 B를 돌린다. F=`교과서/마이크로전자회로/ch10`, R=`docs/superpowers/reports/ch10`, 첫 배치 글자는 `A`다. 약 16배치다.
- [ ] **Step 3:** 완료 검사 C(ch10)를 통과시키고, OVERFLOW 목록을 기록한다.

### Task 6: ch11 116문제

**Files:**
- Modify: `교과서/마이크로전자회로/ch11/{예제,연습문제,장말문제}/*.md`
- Create: `docs/superpowers/reports/ch11/original-A.md` … (기존 `review-H.md`와 이름이 겹치지 않는다)

**Interfaces:**
- Consumes: main(Task 3 병합 뒤)의 `source_pages.py`, `check_md.check_original`
- Produces: `claude/original-ch11`

- [ ] **Step 1: 워크트리**

```bash
cd /Users/hyunjun_macbook_pro/Documents/Univ/전자회로2
git worktree add .claude/worktrees/original-ch11 -b claude/original-ch11 main
```
- [ ] **Step 2:** `WT11`에서 절차 B를 돌린다. F=`교과서/마이크로전자회로/ch11`, R=`docs/superpowers/reports/ch11`, 첫 배치 글자는 `A`다. 약 12배치다.
- [ ] **Step 3:** 완료 검사 C(ch11)를 통과시키고, OVERFLOW 목록을 기록한다.

### Task 7: 기출 22문제

**Files:**
- Modify: `from_the_past/md/{2021-1_중간,2021-1_기말,2023-1_중간,2023-1_기말}/Q*.md`
- Create: `docs/superpowers/reports/exams/original-A.md` … `original-D.md`

**Interfaces:**
- Consumes: main(Task 3 병합 뒤)의 `source_pages.py`, `check_md.check_original`(`check_exam`이 `check_body`로 호출)
- Produces: `claude/original-exams`

- [ ] **Step 1: 워크트리**

```bash
cd /Users/hyunjun_macbook_pro/Documents/Univ/전자회로2
git worktree add .claude/worktrees/original-exams -b claude/original-exams main
```
- [ ] **Step 2: hwp를 PDF로 바꾸기** — `hwp-to-pdf` 스킬로 `from_the_past/2023-1/23-1 기말/2023 전회2 기말.hwp`를 `$SCRATCH/hwp/`에 PDF로 바꾼다. 저장소 안에는 만들지 않는다. 결과 PDF를 fitz로 쪽별 PNG로 만들어 `$SCRATCH/hwp/pages/`에 둔다. 변환에 실패하면 사용자에게 알리고, 2023 기말은 스캔만으로 진행한다.
- [ ] **Step 3:** 시험 폴더마다 배치 하나로 절차 B를 돌린다. 순서와 배치 글자: A=`from_the_past/md/2021-1_중간`, B=`2021-1_기말`, C=`2023-1_중간`, D=`2023-1_기말`. `next`는 폴더 하나만 받으므로 배치마다 F를 바꾼다. 부록 W의 '기출' 항목을 켠다. D 배치에는 `$SCRATCH/hwp/pages/`를 보조 원본으로 넘긴다.
- [ ] **Step 4:** 네 폴더 모두 완료 검사 C(기출판)를 통과시킨다.

```bash
cd "$WTEX"
for e in 2021-1_중간 2021-1_기말 2023-1_중간 2023-1_기말; do
  python3 workbook/source_pages.py missing from_the_past/md/$e > /dev/null || echo "남음 $e"
  python3 from_the_past/md/_tools/check_exam.py from_the_past/md/$e | tail -1
  python3 from_the_past/md/_tools/verify_exam.py from_the_past/md/$e --recrop | tail -1
  python3 workbook/build_workbook.py $e --pdf-dir workbook/build/pdf 2>&1 | grep OVERFLOW
done
```

---

### Task 8: 통합 — 모으기, 쪽 넘침 처리, PDF 다시 만들기

**Files:**
- Modify (넘침이 있을 때만): `workbook/templates/problem.html:286-289`
- Test (넘침이 있을 때만): `workbook/tests/test_templates.py`
- Modify: `workbook/pdf/*.pdf` (14개)

**Interfaces:**
- Consumes: 브랜치 `claude/original-{ch09,ch10,ch11,exams}`. 절차 B에서 모은 OVERFLOW 목록.

- [ ] **Step 1: ch09 브랜치로 모으기** — 다른 파일만 건드렸으므로 충돌은 예상하지 않는다. 충돌이 나면 멈추고 보고한다.

```bash
MAIN=/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2
for x in ch10 ch11 exams; do
  git -C "$MAIN/.claude/worktrees/original-$x" rebase claude/original-ch09 &&
  git -C "$MAIN/.claude/worktrees/original-ch09" merge --ff-only claude/original-$x || break
done
```

- [ ] **Step 2: 전체 검사** (`WT09`)

```bash
cd "$WT09"
for c in ch09 ch10 ch11; do python3 workbook/source_pages.py missing 교과서/마이크로전자회로/$c >/dev/null || echo "남음 $c"; python3 교과서/마이크로전자회로/_tools/verify_chapter.py 교과서/마이크로전자회로/$c --recrop | tail -1; done
for e in 2021-1_중간 2021-1_기말 2023-1_중간 2023-1_기말; do python3 workbook/source_pages.py missing from_the_past/md/$e >/dev/null || echo "남음 $e"; python3 from_the_past/md/_tools/verify_exam.py from_the_past/md/$e --recrop | tail -1; done
python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests 2>&1 | tail -1   # OK (99)
python3 -m unittest discover -s from_the_past/md/_tools/tests 2>&1 | tail -1          # OK (65)
python3 -m unittest discover -s workbook/tests 2>&1 | tail -1                         # OK (77)
```
Expected: "남음"이 없고, 검사 오류가 0이다.

- [ ] **Step 3: 전체 빌드**

```bash
python3 workbook/build_workbook.py --all 2> $SCRATCH/build-all.txt; echo "exit $?"; grep -E "OVERFLOW|ERROR" $SCRATCH/build-all.txt
```
`exit 0`이면 Step 8로 간다. OVERFLOW만 있으면 Step 4–7을 한다. ERROR가 있으면 멈추고 보고한다.

- [ ] **Step 4: 실패하는 테스트** (OVERFLOW가 있을 때만) — `workbook/tests/test_templates.py`의 `test_original_lang_from_data` 뒤에 추가한다.

```python
    def test_fit_steps_end_with_smallest_font(self):
        t = read("problem.html")
        self.assertIn("['--fs', '0.8'], ['--fs', '0.72'],", t)
```
Run: `python3 -m unittest workbook/tests/test_templates.py 2>&1 | tail -1` → `FAILED (failures=1)`

- [ ] **Step 5: 구현** — `problem.html`의 `FIT_STEPS`를 다음처럼 바꾼다.

```js
const FIT_STEPS = [
  ['--pw', '40%'], ['--pw', '50%'],
  ['--fs', '0.9'], ['--fs', '0.8'], ['--fs', '0.72'],
];
```
Run: `python3 -m unittest discover -s workbook/tests 2>&1 | tail -1` → `OK` (78)

- [ ] **Step 6: 다시 빌드** — Step 3 명령을 다시 돌린다. 아직 OVERFLOW가 있으면 **멈춘다.** 넘친 쪽 id와 PNG(Task 3 Step 5 방식)를 사용자에게 보여 주고 대응을 묻는다. 규칙 밖의 일이다.
- [ ] **Step 7: 템플릿 커밋**

```bash
git add workbook/templates/problem.html workbook/tests/test_templates.py
git commit -m "fix(workbook): add a smaller font fit step for long original text

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 8: PDF 확인과 커밋** — 장마다 문제지 쪽을 몇 개 PNG로 그려 확인한다(Task 3 Step 5 방식, `ch10-문제.pdf`, `2023-1_기말-문제.pdf` 등). 그다음 커밋한다.

```bash
git status --short workbook/pdf     # M 14개
git add workbook/pdf/*.pdf
git commit -m "build: regenerate pdfs with original text

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
du -sh /Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/.git
```

- [ ] **Step 9: 사용자 확인 후 main 병합과 정리** — 다음을 보고한다.
  - 커밋 수
  - 리뷰 배치 수와 지적 합계
  - 템플릿 변경 여부
  - `.git` 크기

  그리고 두 가지를 묻는다: "`claude/original-ch09`를 main에 ff-merge하고, 워크트리 4개와 브랜치를 지울까요?" 승인을 받은 뒤 실행한다.

```bash
cd /Users/hyunjun_macbook_pro/Documents/Univ/전자회로2
git merge --ff-only claude/original-ch09
for x in ch09 ch10 ch11 exams; do git worktree remove .claude/worktrees/original-$x && git branch -d claude/original-$x; done
git worktree list
```

---

## 부록 W — 작성자 지시 (오케스트레이터가 `<<…>>`를 채워 Agent prompt로 보냄)

```
# 원문 옮기기 — <<LABEL>> 배치 <<BATCH>>

당신은 작성 에이전트다. 작업 폴더는 <<WT>>이고 모든 명령은 여기서 실행한다(cd <<WT>>).
먼저 교과서/마이크로전자회로/FORMAT.md의 '문제집용 절'을 읽는다. 기출이면 from_the_past/md/FORMAT-EXAM.md도 읽는다.

## 0. 리뷰 반영 (반영할 보고서: <<REPORTS>>, "없음"이면 건너뜀)
- 보고서마다 지적을 하나씩 원본 이미지로 직접 확인한다. 맞으면 고치고, 틀리면 고치지 않고 이유를 최종 메시지에 적는다.
- 페이지가 필요하면: python3 workbook/source_pages.py render <md> --out <<PAGES>>/fix --dpi 300
- git add <고친 md 경로들> <보고서 경로들>
- git commit -m "docs: apply review fixes to <<LABEL>> original batch <보고서 글자들>" (끝에 빈 줄 + Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>)
- 고친 것이 없어도 보고서는 커밋한다.

## 1. 대상 (<<TARGETS>>, "없음"이면 여기서 끝)
python3 workbook/source_pages.py render <<TARGETS>> --out <<PAGES>>
- md마다 <id>-p<쪽>.png가 생긴다(다음 쪽 포함). .txt가 있으면 PDF 글자 층이니 초안으로만 쓴다.
- 작은 글자는 --dpi 300으로 다시 그려 확대해서 본다. tesseract/OCR은 쓰지 않는다.
<<EXAM_NOTES>>

## 2. 옮기기 — md마다
- md를 먼저 읽어 종류(kind), 번호, 조건을 파악하고, 페이지에서 그 문제를 찾는다.
- H1 줄 바로 다음(빈 줄 하나 뒤), 기존 첫 절 앞에 넣는다:
  ## 원문
  <인쇄된 문장>
  (빈 줄)
- 넣는 범위: 예제는 "풀이" 앞의 문제 문장, 연습문제는 그 문장, 장말문제는 번호(예: "9.18")를 뺀 본문과 (a)(b)…, 기출은 문항 번호·배점을 뺀 본문과 (1)(2)….
- 넣지 않는 것: 그림 캡션, 그림 안 글자, 풀이, 손글씨.
- 문단은 빈 줄로 나눈다. 소문항은 인쇄물이 줄을 바꾸었으면 각각 한 문단으로 둔다.
- 기호·수치·단위는 같은 md의 ## 조건과 같은 LaTeX 표기로 쓴다: $R_{out}$, $I_C = 1\ \text{mA}$, $\lambda = 0.1\ \text{V}^{-1}$, $W/L = 20/0.18$. 문장 속 영어 단어는 수식 밖에 둔다.
- 줄 끝 하이픈으로 끊긴 단어는 붙인다(인쇄 줄바꿈은 옮기지 않는다).
- 굵게(**…**)는 인쇄가 굵을 때만 쓰고, 기울임은 표시하지 않는다.
- 오식은 인쇄된 그대로 둔다. ## 조건에 오식 메모가 없으면 조건 끝에 "- (원문의 <x>는 <y>의 오식으로 보임)" 한 줄을 추가해도 된다.
- 원문 안에 작성자 표시(원문에 없음, (원문의 …, 보조 출처), *기울임*, ###, 이미지 줄을 쓰지 않는다.
- 원문과 ## 조건의 값이 다르면 원문은 인쇄된 대로 두고, 조건은 고치지 말고 최종 메시지에 적는다.
- md의 다른 곳은 고치지 않는다.

## 3. 검사
<<CHECK_CMD>>
오류가 0이 될 때까지 고친다.

## 4. 커밋
git add <<TARGETS>>
git commit -m "docs: add <<LABEL>> original text batch <<BATCH>> (<첫 id>–<끝 id>)" (끝에 빈 줄 + Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>)
git add에는 경로를 명시한다(-A나 . 금지). push하지 않는다.

## 최종 메시지
- 커밋 해시(반영 커밋, 배치 커밋)
- 판독이 애매했던 곳: "<id> — <위치> — <적은 글자> — <이유>" 한 줄씩 (없으면 "없음")
- 원문과 조건이 어긋난 곳, 반영하지 않은 리뷰 지적과 이유
```

채울 값:
- `<<LABEL>>`: `ch09`, `ch10`, `ch11`, `exams`
- `<<CHECK_CMD>>`
  - 교과서: `python3 교과서/마이크로전자회로/_tools/check_md.py 교과서/마이크로전자회로/chNN`
  - 기출: `python3 from_the_past/md/_tools/check_exam.py <시험 폴더>`
- `<<EXAM_NOTES>>`: 교과서면 빈 줄이다. 기출이면 아래 목록을 넣는다.
  - "원문은 한국어다. 인쇄된 글자만 옮기고 손글씨(풀이, 채점 표시, 동그라미)는 옮기지 않는다. 가려서 읽을 수 없는 글자는 `[판독 불가]`로 적는다."
  - "2021: `.txt` 글자 층에는 μ, λ, Ω가 빠져 있다. 이미지를 보고 채운다."
  - "2023 기말: `<<HWP_PAGES>>`의 hwp 변환 페이지를 글자 기준으로 쓰고, 스캔은 배치 확인용으로 쓴다."

## 부록 R — 리뷰어 지시

```
# 원문 리뷰 — <<LABEL>> 배치 <<BATCH>>

당신은 리뷰 에이전트다. 작업 폴더는 <<WT>>다. 먼저 교과서/마이크로전자회로/FORMAT.md '문제집용 절'을 읽는다(기출이면 FORMAT-EXAM.md도).

- 대상: <<TARGETS>> (커밋 <<COMMIT>>)
- 작성자가 판독이 애매하다고 한 곳 (특히 독립적으로 확인):
<<FLAGS>>

## 원칙
- 추적되는 파일을 고치지 않고 git 상태도 바꾸지 않는다. 만드는 파일은 보고서 <<REPORT>> 하나뿐이다(폴더가 없으면 만든다).
- 보고서는 <<REPORT>>.part에 쓰고, 다 마친 뒤 mv <<REPORT>>.part <<REPORT>> 한다.
- md를 먼저 믿지 않는다. python3 workbook/source_pages.py render <<TARGETS>> --out <<PAGES>>/review-<<BATCH>> --dpi 300 으로 직접 그리고, 원본을 먼저 읽은 뒤 md와 대조한다. OCR은 쓰지 않는다.
- md마다 확인할 것:
  1. 문장이 빠지거나 더해지지 않았는가 (범위: 예제는 풀이 앞, 장말문제는 번호 뺀 본문, 캡션·풀이·손글씨 제외)
  2. 수치, 단위, 첨자, 부호, 그리스 문자 (μ/λ/Ω, V⁻¹, k/M 접두어)
  3. 소문항 (a)(b)…/(1)(2)… 누락과 순서
  4. 인쇄 오식을 멋대로 고치지 않았는가 (고쳤으면 되돌리라고 지적)
  5. 문단 경계와 하이픈 붙이기
  6. 원문 안에 작성자 표시, *기울임*, ###, 이미지 줄이 없는가
  7. 원문과 ## 조건의 값이 어긋나는가 → 어느 쪽이 원본과 다른지
- 형식 검사를 한 번 돌린다: <<CHECK_CMD>>

## 보고서
# 원문 리뷰 <<BATCH>> — 커밋 <<COMMIT>> (<<TARGETS 요약>>)

방법: <dpi, 본 페이지, 형식 검사 결과>

## 작성자가 애매하다고 한 곳 — 독립 판독
- <항목>: 맞음 | 다름 (<원본 판독>)

### <id> — OK | 수정 필요
- [높음|중간|낮음] <체크 항목 번호>: md는 "…" / 원본은 "…" (근거: PDF p.N, 위치) → 고칠 내용

사실 오류(원본과 다름)와 표기 제안을 구분한다. 확신이 없으면 "불확실"로 표시한다. 최종 메시지에는 수정 필요한 개수를 요약한다.
```
