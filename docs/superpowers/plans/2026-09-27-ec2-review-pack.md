# 전자회로2 복습팩 스킬 (`ec2-review-pack`) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 머신러닝기초 `ml-review-pack`을 본떠, 전자회로2 수업 STT로 정리노트(HTML+MD)와 workbook 문제 약 10개짜리 복습문제 PDF(문제+답안)를 만드는 스킬을 전자회로2 저장소에 만든다.

**Architecture:**
- ML 스킬의 scripts와 tests를 `전자회로2/.claude/skills/ec2-review-pack/`으로 복사한다.
- 복습문제 HTML 경로(카드, review 템플릿, answers.py)는 뺀다.
- 그 자리에 workbook id 목록(`manifest.problems`)과 문제 목록 도구(`problem_index.py`)를 넣는다.
- PDF는 기존 `workbook/build_workbook.py --ids`가 만든다. 스킬 스크립트는 workbook을 고치지 않는다.

**Tech Stack:**
- Python 3 표준 라이브러리(unittest, html.parser)
- `problem_index.py`만 workbook의 `problem.py`(PyYAML)를 import한다.
- 서브에이전트 오케스트레이션은 SKILL.md의 절차로 한다.

**Spec:** `docs/superpowers/specs/2026-09-27-ec2-review-pack-design.md`

## Global Constraints
- 스킬 경로: `/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/.claude/skills/ec2-review-pack`(이하 `SKILL`). ML 원본 경로: `/Users/hyunjun_macbook_pro/Documents/Univ/머신러닝기초/.claude/skills/ml-review-pack`(이하 `ML`).
- `assets/note-template.html`은 `ML/assets/note-template.html`과 **바이트 단위로 같아야** 한다. 템플릿을 고치지 않는다.
- `ML/` 아래와 `workbook/` 아래 파일은 수정하지 않는다.
- 파일 이름:
  - 정리노트: `정리노트_<range>_<slug>.html` / `.md`
  - PDF: `복습문제_<range>_<slug>-문제.pdf`, `복습문제_<range>_<slug>-답안.pdf`
  - 문제 목록: `problems.txt`
- 문제 수:
  - 0~12개, 목표 10개
  - 구성: 예제 2~3, 연습·장말 5~6, 기출 1~2
  - 자작 문제 금지. workbook에 해당 범위 문제가 없으면 0개로 둔다(PDF 없음).
- `scripts/`는 표준 라이브러리만 쓴다. 예외는 `problem_index.py`의 workbook `problem.py` import이다.
- 사용자에게 보이는 글은 한국어, "~해요" 체로 쓰고 이모지는 쓰지 않는다. 스크립트 오류 메시지는 한국어.
- 스킬 파일(tests 제외)에 `MML`, `머신러닝`, `정방철`, `REVIEW_HREF`, `answers.py`, `card-rules`가 남으면 안 된다.
- 작업 브랜치는 `feat/ec2-review-pack`이다. 커밋 메시지 끝에는 다음 줄을 넣는다.
  ```
  Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
  ```
- 테스트 명령(저장소 루트에서):
  ```bash
  python3 -m unittest discover -s .claude/skills/ec2-review-pack/tests
  ```

## Review Focus
1. **문제 0개 팩**(0902–0904처럼 workbook 범위 밖): manifest, 조립, 검사, MD 변환이 PDF 없이 통과해야 한다. 같은 range에 예전 `problems.txt`가 있으면 지워야 한다(Task 1, 2, 3, 4에 테스트).
2. **NFD 한글이 섞인 id**(`2023-1_기말-Q1`을 NFD로 쓴 경우, NFD로 저장된 `problems.txt`): NFC로 맞춰 인식해야 한다(Task 1, 5에 테스트).
3. **PDF 빌드 실패로 PDF가 없는데 노트가 링크하는 경우**: check_html이 `broken-link`로 잡아야 한다(Task 3에 테스트).
4. **같은 range 재실행**: 백업에 PDF와 `problems.txt`도 들어가야 한다(Task 7에 테스트).
5. **html2md가 PDF 링크를 `.md`로 바꾸거나 없는 파일로 판정하는 경우**: PDF 링크는 그대로 두고 통과해야 한다(Task 4에 테스트).

---

## File Structure
```
.claude/skills/ec2-review-pack/
  SKILL.md                         Task 7
  assets/note-template.html        Task 1 (ML에서 복사, 수정 금지)
  scripts/manifest.py              Task 1
  scripts/assemble.py              Task 2
  scripts/check_html.py            Task 3
  scripts/html2md.py               Task 4
  scripts/problem_index.py         Task 5
  references/stt-summary-prompt.md Task 6
  references/manifest-guide.md     Task 6
  references/content-rules.md      Task 6
  references/widget-rules.md       Task 6
  references/problem-selection.md  Task 6
  references/review-prompt.md      Task 6
  references/browser-check.md      Task 6
  tests/_util.py                   Task 1
  tests/fixtures/mini-run/manifest.json, sections/s1.html, sections/s2.html   Task 1
  tests/test_manifest.py           Task 1
  tests/test_assemble.py           Task 2
  tests/test_check_html.py         Task 3
  tests/test_html2md.py            Task 4
  tests/test_problem_index.py      Task 5
  tests/test_skill_files.py        Task 6(참조 문서 검사), Task 7(SKILL.md·백업 스니펫)
```

---

### Task 0: 브랜치

- [ ] **Step 1: 브랜치 만들기**

```bash
cd /Users/hyunjun_macbook_pro/Documents/Univ/전자회로2 && git switch -c feat/ec2-review-pack
```
Expected: `Switched to a new branch 'feat/ec2-review-pack'`

---

### Task 1: 뼈대, 템플릿, manifest 규약

**Files:**
- Create: `SKILL/assets/note-template.html` (ML에서 복사)
- Create: `SKILL/scripts/manifest.py` (ML에서 복사 후 수정)
- Create: `SKILL/tests/_util.py`, `SKILL/tests/fixtures/mini-run/{manifest.json,sections/s1.html,sections/s2.html}`
- Test: `SKILL/tests/test_manifest.py`

**Interfaces:**
- Produces (`manifest.py`):
  - `validate(m: dict, repo: Path | str | None = None) -> list[str]`
  - `load(path, repo=None) -> dict`(오류가 있으면 `ManifestError`)
  - `problem_kind(pid: str) -> str | None`
  - `problem_md_path(repo, pid: str) -> Path`
  - `note_name(m) -> str`
  - `problem_set_name(m) -> str`
  - `problem_pdf_name(m) -> str`
  - `answer_pdf_name(m) -> str`
  - `fig_dir_name(range_) -> str`
  - 상수: `PROBLEMS_TXT = "problems.txt"`, `MAX_PROBLEMS = 12`
  - CLI: `manifest.py MANIFEST [REPO]`
- Produces (`tests/_util.py`): `TESTS, SKILL, SCRIPTS, FIXTURES, MINI_RUN, REPO, ML_SKILL, find_nfc(directory, name)`

- [ ] **Step 1: 복사**

```bash
SKILL=/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/.claude/skills/ec2-review-pack
ML=/Users/hyunjun_macbook_pro/Documents/Univ/머신러닝기초/.claude/skills/ml-review-pack
mkdir -p "$SKILL"/{assets,scripts,references,tests/fixtures/mini-run/sections}
cp "$ML/assets/note-template.html" "$SKILL/assets/"
cp "$ML/scripts/manifest.py" "$SKILL/scripts/"
cp "$ML/tests/fixtures/mini-run/sections/s1.html" "$SKILL/tests/fixtures/mini-run/sections/"
cmp "$ML/assets/note-template.html" "$SKILL/assets/note-template.html" && echo SAME
```
Expected: `SAME`

- [ ] **Step 2: `tests/_util.py` 작성**

```python
"""스킬 테스트 공통 경로·도우미."""

from __future__ import annotations

import os
from pathlib import Path
import sys
import unicodedata

TESTS = Path(__file__).resolve().parent
SKILL = TESTS.parent
SCRIPTS = SKILL / "scripts"
FIXTURES = TESTS / "fixtures"
MINI_RUN = FIXTURES / "mini-run"
REPO = SKILL.parents[2]  # <repo>/.claude/skills/ec2-review-pack
# 템플릿 원본(머신러닝기초 저장소). 없으면 비교 테스트를 건너뛴다.
ML_SKILL = REPO.parent / "머신러닝기초" / ".claude" / "skills" / "ml-review-pack"
sys.path.insert(0, str(SCRIPTS))


def find_nfc(directory: Path, name: str) -> Path | None:
    """macOS NFD 파일명을 NFC 이름으로 찾는다."""
    if not directory.is_dir():
        return None
    for entry in os.listdir(directory):
        if unicodedata.normalize("NFC", entry) == name:
            return directory / entry
    return None
```

- [ ] **Step 3: 픽스처 `tests/fixtures/mini-run/manifest.json` 작성**

```json
{
 "course": "전자회로2",
 "range": "0101-0102",
 "slug": "Mini_Test",
 "note_title": "Mini — 테스트 정리노트",
 "note_subtitle": "테스트용 · 0101 수업",
 "footer_note": "출처: 테스트 픽스처",
 "sessions": [{"date": "0101", "stt": "STT/0101 전회2.md", "summary": "summaries/stt-0101.md", "slides": "L03 s1–2"}],
 "sections": [
  {"id": "s1", "title": "1. 기초 통계", "short": "1 기초", "topics": [
   {"id": "s1-mean", "title": "평균", "required_terms": ["\\bar{x} = \\frac{1}{N}\\sum_{n=1}^{N} x_n", "무게중심"], "layers": ["eli5", "formal", "prof"], "supp": false},
   {"id": "s1-var", "title": "분산", "required_terms": ["\\sigma^2"], "layers": ["eli5", "formal", "prof"], "supp": true}
  ]},
  {"id": "s2", "title": "2. 요약 · 예고", "short": "2 요약·예고", "topics": [
   {"id": "s2-next", "title": "다음 시간 예고", "required_terms": ["d-separation"], "layers": [], "supp": false},
   {"id": "s2-links", "title": "함께 보면 좋은 자료", "required_terms": ["복습문제"], "layers": [], "supp": false}
  ]}
 ],
 "preview_topic": "s2-next",
 "forbidden_outside_preview": ["d-separation"],
 "problems": [
  {"id": "P9.01", "kind": "장말문제", "anchor": "s1-mean", "date": "0101", "why": "테스트용 장말문제"},
  {"id": "2023-1_기말-Q1", "kind": "기출", "anchor": "s1-var", "date": "0101", "why": "테스트용 기출"}
 ],
 "links": [
  {"topic": "s2-links", "href": "복습문제_0101-0102_Mini_Test-문제.pdf"},
  {"topic": "s2-links", "href": "복습문제_0101-0102_Mini_Test-답안.pdf"}
 ]
}
```

- [ ] **Step 4: 픽스처 `tests/fixtures/mini-run/sections/s2.html` 작성**

```html
      <article class="topic" id="s2-next"><h3>다음 시간 예고</h3>
        <ul><li>d-separation</li></ul>
      </article>
      <article class="topic" id="s2-links"><h3>함께 보면 좋은 자료</h3>
        <ul><li><a href="{{PROBLEM_PDF}}">복습문제 PDF</a></li><li><a href="{{ANSWER_PDF}}">복습문제 답안 PDF</a></li></ul>
      </article>
```

- [ ] **Step 5: 실패하는 테스트 작성 `tests/test_manifest.py`**

```python
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unicodedata
import unittest

from _util import MINI_RUN, REPO

import manifest

HAS_WORKBOOK = (REPO / "workbook" / "build_workbook.py").exists()


def mini() -> dict:
    return json.loads((MINI_RUN / "manifest.json").read_text(encoding="utf-8"))


class TestManifest(unittest.TestCase):
    def test_mini_manifest_is_valid(self):
        self.assertEqual(manifest.validate(mini()), [])

    def test_missing_top_level_key(self):
        m = mini()
        del m["problems"]
        self.assertIn("manifest.problems: list 필요", manifest.validate(m))

    def test_review_keys_are_not_required(self):
        # 복습문제 HTML이 없으므로 ML의 review_* / parts 키는 요구하지 않는다.
        for key in ("review_title", "review_intro", "footer_review", "parts"):
            self.assertNotIn(key, manifest.TOP_LEVEL_TYPES)

    def test_bad_range_and_slug(self):
        m = mini()
        m["range"], m["slug"] = "9/21", "한글"
        errors = manifest.validate(m)
        self.assertTrue(any(e.startswith("manifest.range") for e in errors))
        self.assertTrue(any(e.startswith("manifest.slug") for e in errors))

    def test_duplicate_topic_id(self):
        m = mini()
        m["sections"][0]["topics"][1]["id"] = "s1-mean"
        self.assertTrue(any("중복 id: s1-mean" in e for e in manifest.validate(m)))

    def test_unknown_layer(self):
        m = mini()
        m["sections"][0]["topics"][0]["layers"].append("fun")
        self.assertTrue(any("알 수 없는 레이어" in e for e in manifest.validate(m)))

    def test_preview_topic_must_exist(self):
        m = copy.deepcopy(mini())
        m["preview_topic"] = "s9"
        self.assertIn("preview_topic: 토픽 id가 아님: s9", manifest.validate(m))

    def test_problem_anchor_must_be_topic(self):
        m = mini()
        m["problems"][0]["anchor"] = "s9-nope"
        self.assertIn("problems[0].anchor: 없는 토픽: s9-nope", manifest.validate(m))

    def test_problem_id_format(self):
        for bad in ("P9.1", "Q9.01", "2023-1_기말-Q0", "2023-3_기말-Q1", "p9.01"):
            with self.subTest(bad=bad):
                m = mini()
                m["problems"][0]["id"] = bad
                self.assertIn(f"problems[0].id: workbook id 형식 오류: {bad}", manifest.validate(m))

    def test_problem_kind_must_match_id(self):
        m = mini()
        m["problems"][0]["kind"] = "예제"
        self.assertIn("problems[0].kind: P9.01는 장말문제", manifest.validate(m))

    def test_problem_kind_of_each_prefix(self):
        self.assertEqual(manifest.problem_kind("E10.03"), "예제")
        self.assertEqual(manifest.problem_kind("X11.12"), "연습문제")
        self.assertEqual(manifest.problem_kind("P9.40"), "장말문제")
        self.assertEqual(manifest.problem_kind("2021-1_중간-Q7"), "기출")
        self.assertIsNone(manifest.problem_kind("E10.3"))

    def test_nfd_exam_id_is_accepted(self):
        m = mini()
        m["problems"][1]["id"] = unicodedata.normalize("NFD", "2023-1_기말-Q1")
        self.assertEqual(manifest.validate(m), [])

    def test_duplicate_problem(self):
        m = mini()
        m["problems"][1] = dict(m["problems"][0])
        self.assertIn("problems[1].id: 중복 문제: P9.01", manifest.validate(m))

    def test_problem_date_and_why(self):
        m = mini()
        m["problems"][0]["date"] = "9/23"
        m["problems"][0]["why"] = "  "
        errors = manifest.validate(m)
        self.assertIn("problems[0].date: MMDD 형식이어야 함: 9/23", errors)
        self.assertIn("problems[0].why: 빈 문자열", errors)

    def test_too_many_problems(self):
        m = mini()
        m["problems"] = [{"id": f"P9.{i:02d}", "kind": "장말문제", "anchor": "s1-mean", "date": "0101", "why": "x"}
                         for i in range(1, 14)]
        self.assertIn("problems: 최대 12개 (13개)", manifest.validate(m))

    def test_pdf_links_required_when_problems(self):
        m = mini()
        m["links"] = m["links"][:1]
        self.assertIn("links: 복습문제 PDF 링크 필요: 복습문제_0101-0102_Mini_Test-답안.pdf", manifest.validate(m))

    def test_zero_problems_is_valid_without_pdf_links(self):
        m = mini()
        m["problems"], m["links"] = [], []
        self.assertEqual(manifest.validate(m), [])

    def test_zero_problems_rejects_pdf_links(self):
        m = mini()
        m["problems"] = []
        errors = manifest.validate(m)
        self.assertIn("links: 문제가 0개인데 PDF 링크가 있음: 복습문제_0101-0102_Mini_Test-문제.pdf", errors)

    def test_repo_check_finds_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            errors = manifest.validate(mini(), repo=tmp)
        self.assertTrue(any(e.startswith("problems[0].id: 문제 파일 없음:") for e in errors), errors)

    @unittest.skipUnless(HAS_WORKBOOK, "workbook 없음")
    def test_repo_check_passes_on_real_repo(self):
        self.assertEqual(manifest.validate(mini(), repo=REPO), [])

    def test_problem_md_path(self):
        repo = Path("/r")
        self.assertEqual(manifest.problem_md_path(repo, "E10.03"), repo / "교과서/마이크로전자회로/ch10/예제/E10.03.md")
        self.assertEqual(manifest.problem_md_path(repo, "2023-1_기말-Q1"), repo / "from_the_past/md/2023-1_기말/Q1.md")
        with self.assertRaises(ValueError):
            manifest.problem_md_path(repo, "nope")

    def test_load_raises_on_invalid(self):
        m = mini()
        m["problems"][0]["kind"] = "기출"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(manifest.ManifestError) as cm:
                manifest.load(path)
        self.assertIn("problems[0].kind: P9.01는 장말문제", str(cm.exception))

    def test_cli(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(manifest.main([str(MINI_RUN / "manifest.json")]), 0)
        self.assertEqual(out.getvalue().strip(), "OK")

    def test_cli_with_missing_repo_file_exits_1(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(manifest.main([str(MINI_RUN / "manifest.json"), tmp]), 1)
        self.assertIn("문제 파일 없음", out.getvalue())

    def test_non_dict_top_level(self):
        for value in ([], "x", 3, None):
            self.assertEqual(manifest.validate(value), ["manifest: JSON 객체 필요"])

    def test_non_dict_list_item_is_reported_and_skipped(self):
        m = mini()
        m["problems"].insert(0, "oops")
        m["sessions"].append(7)
        errors = manifest.validate(m)
        self.assertIn("problems[0]: 객체 필요", errors)
        self.assertIn(f"sessions[{len(m['sessions']) - 1}]: 객체 필요", errors)

    def test_non_string_layer_is_reported(self):
        m = mini()
        m["sections"][0]["topics"][0]["layers"].append(["eli5"])
        self.assertTrue(any("layers" in e for e in manifest.validate(m)))

    def test_load_invalid_json_raises_manifest_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            path.write_text("{not json", encoding="utf-8")
            with self.assertRaises(manifest.ManifestError):
                manifest.load(path)
            with self.assertRaises(manifest.ManifestError):
                manifest.load(Path(tmp) / "missing.json")

    def test_cli_invalid_manifest_exits_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "manifest.json"
            bad.write_text("[]", encoding="utf-8")
            for arg in (bad, Path(tmp) / "missing.json"):
                with contextlib.redirect_stdout(io.StringIO()) as out, \
                        contextlib.redirect_stderr(io.StringIO()) as err:
                    self.assertEqual(manifest.main([str(arg)]), 1)
                self.assertTrue(out.getvalue().strip())
                self.assertNotIn("Traceback", out.getvalue() + err.getvalue())

    def test_cli_usage_exits_2(self):
        for argv in ([], ["a", "b", "c"]):
            with contextlib.redirect_stdout(io.StringIO()), \
                    contextlib.redirect_stderr(io.StringIO()) as err:
                self.assertEqual(manifest.main(argv), 2)
            self.assertIn("사용법", err.getvalue())

    def test_term_lists_require_nonempty_strings(self):
        for bad in (0.2, 3, None, "", ["x"]):
            with self.subTest(bad=bad):
                m = mini()
                m["sections"][0]["topics"][0]["required_terms"].append(bad)
                m["forbidden_outside_preview"].append(bad)
                errors = manifest.validate(m)
                for where in ("sections[0].topics[0].required_terms[", "forbidden_outside_preview["):
                    self.assertTrue(any(e.startswith(where) and "빈 문자열이 아닌 문자열 필요" in e for e in errors), (where, errors))

    def test_names(self):
        m = mini()
        self.assertEqual(manifest.note_name(m), "정리노트_0101-0102_Mini_Test.html")
        self.assertEqual(manifest.problem_set_name(m), "복습문제_0101-0102_Mini_Test")
        self.assertEqual(manifest.problem_pdf_name(m), "복습문제_0101-0102_Mini_Test-문제.pdf")
        self.assertEqual(manifest.answer_pdf_name(m), "복습문제_0101-0102_Mini_Test-답안.pdf")
        self.assertEqual(manifest.fig_dir_name("0101-0102"), "figures_0101-0102")
        self.assertEqual(manifest.PROBLEMS_TXT, "problems.txt")
        self.assertFalse(hasattr(manifest, "review_name"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 6: 실패 확인**

Run: `python3 -m unittest discover -s .claude/skills/ec2-review-pack/tests -p test_manifest.py`
Expected: FAIL. 이유는 `problem_kind` 없음, `review_title`/`parts` 키 요구 등이다.

- [ ] **Step 7: `scripts/manifest.py` 수정**

(a) 모듈 docstring의 CLI 줄을 다음으로 바꾼다.
```
CLI: manifest.py RUN/manifest.json [REPO]   (검증만. REPO를 주면 문제 md가 있는지도 본다. 오류가 있으면 목록 출력 후 종료 코드 1)
```
(b) `import sys` 다음 줄에 `import unicodedata`를 추가한다.

(c) `TOP_LEVEL_TYPES`부터 `ID_RE` 정의까지를 다음으로 바꾼다.
```python
TOP_LEVEL_TYPES = {
    "course": str, "range": str, "slug": str,
    "note_title": str, "note_subtitle": str, "footer_note": str,
    "sessions": list, "sections": list, "preview_topic": str, "forbidden_outside_preview": list,
    "problems": list, "links": list,
}
RANGE_RE = re.compile(r"\d{4}(-\d{4})?")
SLUG_RE = re.compile(r"[A-Za-z0-9_]+")
ID_RE = re.compile(r"[A-Za-z][A-Za-z0-9-]*")
DATE_RE = re.compile(r"\d{4}")
# workbook/assemble.py의 TEXTBOOK_ID_RE·EXAM_ID_RE·KIND_DIR와 같은 규칙
TEXTBOOK_ID_RE = re.compile(r"([EXP])(\d+)\.(\d{2})")
EXAM_ID_RE = re.compile(r"(\d{4}-[12]_(?:중간|기말))-Q([1-9]\d*)")
KIND_BY_PREFIX = {"E": "예제", "X": "연습문제", "P": "장말문제"}
MAX_PROBLEMS = 12
PROBLEMS_TXT = "problems.txt"
```
(d) `_objects` 함수 바로 뒤에 다음을 추가한다.
```python
def _nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def problem_kind(pid: str) -> str | None:
    """workbook id의 종류(예제/연습문제/장말문제/기출). 형식이 틀리면 None."""
    pid = _nfc(pid)
    if m := TEXTBOOK_ID_RE.fullmatch(pid):
        return KIND_BY_PREFIX[m.group(1)]
    if EXAM_ID_RE.fullmatch(pid):
        return "기출"
    return None


def problem_md_path(repo: Path | str, pid: str) -> Path:
    """workbook id → 문제 md 경로 (workbook/assemble.py ids_selection과 같은 규칙)."""
    repo, pid = Path(repo), _nfc(pid)
    if m := TEXTBOOK_ID_RE.fullmatch(pid):
        return repo / "교과서" / "마이크로전자회로" / f"ch{int(m.group(2)):02d}" / KIND_BY_PREFIX[m.group(1)] / f"{pid}.md"
    if m := EXAM_ID_RE.fullmatch(pid):
        return repo / "from_the_past" / "md" / m.group(1) / f"Q{m.group(2)}.md"
    raise ValueError(f"workbook id 형식 오류: {pid}")
```
(e) `def validate(m: dict) -> list[str]:`를 `def validate(m: dict, repo: Path | str | None = None) -> list[str]:`로 바꾼다.

(f) `validate` 안에서 `part_ids: set[str] = set()`부터 함수 끝 `return errors` 직전까지(parts, problems, links 블록)를 다음으로 바꾼다.
```python
    pids: set[str] = set()
    for i, q in _objects(m["problems"], "problems", errors):
        where = f"problems[{i}]"
        if not all([_need(q, key, str, where, errors) for key in ("id", "kind", "anchor", "date", "why")]):
            continue
        pid = _nfc(q["id"])
        kind = problem_kind(pid)
        if kind is None:
            errors.append(f"{where}.id: workbook id 형식 오류: {q['id']}")
        elif q["kind"] != kind:
            errors.append(f"{where}.kind: {pid}는 {kind}")
        elif repo is not None and not problem_md_path(repo, pid).is_file():
            errors.append(f"{where}.id: 문제 파일 없음: {problem_md_path(repo, pid)}")
        if pid in pids:
            errors.append(f"{where}.id: 중복 문제: {pid}")
        pids.add(pid)
        if q["anchor"] not in topic_ids:
            errors.append(f"{where}.anchor: 없는 토픽: {q['anchor']}")
        if not DATE_RE.fullmatch(q["date"]):
            errors.append(f"{where}.date: MMDD 형식이어야 함: {q['date']}")
        if not q["why"].strip():
            errors.append(f"{where}.why: 빈 문자열")
    if len(m["problems"]) > MAX_PROBLEMS:
        errors.append(f"problems: 최대 {MAX_PROBLEMS}개 ({len(m['problems'])}개)")

    hrefs: set[str] = set()
    for i, link in _objects(m["links"], "links", errors):
        where = f"links[{i}]"
        if _need(link, "topic", str, where, errors) and link["topic"] not in topic_ids:
            errors.append(f"{where}.topic: 없는 토픽: {link['topic']}")
        if _need(link, "href", str, where, errors):
            hrefs.add(link["href"])
    pdfs = {problem_pdf_name(m), answer_pdf_name(m)}
    if m["problems"]:
        errors += [f"links: 복습문제 PDF 링크 필요: {name}" for name in sorted(pdfs - hrefs)]
    else:
        errors += [f"links: 문제가 0개인데 PDF 링크가 있음: {name}" for name in sorted(pdfs & hrefs)]
```
(g) `load`를 다음으로 바꾼다.
```python
def load(path: Path | str, repo: Path | str | None = None) -> dict:
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise ManifestError(f"{path}: 파일을 읽을 수 없음: {e}") from e
    try:
        m = json.loads(text)
    except json.JSONDecodeError as e:
        raise ManifestError(f"{path}: JSON 형식 오류: {e}") from e
    errors = validate(m, repo)
    if errors:
        raise ManifestError("\n".join(errors))
    return m
```
(h) `review_name`을 지우고 이름 함수를 다음으로 둔다(`note_name`, `fig_dir_name`은 그대로).
```python
def problem_set_name(m: dict) -> str:
    """build_workbook.py --name 값. PDF는 이 이름 + '-문제.pdf' / '-답안.pdf'."""
    return f"복습문제_{m['range']}_{m['slug']}"


def problem_pdf_name(m: dict) -> str:
    return f"{problem_set_name(m)}-문제.pdf"


def answer_pdf_name(m: dict) -> str:
    return f"{problem_set_name(m)}-답안.pdf"
```
(i) `main`을 다음으로 바꾼다.
```python
def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) not in (1, 2):
        print("사용법: manifest.py RUN/manifest.json [REPO]", file=sys.stderr)
        return 2
    try:
        load(argv[0], argv[1] if len(argv) == 2 else None)
    except ManifestError as e:
        print(e)
        return 1
    print("OK")
    return 0
```

- [ ] **Step 8: 통과 확인**

Run: `python3 -m unittest discover -s .claude/skills/ec2-review-pack/tests -p test_manifest.py`
Expected: `OK`

- [ ] **Step 9: 커밋**

```bash
git add .claude/skills/ec2-review-pack/assets .claude/skills/ec2-review-pack/scripts/manifest.py .claude/skills/ec2-review-pack/tests
git commit -m "feat(ec2-review-pack): add manifest contract with workbook problem ids

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: 조립기 (정리노트 + problems.txt)

**Files:**
- Create: `SKILL/scripts/assemble.py`
- Test: `SKILL/tests/test_assemble.py`

**Interfaces:**
- Consumes: `manifest.load`, `note_name`, `problem_pdf_name`, `answer_pdf_name`, `PROBLEMS_TXT`
- Produces:
  - `assemble(run_dir, out_dir) -> Path`(정리노트 경로)
  - `AssembleError`
  - `fill(template, values) -> str`
  - `problems_txt(m) -> str`
  - 조각 토큰: `{{NOTE_HREF}}`, `{{PROBLEM_PDF}}`, `{{ANSWER_PDF}}`
  - CLI: `assemble.py --run RUN --out DIR`

- [ ] **Step 1: 실패하는 테스트 작성 `tests/test_assemble.py`**

```python
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from _util import ML_SKILL, MINI_RUN, SKILL

import assemble


class TestAssemble(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.note = assemble.assemble(MINI_RUN, self.tmp)
        self.html = self.note.read_text(encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def copy_run(self) -> Path:
        run = self.tmp / "run"
        shutil.copytree(MINI_RUN, run)
        return run

    def test_output_name(self):
        self.assertEqual(self.note.name, "정리노트_0101-0102_Mini_Test.html")

    def test_only_note_is_written(self):
        self.assertEqual(sorted(p.name for p in self.tmp.iterdir()), ["problems.txt", "정리노트_0101-0102_Mini_Test.html"])

    def test_sections_toc_and_titles(self):
        self.assertIn('<nav class="toc" aria-label="목차"><a href="#s1">1 기초</a><a href="#s2">2 요약·예고</a></nav>', self.html)
        self.assertIn('<section id="s1"><h2>1. 기초 통계</h2>', self.html)
        self.assertIn("<h1>Mini — 테스트 정리노트</h1>", self.html)
        self.assertIn("<title>전자회로2 정리노트 0101-0102</title>", self.html)

    def test_scripts_moved_after_main(self):
        self.assertGreater(self.html.index('<script id="widget-mean-ui">'), self.html.index("</main>"))

    def test_pdf_tokens_replaced_and_no_slots_left(self):
        self.assertIn('href="복습문제_0101-0102_Mini_Test-문제.pdf"', self.html)
        self.assertIn('href="복습문제_0101-0102_Mini_Test-답안.pdf"', self.html)
        self.assertNotIn("{{", self.html)

    def test_progress_key_and_theme(self):
        self.assertIn('data-range="0101-0102"', self.html)
        self.assertIn("const KEY = 'od-note-read:' + RANGE;", self.html)
        self.assertIn('id="theme-toggle"', self.html)
        self.assertIn("localStorage.getItem('od-theme')", self.html.split("</head>", 1)[0])

    @unittest.skipUnless((ML_SKILL / "assets" / "note-template.html").exists(), "ML 스킬 없음")
    def test_template_is_identical_to_ml(self):
        ours = (SKILL / "assets" / "note-template.html").read_bytes()
        self.assertEqual(ours, (ML_SKILL / "assets" / "note-template.html").read_bytes())

    def test_problems_txt(self):
        self.assertEqual((self.tmp / "problems.txt").read_text(encoding="utf-8"),
                         "P9.01 | 테스트용 장말문제\n2023-1_기말-Q1 | 테스트용 기출\n")

    def test_zero_problems_removes_stale_problems_txt(self):
        run = self.copy_run()
        m = json.loads((run / "manifest.json").read_text(encoding="utf-8"))
        m["problems"], m["links"] = [], []
        (run / "manifest.json").write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8")
        assemble.assemble(run, self.tmp)
        self.assertFalse((self.tmp / "problems.txt").exists())

    def test_missing_fragment_writes_nothing(self):
        run = self.copy_run()
        (run / "sections" / "s2.html").unlink()
        out = self.tmp / "out"
        with self.assertRaises(assemble.AssembleError):
            assemble.assemble(run, out)
        self.assertFalse(out.exists())
        before = self.note.read_bytes()
        with self.assertRaises(assemble.AssembleError):
            assemble.assemble(run, self.tmp)
        self.assertEqual(self.note.read_bytes(), before)

    def test_fill_rejects_missing_slot(self):
        with self.assertRaises(assemble.AssembleError):
            assemble.fill("<p>{{NOPE}}</p>", {})

    def test_fill_does_not_expand_slots_inside_values(self):
        self.assertEqual(assemble.fill("{{A}}", {"A": "{{B}}"}), "{{B}}")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 실패 확인**

Run: `python3 -m unittest discover -s .claude/skills/ec2-review-pack/tests -p test_assemble.py`
Expected: FAIL (`ModuleNotFoundError: No module named 'assemble'`)

- [ ] **Step 3: `scripts/assemble.py` 작성**

```python
#!/usr/bin/env python3
"""
manifest + 섹션 조각 → 정리노트 HTML (표준 라이브러리만 사용).

실행 폴더 구조:
  RUN/manifest.json
  RUN/sections/<section-id>.html   (섹션 안쪽: <article class="topic"> 들, <script> 가능)
조각 안의 {{NOTE_HREF}} / {{PROBLEM_PDF}} / {{ANSWER_PDF}} 는 실제 파일명으로 바뀐다.
<script> 블록은 조각에서 빼서 </body> 앞({{SCRIPTS}})으로 모은다.
문제가 있으면 같은 폴더에 problems.txt(`id | why` 한 줄씩)를 쓰고, 없으면 예전 problems.txt를 지운다.
CLI: assemble.py --run RUN --out 복습노트/<range>
"""

from __future__ import annotations

import argparse
import html
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import manifest as manifest_mod  # noqa: E402

ASSETS = Path(__file__).resolve().parent.parent / "assets"
SLOT_RE = re.compile(r"\{\{([A-Z_]+)\}\}")
SCRIPT_RE = re.compile(r"<script\b[^>]*>.*?</script>", re.S | re.I)


class AssembleError(RuntimeError):
    pass


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def fill(template: str, values: dict[str, str]) -> str:
    missing = sorted(set(SLOT_RE.findall(template)) - values.keys())
    if missing:
        raise AssembleError(f"템플릿 슬롯 값 없음: {missing}")
    return SLOT_RE.sub(lambda mo: values[mo.group(1)], template)


def split_scripts(fragment: str) -> tuple[str, list[str]]:
    scripts = SCRIPT_RE.findall(fragment)
    return SCRIPT_RE.sub("", fragment), scripts


def read_fragment(path: Path, m: dict) -> str:
    if not path.exists():
        raise AssembleError(f"조각 파일 없음: {path}")
    text = path.read_text(encoding="utf-8")
    for token, value in (("{{NOTE_HREF}}", manifest_mod.note_name(m)),
                         ("{{PROBLEM_PDF}}", manifest_mod.problem_pdf_name(m)),
                         ("{{ANSWER_PDF}}", manifest_mod.answer_pdf_name(m))):
        text = text.replace(token, value)
    return text


def build_note(m: dict, run_dir: Path) -> str:
    sections, scripts = [], []
    for sec in m["sections"]:
        body, found = split_scripts(read_fragment(run_dir / "sections" / f"{sec['id']}.html", m))
        scripts += found
        sections.append(f'    <section id="{sec["id"]}"><h2>{esc(sec["title"])}</h2>\n{body.strip()}\n    </section>')
    return fill((ASSETS / "note-template.html").read_text(encoding="utf-8"), {
        "PAGE_TITLE": esc(f"전자회로2 정리노트 {m['range']}"),
        "DESCRIPTION": esc(m["note_subtitle"]),
        "TOC": "".join(f'<a href="#{s["id"]}">{esc(s["short"])}</a>' for s in m["sections"]),
        "TITLE": esc(m["note_title"]),
        "SUBTITLE": esc(m["note_subtitle"]),
        "SECTIONS": "\n".join(sections),
        "FOOTER": m["footer_note"],
        "SCRIPTS": "\n".join(f"  {s}" for s in scripts),
        "RANGE": m["range"],
    })


def problems_txt(m: dict) -> str:
    return "".join(f"{q['id']} | {q['why']}\n" for q in m["problems"])


def assemble(run_dir: Path | str, out_dir: Path | str) -> Path:
    run_dir, out_dir = Path(run_dir), Path(out_dir)
    m = manifest_mod.load(run_dir / "manifest.json")
    note_html = build_note(m, run_dir)  # 조각이 하나라도 없으면 아무것도 쓰지 않는다
    out_dir.mkdir(parents=True, exist_ok=True)
    note_path = out_dir / manifest_mod.note_name(m)
    note_path.write_text(note_html, encoding="utf-8")
    listing = out_dir / manifest_mod.PROBLEMS_TXT
    if m["problems"]:
        listing.write_text(problems_txt(m), encoding="utf-8")
    elif listing.exists():
        listing.unlink()
    return note_path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    try:
        print(assemble(args.run, args.out))
    except (AssembleError, manifest_mod.ManifestError) as e:
        print(f"assemble 실패: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: 통과 확인**

Run: `python3 -m unittest discover -s .claude/skills/ec2-review-pack/tests -p test_assemble.py`
Expected: `OK`

- [ ] **Step 5: 커밋**

```bash
git add .claude/skills/ec2-review-pack/scripts/assemble.py .claude/skills/ec2-review-pack/tests/test_assemble.py
git commit -m "feat(ec2-review-pack): assemble note and problems.txt

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: HTML 검사기 (정리노트만)

**Files:**
- Create: `SKILL/scripts/check_html.py` (ML에서 복사 후 수정)
- Test: `SKILL/tests/test_check_html.py`

**Interfaces:**
- Consumes: `assemble.assemble`, `manifest.problem_pdf_name/answer_pdf_name`
- Produces:
  - `check_pack(m, note_path) -> list[Problem]`
  - `check_file(path)`, `check_common(doc, source, path)`, `parse_html(src)`, `math_delimiter_errors(text)`
  - CLI: `check_html.py --manifest M --note NOTE.html` / `check_html.py FILE…`. 출력 끝줄은 `OK` 또는 `FAIL (n)`

- [ ] **Step 1: 복사**

```bash
cp /Users/hyunjun_macbook_pro/Documents/Univ/머신러닝기초/.claude/skills/ml-review-pack/scripts/check_html.py /Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/.claude/skills/ec2-review-pack/scripts/
```

- [ ] **Step 2: 실패하는 테스트 작성 `tests/test_check_html.py`**

```python
import contextlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from _util import MINI_RUN

import assemble
import check_html
import manifest


class TestPrimitives(unittest.TestCase):
    def test_adjacent_inline_math_in_list_items_is_not_display_math(self):
        doc = check_html.parse_html('<html lang="ko"><body><ol><li>$a$</li><li>$b$</li></ol></body></html>')
        self.assertEqual(check_html.math_delimiter_errors(doc.body_text), [])

    def test_unbalanced_inline_math(self):
        self.assertEqual(check_html.math_delimiter_errors("a $x b"), ["unbalanced $ (inline math)"])

    def test_widget_without_static(self):
        src = '<html lang="ko"><body><div class="widget" id="w1"><h4>x</h4></div></body></html>'
        problems = check_html.check_common(check_html.parse_html(src), src, Path("x.html"))
        self.assertEqual([p.code for p in problems], ["widget-static-missing"])

    def test_leftover_slot_and_external(self):
        src = '<html lang="ko"><head><script src="https://cdn.tailwindcss.com"></script></head><body>{{TOC}}</body></html>'
        codes = sorted(p.code for p in check_html.check_common(check_html.parse_html(src), src, Path("x.html")))
        self.assertEqual(codes, ["external", "leftover-slot"])

    def test_no_review_checker_left(self):
        self.assertFalse(hasattr(check_html, "check_review"))


class TestPack(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.run = self.tmp / "run"
        shutil.copytree(MINI_RUN, self.run)
        self.out = self.tmp / "out"

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def m(self) -> dict:
        return json.loads((self.run / "manifest.json").read_text(encoding="utf-8"))

    def build(self) -> Path:
        note = assemble.assemble(self.run, self.out)
        m = self.m()
        if m["problems"]:  # 실제로는 build_workbook.py가 만든다
            for name in (manifest.problem_pdf_name(m), manifest.answer_pdf_name(m)):
                (self.out / name).write_bytes(b"%PDF-1.4\n")
        return note

    def codes(self, note: Path | None = None) -> list[str]:
        note = note or self.build()
        return sorted(p.code for p in check_html.check_pack(self.m(), note))

    def edit(self, rel: str, old: str, new: str):
        path = self.run / rel
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text)
        path.write_text(text.replace(old, new), encoding="utf-8")

    def test_mini_pack_passes(self):
        self.assertEqual(self.codes(), [])

    def test_missing_required_term(self):
        self.edit("sections/s1.html", "무게중심", "가운데")
        self.assertEqual(self.codes(), ["missing-term"])

    def test_forbidden_term_outside_preview(self):
        self.edit("sections/s1.html", "분산은 흩어진 정도예요.", "분산은 d-separation과 무관해요.")
        self.assertEqual(self.codes(), ["forbidden-term"])

    def test_missing_layer(self):
        self.edit("sections/s1.html", '<div class="layer prof"><span class="layer-title">교수님 말씀</span><p>"평균부터 봐요." (0101 01:00)</p></div>', "")
        self.assertEqual(self.codes(), ["missing-layer"])

    def test_missing_supp_badge(self):
        self.edit("sections/s1.html", '<span class="badge supp">보충 · 수업에서 유도하진 않았어요</span>', "")
        self.assertEqual(self.codes(), ["missing-supp"])

    def test_missing_sum(self):
        self.edit("sections/s1.html", '<div class="sum" hidden>\n          <p class="sum-lead">평균은', '<div class="summary" hidden>\n          <p class="sum-lead">평균은')
        self.assertEqual(self.codes(), ["missing-sum"])

    def test_widget_static_required(self):
        self.edit("sections/s1.html", 'class="widget-static"', 'class="widget-snap"')
        self.assertEqual(self.codes(), ["widget-static-missing"])

    def test_missing_pdf_is_broken_link(self):
        note = self.build()
        (self.out / manifest.answer_pdf_name(self.m())).unlink()
        self.assertEqual(self.codes(note), ["broken-link"])

    def test_leftover_review_token(self):
        self.edit("sections/s2.html", "{{PROBLEM_PDF}}", "{{REVIEW_HREF}}")
        self.assertEqual(self.codes(), ["broken-link", "leftover-slot", "missing-link"])

    def test_zero_problem_pack_passes_without_pdfs(self):
        m = self.m()
        m["problems"], m["links"] = [], []
        (self.run / "manifest.json").write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8")
        self.edit("sections/s2.html",
                  '<ul><li><a href="{{PROBLEM_PDF}}">복습문제 PDF</a></li><li><a href="{{ANSWER_PDF}}">복습문제 답안 PDF</a></li></ul>',
                  "<p>이번 범위에는 복습문제가 없어요.</p>")
        self.assertEqual(self.codes(), [])

    def test_cli_exit_codes(self):
        note = self.build()
        args = ["--manifest", str(self.run / "manifest.json"), "--note", str(note)]
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(check_html.main(args), 0)
            self.assertEqual(check_html.main([str(note)]), 0)
            note.write_text(note.read_text(encoding="utf-8").replace('lang="ko"', 'lang="en"'), encoding="utf-8")
            self.assertEqual(check_html.main(args), 1)
        self.assertIn("[lang]", out.getvalue())

    def test_cli_manifest_requires_note(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            check_html.main(["--manifest", str(self.run / "manifest.json")])


if __name__ == "__main__":
    unittest.main()
```
`test_zero_problem_pack_passes_without_pdfs`는 예전 필수 용어 `복습문제`가 새 문장("…복습문제가 없어요")에 남아 있어서 통과한다.

- [ ] **Step 3: 실패 확인**

Run: `python3 -m unittest discover -s .claude/skills/ec2-review-pack/tests -p test_check_html.py`
Expected: FAIL. 이유는 `check_pack()`의 인자 수가 맞지 않고(`missing 1 required positional argument: 'review_path'`), `check_review`가 아직 있기 때문이다.

- [ ] **Step 4: `scripts/check_html.py` 수정**

(a) 모듈 docstring 전체를 다음으로 바꾼다.
```python
"""
정리노트 HTML 검사기 (표준 라이브러리만 사용).

- 공통 검사: lang, 중복 id, 외부 리소스 허용 목록, 수식 구분자, 링크(복습문제 PDF 포함), 남은 슬롯, 위젯 정적 대체물
- manifest 검사: 섹션·토픽 id, 필수 용어, 레이어, 보충 배지, 페이지 요약, 예고 밖 금지어, 링크
CLI:
  check_html.py FILE [FILE ...]
  check_html.py --manifest run/manifest.json --note NOTE.html
"""
```
(b) `CARD_PARTS = {…}` 줄을 지운다.

(c) `def check_review(...)` 함수 전체를 지운다.

(d) `check_pack`을 다음으로 바꾼다.
```python
def check_pack(m: dict, note_path: Path | str) -> list[Problem]:
    source = Path(note_path).read_text(encoding="utf-8")
    doc = parse_html(source)
    return check_common(doc, source, Path(note_path)) + check_note(doc, m)
```
(e) `main`에서 `ap.add_argument("--review")` 줄을 지우고, manifest 분기를 다음으로 바꾼다.
```python
    if args.manifest:
        if not args.note:
            ap.error("--manifest에는 --note가 필요")
        problems += check_pack(manifest_mod.load(args.manifest), args.note)
```

- [ ] **Step 5: 통과 확인**

Run: `python3 -m unittest discover -s .claude/skills/ec2-review-pack/tests -p test_check_html.py`
Expected: `OK`

- [ ] **Step 6: 커밋**

```bash
git add .claude/skills/ec2-review-pack/scripts/check_html.py .claude/skills/ec2-review-pack/tests/test_check_html.py
git commit -m "feat(ec2-review-pack): check note html only

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: MD 변환기 (정리노트 하나)

**Files:**
- Create: `SKILL/scripts/html2md.py` (ML에서 복사 후 수정)
- Test: `SKILL/tests/test_html2md.py`

**Interfaces:**
- Consumes: `assemble.assemble`, `manifest.problem_pdf_name/answer_pdf_name`
- Produces:
  - `convert_note(note_path) -> tuple[str, int]`(md 경로, 그림 수)
  - `check_md(html_path, md_path) -> list[str]`
  - `Ctx`, `Builder`, `render_table`, `export_svg`(ML 그대로)
  - CLI: `html2md.py NOTE.html [--check]`

- [ ] **Step 1: 복사**

```bash
cp /Users/hyunjun_macbook_pro/Documents/Univ/머신러닝기초/.claude/skills/ml-review-pack/scripts/html2md.py /Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/.claude/skills/ec2-review-pack/scripts/
```

- [ ] **Step 2: 실패하는 테스트 작성 `tests/test_html2md.py`**

```python
from pathlib import Path
import shutil
import tempfile
import unicodedata
import unittest
import xml.dom.minidom

from _util import MINI_RUN

import assemble
import html2md
import manifest


def page(body):
    return f'<html><body><main><div class="hero"><h1>t</h1></div>{body}</main></body></html>'


def small_note(directory, body, nfd=False):
    name = "정리노트_0101_X.html"
    note = Path(directory) / (unicodedata.normalize("NFD", name) if nfd else name)
    note.write_text(page(body), encoding="utf-8")
    return note


class TestHtml2Md(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.note = assemble.assemble(MINI_RUN, self.tmp)
        m = manifest.load(MINI_RUN / "manifest.json")
        for name in (manifest.problem_pdf_name(m), manifest.answer_pdf_name(m)):
            (self.tmp / name).write_bytes(b"%PDF-1.4\n")
        self.note_md, self.figs = html2md.convert_note(self.note)
        self.md = Path(self.note_md).read_text(encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_output_and_check_pass(self):
        self.assertEqual(Path(self.note_md).name, "정리노트_0101-0102_Mini_Test.md")
        self.assertEqual(html2md.check_md(self.note, self.note_md), [])

    def test_pdf_links_kept_as_pdf(self):
        self.assertIn("(복습문제_0101-0102_Mini_Test-문제.pdf)", self.md)
        self.assertIn("(복습문제_0101-0102_Mini_Test-답안.pdf)", self.md)

    def test_missing_pdf_is_reported(self):
        (self.tmp / "복습문제_0101-0102_Mini_Test-답안.pdf").unlink()
        problems = html2md.check_md(self.note, self.note_md)
        self.assertEqual(problems, ["링크 파일 없음: 복습문제_0101-0102_Mini_Test-답안.pdf"])

    def test_page_summary_rendered(self):
        self.assertIn("**페이지 요약**", self.md)
        self.assertIn("*핵심 식*", self.md)
        self.assertIn("- **분산(variance)** — 평균과의 차이를 제곱해 평균낸 값", self.md)

    def test_widget_static_becomes_figure_and_table(self):
        self.assertEqual(self.figs, 1)
        self.assertTrue((self.tmp / "figures_0101-0102" / "widget-mean-static.svg").exists())
        self.assertIn('<a id="widget-mean"></a>', self.md)
        self.assertIn("![평균 1.5 막대](figures_0101-0102/widget-mean-static.svg)", self.md)
        self.assertIn("| 1, 2 | $\\frac{3}{2}$ |", self.md)

    def test_reconversion_removes_orphan_svgs_only(self):
        fig = self.tmp / "figures_0101-0102"
        (fig / "old-orphan.svg").write_text("<svg/>", encoding="utf-8")
        (fig / "keep.txt").write_text("x", encoding="utf-8")
        (self.tmp / "outside.svg").write_text("<svg/>", encoding="utf-8")
        _, figs = html2md.convert_note(self.note)
        self.assertEqual(figs, 1)
        self.assertEqual(sorted(p.name for p in fig.iterdir()), ["keep.txt", "widget-mean-static.svg"])
        self.assertTrue((self.tmp / "outside.svg").exists())

    def test_table_math_pipes(self):
        ctx = html2md.Ctx([], str(self.tmp), "figures_x")
        b = html2md.Builder()
        b.feed(r"<table><tr><th>a</th></tr><tr><td>$\|x\|$ | $|y|$</td></tr></table>")
        table = next(b.root.find_all(lambda n: n.tag == "table"))
        self.assertEqual(html2md.render_table(table, ctx)[2], r"| $\Vert x\Vert $ \| $\vert y\vert $ |")

    def test_check_md_detects_missing_math(self):
        Path(self.note_md).write_text(self.md.replace(r"\bar{x} = ", ""), encoding="utf-8")
        problems = html2md.check_md(self.note, self.note_md)
        self.assertEqual(len(problems), 1)
        self.assertTrue(problems[0].startswith("수식 누락"))

    def test_bad_filename_rejected(self):
        for bad in ("note.html", "복습문제_0101_X.html"):
            with self.subTest(bad=bad):
                path = self.tmp / bad
                shutil.copyfile(self.note, path)
                with self.assertRaises(ValueError):
                    html2md.convert_note(path)

    def test_svg_export_keeps_viewbox_case_and_size(self):
        ctx = html2md.Ctx([], str(self.tmp), "f")
        b = html2md.Builder()
        b.feed('<svg id="t" viewBox="0 0 720 400" width="100%" preserveAspectRatio="xMidYMid meet">'
               '<defs><marker id="m" markerWidth="6" markerHeight="6" refX="3" refY="3"/></defs></svg>')
        svg = next(b.root.find_all(lambda n: n.tag == "svg"))
        html2md.export_svg(svg, ctx)
        root = xml.dom.minidom.parse(str(self.tmp / "t.svg")).documentElement
        self.assertEqual(root.getAttribute("viewBox"), "0 0 720 400")
        self.assertEqual((root.getAttribute("width"), root.getAttribute("height")), ("720", "400"))
        marker = root.getElementsByTagName("marker")[0]
        self.assertEqual((marker.getAttribute("refX"), marker.getAttribute("markerWidth")), ("3", "6"))

    def test_unnamed_and_duplicate_figures_are_distinct_files(self):
        d = self.tmp / "p"
        d.mkdir()
        fig = '<figure><svg viewBox="0 0 10 10"><circle r="3"/></svg></figure>'
        dup = '<figure><svg id="same" viewBox="0 0 10 10"><rect width="1" height="1"/></svg></figure>'
        note = small_note(d, f'<section id="s"><h2>A</h2>{fig}{dup}{fig}{dup}</section>')
        note_md, figs = html2md.convert_note(note)
        self.assertEqual(figs, 4)
        self.assertEqual(sorted(x.name for x in (d / "figures_0101").iterdir()),
                         ["note-fig-1.svg", "note-fig-2.svg", "same-2.svg", "same.svg"])
        self.assertEqual(html2md.check_md(note, note_md), [])

    def test_check_md_detects_deleted_short_math(self):
        d = self.tmp / "m"
        d.mkdir()
        note = small_note(d, r'<section id="s"><h2>A</h2><p>Let $a$ be a value, $\alpha$ and $\alpha$.</p></section>')
        note_md, _ = html2md.convert_note(note)
        md = Path(note_md).read_text(encoding="utf-8")
        self.assertEqual(html2md.check_md(note, note_md), [])
        Path(note_md).write_text(md.replace("Let $a$ be", "Let be"), encoding="utf-8")
        problems = html2md.check_md(note, note_md)
        self.assertEqual(len(problems), 1)
        self.assertTrue(problems[0].startswith("수식 누락: $a$"))
        Path(note_md).write_text(md.replace(r" and $\alpha$", " and"), encoding="utf-8")
        self.assertIn("(1/2)", html2md.check_md(note, note_md)[0])

    def test_check_md_detects_unrewritten_and_broken_links(self):
        md = self.md + "\n[a](./정리노트_0101-0102_Mini_Test.html#s1)\n[x](../%EC%97%86%EC%9D%8C/x.html)\n"
        Path(self.note_md).write_text(md, encoding="utf-8")
        problems = html2md.check_md(self.note, self.note_md)
        self.assertEqual(len(problems), 2)
        self.assertTrue(problems[0].startswith("링크 미변환(.html): ./정리노트"))
        self.assertTrue(problems[1].startswith("링크 파일 없음: ../"))

    def test_nfd_named_note_converts(self):
        d = self.tmp / "nfd"
        d.mkdir()
        nfd_link = unicodedata.normalize("NFD", "./정리노트_0101_X.html") + "#s"
        note = small_note(d, f'<section id="s"><h2>A</h2><p><a href="{nfd_link}">self</a></p></section>', nfd=True)
        note_md, _ = html2md.convert_note(note)
        self.assertEqual(Path(note_md).name, "정리노트_0101_X.md")
        self.assertIn("(./정리노트_0101_X.md#s)", Path(note_md).read_text(encoding="utf-8"))
        self.assertEqual(html2md.check_md(note, note_md), [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: 실패 확인**

Run: `python3 -m unittest discover -s .claude/skills/ec2-review-pack/tests -p test_html2md.py`
Expected: FAIL (`AttributeError: module 'html2md' has no attribute 'convert_note'`)

- [ ] **Step 4: `scripts/html2md.py` 수정**

(a) docstring 첫 줄과 CLI 두 줄을 바꾼다.
```
r"""정리노트 HTML → GitHub 마크다운 변환기 (표준 라이브러리만 사용).
...
CLI:
  html2md.py NOTE.html            # 같은 폴더에 .md + figures_<range>/
  html2md.py NOTE.html --check    # 변환 후 누락 검사(수식·앵커·그림·링크)
```
("…"는 원본의 가운데 설명 줄 5개를 그대로 둔다는 뜻이다.)

(b) `def convert_pack(note_path, review_path):` 함수 전체를 다음으로 바꾼다.
```python
def convert_note(note_path):
    """정리노트 HTML을 같은 폴더에 .md로 변환한다. (md 경로, 그림 파일 수)를 돌려준다."""
    src = os.path.abspath(note_path)
    out_dir = os.path.dirname(src)
    name = nfc(os.path.basename(src))
    m = NAME_RE.match(name)
    if not m or m.group(1) != "정리노트":
        raise ValueError(f"파일명 규칙 위반: {name}")
    fig_name = f"figures_{m.group(2)}"
    fig_abs = os.path.join(out_dir, fig_name)
    os.makedirs(fig_abs, exist_ok=True)
    for entry in os.listdir(fig_abs):  # 다시 변환할 때 이전 실행의 고아 SVG를 남기지 않는다(.svg만, 이 폴더만)
        old_svg = os.path.join(fig_abs, entry)
        if entry.lower().endswith(".svg") and os.path.isfile(old_svg) and not os.path.islink(old_svg):
            os.remove(old_svg)
    link_map = [(name, name[:-5] + ".md")]  # fix_href가 NFC로 비교하므로 NFD 링크도 잡힌다
    intro = [f"> `{name}`를 마크다운으로 옮겼어요. 그림은 `{fig_name}/` 폴더의 SVG, "
             "위젯은 대표 설정의 정적 그림으로 바꿨어요. 수식은 `$…$` / `$$…$$`라서 GitHub, Obsidian, Typora에서 보여요."]
    registry = set()
    ctx = Ctx(link_map, fig_abs, fig_name, prefix="note", registry=registry)
    out = os.path.join(out_dir, name[:-5] + ".md")
    convert(src, out, ctx, intro)
    return out, len(registry)
```
(c) `main`을 다음으로 바꾼다.
```python
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("note")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    out, fig_count = convert_note(args.note)
    print(out)
    print(f"figures: {fig_count}")
    if not args.check:
        return 0
    problems = [f"{os.path.basename(out)}: {p}" for p in check_md(args.note, out)]
    for p in problems:
        print(p)
    print("OK" if not problems else f"FAIL ({len(problems)})")
    return int(bool(problems))
```

- [ ] **Step 5: 통과 확인**

Run: `python3 -m unittest discover -s .claude/skills/ec2-review-pack/tests -p test_html2md.py`
Expected: `OK`

- [ ] **Step 6: 커밋**

```bash
git add .claude/skills/ec2-review-pack/scripts/html2md.py .claude/skills/ec2-review-pack/tests/test_html2md.py
git commit -m "feat(ec2-review-pack): convert single note to markdown

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: workbook 문제 목록 (`problem_index.py`)

**Files:**
- Create: `SKILL/scripts/problem_index.py`
- Test: `SKILL/tests/test_problem_index.py`

**Interfaces:**
- Consumes: `REPO/workbook/problem.py`의 `load_problem(path) -> Problem`(`.id`, `.meta`, `.title`)과 `ProblemError`. import 경로는 `REPO/workbook`이다.
- Produces:
  - `HEADER`
  - `secnum(meta) -> str`
  - `used_ids(notes_dir) -> set[str]`
  - `md_paths(repo, chapters) -> list[Path]`
  - `index(repo, used_dir=None, chapters=None) -> tuple[list[list[str]], list[str]]`(행, 오류)
  - CLI: `problem_index.py --repo REPO [--used DIR] [--chapters 9,10]`. 종료 코드는 오류가 없으면 0, 있으면 1이다.

- [ ] **Step 1: 실패하는 테스트 작성 `tests/test_problem_index.py`**

```python
import contextlib
import io
from pathlib import Path
import tempfile
import unicodedata
import unittest

from _util import REPO

import problem_index

HAS_WORKBOOK = (REPO / "workbook" / "problem.py").exists()


def by_id(rows):
    return {r[0]: r for r in rows}


class TestUnits(unittest.TestCase):
    def test_secnum(self):
        self.assertEqual(problem_index.secnum({"kind": "장말문제", "section": "10.2.3 소신호 해석"}), "10.2.3")
        self.assertEqual(problem_index.secnum({"kind": "장말문제", "section": "Design Problems"}), "Design Problems")
        self.assertEqual(problem_index.secnum({"kind": "기출", "textbook_chapters": [9, 10]}), "ch9,10")

    def test_used_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            notes = Path(tmp)
            (notes / "0909").mkdir()
            (notes / "0909" / "problems.txt").write_text(
                "P9.01 | 이유\n\n" + unicodedata.normalize("NFD", "2023-1_기말-Q1") + " | 기출\n", encoding="utf-8")
            self.assertEqual(problem_index.used_ids(notes), {"P9.01", "2023-1_기말-Q1"})
            self.assertEqual(problem_index.used_ids(notes / "missing"), set())


@unittest.skipUnless(HAS_WORKBOOK, "workbook 없음")
class TestRealRepo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows, cls.errors = problem_index.index(REPO)

    def test_no_errors(self):
        self.assertEqual(self.errors, [])

    def test_textbook_row(self):
        row = by_id(self.rows)["P9.01"]
        self.assertEqual(row[1:6], ["장말문제", "9.1.1", "9.1.1 전류원으로서의 캐스코드", "0", "-"])
        self.assertTrue(row[6].startswith("바이폴라 캐스코드"))

    def test_exam_row(self):
        row = by_id(self.rows)["2023-1_기말-Q1"]
        self.assertEqual(row[1:3], ["기출", "ch10,11"])
        self.assertEqual(row[4], "-")

    def test_chapter_filter(self):
        rows, _ = problem_index.index(REPO, chapters={9})
        ids = set(by_id(rows))
        textbook = {i for i in ids if not i[0].isdigit()}
        self.assertTrue(textbook and all(i[1:].startswith("9.") for i in textbook))
        self.assertEqual(len(textbook), 110)
        self.assertNotIn("2023-1_기말-Q1", ids)  # textbook_chapters [10, 11]

    def test_used_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "0909").mkdir()
            (Path(tmp) / "0909" / "problems.txt").write_text("P9.01 | x\n", encoding="utf-8")
            rows, _ = problem_index.index(REPO, used_dir=Path(tmp), chapters={9})
        table = by_id(rows)
        self.assertEqual(table["P9.01"][5], "USED")
        self.assertEqual(table["P9.02"][5], "-")

    def test_cli(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(problem_index.main(["--repo", str(REPO), "--chapters", "9"]), 0)
        lines = out.getvalue().splitlines()
        self.assertEqual(lines[0], problem_index.HEADER)
        self.assertTrue(all(len(line.split("\t")) == 7 for line in lines))

    def test_bad_md_is_reported_and_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "workbook").symlink_to(REPO / "workbook", target_is_directory=True)
            bad = repo / "교과서" / "마이크로전자회로" / "ch99" / "예제"
            bad.mkdir(parents=True)
            (bad / "E99.01.md").write_text("no frontmatter\n", encoding="utf-8")
            (repo / "from_the_past" / "md").mkdir(parents=True)
            rows, errors = problem_index.index(repo)
            self.assertEqual(rows, [])
            self.assertEqual(len(errors), 1)
            self.assertIn("E99.01.md", errors[0])
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as err:
                self.assertEqual(problem_index.main(["--repo", str(repo)]), 1)
            self.assertIn("ERROR", err.getvalue())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 실패 확인**

Run: `python3 -m unittest discover -s .claude/skills/ec2-review-pack/tests -p test_problem_index.py`
Expected: FAIL (`ModuleNotFoundError: No module named 'problem_index'`)

- [ ] **Step 3: `scripts/problem_index.py` 작성**

```python
#!/usr/bin/env python3
"""
workbook 문제 목록 (복습문제 선별용). 문제 md는 workbook/problem.py의 load_problem으로 읽는다.

한 줄에 문제 하나, 탭으로 구분:
  id  kind  secnum  section  difficulty  used  title
- secnum: 교과서는 section 앞 절 번호(예: 9.1.2. 번호가 없으면 section 그대로), 기출은 "ch" + textbook_chapters(예: ch9,10)
- difficulty: 교과서 frontmatter 값, 기출은 "-"
- used: 이전 팩 problems.txt에 있으면 "USED", 아니면 "-"
CLI: problem_index.py --repo REPO [--used REPO/복습노트] [--chapters 9,10]
읽을 수 없는 md는 stderr에 `ERROR <경로>: <이유>`로 적고 건너뛴다(종료 코드 1).
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys
import unicodedata

HEADER = "id\tkind\tsecnum\tsection\tdifficulty\tused\ttitle"
KIND_DIRS = ("예제", "연습문제", "장말문제")
SECNUM_RE = re.compile(r"\d+(?:\.\d+)*")
CHAPTER_DIR_RE = re.compile(r"ch(\d{2})")
EXAM_FILE_RE = re.compile(r"Q([1-9]\d*)\.md")


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def _workbook(repo: Path):
    """REPO/workbook/problem.py 모듈."""
    path = str(Path(repo) / "workbook")
    if path not in sys.path:
        sys.path.insert(0, path)
    import problem  # noqa: E402
    return problem


def secnum(meta: dict) -> str:
    if meta.get("kind") == "기출":
        return "ch" + ",".join(str(c) for c in meta.get("textbook_chapters") or [])
    section = str(meta.get("section", ""))
    m = SECNUM_RE.match(section)
    return m.group(0) if m else section


def used_ids(notes_dir: Path | str) -> set[str]:
    """<notes_dir>/*/problems.txt 의 id (줄 형식 `id | why`)."""
    notes_dir, ids = Path(notes_dir), set()
    if not notes_dir.is_dir():
        return ids
    for path in notes_dir.glob("*/problems.txt"):
        for line in path.read_text(encoding="utf-8").splitlines():
            pid = nfc(line.split("|", 1)[0].strip())
            if pid:
                ids.add(pid)
    return ids


def _exam_number(path: Path) -> int:
    return int(EXAM_FILE_RE.fullmatch(nfc(path.name)).group(1))


def md_paths(repo: Path | str, chapters: set[int] | None = None) -> list[Path]:
    """교과서(장 순서, 종류 순서, 파일명 순서) 다음 기출(회차 순서, 문항 번호 순서) md 경로."""
    repo, out = Path(repo), []
    textbook = repo / "교과서" / "마이크로전자회로"
    for ch_dir in sorted(textbook.iterdir()) if textbook.is_dir() else []:
        m = CHAPTER_DIR_RE.fullmatch(nfc(ch_dir.name))
        if not m or not ch_dir.is_dir() or (chapters and int(m.group(1)) not in chapters):
            continue
        for kind in KIND_DIRS:
            out += sorted((ch_dir / kind).glob("*.md"))
    exams = repo / "from_the_past" / "md"
    for exam_dir in sorted(p for p in exams.iterdir() if p.is_dir()) if exams.is_dir() else []:
        out += sorted((p for p in exam_dir.glob("*.md") if EXAM_FILE_RE.fullmatch(nfc(p.name))), key=_exam_number)
    return out


def index(repo: Path | str, used_dir: Path | str | None = None,
          chapters: set[int] | None = None) -> tuple[list[list[str]], list[str]]:
    problem = _workbook(Path(repo))
    used = used_ids(used_dir) if used_dir else set()
    rows, errors = [], []
    for path in md_paths(repo, chapters):
        try:
            p = problem.load_problem(path)
        except (problem.ProblemError, OSError, KeyError) as e:
            errors.append(f"{path}: {e}")
            continue
        meta, pid = p.meta, nfc(p.id)
        exam = meta.get("kind") == "기출"
        if exam and chapters and not set(meta.get("textbook_chapters") or []) & chapters:
            continue
        rows.append([pid, str(meta["kind"]), secnum(meta), str(meta.get("section", "-")),
                     "-" if exam else str(meta.get("difficulty", "-")),
                     "USED" if pid in used else "-", p.title.replace("\t", " ")])
    return rows, errors


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--used", help="이전 팩 폴더들의 부모(보통 REPO/복습노트)")
    ap.add_argument("--chapters", help="쉼표로 구분한 장 번호 (예: 9,10)")
    args = ap.parse_args(argv)
    chapters = {int(c) for c in args.chapters.split(",")} if args.chapters else None
    rows, errors = index(Path(args.repo), args.used, chapters)
    print(HEADER)
    for row in rows:
        print("\t".join(row))
    for e in errors:
        print(f"ERROR {e}", file=sys.stderr)
    return int(bool(errors))


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: 통과 확인**

Run: `python3 -m unittest discover -s .claude/skills/ec2-review-pack/tests -p test_problem_index.py`
Expected: `OK`

`test_textbook_row`가 제목이나 `difficulty` 값 때문에 실패하면 `sed -n 1,20p 교과서/마이크로전자회로/ch09/장말문제/P9.01.md`로 실제 값을 확인하고, 테스트 기대값을 실제 md에 맞춘다. md는 고치지 않는다.

- [ ] **Step 5: 실제 출력 한번 보기**

Run: `python3 .claude/skills/ec2-review-pack/scripts/problem_index.py --repo . --chapters 10 | head -5`
Expected: 헤더 다음 줄에 `E10.01	예제	10.…` 같은 탭 구분 행이 나오고, 종료 코드는 0이다.

- [ ] **Step 6: 커밋**

```bash
git add .claude/skills/ec2-review-pack/scripts/problem_index.py .claude/skills/ec2-review-pack/tests/test_problem_index.py
git commit -m "feat(ec2-review-pack): add workbook problem index for selection

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: 참조 문서 (references/)

**Files:**
- Create: `SKILL/references/{stt-summary-prompt,manifest-guide,content-rules,widget-rules,problem-selection,review-prompt,browser-check}.md`
- Test: `SKILL/tests/test_skill_files.py`(`TestReferences`만. SKILL.md 검사는 Task 7)

**Interfaces:**
- Consumes: Task 1~5의 CLI 이름과 토큰(`{{PROBLEM_PDF}}`, `{{ANSWER_PDF}}`, `problem_index.py`, `manifest.py <m> <REPO>`)
- Produces: SKILL.md(Task 7)가 가리킬 참조 문서 7개

- [ ] **Step 1: 실패하는 테스트 작성 `tests/test_skill_files.py`**

```python
"""참조 문서·SKILL.md 형식과, 본문이 가리키는 파일이 모두 있는지 확인한다."""

import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unicodedata
import unittest

from _util import SKILL

REFERENCES = ("stt-summary-prompt", "manifest-guide", "content-rules", "widget-rules",
              "problem-selection", "review-prompt", "browser-check")
ML_LEFTOVERS = ("MML", "머신러닝", "정방철", "REVIEW_HREF", "answers.py", "card-rules", "review-template")


def skill_texts():
    for path in sorted(SKILL.rglob("*")):
        if path.suffix in (".md", ".py") and "tests" not in path.parts and "__pycache__" not in path.parts:
            yield path, path.read_text(encoding="utf-8")


class TestReferences(unittest.TestCase):
    def test_reference_files_exist(self):
        for name in REFERENCES:
            with self.subTest(name=name):
                self.assertTrue((SKILL / "references" / f"{name}.md").exists())

    def test_no_ml_leftovers(self):
        for path, text in skill_texts():
            for word in ML_LEFTOVERS:
                with self.subTest(path=path.name, word=word):
                    self.assertNotIn(word, text)

    def test_pdf_tokens_documented(self):
        rules = (SKILL / "references" / "content-rules.md").read_text(encoding="utf-8")
        self.assertIn("{{PROBLEM_PDF}}", rules)
        self.assertIn("{{ANSWER_PDF}}", rules)

    def test_selection_rules_use_index_tool(self):
        text = (SKILL / "references" / "problem-selection.md").read_text(encoding="utf-8")
        self.assertIn("scripts/problem_index.py", text)
        self.assertIn("--used", text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 실패 확인**

Run: `python3 -m unittest discover -s .claude/skills/ec2-review-pack/tests -p test_skill_files.py`
Expected: FAIL. `test_reference_files_exist`가 실패한다. `test_no_ml_leftovers`도 실패할 수 있다. html2md.py 등 복사한 스크립트에 해당 단어가 없으면 통과하지만, 남아 있으면 Step 10에서 고친다.

- [ ] **Step 3: `references/stt-summary-prompt.md` 작성**

````markdown
# STT 요약 에이전트 지시문

메인 에이전트는 날짜마다 아래 브리프로 에이전트 1명을 띄운다(병렬, model: opus / lite: sonnet).

---
전자회로2(권익진 교수님) <MMDD> 수업 녹음 전사를 정밀 요약한다.

- 입력(읽기 전용): `<RUN>/repo/STT/<MMDD 전회2.md>` — **처음부터 끝까지 전부** 읽는다. 건너뛰지 않는다.
- 대조 자료: `<RUN>/repo/강의노트/<2026F_LecN_*.pdf>` 슬라이드 텍스트(메인이 추출해 `<RUN>/slides.txt`에 둠, 쪽마다 `=== LNN sK ===`)
- 출력: `<RUN>/summaries/stt-<MMDD>.md` 한 파일만 쓴다. 다른 곳에는 쓰지 않는다(임시 파일은 아래 규칙).
- 임시·보조 파일(스크립트, 초안, 그림 생성 폴더)은 `<RUN>/work/` 아래에만 둔다. 저장소(`STT/`, `강의노트/`, `교과서/`, `workbook/`, `복습노트/`)와 scratchpad 루트, `/tmp`에는 아무것도 쓰지 않는다. 한글(NFD) 파일명은 복사하거나 이름을 바꾸지 말고 Python `os.listdir` + `unicodedata.normalize('NFC', …)`로 찾아 그 경로로 연다.

출력 형식:
1. `# <MMDD> 전자회로2 강의 개요 (권익진 교수, <YYYY-MM-DD>)`
2. **총평**: 녹음 길이, 이번 수업이 다룬 강의자료와 슬라이드 범위(예: "L03 s7–12"), **시작하지 않은** 슬라이드, 흐름 한 줄.
3. 흐름 순서대로 `## N. 제목 (MM:SS–MM:SS)` 절. 각 절에:
   - **핵심 내용**: 정의, 식(TeX `$…$`), 칠판 유도 단계, 소신호 등가회로를 말로 설명한 것(어느 노드에 무엇이 연결되는지). 슬라이드에 없는 설명은 `[슬라이드 외]` 표시.
   - **교과서 연결**: 교수님이 언급한 Razavi 절·예제·그림 번호(예: "Example 9.3", "Fig. 9.12"). 없으면 생략.
   - **비유와 일화**: 개념을 싣는 비유만. 순수 잡담(출석, 자리, 이메일 등)은 쓰지 않는다.
   - **학생과의 대화**: 학생 이름은 "한 학생".
   - 강조 발언: 원문 인용 + `(MM:SS)`. "중요", "시험", "꼭" 같은 표현이 붙은 발언은 모두.
   - "나중에 할게요/유도는 생략" 처럼 **미룬 유도**는 `🕳️ 미룬 유도:`로 표시.
4. `## 슬라이드 대조표`: | 슬라이드 | 다룸/일부/예고만/안 다룸 | 근거 타임스탬프 |
5. `## 교과서 절 대조`: 이번 수업이 다룬 Razavi 절 번호(예: 9.1.1, 9.1.2)와 다룸/일부. 복습문제 선별에 쓴다.
6. `## 용어·식 목록`: 수업에서 실제로 쓴 용어와 식을 TeX 그대로 나열(정리노트 required_terms 후보). 표기는 `g_m`, `r_O`, `R_{out}`, `V_{GS}`, `\parallel`로 맞춘다.
7. `## 말실수 정정`: STT 오인식(예: "캐스코드"가 "케스 코드"로 적힘) 또는 교수님 말실수와 올바른 형태.

보고: 파일 경로와 총평 3줄만 돌려준다.
---
````

- [ ] **Step 4: `references/manifest-guide.md` 작성**

````markdown
# manifest.json 작성 규칙 (메인 에이전트)

manifest는 이번 팩의 계약이다. 작성자, 검사기, 조립기가 모두 이 파일을 기준으로 삼는다.
정본 예시: `tests/fixtures/mini-run/manifest.json`.
작성 후 반드시 `python3 <SKILL>/scripts/manifest.py <RUN>/manifest.json <REPO>` → `OK`(REPO를 주면 문제 md가 있는지도 본다).

## 최상위
| 키 | 값 |
|---|---|
| `course` | `"전자회로2"` |
| `range` | `"0923"` 또는 `"0916-0918"` (첫 STT–마지막 STT 날짜) |
| `slug` | 이번 범위 대표 주제의 영문 밑줄 형태, 예: `"Cascode_Stage"`, `"Differential_Amplifiers"`. 두 주제에 걸치면 뒤쪽 것 |
| `note_title` | `"<주제> — 5살도 이해하는 정리노트"` |
| `note_subtitle` | `"권익진 교수님 전자회로2 · 0916 · 0918 수업 (Lec3, Razavi 9장)"` 형식 |
| `footer_note` | HTML 허용. `출처: 권익진 교수님 강의자료(LecN) · 수업 녹음 전사(MMDD…) · B. Razavi, <i>Microelectronics</i>, 2nd ed. (Wiley) N장.` |
| `sessions` | 날짜별 `{date, stt, summary, slides}` |

## sections / topics
- 섹션 id는 `s0`, `s1`, … 순서. 마지막 섹션은 항상 "요약 · 예고"이며 토픽 `s<N>-cheatsheet`, `s<N>-next`, `s<N>-links`를 둔다.
- 섹션은 **개념 순서(슬라이드 로드맵)** 로 묶는다. 날짜는 토픽 태그로만 드러낸다.
- 토픽 id는 `s<n>-<kebab>`(영문 소문자). 토픽 하나 = 슬라이드 1~3장 또는 칠판 유도 하나.
- `short`는 상단 목차 글자(예: `"2 출력저항"`), `title`은 `"2. 캐스코드의 출력저항"`.
- `layers`: 개념 토픽은 `["eli5", "formal", "prof"]`. 교수님 발언이 없으면 `prof` 대신 빼되 이유를 보고서 "스킬이 정한 사항"에 적는다. 요약·예고 섹션 토픽은 `[]`.
- `supp`: 요약의 `🕳️ 미룬 유도`를 보충으로 싣는 토픽만 `true`.
- `required_terms`: 토픽당 3~9개. 요약의 **용어·식 목록과 강조 발언**에서 고른다.
  - 식은 작성자가 **공백까지 그대로** 쓸 TeX 문자열이다(예: `"R_{out} \\approx g_m r_O^2"`).
  - 교수님 비유의 핵심 단어를 최소 하나 넣어 교수님 말씀(prof) 레이어 누락을 잡는다.
- `preview_topic`: `s<N>-next`.
- `forbidden_outside_preview`: 슬라이드 대조표에서 "예고만/안 다룸"인 슬라이드의 핵심 용어 3~8개. 본문에 나오면 검사 실패.

## problems
- 선별은 `references/problem-selection.md`. 0~12개, 목표 10개. workbook에 맞는 문제가 없으면 `[]`.
- 항목: `{"id": "P9.05", "kind": "장말문제", "anchor": "s2-rout", "date": "0916", "why": "캐스코드 출력저항 수치 계산"}`
  - `id`: workbook id. 교과서 `E`(예제)/`X`(연습문제)/`P`(장말문제) + `장.두자리`(예: `E10.03`), 기출 `<연도>-<학기>_<중간|기말>-Q<n>`(예: `2023-1_기말-Q1`).
  - `kind`: id에서 정해진다(`E`→예제, `X`→연습문제, `P`→장말문제, 기출). 틀리면 manifest.py가 실패.
  - `anchor`: 문제가 기대는 정리노트 토픽 id. `date`: 관련 수업 날짜(MMDD).
  - `why`: 이 문제를 고른 이유 한 줄. `problems.txt`와 보고서에 그대로 쓰인다.
- 배열 순서가 PDF 순서다. 수업 순서(=토픽 순서)대로 둔다.

## links
- `href`는 작성자가 `<a href="…">`에 **글자 그대로** 넣을 값이다(검사기가 해당 `topic` 안의 링크와 정확히 비교한다).
- 문제가 1개 이상이면 `{"topic": "s<N>-links", "href": "복습문제_<range>_<slug>-문제.pdf"}`와 `…-답안.pdf` 두 항목을 **반드시** 넣는다(없으면 manifest.py 실패). 문제가 0개면 두 항목을 넣지 않는다.
- 이전 복습팩과 이어지는 개념이면 `../<이전 range>/정리노트_<이전 range>_<slug>.html#<토픽>` 링크를 건다(팩마다 `복습노트/<range>/` 폴더라 한 단계 위로 올라간다).
- 문제집 전체를 보고 싶을 때를 위해 `../../workbook/pdf/chNN-문제.pdf` 링크를 걸어도 된다(그 장을 다뤘을 때만, 파일이 있을 때만).
````

- [ ] **Step 5: `references/content-rules.md` 작성**

ML의 `references/content-rules.md`를 복사한 뒤 아래 5곳만 바꾼다. 바꾼 뒤 파일 전체가 아래 결과와 같아야 한다.

```bash
cp /Users/hyunjun_macbook_pro/Documents/Univ/머신러닝기초/.claude/skills/ml-review-pack/references/content-rules.md /Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/.claude/skills/ec2-review-pack/references/
```
바꿀 곳(Edit 도구로 old → new):
1. `머신러닝기초 정리노트의 섹션` → `전자회로2 정리노트의 섹션`
2. 줄 `- 링크: manifest \`links\` 중 … 복습문제 링크만은 \`{{REVIEW_HREF}}\`로 써도 된다(조립 뒤 실제 파일명이 되어 검사를 통과한다).`의 마지막 문장을 → `복습문제 PDF 링크만은 \`{{PROBLEM_PDF}}\`, \`{{ANSWER_PDF}}\`로 써도 된다(조립 뒤 실제 파일명이 되어 검사를 통과한다).`
3. 줄 `- 근거: \`<RUN>/summaries/stt-*.md\`(해당 날짜), \`<RUN>/slides.txt\`, 필요하면 MML \`<RUN>/repo/교과서/Mathematics_for_Machine_Learning.pdf\` <쪽>` → `- 근거: \`<RUN>/summaries/stt-*.md\`(해당 날짜), \`<RUN>/slides.txt\`, 필요하면 Razavi \`<RUN>/repo/교과서/마이크로전자회로/<N>장.pdf\` <쪽>과 그 장 문제 md(\`<RUN>/repo/교과서/마이크로전자회로/chNN/\`, 수치·그림 확인용)`
4. 자기 검사 문장의 `전문용어·기호(θ, σ, 식, 영어 용어)` → `전문용어·기호(g_m, r_O, 식, 영어 용어)`
5. 줄 `- 복습문제 링크는 \`href="{{REVIEW_HREF}}"\`로 쓴다(조립기가 실제 파일명으로 바꾼다. manifest의 파일명을 그대로 써도 된다). 다른 링크는 manifest \`href\`를 글자 그대로.` → `- 복습문제 PDF 링크는 \`href="{{PROBLEM_PDF}}"\`(문제), \`href="{{ANSWER_PDF}}"\`(답안)로 쓴다(조립기가 실제 파일명으로 바꾼다). 링크 글자는 "복습문제 N개 (PDF)", "답안 (PDF)"처럼 쓴다. 문제가 0개인 팩은 링크 대신 "이번 범위에는 workbook 문제가 없어요." 한 줄을 쓴다. 다른 링크는 manifest \`href\`를 글자 그대로.`

그다음 두 곳을 더 바꾼다.

6. 문체 절의 `전문용어는 영어 병기(예: 과적합(overfitting))` → `전문용어는 영어 병기(예: 출력저항(output resistance))`
7. 수식 절의 벡터 줄 `- 벡터는 \`\mathbf{x}\`, 파라미터 벡터는 \`\boldsymbol{\theta}\`, 행렬 \`\mathbf{X}\` — manifest \`required_terms\`와 같은 표기.`를 아래 세 줄로 바꾼다.
```
- 표기 고정(manifest `required_terms`와 같게): 트랜스컨덕턴스 `g_m`, 출력저항 `r_O`, 단의 출력저항 `R_{out}`, 전압 `V_{GS}`·`V_{DS}`·`V_{BE}`·`V_{CE}`, 이득 `A_v`, 병렬은 `\parallel`(`||`, `//` 금지).
- 근사는 `\approx`, 조건은 글로 쓴다(예: "$g_m r_O \gg 1$일 때").
- 소신호 유도는 "등가회로 → KCL/KVL 한 줄씩 → 결과" 순서로 `ol.steps`에 쓴다.
```

마지막으로 SVG 절 끝에 다음 두 줄을 추가한다.
```
- 회로도: 트랜지스터·저항·전류원은 `fig-ink` 선으로, 지금 설명하는 경로(예: 출력저항을 들여다보는 노드)는 `fig-accent`로 그린다. 소자 이름·값은 `fig-text`(예: "M1", "R_D" 대신 유니코드 "R D"가 어색하면 `<tspan baseline-shift="sub">`), 노드 이름은 `fig-muted`.
- 교과서 그림 PNG(`교과서/마이크로전자회로/chNN/figures/`)를 붙이지 않는다. 다크모드와 MD 변환이 SVG 클래스 전제이기 때문이다.
```
그리고 SVG 절의 `SVG \`<text>\`에 \`$\` 금지(θ, σ, ₁ 같은 유니코드)`를 → `SVG \`<text>\`에 \`$\` 금지(Ω, ∥, ₁, ₘ 같은 유니코드)`로 바꾼다.

- [ ] **Step 6: `references/widget-rules.md` 작성**

```bash
cp /Users/hyunjun_macbook_pro/Documents/Univ/머신러닝기초/.claude/skills/ml-review-pack/references/widget-rules.md /Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/.claude/skills/ec2-review-pack/references/
```
바꿀 곳: `(예: λ와 과적합, prior 강도와 MAP)` → `(예: $r_O$를 키우면 캐스코드 $R_{out}$이 얼마나 커지는지, 미러 폭 비율과 출력 전류, 차동 입력 크기와 두 드레인 전류)`

- [ ] **Step 7: `references/problem-selection.md` 작성**

````markdown
# 복습문제 선별 규칙 (메인 에이전트)

복습문제는 **workbook에 이미 있는 문제를 고르기만** 한다. 자작·변형 문제는 만들지 않는다. 모든 문제에 `## 풀이`가 있으므로 정답을 따로 계산하지 않는다.

## 1. 후보 목록
```bash
python3 <SKILL>/scripts/problem_index.py --repo <REPO> --used <REPO>/복습노트 --chapters <이번 범위 장, 예: 9,10> > <RUN>/candidates.tsv
```
- 열: `id  kind  secnum  section  difficulty  used  title`
- 종료 코드 1이면 stderr의 `ERROR` md는 후보에서 빠진 것이다. 보고서 "미해결"에 적는다(md는 고치지 않는다).
- `used`가 `USED`인 id는 이전 팩에서 썼으므로 고르지 않는다.

## 2. 범위 맞추기
- 요약의 `## 교과서 절 대조`에서 "다룸"인 절 번호 집합을 만든다(예: `{9.1.1, 9.1.2}`).
- 교과서 문제: `secnum`이 그 집합의 절이거나 그 하위 절(9.1.2 → 9.1.2.x)인 것만 후보다. `secnum`이 `10.2`처럼 상위 절이면 제목과 원문을 읽고 다룬 내용만으로 풀리는지 판단한다.
- `Design Problems`: 도전 문제로 최대 1개. 원문을 읽고 다룬 절만으로 풀리는 것만.
- 기출: `secnum`이 `ch9,10`처럼 장만 알려 주므로 **md 원문(`## 원문`)과 `## 풀이`를 읽고** 배운 내용만으로 풀리는지 확인한다.
- 풀이에 수업에서 안 다룬 개념(예: 아직 안 배운 주파수 응답, 피드백)이 한 단계라도 필요하면 제외.
- `forbidden_outside_preview` 용어가 핵심인 문제는 제외.

## 3. 구성
- 목표 10문항(8~12). 구성: 예제 2~3, 연습문제·장말문제 5~6, 기출 1~2.
- 난이도: `difficulty` 0 위주, 1~2는 한두 개.
- 한 절에 몰리지 않게 "다룸" 절마다 최소 1문항.
- 순서: 토픽(수업) 순서. 같은 토픽 안에서는 예제 → 연습문제 → 장말문제 → 기출.
- 후보가 8개보다 적으면 있는 만큼만 넣는다. 0개면 `problems: []`로 두고 PDF를 만들지 않는다. 채우려고 범위 밖 문제나 자작 문제를 넣지 않는다. 보고서에 "해당 문제 N개뿐"과 이유를 적는다.
- 이번 range의 수업이 전부 전자회로1 복습(Lec1–2)이면 workbook(9~11장) 범위 밖이므로 0개가 정상이다.

## 4. manifest에 적기
각 문제를 `{id, kind, anchor, date, why}`로 적는다(`references/manifest-guide.md`). `why`는 "캐스코드 출력저항 $g_m r_O^2$ 수치 계산"처럼 무엇을 연습하는지 한 줄.

## 5. PDF 만들기 (4단계 조립에서)
```bash
python3 <REPO>/workbook/build_workbook.py --ids <id1,id2,…(manifest 순서)> --name 복습문제_<range>_<slug> \
  --pdf-dir <REPO>/복습노트/<range> --build-dir <RUN>/workbook-build
```
- 결과: `복습노트/<range>/복습문제_<range>_<slug>-문제.pdf`, `-답안.pdf`.
- 종료 코드 2 또는 `ERROR` 줄: 그 id를 후보에서 같은 절의 다른 문제로 바꿔 manifest를 고치고 한 번만 다시 만든다. 또 실패하면 그 id를 빼고 "미해결"로 보고한다.
- `OVERFLOW <파일>: <id>`: PDF는 남는다. 그 문제 쪽이 넘친 것이므로 "미해결"로 보고한다(workbook md 수정은 이 스킬의 일이 아니다).
- 인터넷이 필요하다(Pretendard, KaTeX CDN).
````

- [ ] **Step 8: `references/review-prompt.md` 작성**

````markdown
# 리뷰어 지시문 (lite에서는 생략)

---
전자회로2 복습팩 초안을 검토한다. 파일은 수정하지 않는다.

- 대상: `<RUN>/repo/복습노트/<range>/<정리노트 html>`, `<RUN>/manifest.json`의 `problems`
- 근거: `<RUN>/summaries/stt-*.md`, `<RUN>/slides.txt`, `<RUN>/candidates.tsv`, Razavi `<RUN>/repo/교과서/마이크로전자회로/<N>장.pdf`, 문제 md(`<RUN>/repo/교과서/마이크로전자회로/chNN/…`, `<RUN>/repo/from_the_past/md/…`)
- 규칙: `<SKILL>/references/content-rules.md`, `problem-selection.md`

확인할 것:
1. **사실 오류**: 식, 정의, 부호, 근사 조건(예: "$g_m r_O \gg 1$일 때"), 소신호 등가회로가 요약·슬라이드·교과서와 맞는가. 출력저항·이득 식은 한 번 직접 유도해 본다.
2. **누락**: 요약의 핵심 내용·강조 발언·미룬 유도 중 노트에 없는 것.
3. **범위**: "예고만/안 다룸" 내용이 본문에 설명되어 있는가.
4. **ELI5 품질**: 쉽게 말하면(eli5) 레이어가 전문용어 없이 1~3문장인가, 그림(회로도)이 개념을 실제로 보여 주는가.
5. **문제 선별**: 각 `problems[]`에 대해 md 원문과 풀이를 읽고 — 수업에서 다룬 절만으로 풀리는가, `why`가 실제 문제 내용과 맞는가, `anchor` 토픽이 맞는가, 구성(예제·연습/장말·기출 비율, 절마다 최소 1개)이 규칙과 맞는가. 빠진 "다룸" 절이 있으면 `candidates.tsv`에서 대체 후보 id를 제안한다.
6. **표현**: 표 첫 열이 한 글자씩 줄바꿈되거나 빈 칸이 있는 표, 잘린 문장.

출력 형식(이것만):
```
## Critical
- [s2-rout] 문제 → 고칠 내용
## Important
- [P9.12] …
## Minor
- …
```
각 항목은 토픽 id 또는 문제 id로 시작한다. 없으면 "없음".
---
````

- [ ] **Step 9: `references/browser-check.md` 작성**

ML 파일을 복사한 뒤 `## 복습문제` 절을 지우고 PDF 확인 절을 넣는다.
```bash
SKILL=/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/.claude/skills/ec2-review-pack
cp /Users/hyunjun_macbook_pro/Documents/Univ/머신러닝기초/.claude/skills/ml-review-pack/references/browser-check.md "$SKILL/references/"
SKILL="$SKILL" python3 - <<'EOF'
import os, re
p = os.path.join(os.environ["SKILL"], "references", "browser-check.md")
t = open(p, encoding="utf-8").read()
new = """## 복습문제 PDF (문제가 1개 이상일 때)
정리노트의 `s<N>-links` 토픽으로 넘긴 뒤 아래를 실행한다.
```js
await Promise.all(Array.from(document.querySelectorAll('a[href$=".pdf"]')).map(async (a) => {
  const r = await fetch(a.href, { method: 'HEAD' });
  return { href: a.getAttribute('href'), status: r.status, type: r.headers.get('content-type') };
}))
```
통과: 링크가 2개(문제·답안)이고 모두 `status: 200`, `type: "application/pdf"`. PDF 내용은 `Read` 도구(`pages: "1-2"`)로 첫 두 쪽을 열어 제목이 `복습문제_<range>_<slug>`이고 첫 문제가 manifest의 첫 id인지 확인한다.

"""
t2, n = re.subn(r"## 복습문제\n.*?(?=## 마무리)", new, t, flags=re.S)
assert n == 1, "## 복습문제 절을 찾지 못함"
t2 = t2.replace("## 가로 넘침 측정 (두 페이지 공통)", "## 가로 넘침 측정")
open(p, "w", encoding="utf-8").write(t2)
print("OK")
EOF
```
Expected: `OK`

- [ ] **Step 10: 통과 확인**

Run: `python3 -m unittest discover -s .claude/skills/ec2-review-pack/tests -p test_skill_files.py`
Expected: `OK`

`test_no_ml_leftovers`가 복사한 스크립트(`html2md.py`, `check_html.py`)의 주석이나 docstring 때문에 실패하면, 그 줄의 해당 단어만 전자회로2에 맞는 말로 바꾼다. 예: `복습문제` 카드 주석은 그대로 두고, `MML`만 `교과서`로 바꾼다. 동작 코드는 바꾸지 않는다.

- [ ] **Step 11: 전체 테스트**

Run: `python3 -m unittest discover -s .claude/skills/ec2-review-pack/tests`
Expected: `OK`

- [ ] **Step 12: 커밋**

```bash
git add .claude/skills/ec2-review-pack/references .claude/skills/ec2-review-pack/tests/test_skill_files.py .claude/skills/ec2-review-pack/scripts
git commit -m "docs(ec2-review-pack): add reference briefs for summary, notes, selection, review

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: SKILL.md

**Files:**
- Create: `SKILL/SKILL.md`
- Modify: `SKILL/tests/test_skill_files.py`(`TestSkillMd`, `TestBackupSnippet` 추가)

**Interfaces:**
- Consumes: Task 1~6의 모든 CLI와 참조 문서 경로
- Produces: `/ec2-review-pack` 스킬

- [ ] **Step 1: 실패하는 테스트 추가 (`tests/test_skill_files.py`의 `if __name__` 위에)**

```python
SKILL_MD = SKILL / "SKILL.md"


class TestSkillMd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SKILL_MD.read_text(encoding="utf-8")

    def test_frontmatter(self):
        m = re.match(r"---\nname: (.+)\ndescription: (.+)\n---\n", self.text)
        self.assertIsNotNone(m, "frontmatter는 name, description 두 줄")
        self.assertEqual(m.group(1), "ec2-review-pack")
        for word in ("전자회로2", "정리노트", "복습문제"):
            self.assertIn(word, m.group(2))
        self.assertLessEqual(len(m.group(2)), 1024)

    def test_referenced_files_exist(self):
        refs = set(re.findall(r"(?:references|scripts|assets)/[\w.-]+\.(?:md|py|html)", self.text))
        self.assertGreaterEqual(len(refs), 12)
        for rel in sorted(refs):
            with self.subTest(rel=rel):
                self.assertTrue((SKILL / rel).exists(), rel)

    def test_every_reference_is_used(self):
        for path in sorted((SKILL / "references").glob("*.md")):
            with self.subTest(ref=path.name):
                self.assertIn(f"references/{path.name}", self.text)

    def test_steps_present(self):
        for n in range(10):
            with self.subTest(step=n):
                self.assertRegex(self.text, rf"\n### {n}\. ")

    def test_workbook_build_command(self):
        self.assertIn("workbook/build_workbook.py --ids", self.text)
        self.assertIn("--pdf-dir", self.text)
        self.assertIn("--build-dir", self.text)


class TestBackupSnippet(unittest.TestCase):
    """SKILL.md 4단계 백업 스니펫(python 부분)을 임시 폴더에서 실제로 실행한다."""

    @classmethod
    def setUpClass(cls):
        text = SKILL_MD.read_text(encoding="utf-8")
        m = re.search(r"```bash\nRANGE=<range> REPO=… RUN=… python3 - <<'EOF'\n(.*?)\nEOF\n```", text, re.S)
        assert m, "SKILL.md 4단계 백업 스니펫을 찾지 못함"
        cls.code = m.group(1)

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.notes = self.tmp / "repo" / "복습노트"
        self.notes.mkdir(parents=True)
        self.run_dir = self.tmp / "run"
        self.run_dir.mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def backup(self, range_):
        env = dict(os.environ, RANGE=range_, REPO=str(self.tmp / "repo"), RUN=str(self.run_dir))
        return subprocess.run([sys.executable, "-"], input=self.code, env=env, capture_output=True, text=True)

    def backups(self):
        return sorted(p for p in self.run_dir.iterdir() if p.name.startswith("previous-"))

    def test_nothing_to_back_up(self):
        r = self.backup("0923")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("백업할 기존 팩 없음", r.stdout)
        self.assertEqual(self.backups(), [])

    def test_backs_up_note_pdfs_and_problem_list(self):
        pack = self.notes / "0923"
        (pack / "figures_0923").mkdir(parents=True)
        (pack / "figures_0923" / "a.svg").write_text("<svg/>", encoding="utf-8")
        (pack / "정리노트_0923_A.html").write_text("n", encoding="utf-8")
        (pack / unicodedata.normalize("NFD", "정리노트_0923_A.md")).write_text("m", encoding="utf-8")
        (pack / "복습문제_0923_A-문제.pdf").write_bytes(b"%PDF")
        (pack / unicodedata.normalize("NFD", "복습문제_0923_A-답안.pdf")).write_bytes(b"%PDF")
        (pack / "problems.txt").write_text("P10.01 | x\n", encoding="utf-8")
        (self.notes / "0918").mkdir()
        (self.notes / "0918" / "정리노트_0918_B.html").write_text("other", encoding="utf-8")
        for _ in range(2):  # 같은 세션에서 다시 실행해도 이전 백업을 덮지 않는다
            r = self.backup("0923")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("백업 6항목(파일 6개)", r.stdout)
        dirs = self.backups()
        self.assertEqual(len(dirs), 2)
        names = sorted(unicodedata.normalize("NFC", n) for n in os.listdir(dirs[0]))
        self.assertEqual(names, ["figures_0923", "problems.txt", "복습문제_0923_A-답안.pdf",
                                 "복습문제_0923_A-문제.pdf", "정리노트_0923_A.html", "정리노트_0923_A.md"])

    def test_bad_range_fails_loudly(self):
        for bad in ("", "<range>", "923"):
            with self.subTest(bad=bad):
                r = self.backup(bad)
                self.assertEqual(r.returncode, 1)
                self.assertIn("백업 중단", r.stderr)
        self.assertEqual(self.backups(), [])
```

- [ ] **Step 2: 실패 확인**

Run: `python3 -m unittest discover -s .claude/skills/ec2-review-pack/tests -p test_skill_files.py`
Expected: FAIL (`FileNotFoundError: … SKILL.md`)

- [ ] **Step 3: `SKILL.md` 작성**

````markdown
---
name: ec2-review-pack
description: 전자회로2 수업의 STT·강의노트·Razavi 교과서로 ELI5 정리노트 HTML(+MD, 그림)을 만들고, 그 수업 범위에 맞는 workbook 문제 약 10개를 골라 복습문제 PDF(문제+답안)를 만들어 복습노트/<날짜>/에 저장한다. "정리노트", "복습문제", "복습팩", "0923 정리해줘"처럼 전자회로2 수업 정리를 요청하거나 /ec2-review-pack [MMDD|MMDD-MMDD] [lite]로 부를 때 사용한다.
---

# 전자회로2 복습팩

수업 녹음 전사(STT)와 강의자료, Razavi 교과서로 한 기간의 정리노트를 만들고, workbook에서 그 범위 문제를 골라 복습문제 PDF를 만든다. 중간에 사용자에게 묻지 않고 끝에 한 번 보고한다. 커밋은 제안만 한다.

**산출물** (`복습노트/<range>/`):
`정리노트_<range>_<slug>.html`, 같은 이름의 `.md`, `figures_<range>/`, 그리고 문제가 1개 이상이면 `복습문제_<range>_<slug>-문제.pdf`, `복습문제_<range>_<slug>-답안.pdf`, `problems.txt`

**인자**: `[MMDD | MMDD-MMDD] [lite]`
- `lite`: 작성자·요약 에이전트를 sonnet으로, 6단계 리뷰를 생략한다. 기계 검사와 브라우저 검사는 그대로 한다.

**진행 표시**: 단계마다 한 줄만 쓴다. 예: `3/9 작성 중: 섹션 5개 (병렬)`

**경로 약속**
- `SKILL` = 이 파일이 있는 폴더(`.claude/skills/ec2-review-pack`)의 절대 경로
- `REPO` = 저장소 루트
- `RUN` = `<scratchpad>/review-pack/<range>/`
- 셸 상태는 Bash 호출 사이에 이어지지 않는다. 아래 명령의 `$SKILL`, `$RUN`, `$REPO`는 실행할 때마다 실제 절대 경로로 바꿔 쓰거나, 같은 명령 앞에 `SKILL=… RUN=… REPO=…`를 붙여 설정한다. `cd`는 쓰지 않고 파일도 절대 경로로 넘긴다.

## 절차

### 0. 준비
1. `REPO`에 `STT/`, `강의노트/`, `교과서/마이크로전자회로/`, `workbook/build_workbook.py`가 모두 있는지 확인한다. 하나라도 없으면 "전자회로2 저장소에서만 동작합니다"라고 알리고 멈춘다.
2. STT 목록은 NFC로 읽는다. macOS에는 NFD 파일명이 섞여 있다.
   ```bash
   python3 -c "import os,unicodedata as u,re;n=[u.normalize('NFC',f) for f in os.listdir('$REPO/STT')];print(sorted(m.group(1) for f in n if f.endswith('전회2.md') and (m:=re.match(r'(\d{4})',f))))"
   ```
3. 기간을 정한다.
   - 인자가 있으면 그 기간을 쓴다.
   - 인자가 없으면 `복습노트/*/정리노트_<range>_*.html` 중 가장 늦은 끝 날짜를 찾고, 그 뒤의 STT를 모두 쓴다. 팩이 하나도 없으면 사용 가능한 STT 날짜를 보여 주고 "기간을 인자로 주세요(예: /ec2-review-pack 0923)"라고 알린 뒤 멈춘다.
   - 해당 STT가 하나도 없으면 사용 가능한 날짜를 보여 주고 멈춘다.
   - `range`는 첫 STT 날짜 하나이거나 `첫-끝` 형식이다.
4. 실행 폴더를 만든다. 서브에이전트에게는 `RUN`, `RUN/repo`, `SKILL` 경로만 넘긴다.
   ```bash
   mkdir -p "$RUN"/{summaries,sections,work} && ln -sfn "$REPO" "$RUN/repo"
   ```
   에이전트는 `RUN` 밖에 쓰지 않는다. 임시·보조 파일은 `RUN/work/`에만 둔다. 저장소(`STT/`, `강의노트/`, `교과서/`, `workbook/`, `from_the_past/`)에는 아무도 쓰지 않고, `복습노트/`에는 메인 에이전트만 쓴다.

### 1. 범위 파악
1. **먼저** 관련 `강의노트/2026F_Lec*_*.pdf` 텍스트를 슬라이드 번호와 함께 `RUN/slides.txt`에 추출한다(PyMuPDF, 쪽마다 `=== LNN sK ===`, `LNN`은 파일명의 `LecN`을 두 자리로). 요약 에이전트는 이 파일이 있다고 보고 시작하므로 추출이 끝난 뒤에 띄운다.
   - 관련 PDF: 이전 팩(`복습노트/*/정리노트_*`)이 끝까지 다루지 않은 Lec PDF 전부. 확실하지 않으면 넉넉히 넣는다.
   - 추출에 실패하면 STT만으로 진행하고 보고서에 적는다(브리프의 `slides.txt` 줄은 "없음"으로 바꿔 넘긴다).
2. 그다음 STT 날짜마다 요약 에이전트 1명을 **병렬로** 띄운다. 브리프는 `references/stt-summary-prompt.md`에 있다.
   - `<2026F_LecN_*.pdf>`: 그 날짜가 다룬 슬라이드가 들어 있는 PDF. 확실하지 않으면 1의 관련 PDF를 모두 적는다.
   - `<YYYY-MM-DD>`: 연도는 이번 학기 연도(오늘 날짜 기준), 월·일은 `<MMDD>`.
3. 에이전트가 도는 동안 메인 에이전트는 후보 문제 목록을 만든다(`references/problem-selection.md` 1).
   ```bash
   python3 "$SKILL/scripts/problem_index.py" --repo "$REPO" --used "$REPO/복습노트" --chapters <장> > "$RUN/candidates.tsv"
   ```
   장은 slides.txt의 강의자료 제목(예: `Lec3_Ch9_…` → 9)으로 정한다. 강의자료가 전자회로1 복습(Lec1–2)뿐이면 이 단계를 건너뛴다.

### 2. manifest
- 요약들의 슬라이드 대조표와 용어·식 목록으로 `RUN/manifest.json`을 쓴다. 규칙은 `references/manifest-guide.md`에 있다.
- 문제 선별은 `references/problem-selection.md`를 따른다. 요약의 `## 교과서 절 대조`와 `RUN/candidates.tsv`로 고른다.
- 검증: `python3 "$SKILL/scripts/manifest.py" "$RUN/manifest.json" "$REPO"` 결과가 `OK`여야 한다.

### 3. 작성
- 섹션마다 작성자 1명을 띄운다. 브리프는 `references/content-rules.md`, 위젯 규칙은 `references/widget-rules.md`에 있다.
- 모두 **한 메시지에서 병렬로** 띄운다. 모델은 opus, `lite`이면 sonnet이다.
- 브리프의 `<…>` 자리는 실제 경로, id, 금지어 목록(`<forbidden 목록>`), 예고 토픽 id(`<preview_topic>`), 섹션 작성자에게 필요한 교과서 장 PDF와 쪽(`<N>장.pdf`, `<쪽>`), 그리고 manifest `links` 중 그 섹션 토픽에 속한 것만(`<이 섹션의 links 목록>`) 채워 넣는다. 요약·예고 섹션 작성자에게는 문제 수(0이면 "문제 없음")도 알린다.
- 위젯은 팩 전체에 0~2개다. 병렬 작성자끼리는 서로를 모르므로 **메인 에이전트가 띄우기 전에** 위젯을 둘 토픽(0~2개)을 정하고, 그 토픽의 섹션 작성자 브리프에만 `<위젯>` 자리에 "토픽 `<토픽 id>`에 위젯 1개: <무엇을 움직이면 무엇이 보이는지>"를 적는다. 나머지 작성자의 `<위젯>` 자리에는 "위젯 없음"이라고 적는다. 정한 토픽과 이유는 보고서 "스킬이 정한 사항"에 적는다.

### 4. 조립
- **처음 조립할 때만**: `복습노트/<range>/`에 이번 `range`의 산출물(`정리노트_<range>_*`, `복습문제_<range>_*`, `problems.txt`, `figures_<range>/`)이 하나라도 있으면 먼저 백업한다. 다시 조립할 때(5~8단계에서 돌아온 경우)는 백업하지 않는다. 이미 스킬이 만든 초안이 백업에 섞이기 때문이다.
  - `RANGE`, `REPO`, `RUN`을 모두 실제 값으로 바꿔 한 명령으로 실행한다. 파일명은 NFC로 비교하므로 NFD 파일명도 잡힌다.
  - 백업은 매번 새 폴더 `RUN/previous-<시각>-<임의>/`에 만든다. `RANGE`가 형식에 안 맞거나, 대상이 있는데 복사된 파일 수가 다르면 종료 코드 1로 멈춘다. 이때는 조립하지 말고 원인을 고친다.
```bash
RANGE=<range> REPO=… RUN=… python3 - <<'EOF'
import os, re, shutil, sys, tempfile, time, unicodedata as u
r, run = os.environ["RANGE"], os.environ["RUN"]
notes = os.path.join(os.environ["REPO"], "복습노트")
if not re.fullmatch(r"\d{4}(-\d{4})?", r) or not os.path.isdir(run):
    sys.exit(f"백업 중단: RANGE={r!r} 또는 RUN={run!r} 잘못됨")
def want(n):
    n = u.normalize("NFC", n)
    return n.startswith((f"정리노트_{r}_", f"복습문제_{r}_")) or n in (f"figures_{r}", "problems.txt")
def listdir_nfc(d):  # NFD 폴더명도 찾는다
    return {u.normalize("NFC", n): os.path.join(d, n) for n in os.listdir(d)} if os.path.isdir(d) else {}
pack = listdir_nfc(notes).get(r)
hits = sorted((n, p) for n, p in listdir_nfc(pack).items() if want(n)) if pack else []
if not hits:
    print("백업할 기존 팩 없음"); sys.exit(0)
def count(p):
    return sum(len(f) for _, _, f in os.walk(p)) if os.path.isdir(p) else 1
dst = tempfile.mkdtemp(prefix=time.strftime("previous-%Y%m%d-%H%M%S-"), dir=run)  # 항상 새 폴더
for n, a in hits:
    b = os.path.join(dst, n)
    shutil.copytree(a, b) if os.path.isdir(a) else shutil.copy2(a, b)
want_n, got_n = sum(count(a) for _, a in hits), count(dst)
if got_n != want_n:
    sys.exit(f"백업 실패: 파일 {want_n}개 중 {got_n}개만 복사됨 → {dst}")
print(f"백업 {len(hits)}항목(파일 {got_n}개): {dst}", *(a for _, a in hits), sep="\n")
EOF
```
- 정리노트를 조립한다.
```bash
python3 "$SKILL/scripts/assemble.py" --run "$RUN" --out "$REPO/복습노트/<range>"
```
- 문제가 1개 이상이면 PDF를 만든다(`references/problem-selection.md` 5). `--ids`는 manifest `problems` 순서대로 쉼표로 잇는다.
```bash
python3 "$REPO/workbook/build_workbook.py" --ids <id,…> --name 복습문제_<range>_<slug> --pdf-dir "$REPO/복습노트/<range>" --build-dir "$RUN/workbook-build"
```
  - 빌드 오류로 id를 바꿨으면 manifest를 고쳐 2단계 검증부터 다시 하고 이 단계를 다시 한다(백업은 하지 않는다).

### 5. 기계 검사
```bash
python3 "$SKILL/scripts/check_html.py" --manifest "$RUN/manifest.json" --note "$REPO/복습노트/<range>/<정리노트>.html"
```
- `FAIL`이면 Problem의 `where`(토픽 id, 섹션 id)로 담당 작성자를 찾는다. `broken-link`가 PDF이면 4단계 PDF 빌드를 확인한다.
- 그 작성자에게 문제 목록을 보내 조각을 고치게 한다(SendMessage, 안 되면 같은 브리프로 새 에이전트).
- 고친 뒤 4단계부터 다시 한다. 최대 2회까지이며, 그래도 남으면 "미해결"로 보고한다.

### 6. 리뷰 (`lite`면 생략)
- 리뷰어 1명을 띄운다. 브리프는 `references/review-prompt.md`에 있다.
- Critical과 Important는 모두, Minor는 쉬운 것만 고친다. 문제 선별 지적은 메인 에이전트가 manifest를 고치고 PDF를 다시 만든다.
- 담당 작성자별로 **한 번에 모아서** 수정을 요청한다. 수정은 한 번만 한다.
- 수정 후 4~5단계를 다시 한다. 반영하지 않은 항목은 보고서에 적는다.

### 7. 브라우저 검증
- `references/browser-check.md`대로 한다.
  - http.server를 빈 포트에 띄운다.
  - 확인: KaTeX 오류 0, 남은 `$` 없음, 375px에서 가로 스크롤 없음, 다크모드, 위젯, 링크(복습문제 PDF 포함), 콘솔 오류
- 결함은 5단계와 같은 방식으로 작성자에게 되돌린다. 이것도 최대 2회 규칙에 포함된다.
- 끝나면 서버를 종료한다.

### 8. MD 변환
```bash
python3 "$SKILL/scripts/html2md.py" "$REPO/복습노트/<range>/<정리노트>.html" --check
```
- `OK`가 나와야 한다.
- 누락이 나오면 대부분 HTML 조각의 마크업 문제다(수식이 `svg`나 `.controls` 안에 있는 경우 등). 조각을 고치고 4단계부터 다시 한다.

### 9. 보고
다음 형식으로 끝낸다.
```
## 복습팩 <range> 완료
- 파일: 복습노트/<range>/… (html 1, md 1, pdf 2, figures_<range>/ N개)
- 범위: 배운 슬라이드 … / 교과서 절 … / 예고만: …
- 문제 N개: P9.05(장말, 9.1.2) — <why>, … (문제가 0개면 "없음 — <이유>")
- 스킬이 정한 사항: slug, 섹션 구성, 위젯, 문제 구성, 뺀 내용과 이유
- 미해결: … (없으면 "없음")
- 커밋 제안: git add 복습노트/<range> && git commit -m "docs(notes): add review pack <range>"
```
실행 폴더 경로(`RUN`)도 적는다. 수정이 필요하면 조각을 고쳐 4단계부터 다시 돌리면 된다.

## 오류 처리
| 상황 | 동작 |
|---|---|
| 저장소가 아님 | 알리고 멈춤 |
| 기간에 해당하는 STT 없음 / 인자 없음 + 팩 없음 | 사용 가능한 날짜를 보여 주고 멈춤 |
| PDF 텍스트 추출 실패 | STT만으로 진행하고 보고서에 표시 |
| 범위가 workbook(9~11장) 밖 | 문제 0개, PDF 없이 정리노트만. 보고서에 이유 |
| `problem_index.py`가 ERROR md를 냄 | 그 md는 후보에서 빼고 "미해결"에 적음 |
| `build_workbook.py` 오류(종료 코드 1·2) | 해당 id를 같은 절 후보로 한 번 교체해 재빌드. 또 실패하면 그 id를 빼고 "미해결" |
| `OVERFLOW` | PDF는 남음. "미해결"에 적음 |
| 포트 사용 중 | 다른 빈 포트 사용 |
| 같은 range의 팩이 이미 있음 | 4단계 첫 조립 전에 기존 html·md·pdf·`problems.txt`·`figures_<range>/`를 새 폴더 `RUN/previous-<시각>-<임의>/`에 복사하고(다시 조립할 때는 복사하지 않음) 백업 경로를 보고서에 적음. 백업 명령이 실패하면 조립하지 않고 원인을 고친다 |
| 검사 2회 실패 | 멈추지 않고 나머지 단계를 끝낸 뒤 "미해결"로 보고 |
````

- [ ] **Step 4: 통과 확인**

Run: `python3 -m unittest discover -s .claude/skills/ec2-review-pack/tests`
Expected: `OK`(모든 테스트)

- [ ] **Step 5: 커밋**

```bash
git add .claude/skills/ec2-review-pack/SKILL.md .claude/skills/ec2-review-pack/tests/test_skill_files.py
git commit -m "feat(ec2-review-pack): add skill procedure

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 8: 시험 실행 (0923)

**Files:** 없음(검증만). `복습노트/0923/` 산출물은 **커밋하지 않고** 사용자에게 보여 준 뒤 커밋 여부를 묻는다.

- [ ] **Step 1: 스킬 실행**

`/ec2-review-pack 0923`을 SKILL.md 절차 그대로 실행한다(lite 아님).

- [ ] **Step 2: 산출물 확인**

Run: `ls 복습노트/0923/`
Expected: `정리노트_0923_<slug>.html`, `.md`, `복습문제_0923_<slug>-문제.pdf`, `-답안.pdf`, `problems.txt`(그리고 그림이 있으면 `figures_0923/`)

- [ ] **Step 3: 기계 검증 재확인**

```bash
python3 .claude/skills/ec2-review-pack/scripts/check_html.py --manifest <RUN>/manifest.json --note 복습노트/0923/<정리노트>.html
python3 .claude/skills/ec2-review-pack/scripts/html2md.py 복습노트/0923/<정리노트>.html --check
```
Expected: 둘 다 마지막 줄 `OK`

- [ ] **Step 4: PDF 눈으로 확인**

`Read` 도구로 `복습노트/0923/복습문제_0923_<slug>-문제.pdf`(pages "1-3")를 연다. 문제 수가 8~12개이고, 모두 10장 차동증폭기의 "다룸" 절 문제이며, 기출이 1~2개 들어 있는지 확인한다.

- [ ] **Step 5: 결과 보고와 스킬 보완**

보고서를 사용자에게 보여 준다. 실행 중 드러난 SKILL.md나 references의 모호함은 해당 파일을 고치고 전체 테스트(`python3 -m unittest discover -s .claude/skills/ec2-review-pack/tests`)를 통과시킨 뒤 커밋한다.
```bash
git add .claude/skills/ec2-review-pack
git commit -m "fix(ec2-review-pack): clarify steps found in 0923 pilot

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```
`복습노트/0923/` 커밋, main 병합, push는 사용자에게 묻는다.
