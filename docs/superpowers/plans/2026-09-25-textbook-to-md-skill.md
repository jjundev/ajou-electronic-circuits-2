# 교과서 문제 → MD 변환 스킬 (`textbook-to-md`) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 12장 이후의 장을 "N장 변환해줘" 한 번으로 9–11장과 같은 품질로 변환하는 프로젝트 스킬을 만든다. 스킬은 장 단위 검증 도구, FORMAT 관례 정리, 프롬프트 템플릿과 함께 동작한다.

**Architecture:** 새 도구 `_tools/verify_chapter.py`가 장 단위 정합성을 검사한다. 대상은 번호 연속, 그림 id 세 집합, 이미지 링크, 절 순서, README 최신 여부, 다시 크롭한 결과와의 픽셀 비교다. 판독 관례는 FORMAT.md가 이미 절마다 담고 있으므로(커밋 `10b7995`) 그 구조를 따르고, 빠진 두 줄만 해당 절에 더한다. 스킬(`.claude/skills/textbook-to-md/`)은 절차만 담고, 형식은 FORMAT.md를 가리킨다. 작성·리뷰·조사 에이전트 프롬프트는 `<<자리표시자>>` 템플릿으로 둔다. 리뷰 보고서는 `docs/superpowers/reports/ch<N>/`에 커밋한다.

**Tech Stack:** Python 3 (Homebrew), PyMuPDF (`import fitz`), PyYAML, 표준 라이브러리 `unittest` (pytest는 설치돼 있지 않음). Claude Code 프로젝트 스킬(SKILL.md + references).

**Spec:** `docs/superpowers/specs/2026-09-25-textbook-to-md-skill-design.md`

## Global Constraints

- 모든 경로는 저장소 루트 `/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2` 기준이다.
- **작업 위치:** main에서 브랜치 `feat/textbook-to-md-skill`을 따서 **메인 checkout에서** 작업한다. worktree에서 하지 않는다. Task 3의 `--recrop` 인수 검사에 추적하지 않는 PDF(`교과서/마이크로전자회로/9장.pdf`, `10장.pdf`, `11장.pdf`)가 필요하기 때문이다.
- **git add:** 추적하지 않는 파일(`STT/`, `강의노트/`, `교과서/**/*.pdf`)은 절대 add하지 않는다. `git add -A`, `git add .`는 쓰지 않고 항상 경로를 명시한다.
- **커밋 메시지:** 마지막 줄은 빈 줄 뒤 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`이다.
- **도구 코드 스타일:** 기존 `_tools/*.py`를 따른다. 모듈 docstring에 사용법을 적고, `main(argv)`가 exit code를 돌려주며, 메시지는 한국어다. 기존 도구의 함수는 import해서 재사용한다(`check_md.KIND_BY_PREFIX`, `ID_RE`, `md_files`, `split_frontmatter`, `crop_figures.crop_all`, `figure_filename`, `make_index.build_index`).
- **테스트 실행:** `python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests`로 한다. 지금은 테스트 39개가 모두 통과한다.
- **기존 결과물:** 9–11장 md·그림·README(377문제)는 이 계획에서 **수정하지 않는다.** 검증 도구가 오류를 내면 도구 쪽을 의심하고, 실제 결함이면 고치지 말고 보고한다.
- **스킬 위치:** `.claude/skills/textbook-to-md/`에 두고 git으로 추적한다(사용자 결정 #1).
- **리뷰 보고서:** `docs/superpowers/reports/ch<N>/review-<묶음>.md`로 커밋한다. 지적이 없는 묶음도 커밋한다(사용자 결정 #7).
- **서브에이전트:** 스킬이 띄우는 서브에이전트는 모두 opus다. 렌더링 검증(md → PNG)은 하지 않는다(사용자 지시).

## Review Focus

1. **따옴표 없는 그림 id:** figures.yaml에 따옴표 없는 그림 id(`9.30:` → 숫자 9.3)가 있으면 `verify_chapter`는 traceback 없이 "따옴표" 오류 한 줄을 내야 한다. → Task 1 `test_unquoted_figure_id`
2. **깨진 frontmatter:** frontmatter가 깨진 md가 하나 있어도 파일 이름을 담은 오류를 내고, 나머지 검사는 계속해야 한다. → Task 1 `test_broken_frontmatter_reported_not_raised`
3. **PDF가 없는 상태의 `--recrop`:** worktree에서 PDF 심볼릭 링크를 빠뜨린 경우처럼 PDF가 없으면, traceback 없이 "다시 자르기 실패" 오류를 내야 한다. → Task 2 `test_recrop_missing_pdf_is_error`
4. **원문에 연습문제가 없는 예제:** 예제 11.29처럼 원문에 연습문제가 없는 예제는 오류가 아니라 INFO여야 하고, exit 0이어야 한다. → Task 1 `test_example_without_exercise_is_info`, Task 3 수용 검사(ch11)
5. **md가 하나도 없는 장 폴더:** 막 만든 장 폴더처럼 md가 없으면 "문제 md가 없음" 오류와 exit 1을 내야 한다. 통과로 보이면 안 된다. → Task 1 `test_empty_chapter_is_error`

---

## File Structure

| 경로 | 상태 | 책임 |
|---|---|---|
| `교과서/마이크로전자회로/_tools/verify_chapter.py` | 새로 만듦 | 장 단위 정합성 검사 (CLI + `verify()`) |
| `교과서/마이크로전자회로/_tools/tests/test_verify_chapter.py` | 새로 만듦 | 위 도구의 unittest |
| `교과서/마이크로전자회로/FORMAT.md` | 수정 | 새 도구 등록(폴더·검사 절), 빠진 관례 두 줄(변압기 결합, 연습문제 없는 예제) |
| `docs/superpowers/reports/README.md` | 새로 만듦 | 보고서 폴더 규칙과 장별 보존 현황 |
| `docs/superpowers/reports/ch09/review-{A..G}.md`, `ch11/review-H.md` | 새로 만듦 (복사) | 남아 있는 과거 리뷰 보고서 |
| `.claude/skills/textbook-to-md/references/{survey,common,writer,reviewer}.md` | 새로 만듦 | 에이전트 프롬프트 템플릿 |
| `.claude/skills/textbook-to-md/SKILL.md` | 새로 만듦 | 절차, 멈춤 조건, 자리표시자 표 |

---

### Task 0: 작업 브랜치

- [ ] **Step 1: 브랜치를 만든다**

```bash
cd "/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2"
git status --short | grep -v '^??'   # 출력이 비어 있어야 함
git checkout -b feat/textbook-to-md-skill main
```
Expected: `Switched to a new branch 'feat/textbook-to-md-skill'`

- [ ] **Step 2: 설계·계획 문서를 커밋한다** (두 파일은 이미 작업 트리에 있다)

```bash
git add docs/superpowers/specs/2026-09-25-textbook-to-md-skill-design.md docs/superpowers/plans/2026-09-25-textbook-to-md-skill.md
git commit -m "docs: add textbook-to-md skill design and plan

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 1: `verify_chapter.py` — 번호·그림·구조 검사와 CLI

**Files:**
- Create: `교과서/마이크로전자회로/_tools/verify_chapter.py`
- Test: `교과서/마이크로전자회로/_tools/tests/test_verify_chapter.py`

**Interfaces:**
- Consumes:
  - `check_md.KIND_BY_PREFIX: dict[str, str]` (`{"E": "예제", "X": "연습문제", "P": "장말문제"}`)
  - `check_md.ID_RE` (`^([EXP])(\d+)\.(\d{2})$`)
  - `check_md.md_files(ch_dir) -> list[Path]`
  - `check_md.split_frontmatter(text) -> (dict, str)` (형식이 틀리면 ValueError)
  - `crop_figures.figure_filename(fig_id: str) -> str` (`"9.2"` → `"fig9-02.png"`)
  - 테스트 픽스처용: `crop_figures.crop_all(ch_dir) -> list[Path]`, `make_index.build_index(ch_dir, title) -> str`
- Produces:
  - `verify(ch_dir, recrop=False) -> tuple[list[str], list[str]]`: (errors, infos). `recrop`은 Task 2에서 쓴다.
  - `main(argv: list[str]) -> int`: 0 = 통과, 1 = 오류 있음, 2 = 사용법 오류.
  - 출력 형식: 줄마다 `ERROR <msg>` 또는 `INFO  <msg>`, 마지막 줄은 `<장 폴더>: 오류 N개, 참고 M개`.

- [ ] **Step 1: 실패하는 테스트를 쓴다**

`교과서/마이크로전자회로/_tools/tests/test_verify_chapter.py`:

```python
import io
import re
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from crop_figures import crop_all, figure_filename  # noqa: E402
from make_index import build_index  # noqa: E402
from verify_chapter import main, verify  # noqa: E402

KIND = {"E": "예제", "X": "연습문제", "P": "장말문제"}
FIGURES_YAML = (
    "pdf: ../../book.pdf\n"
    "dpi: 144\n"
    "figures:\n"
    '  "9.2": {pdf_page: 1, bbox: [0, 0, 72, 36]}\n'
)


def make_md(id_, figures=(), depends=(), sections=None):
    prefix, chapter, num = id_[0], id_[1:].split(".")[0], id_.split(".")[1]
    kind = KIND[prefix]
    number = f"{int(chapter)}.{int(num)}"
    fm = ["---", f"id: {id_}", f"kind: {kind}", f'number: "{number}"', 'section: "9.1.1 절"',
          "book_page: 451", "pdf_page: 2"]
    if prefix == "P":
        fm += ["difficulty: 0", "sol: false"]
    fm += ["source_lang: ko"]
    if figures:
        fm += ["figures:"] + [f'  - {{id: "{f}", role: problem, panels: []}}' for f in figures]
    else:
        fm += ["figures: []"]
    fm += [f"depends_on: [{', '.join(depends)}]", "refs: []", "---"]
    if sections is None:
        sections = ["## 조건", "## 구할 것"]
        sections += [f"## 회로 — Fig {f}\n![Fig {f}](../figures/{figure_filename(f)})" for f in figures] \
            or ["## 회로 — 없음 (그림 없는 글 문제)"]
        if prefix == "E":
            sections.append("## 답 (검증용)")
    title = f"# {kind} {number} — 제목 {id_}"
    return "\n".join(fm) + "\n" + title + "\n\n" + "\n\n".join(s + "\n- 내용" for s in sections) + "\n"


def write_md(ch, id_, text=None, **kw):
    path = ch / KIND[id_[0]] / f"{id_}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text is not None else make_md(id_, **kw), encoding="utf-8")
    return path


def make_chapter(root: Path) -> Path:
    doc = fitz.open()
    page = doc.new_page(width=200, height=100)
    page.draw_rect(fitz.Rect(10, 10, 40, 30), color=(0, 0, 0), fill=(0, 0, 0))
    doc.save(str(root / "book.pdf"))
    ch = root / "ch09"
    (ch / "figures").mkdir(parents=True)
    (ch / "figures" / "figures.yaml").write_text(FIGURES_YAML, encoding="utf-8")
    write_md(ch, "E9.01", figures=["9.2"])
    write_md(ch, "X9.01", figures=["9.2"], depends=["E9.01"])
    write_md(ch, "P9.01")
    crop_all(ch)
    (ch / "README.md").write_text(build_index(ch, "9장 테스트"), encoding="utf-8")
    return ch


class ChapterCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.ch = make_chapter(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def assertError(self, *needles, recrop=False):
        errors, _ = verify(self.ch, recrop=recrop)
        self.assertTrue(any(all(n in e for n in needles) for e in errors),
                        f"{needles} 를 담은 오류가 없음: {errors}")


class CleanChapterTest(ChapterCase):
    def test_clean_chapter_passes(self):
        self.assertEqual(verify(self.ch), ([], []))


class NumberingTest(ChapterCase):
    def test_gap_in_problem_numbers(self):
        write_md(self.ch, "P9.03")
        self.assertError("장말문제", "P9.02")

    def test_exercise_without_example(self):
        write_md(self.ch, "X9.02")
        self.assertError("X9.02", "E9.02")

    def test_example_without_exercise_is_info(self):
        write_md(self.ch, "E9.02")
        errors, infos = verify(self.ch)
        self.assertFalse(any("E9.02" in e for e in errors), errors)
        self.assertTrue(any("E9.02" in i and "연습문제 없음" in i for i in infos), infos)


class FigureTest(ChapterCase):
    def add_yaml_line(self, line):
        path = self.ch / "figures" / "figures.yaml"
        path.write_text(path.read_text(encoding="utf-8") + line + "\n", encoding="utf-8")

    def test_unused_figure_in_yaml(self):
        self.add_yaml_line('  "9.5": {pdf_page: 1, bbox: [0, 0, 10, 10]}')
        crop_all(self.ch)
        self.assertError("figures.yaml에만", "9.5")

    def test_md_refs_figure_missing_from_yaml(self):
        write_md(self.ch, "P9.02", figures=["9.7"])
        self.assertError("figures.yaml에 없는", "9.7")

    def test_missing_png(self):
        (self.ch / "figures" / "fig9-02.png").unlink()
        self.assertError("PNG 없음", "fig9-02.png")

    def test_stray_png(self):
        shutil.copy(self.ch / "figures" / "fig9-02.png", self.ch / "figures" / "fig9-99.png")
        self.assertError("figures.yaml에 없는 PNG", "fig9-99.png")

    def test_missing_image_link(self):
        write_md(self.ch, "E9.01", figures=["9.2"],
                 sections=["## 조건", "## 구할 것", "## 회로 — Fig 9.2", "## 답 (검증용)"])
        self.assertError("E9.01", "9.2", "이미지 링크 없음")

    def test_broken_image_link(self):
        text = make_md("P9.02").replace("## 회로 — 없음 (그림 없는 글 문제)",
                                        "## 회로 — 없음 (그림 없는 글 문제)\n![x](../figures/nope.png)")
        write_md(self.ch, "P9.02", text=text)
        self.assertError("P9.02", "깨진 이미지 링크", "nope.png")

    def test_unquoted_figure_id(self):
        self.add_yaml_line("  9.30: {pdf_page: 1, bbox: [0, 0, 10, 10]}")
        self.assertError("따옴표")


class StructureTest(ChapterCase):
    def test_section_order(self):
        write_md(self.ch, "P9.02", sections=["## 구할 것", "## 조건", "## 회로 — 없음 (그림 없는 글 문제)"])
        self.assertError("P9.02", "순서")

    def test_missing_required_section(self):
        write_md(self.ch, "P9.02", sections=["## 조건", "## 회로 — 없음 (그림 없는 글 문제)"])
        self.assertError("P9.02", "필수 절 없음", "구할 것")

    def test_unknown_section(self):
        write_md(self.ch, "P9.02", sections=["## 조건", "## 구할 것", "## 메모",
                                             "## 회로 — 없음 (그림 없는 글 문제)"])
        self.assertError("P9.02", "알 수 없는 절", "메모")

    def test_example_without_answer(self):
        write_md(self.ch, "E9.01", figures=["9.2"],
                 sections=["## 조건", "## 구할 것", "## 회로 — Fig 9.2\n![Fig 9.2](../figures/fig9-02.png)"])
        self.assertError("E9.01", "'## 답' 절 없음")

    def test_problem_with_answer(self):
        write_md(self.ch, "P9.02", sections=["## 조건", "## 구할 것",
                                             "## 회로 — 없음 (그림 없는 글 문제)", "## 답 (검증용)"])
        self.assertError("P9.02", "예제가 아닌데")

    def test_missing_title_line(self):
        text = re.sub(r"^# .*\n", "", make_md("P9.02"), flags=re.M)
        write_md(self.ch, "P9.02", text=text)
        self.assertError("P9.02", "제목 줄")


class RobustnessTest(ChapterCase):
    def test_broken_frontmatter_reported_not_raised(self):
        write_md(self.ch, "P9.02", text="frontmatter 없음\n")
        self.assertError("P9.02.md", "frontmatter")

    def test_empty_chapter_is_error(self):
        empty = self.root / "ch12"
        (empty / "figures").mkdir(parents=True)
        (empty / "figures" / "figures.yaml").write_text("pdf: ../../book.pdf\nfigures:\n", encoding="utf-8")
        errors, _ = verify(empty)
        self.assertIn("문제 md가 없음", errors)


class CliTest(ChapterCase):
    def run_main(self, *args):
        out = io.StringIO()
        with redirect_stdout(out):
            code = main(["verify_chapter.py", *args])
        return code, out.getvalue()

    def test_clean_exit_zero(self):
        code, out = self.run_main(str(self.ch))
        self.assertEqual(code, 0)
        self.assertIn("오류 0개, 참고 0개", out)

    def test_error_exit_one(self):
        write_md(self.ch, "P9.03")
        code, out = self.run_main(str(self.ch))
        self.assertEqual(code, 1)
        self.assertIn("ERROR ", out)

    def test_info_only_exit_zero(self):
        write_md(self.ch, "E9.02")
        (self.ch / "README.md").write_text(build_index(self.ch, "9장 테스트"), encoding="utf-8")
        code, out = self.run_main(str(self.ch))
        self.assertEqual(code, 0)
        self.assertIn("INFO  E9.02", out)

    def test_usage(self):
        self.assertEqual(main(["verify_chapter.py"]), 2)
        self.assertEqual(main(["verify_chapter.py", str(self.root / "없는폴더")]), 2)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 테스트를 돌려 실패하는지 확인한다**

Run: `python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests -p 'test_verify_chapter.py'`
Expected: FAIL (`ModuleNotFoundError: No module named 'verify_chapter'`)

- [ ] **Step 3: 구현한다**

`교과서/마이크로전자회로/_tools/verify_chapter.py`:

```python
#!/usr/bin/env python3
"""장 폴더 전체의 정합성을 검사한다. check_md.py가 파일 하나씩 보는 것을 장 단위로 보완한다.

사용법: python3 verify_chapter.py <장 폴더> [--recrop]    예) python3 verify_chapter.py ../ch09
"""
import re
import sys
from pathlib import Path

import yaml

from check_md import ID_RE, KIND_BY_PREFIX, md_files, split_frontmatter
from crop_figures import figure_filename

SECTION_ORDER = ["## 조건", "## 구할 것", "## 상속·참조", "## 회로", "## 답"]
REQUIRED = {0: "조건", 1: "구할 것", 3: "회로"}
ANSWER = 4
HEADING_RE = re.compile(r"^## .+$", re.M)
IMG_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)\)")


def load_docs(ch_dir):
    docs, errors = {}, []
    for path in md_files(ch_dir):
        try:
            fm, body = split_frontmatter(path.read_text(encoding="utf-8"))
            docs[str(fm["id"])] = (path, fm, body)
        except Exception as e:  # 깨진 파일 하나가 나머지 검사를 막지 않게
            errors.append(f"{path.name}: frontmatter 읽기 실패 ({e})")
    return docs, errors


def check_numbering(docs):
    errors, infos = [], []
    for prefix, kind in KIND_BY_PREFIX.items():
        ids = [i for i in docs if (m := ID_RE.match(i)) and m.group(1) == prefix]
        if not ids:
            continue
        chapter = ID_RE.match(ids[0]).group(2)
        nums = {int(ID_RE.match(i).group(3)) for i in ids}
        missing = [f"{prefix}{chapter}.{n:02d}" for n in range(1, max(nums) + 1) if n not in nums]
        if missing:
            errors.append(f"{kind} 번호가 빠짐: {', '.join(missing)}")
    for i in sorted(docs):
        if i.startswith("X") and "E" + i[1:] not in docs:
            errors.append(f"{i}: 짝이 되는 예제 E{i[1:]}가 없음")
        if i.startswith("E") and "X" + i[1:] not in docs:
            infos.append(f"{i}: 연습문제 없음 (원문에 연습문제가 없는지 확인)")
    return errors, infos


def check_figures(ch_dir, docs):
    fig_dir = ch_dir / "figures"
    yaml_path = fig_dir / "figures.yaml"
    if not yaml_path.exists():
        return ["figures/figures.yaml 없음"]
    errors = []
    figures = (yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}).get("figures") or {}
    for key in figures:
        if not isinstance(key, str):
            errors.append(f"figures.yaml 그림 id {key!r}는 따옴표로 감싼 문자열이어야 함 (예: \"9.30\")")
    yaml_ids = {str(k) for k in figures}
    used = set()
    for i, (path, fm, body) in sorted(docs.items()):
        links = IMG_RE.findall(body)
        names = {Path(link).name for link in links}
        for fig in fm.get("figures") or []:
            fid = str(fig["id"])
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
        errors.append(f"PNG 없음: {', '.join(sorted(expected - pngs))} (crop_figures.py 실행)")
    if pngs - expected:
        errors.append(f"figures.yaml에 없는 PNG: {', '.join(sorted(pngs - expected))}")
    return errors


def check_structure(docs):
    errors = []
    for i, (path, fm, body) in sorted(docs.items()):
        first = next((line for line in body.splitlines() if line.strip()), "")
        if not first.startswith("# "):
            errors.append(f"{i}: 제목 줄(# …)이 없음")
        heads = HEADING_RE.findall(body)
        order = []
        for h in heads:
            k = next((k for k, s in enumerate(SECTION_ORDER) if h.startswith(s)), None)
            if k is None:
                errors.append(f"{i}: 알 수 없는 절 '{h}'")
            else:
                order.append(k)
        if order != sorted(order):
            errors.append(f"{i}: 절 순서가 FORMAT과 다름 ({' → '.join(heads)})")
        for k, name in REQUIRED.items():
            if k not in order:
                errors.append(f"{i}: 필수 절 없음 ({name})")
        has_answer = ANSWER in order
        if i.startswith("E") and not has_answer:
            errors.append(f"{i}: 예제에 '## 답' 절 없음")
        if not i.startswith("E") and has_answer:
            errors.append(f"{i}: 예제가 아닌데 '## 답' 절이 있음")
    return errors


def verify(ch_dir, recrop=False):
    ch_dir = Path(ch_dir)
    docs, errors = load_docs(ch_dir)
    if not docs and not errors:
        return ["문제 md가 없음"], []
    numbering_errors, infos = check_numbering(docs)
    errors += numbering_errors
    errors += check_figures(ch_dir, docs)
    errors += check_structure(docs)
    return errors, infos


def main(argv):
    args = [a for a in argv[1:] if a != "--recrop"]
    if len(args) != 1:
        print("사용법: python3 verify_chapter.py <장 폴더> [--recrop]", file=sys.stderr)
        return 2
    ch_dir = Path(args[0])
    if not ch_dir.is_dir():
        print(f"장 폴더가 없음: {ch_dir}", file=sys.stderr)
        return 2
    errors, infos = verify(ch_dir, recrop="--recrop" in argv[1:])
    for e in errors:
        print(f"ERROR {e}")
    for i in infos:
        print(f"INFO  {i}")
    print(f"{ch_dir}: 오류 {len(errors)}개, 참고 {len(infos)}개")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

- [ ] **Step 4: 테스트를 돌려 통과하는지 확인한다**

Run: `python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests`
Expected: `OK`. 기존 39개와 새 테스트를 합쳐 모두 통과해야 한다.

- [ ] **Step 5: 실행 권한을 주고 커밋한다**

```bash
chmod +x 교과서/마이크로전자회로/_tools/verify_chapter.py
git add 교과서/마이크로전자회로/_tools/verify_chapter.py 교과서/마이크로전자회로/_tools/tests/test_verify_chapter.py
git commit -m "feat: add verify_chapter tool for chapter-level consistency checks

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: `verify_chapter.py` — README 최신 여부와 `--recrop`

**Files:**
- Modify: `교과서/마이크로전자회로/_tools/verify_chapter.py` (import 절, 새 함수 두 개, `verify()`)
- Test: `교과서/마이크로전자회로/_tools/tests/test_verify_chapter.py` (새 테스트 클래스 두 개)

**Interfaces:**
- Consumes:
  - Task 1의 `verify(ch_dir, recrop=False)`
  - `make_index.build_index(ch_dir, title) -> str`
  - `crop_figures.crop_all(ch_dir) -> list[Path]`: `ch_dir/figures/figures.yaml`의 `pdf`를 figures 폴더 기준으로 풀고 PNG를 쓴다. 문제가 있으면 ValueError를 낸다.
- Produces:
  - `check_readme(ch_dir) -> list[str]`
  - `check_recrop(ch_dir) -> list[str]`
  - `verify()`가 README 검사를 항상 하고, `recrop=True`일 때만 다시 크롭해서 비교하도록 바뀐다.

- [ ] **Step 1: 실패하는 테스트를 추가한다**

`test_verify_chapter.py`의 `class CliTest` 바로 앞에 넣는다:

```python
class ReadmeTest(ChapterCase):
    def test_missing_readme(self):
        (self.ch / "README.md").unlink()
        self.assertError("README.md 없음")

    def test_stale_readme(self):
        readme = self.ch / "README.md"
        readme.write_text(readme.read_text(encoding="utf-8") + "손으로 고친 줄\n", encoding="utf-8")
        self.assertError("README.md가 최신이 아님")

    def test_bad_heading(self):
        (self.ch / "README.md").write_text("# 아무 제목\n", encoding="utf-8")
        self.assertError("README.md 첫 줄")


class RecropTest(ChapterCase):
    def test_clean_recrop_passes(self):
        self.assertEqual(verify(self.ch, recrop=True), ([], []))

    def test_tampered_png_detected_only_with_recrop(self):
        fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 5, 5), False).save(str(self.ch / "figures" / "fig9-02.png"))
        self.assertEqual(verify(self.ch), ([], []))
        self.assertError("fig9-02.png", "다시 자른 결과와 다름", recrop=True)

    def test_recrop_missing_pdf_is_error(self):
        (self.root / "book.pdf").unlink()
        self.assertError("다시 자르기 실패", recrop=True)
```

- [ ] **Step 2: 테스트를 돌려 실패하는지 확인한다**

Run: `python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests -p 'test_verify_chapter.py'`
Expected: FAIL. `ReadmeTest` 3개와 `test_tampered_png_detected_only_with_recrop`, `test_recrop_missing_pdf_is_error`가 실패한다(오류 목록이 비어 있음). `test_clean_recrop_passes`는 이미 통과한다.

- [ ] **Step 3: 구현한다**

`verify_chapter.py`의 import 절을 다음으로 바꾼다:

```python
import re
import sys
import tempfile
from pathlib import Path

import fitz
import yaml

from check_md import ID_RE, KIND_BY_PREFIX, md_files, split_frontmatter
from crop_figures import crop_all, figure_filename
from make_index import build_index
```

상수 블록(`IMG_RE = …` 줄) 아래에 추가한다:

```python
H1_RE = re.compile(r"^# (.+) — 문제 인덱스$", re.M)
```

`check_structure` 함수 뒤에 추가한다:

```python
def check_readme(ch_dir):
    readme = ch_dir / "README.md"
    if not readme.exists():
        return ["README.md 없음 (make_index.py 실행)"]
    text = readme.read_text(encoding="utf-8")
    m = H1_RE.match(text)
    if not m:
        return ["README.md 첫 줄이 '# <제목> — 문제 인덱스' 형식이 아님"]
    try:
        fresh = build_index(ch_dir, m.group(1))
    except Exception as e:  # 깨진 md가 있으면 인덱스를 만들 수 없음 — 그 원인은 다른 검사가 보고
        return [f"README.md 비교 실패 ({e})"]
    return [] if fresh == text else ["README.md가 최신이 아님 (make_index.py 다시 실행)"]


def check_recrop(ch_dir):
    fig_dir = ch_dir / "figures"
    errors = []
    try:
        spec = yaml.safe_load((fig_dir / "figures.yaml").read_text(encoding="utf-8"))
        spec["pdf"] = str((fig_dir / spec["pdf"]).resolve())
        with tempfile.TemporaryDirectory() as t:
            tmp_ch = Path(t) / ch_dir.name
            (tmp_ch / "figures").mkdir(parents=True)
            (tmp_ch / "figures" / "figures.yaml").write_text(
                yaml.safe_dump(spec, allow_unicode=True), encoding="utf-8")
            for out in crop_all(tmp_ch):
                current = fig_dir / out.name
                if not current.exists():
                    continue  # PNG 없음은 check_figures가 보고
                a, b = fitz.Pixmap(str(current)), fitz.Pixmap(str(out))
                if (a.width, a.height, a.samples) != (b.width, b.height, b.samples):
                    errors.append(f"{out.name}: figures.yaml로 다시 자른 결과와 다름 (crop_figures.py 다시 실행)")
    except Exception as e:  # PDF 없음(worktree 심볼릭 링크 누락 등), bbox 오류
        errors.append(f"다시 자르기 실패 ({e})")
    return errors
```

`verify()`를 다음으로 바꾼다:

```python
def verify(ch_dir, recrop=False):
    ch_dir = Path(ch_dir)
    docs, errors = load_docs(ch_dir)
    if not docs and not errors:
        return ["문제 md가 없음"], []
    numbering_errors, infos = check_numbering(docs)
    errors += numbering_errors
    errors += check_figures(ch_dir, docs)
    errors += check_structure(docs)
    errors += check_readme(ch_dir)
    if recrop:
        errors += check_recrop(ch_dir)
    return errors, infos
```

- [ ] **Step 4: 테스트를 돌려 통과하는지 확인한다**

Run: `python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests`
Expected: `OK` (모두 통과).

`NumberingTest`, `FigureTest` 등 Task 1 테스트는 파일을 더하면서 README를 다시 만들지 않는다. 그래서 이제 "README.md가 최신이 아님" 오류가 함께 나오지만, 이 테스트들은 특정 오류가 포함됐는지만 보므로 그대로 통과한다. `test_example_without_exercise_is_info`는 오류에 "E9.02"가 없어야 하는데, README 오류 문구에는 문제 id가 들어가지 않으므로 통과한다.

- [ ] **Step 5: 커밋한다**

```bash
git add 교과서/마이크로전자회로/_tools/verify_chapter.py 교과서/마이크로전자회로/_tools/tests/test_verify_chapter.py
git commit -m "feat: check README freshness and re-crop pixels in verify_chapter

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: FORMAT.md 보강과 기존 장 수용 검사

FORMAT.md는 이미 10·11장 관례를 담고 있다(커밋 `10b7995 docs: add ch10–11 conventions to FORMAT.md`). 관례는 새 절에 모으지 않고 해당 규칙이 쓰이는 절마다 들어가 있으니, 이 구조를 **그대로 따른다.** 새 절을 만들지 않고, 이미 있는 규칙을 다시 적지 않는다. 이 Task가 FORMAT에 더하는 것은 셋뿐이다.
- 새 도구 등록
- FORMAT에 아직 없는 관례 두 줄: 변압기 결합(E10.01, E10.02, X10.02, P10.01에서 사용), 연습문제가 없는 예제(E11.29)

**Files:**
- Modify: `교과서/마이크로전자회로/FORMAT.md`
  - 폴더 절의 `_tools/make_index.py` 줄(12행 부근)
  - `번호는 두 자리로 채운다` 줄(20행 부근)
  - 넷리스트 절의 `기호가 분수·식인 값은` 줄(99행 부근)
  - 파일 끝 `## 검사` 절

**Interfaces:**
- Consumes: Task 2의 `verify_chapter.py` CLI
- Produces:
  - FORMAT.md에 도구 등록과 관례 두 줄. Task 5·6의 템플릿과 스킬은 "형식과 관례는 FORMAT.md 전체"라고만 가리키고, 특정 절 이름에 기대지 않는다.
  - 9–11장 수용 검사 결과

- [ ] **Step 1: 기존 장에 수용 검사를 돌린다** (문서를 바꾸기 전에 도구가 실제 데이터에서 맞게 동작하는지 먼저 본다)

```bash
for c in ch09 ch10 ch11; do python3 교과서/마이크로전자회로/_tools/verify_chapter.py 교과서/마이크로전자회로/$c --recrop; echo "exit $?"; done
```
Expected (정확히 이 결과):
```
교과서/마이크로전자회로/ch09: 오류 0개, 참고 0개
exit 0
교과서/마이크로전자회로/ch10: 오류 0개, 참고 0개
exit 0
INFO  E11.29: 연습문제 없음 (원문에 연습문제가 없는지 확인)
교과서/마이크로전자회로/ch11: 오류 0개, 참고 1개
exit 0
```
이것과 다르게 나오면 장 파일을 고치지 않는다. 오류 줄을 그대로 보고하고 멈춘다. 이 결과는 설계 단계에서 임시 스크립트로 같은 항목을 확인한 결과와 같아야 한다(E11.29는 원문 p.31에서 연습문제가 없음을 확인함).

- [ ] **Step 2: 폴더 절에 도구를 등록한다**

`교과서/마이크로전자회로/FORMAT.md`에서
```
  _tools/make_index.py        # frontmatter → ch<장>/README.md 문제 인덱스
```
를 다음으로 바꾼다:
```
  _tools/make_index.py        # frontmatter → ch<장>/README.md 문제 인덱스
  _tools/verify_chapter.py    # 장 단위 정합성 검사 (번호, 그림, 절 순서, README, --recrop)
```

- [ ] **Step 3: FORMAT에 없는 관례 두 줄을 해당 절에 넣는다**

(a) 폴더 절의
```
번호는 두 자리로 채운다 (9.1 → `9.01`).
```
를 다음으로 바꾼다:
```
번호는 두 자리로 채운다 (9.1 → `9.01`).
원문에서 예제 바로 뒤에 연습문제가 없으면 X 파일을 만들지 않는다 (예: 예제 11.29). `verify_chapter.py`가 이런 예제를 참고(INFO)로 알려 주니, 원본에서 한 번 더 확인한다.
```

(b) 넷리스트 절의
```
- 기호가 분수·식인 값은 중괄호로 그대로 적는다: `{R_E/2}`, `{r_O3||(1/g_m3)}`. 소문자로 시작하는 소자(r_O)는 `RO X Y {r_O}`처럼 대문자 이름을 쓴다
```
바로 뒤에 한 줄을 넣는다:
```
- 변압기처럼 자기 결합된 코일은 L 두 개(가운데 탭이 있으면 탭 양쪽으로 나눈 L)로 적고, 결합 관계는 SPICE K 문 대신 주석으로 적는다: `* LP와 LS는 자기 결합된 변압기 (결합은 K 문 대신 주석, 원문에 없음)` (예: E10.01, E10.02)
```

그 밖의 관례는 이미 FORMAT에 있다. 대응은 아래와 같고, 이 Task에서 다시 적지 않는다.

| 관례 | FORMAT 위치 |
|---|---|
| 패널별 role, 여러 쪽에 걸친 문제, 다른 장 참조, "Repeat Problem" | frontmatter 절 아래 bullet |
| 본문 그림 크롭 기준, Design Problems 공통 가정 | 본문 절 4 |
| 그래프·파형 문제 그림 | 본문 절 5 (크롭해서 `role: problem`, 이미지는 `## 상속·참조` 끝) |
| 그래프뿐인 풀이 그림 | 본문 절 6 |
| "설계하라", "Note that" 메모, 원문 오식 | "원문에 없는 보충", "원문 오식" 문단 |
| 라벨 없는 출력, 소신호 라벨, 차동 출력, 교류 접지 `VAC` | 넷리스트 절 노드 이름 |
| 화살표 좌우 반전 등 | 표시 절 화살표 |

- [ ] **Step 4: 검사 절에 장 단위 검사를 추가한다**

파일 끝의 `## 검사` 절에 있는 첫 코드 블록
```bash
python3 교과서/마이크로전자회로/_tools/check_md.py 교과서/마이크로전자회로/ch09
```
바로 뒤에 넣는다:

````markdown
장을 마치면 장 단위 검사도 통과해야 한다 (`--recrop`은 figures.yaml로 다시 잘라 PNG와 픽셀을 비교한다. 원본 PDF가 있어야 함).
```bash
python3 교과서/마이크로전자회로/_tools/verify_chapter.py 교과서/마이크로전자회로/ch09 --recrop
```
````

- [ ] **Step 5: 문서를 바꾼 뒤에도 모든 검사가 통과하는지 확인한다**

```bash
for c in ch09 ch10 ch11; do python3 교과서/마이크로전자회로/_tools/check_md.py 교과서/마이크로전자회로/$c | tail -1; python3 교과서/마이크로전자회로/_tools/verify_chapter.py 교과서/마이크로전자회로/$c | tail -1; done
python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests 2>&1 | tail -1
F=교과서/마이크로전자회로/FORMAT.md
grep -c "_tools/verify_chapter.py    #" $F
grep -c "verify_chapter.py 교과서/마이크로전자회로/ch09 --recrop" $F
grep -c "X 파일을 만들지 않는다" $F
grep -c "K 문 대신 주석" $F
grep -c "^## 판독 관례" $F
git diff --numstat -- $F
```
Expected:
- check_md: `110개 파일, 오류 0개`, `151개 파일, 오류 0개`, `116개 파일, 오류 0개`
- verify: 세 장 모두 `오류 0개`
- 테스트: `OK`
- grep 다섯 개: 순서대로 `1`, `1`, `1`, `1`, `0` (마지막 `0`은 새 절을 만들지 않았다는 뜻)
- numstat: 삭제 0줄, 추가 7–9줄 (폴더 1, 연습문제 1, 변압기 1, 검사 절 4에 빈 줄 몇 개). 삭제가 0이 아니면 기존 규칙을 건드린 것이니 되돌린다

- [ ] **Step 6: 커밋한다**

```bash
git add 교과서/마이크로전자회로/FORMAT.md
git commit -m "docs: register verify_chapter and add two missing conventions to FORMAT

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: 리뷰 보고서 폴더와 과거 보고서 옮기기

**Files:**
- Create: `docs/superpowers/reports/README.md`
- Create (복사): `docs/superpowers/reports/ch09/review-A.md` … `review-G.md`, `docs/superpowers/reports/ch11/review-H.md`

**Interfaces:**
- Produces: 보고서 폴더 규칙 `docs/superpowers/reports/ch<N>/review-<묶음>.md`. Task 5의 `reviewer.md`, `writer.md`와 Task 6의 SKILL.md가 이 경로를 쓴다.

- [ ] **Step 1: 원본 보고서가 남아 있는지 확인한다**

```bash
SRC=/private/tmp/claude-501/-Users-hyunjun-macbook-pro-Documents-Univ-----2/bc9385b7-8ec6-44b5-83e0-e07ca7047701/scratchpad
ls "$SRC"/review-*.md
```
Expected: `review-A.md` … `review-G.md`, `review-ch11-H.md`. 폴더가 사라졌으면(재부팅 등) Step 2의 복사를 건너뛴다. 그리고 README의 보존 현황 표에서 9장·11장 행을 "남아 있지 않음"으로 적는다.

- [ ] **Step 2: 보고서를 읽고 복사한다**

각 파일을 끝까지 읽는다. 리뷰 메모 말고 다른 내용(개인 정보, 경로 외 비밀)이 없는지 확인한 뒤 복사한다.
```bash
mkdir -p docs/superpowers/reports/ch09 docs/superpowers/reports/ch11
for b in A B C D E F G; do cp "$SRC/review-$b.md" docs/superpowers/reports/ch09/review-$b.md; done
cp "$SRC/review-ch11-H.md" docs/superpowers/reports/ch11/review-H.md
```

- [ ] **Step 3: 폴더 README를 쓴다**

`docs/superpowers/reports/README.md`:

```markdown
# 리뷰·검증 보고서

교과서 문제 → md 변환(`.claude/skills/textbook-to-md`)의 묶음별 원본 대조 리뷰 보고서다.

- 경로: `ch<N>/review-<묶음>.md` (묶음 이름 A, B, C …)
- 리뷰 에이전트가 보고서를 쓰고, 다음 작성 에이전트가 원본을 확인해 지적을 반영하면서 함께 커밋한다. 지적이 없는 묶음도 보고서를 커밋한다.
- `2026-09-24-ch09-sample-round-1.md`는 9장 형식을 정하던 샘플 라운드 보고서다.

## 보존 현황 (스킬 도입 전)
| 장 | 보고서 | 묶음 → 대상 |
|---|---|---|
| 9장 | A–G | A: E/X9.02–9.07, B: E/X9.08–9.14, C: E9.17–9.21·X9.16–9.21, D: P9.01–9.15, E: P9.16–9.33, F: P9.34–9.53, G: P9.54–9.68 |
| 10장 | 없음 | 당시 세션 scratchpad에만 있어 남지 않음 (반영 커밋은 git 이력에 있음) |
| 11장 | H만 | H: P11.44–P11.59 (병합 후 추가 리뷰). A–G는 남지 않음 |
```

- [ ] **Step 4: 커밋한다**

```bash
git add docs/superpowers/reports/README.md docs/superpowers/reports/ch09 docs/superpowers/reports/ch11
git status --short | grep -v '^??'   # 위 파일만 A로 보여야 함
git commit -m "docs: keep batch review reports under docs/superpowers/reports

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: 스킬 프롬프트 템플릿

**Files:**
- Create: `.claude/skills/textbook-to-md/references/survey.md`
- Create: `.claude/skills/textbook-to-md/references/common.md`
- Create: `.claude/skills/textbook-to-md/references/writer.md`
- Create: `.claude/skills/textbook-to-md/references/reviewer.md`

**Interfaces:**
- Consumes:
  - FORMAT.md 전체 (관례는 절마다 들어 있음. 템플릿은 특정 절 이름을 가리키지 않는다)
  - Task 1·2의 `verify_chapter.py` CLI
  - Task 4의 보고서 경로 규칙
- Produces: 자리표시자 집합. Task 6의 SKILL.md 자리표시자 표가 이 이름과 정확히 같아야 한다. 템플릿마다 쓰는 자리표시자는 다음과 같다.
  - `survey.md`: `N`, `REPO`, `PDF`, `SCRATCH`
  - `common.md`: `N`, `REPO`, `PDF`, `CH`, `SCRATCH`, `PAGE_MAP`
  - `writer.md`: `N`, `COMMON`, `BATCH`, `TARGETS`, `LOCATIONS`, `EXPECTED_TOTAL`, `BUSY_FILES`, `PREV_BATCH`, `PREV_TARGETS`, `PREV_REVIEW`
  - `reviewer.md`: `N`, `COMMON`, `BATCH`, `TARGETS`, `COMMIT`, `FLAGS`, `REPORT`, `PREV_FIX_COMMIT`
  - 자리표시자는 `<<이름>>` 형식이다. LaTeX·SPICE의 `{…}`와 겹치지 않게 하려고 이 형식을 쓴다.

- [ ] **Step 1: 자리표시자 검사를 먼저 돌려 실패하는지 확인한다**

```bash
python3 - <<'EOF'
import re, pathlib
allowed = {
    "survey.md": {"N", "REPO", "PDF", "SCRATCH"},
    "common.md": {"N", "REPO", "PDF", "CH", "SCRATCH", "PAGE_MAP"},
    "writer.md": {"N", "COMMON", "BATCH", "TARGETS", "LOCATIONS", "EXPECTED_TOTAL", "BUSY_FILES",
                  "PREV_BATCH", "PREV_TARGETS", "PREV_REVIEW"},
    "reviewer.md": {"N", "COMMON", "BATCH", "TARGETS", "COMMIT", "FLAGS", "REPORT", "PREV_FIX_COMMIT"},
}
d = pathlib.Path(".claude/skills/textbook-to-md/references")
for name, ok in allowed.items():
    found = set(re.findall(r"<<([A-Z_]+)>>", (d / name).read_text(encoding="utf-8")))
    assert found == ok, (name, sorted(found ^ ok))
print("placeholders OK")
EOF
```
Expected: FAIL (`FileNotFoundError`)

- [ ] **Step 2: `survey.md`를 쓴다**

`.claude/skills/textbook-to-md/references/survey.md`:

````markdown
# 0단계 조사 — <<N>>장

당신은 조사 에이전트다. 저장소 파일을 만들거나 고치지 않고 git 상태도 바꾸지 않는다. 결과는 `<<SCRATCH>>/survey-ch<<N>>.md` 한 파일에만 쓴다. 확대 이미지도 `<<SCRATCH>>/` 아래에 둔다.

- 작업 루트: `<<REPO>>` (셸 명령은 이 폴더에서 실행)
- 원본: `<<PDF>>` (Razavi 마이크로전자회로 <<N>>장, 스캔본. 텍스트 레이어가 없으므로 페이지를 이미지로 렌더링해 읽는다)
- 먼저 `교과서/마이크로전자회로/FORMAT.md`를 전부 읽는다. 앞 장 README(`교과서/마이크로전자회로/ch09/README.md`)를 훑어 산출물 규모를 가늠한다.

## 도구
```bash
# 페이지 크기 — 너비 약 1100pt 이상이면 두 쪽 펼침
python3 -c "import fitz; d=fitz.open('<<PDF>>'); print([(i+1, round(p.rect.width), round(p.rect.height)) for i,p in enumerate(d)])"
# 페이지 전체 저해상도 (훑기용, 72–100 dpi)
python3 -c "import fitz,sys; d=fitz.open('<<PDF>>'); d[int(sys.argv[1])-1].get_pixmap(dpi=int(sys.argv[3])).save(sys.argv[2])" PAGE <<SCRATCH>>/pPAGE.png 90
# 부분 확대 (좌표 PDF pt, 왼쪽 위 원점)
python3 -c "import fitz,sys; d=fitz.open('<<PDF>>'); d[int(sys.argv[1])-1].get_pixmap(dpi=int(sys.argv[7]), clip=fitz.Rect(*map(float, sys.argv[2:6]))).save(sys.argv[6])" PAGE X0 Y0 X1 Y1 <<SCRATCH>>/OUT.png DPI
```

## 조사 순서
1. 페이지 크기로 펼침 페이지와 한 쪽 페이지를 가른다.
2. 모든 페이지를 90 dpi로 훑는다. 쪽 머리 번호로 PDF 페이지 ↔ 교재 쪽 대응을 만든다. 펼침 페이지는 왼쪽·오른쪽 쪽 번호를 둘 다 적는다.
3. 예제마다 위치(PDF 페이지, 교재 쪽, 펼침이면 왼쪽/오른쪽), 절, 문제 그림, 풀이 그림, 바로 뒤 연습문제 유무를 적는다. 연습문제가 없으면 그 자리를 확대해서 확인한다.
4. 장말 PROBLEMS를 조사한다.
   - 페이지별 문제 번호 범위, 절 머리(`Sec. N.x`) 위치, 그림 번호 범위
   - 별표(*) 개수와 SOL 표시: 여백을 200 dpi로 확인한다
   - Design Problems 머리와 공통 가정 머리말이 있는지, 있으면 위치
   - SPICE Problems 시작 위치 (범위 밖)
   - 마지막 문제가 다음 페이지로 이어지는지
5. FORMAT이 다루지 않는 그림 유형을 찾는다. FORMAT이 다루는 것은 회로, 등가회로, 회로 없이 그래프·파형·영상뿐인 그림, 회로와 파형 패널이 섞인 그림이다(FORMAT `## 본문 절` 5·6). 그 밖의 것(예: 스미스 차트, 표, 블록도)을 적는다.

## 산출물 (`<<SCRATCH>>/survey-ch<<N>>.md`)
```
# <<N>>장 조사

## 장 제목
<교재 인쇄 제목 (한국어)>

## 쪽 대응
| PDF | 교재 쪽 | 구성 (펼침/한 쪽, 본문/요약/PROBLEMS) |

## 예제
| 예제 | PDF | 교재 쪽 | 절 | 문제 그림 | 풀이 그림 | 연습문제 |

## 장말문제
| PDF | 교재 쪽 | 문제 번호 | 절 머리 | 그림 번호 |
- 별표: <번호: 개수 …>
- SOL: <번호 …>
- Design Problems: <머리 위치> / 공통 가정 머리말: 있음(PDF p, y 범위) | 없음
- SPICE Problems 시작: <위치>
- 마지막 문제의 끝: <위치>

## 새 그림 유형
<없음> 또는 <그림 번호, 모양, 어느 문제가 쓰는지>

## 묶음 제안
| 묶음 | 대상 | PDF 페이지 | 개수 |
(12–18개씩. 예제와 연습문제를 먼저 예제 순으로, 장말문제는 PDF 페이지 경계로 나눈다. 이름은 A, B, C …)
```
최종 메시지에는 산출물 경로와 다섯 줄 요약(예제 수, 연습문제 수, 장말문제 수, 새 그림 유형 유무, 묶음 수)만 적는다.
````

- [ ] **Step 3: `common.md`를 쓴다**

`.claude/skills/textbook-to-md/references/common.md`:

````markdown
# 공통 지침 — <<N>>장 교과서 문제 → MD 변환

- 작업 루트: `<<REPO>>` (경로는 모두 여기 기준이고, 셸 명령은 이 폴더에서 실행한다)
- 원본: `<<PDF>>` (Razavi 마이크로전자회로 <<N>>장, 스캔본. 텍스트 레이어가 없으므로 페이지를 이미지로 렌더링해 읽는다)
- 장 폴더: `<<CH>>`
- 임시 파일은 `<<SCRATCH>>/` 아래에만 둔다. 저장소 안에 임시 파일을 만들지 않는다.

## 반드시 먼저 읽을 것
1. `교과서/마이크로전자회로/FORMAT.md` **전체**. 형식과 판독 관례의 유일한 기준이다. 관례는 절마다 들어 있다(frontmatter 아래 bullet, 본문 절, 원문에 없는 보충·원문 오식 문단, 넷리스트 노드 이름, 표시 절).
2. 앞 장의 완성 파일(`교과서/마이크로전자회로/` 기준). 비슷한 상황의 파일을 찾아 본다.
   - 예제 + 정답 회로: `ch09/예제/E9.03.md`, `ch09/예제/E9.07.md`, `ch09/예제/E9.14.md`
   - 연습문제 상속: `ch09/연습문제/X9.01.md`, `ch09/연습문제/X9.16.md`
   - 여러 패널 그림: `ch09/장말문제/P9.11.md`
   - 그림 없는 문제: `ch09/장말문제/P9.35.md`
   - 그래프·파형뿐인 문제 그림: `ch10/장말문제/P10.17.md`, `ch10/장말문제/P10.24.md`
   - 회로 패널과 파형 패널이 섞인 그림: `ch10/예제/E10.09.md`
   - 그래프뿐인 풀이 그림: `ch10/예제/E10.19.md`
   - 변압기 결합: `ch10/예제/E10.01.md`
   - Design Problems 공통 가정: `ch09/장말문제/P9.59.md`
   - 원문 오식: `ch09/장말문제/P9.26.md`, `ch10/장말문제/P10.10.md`, `ch11/예제/E11.11.md`
3. `<<CH>>/figures/figures.yaml`

## 도구
```bash
# 원본 확대 (PAGE 1부터, 좌표 PDF pt, 왼쪽 위 원점). 216–400 dpi
python3 -c "import fitz,sys; d=fitz.open('<<PDF>>'); d[int(sys.argv[1])-1].get_pixmap(dpi=int(sys.argv[7]), clip=fitz.Rect(*map(float, sys.argv[2:6]))).save(sys.argv[6])" PAGE X0 Y0 X1 Y1 <<SCRATCH>>/OUT.png DPI
# 그림 크롭 (figures.yaml 전체를 다시 자름)
python3 교과서/마이크로전자회로/_tools/crop_figures.py <<CH>>
# 형식 검사 (파일 단위)
python3 교과서/마이크로전자회로/_tools/check_md.py <<CH>>
# 장 단위 검사 (번호, 그림, 절 순서. README는 마지막에 만들므로 작성 중에는 README 오류가 정상)
python3 교과서/마이크로전자회로/_tools/verify_chapter.py <<CH>>
# 도구 테스트
python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests
```
스캔 해상도가 약 144 dpi라서 300–400 dpi를 넘게 확대해도 정보가 늘지 않는다.

## 쪽 대응과 위치 (0단계 조사 결과)
<<PAGE_MAP>>

위치는 조사 결과이니 작성 전에 원본에서 확인한다.

## 핵심 규칙
- 문제 1개 = md 1개. md 텍스트만으로 원본 문제(조건, 구할 것, 회로도)를 복원할 수 있어야 한다.
- 한국어로 재구성하고, 원문을 그대로 옮기지 않는다. 수치·단위·지수·소문항은 하나도 빠뜨리지 않는다. 원문에 없는 보충은 줄 끝에 `(원문에 없음)`을 붙인다.
- 연습문제는 이어받는 조건을 `## 상속·참조`에 풀어 적고 `depends_on: [E<<N>>.NN]`을 둔다. 예제를 먼저 써야 WARN이 나지 않는다.
- 풀이 그림은 `role: answer`로 두고 `## 답 (검증용)`의 `### 정답 회로`에만 넣는다.
- YAML 그림 id는 반드시 따옴표로 감싼다 (`"<<N>>.30"`).
- 렌더링 검증(md → PNG)은 하지 않는다.
- SPICE Problems는 범위 밖이다.

## 원본 대조 체크리스트
1. 소자 종류와 극성 (npn/pnp, nmos/pmos). 좌우 반전된 소자는 화살표 방향으로 확인한다
2. 모든 단자의 연결
3. 점으로 접속한 곳인지, 그냥 교차한 곳인지 (선이 소자 기호를 관통하는 경우 포함)
4. 화살표 방향과 모양, 그리고 이름이 인쇄돼 있는지
5. 라벨, 첨자, 면적 배수 (같은 라벨이 두 번 인쇄된 오식 포함)
6. 수치, 단위, 지수
7. 소문항 누락
8. 별표·SOL 표시와 section

## git 규칙 (엄수)
- 현재 브랜치는 `feat/ch<<N>>-problem-md`다. 브랜치 전환, rebase, reset, merge, push는 하지 않는다.
- 추적하지 않는 파일(PDF와 PDF 심볼릭 링크, `STT/`, `강의노트/`)은 절대 add하지 않는다. `git add -A`, `git add .`는 쓰지 않고 항상 경로를 명시한다.
- 커밋 메시지는 빈 줄 뒤 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`로 끝낸다.
````

- [ ] **Step 4: `writer.md`를 쓴다**

`.claude/skills/textbook-to-md/references/writer.md`:

````markdown
# 작성 지시 — <<N>>장 묶음 <<BATCH>>

당신은 교과서 문제 → md 변환의 작성 에이전트다. 먼저 `<<COMMON>>`를 읽고 그 지침(FORMAT.md 전체, 앞 장 참고 파일, 도구, git 규칙)을 그대로 따른다.

지금 다른 리뷰 에이전트가 다음 파일을 읽고 있으니 수정하지 않는다: <<BUSY_FILES>>

## 1단계: 리뷰 반영 (`<<PREV_REVIEW>>`가 "없음"이면 건너뛴다)
1. 리뷰 보고서 `<<PREV_REVIEW>>`를 읽는다 (묶음 <<PREV_BATCH>>: <<PREV_TARGETS>>).
2. 지적마다 원본을 직접 확대해 확인하고, 사실인 것만 반영한다. 선택 제안은 원문에서 멀어지지 않을 때만 반영한다.
3. 형식 검사가 오류 0·WARN 0인지 확인한다.
4. 보고서 파일과 고친 파일을 경로를 명시해 add하고 커밋한다.
   - 고친 파일이 있으면: `docs: apply review fixes to ch<<N>> batch <<PREV_BATCH>> (<<PREV_TARGETS>>)`
   - 고친 것 없이 보고서만 있으면: `docs: record review of ch<<N>> batch <<PREV_BATCH>> (no fixes)`

## 2단계: 묶음 <<BATCH>> 작성 (대상이 "없음"이면 건너뛴다)
대상: <<TARGETS>>

위치 (0단계 조사, 대략):
<<LOCATIONS>>

1. 해당 페이지를 저해상도로 훑어 위치를 잡고, 216–400 dpi로 확대해 꼼꼼히 읽는다.
2. 그림을 등록하고 자른다.
   - 필요한 그림(문제 그림, 예제의 풀이 그림)을 `figures.yaml`에 bbox로 추가한다. 이미 등록된 그림은 다시 쓴다.
   - `crop_figures.py`를 실행한다.
   - 새 PNG를 **Read로 열어** 라벨·화살표·패널 글자가 잘리지 않았는지, 옆 그림이 들어오지 않았는지 확인한다. 잘렸으면 bbox를 고쳐 다시 자른다.
3. md를 쓴다. 예제를 먼저 쓰고 그다음 연습문제를 쓰며, 장말문제는 번호 순으로 쓴다.
4. 형식 검사 결과가 `<<EXPECTED_TOTAL>>개 파일, 오류 0개`, WARN 0이 될 때까지 고친다. 도구 테스트 통과도 확인한다.
5. 새 md, `figures.yaml`, 새 PNG를 경로를 명시해 add하고 커밋한다. 메시지 예: `docs: add ch<<N>> examples E<<N>>.01–E<<N>>.07 and exercises`, `docs: add ch<<N>> problems P<<N>>.14–P<<N>>.28`

컨텍스트가 부족해질 것 같으면 대상의 앞 절반을 먼저 커밋하고 나머지를 두 번째 커밋으로 나눠도 된다.

## 보고 (최종 메시지)
- **1단계:** 반영한 것, 반영하지 않은 것과 그 이유, 커밋 해시
- **2단계:** 파일 목록(PDF 페이지·교재 쪽, section, 장말문제는 difficulty/sol), 그림 id·bbox, add 커밋 해시, 형식 검사 결과 줄
- **판독이 애매했던 곳:** 그림, 위치, 무엇이 애매했고 어떻게 적었는지를 구체적으로 적는다. 리뷰어가 이 목록을 그대로 받아 집중 확인한다
- **FORMAT으로 정하기 애매했던 결정**
- **다음 묶음 대상의 실제 시작 위치:** 조사 결과와 다를 때만 적는다
````

- [ ] **Step 5: `reviewer.md`를 쓴다**

`.claude/skills/textbook-to-md/references/reviewer.md`:

````markdown
# 리뷰 지시 — <<N>>장 묶음 <<BATCH>>

당신은 리뷰 에이전트다. 먼저 `<<COMMON>>`와 FORMAT.md 전체를 읽는다.

- 대상: <<TARGETS>> (커밋 <<COMMIT>>)
- 작성자가 판독이 애매했다고 보고한 곳 (특히 독립적으로 확인할 것):
<<FLAGS>>
- 앞 묶음 리뷰 반영 커밋: <<PREV_FIX_COMMIT>>. "없음"이 아니면 `git show`로 반영 내용이 원본과 맞는지 빠르게 확인한다.

## 원칙
- **추적되는 파일을 수정하지 않고, git 상태도 바꾸지 않는다.** 만드는 파일은 보고서 `<<REPORT>>` 하나뿐이다(필요하면 폴더를 만든다). 커밋은 다음 작성 에이전트가 한다.
- md를 먼저 믿지 않는다. 원본을 216–400 dpi로 **직접 확대해** 독립적으로 판독한 뒤 md와 대조한다. 작성자의 판독은 검증 대상이지 근거가 아니다.
- 크롭 PNG(`교과서/마이크로전자회로/ch<<N>>/figures/*.png`)를 Read로 열어 잘림과 옆 그림 침범을 확인한다.
- 파일마다 원본 대조 체크리스트 8항목을 모두 확인한다. 추가로 확인할 것:
  - 조건·구할 것의 수치와 소문항 누락, 의미 왜곡
  - 연습문제의 상속·참조와 depends_on
  - 예제의 답이 원본 풀이와 맞는지
  - frontmatter (book_page, pdf_page, section, difficulty, sol, figures의 role·panels)
  - 원문에 없는 보충인데 `(원문에 없음)`이 빠진 곳
  - Design Problems 공통 가정이 원본 머리말, 그리고 같은 장의 다른 파일과 같은지
- 형식 검사를 한 번 돌린다.

## 보고서 (`<<REPORT>>`에 저장하고, 최종 메시지에 요약)
```
# 리뷰 <<BATCH>> — 커밋 <<COMMIT>> (<<TARGETS>>)

방법: <렌더링 dpi, 본 페이지, 크롭 확인 결과, 형식 검사 결과>

## 작성자가 애매하다고 한 곳 — 독립 판독 결과
- <항목>: 맞음 | 다름 (<원본 판독>)

### <id> — OK | 수정 필요
- [높음|중간|낮음] <체크 항목>: md는 "…" / 원본은 "…" (근거: PDF p.N, 위치) → 고칠 내용
```
사실 오류(원본과 다름)와 형식·표현 제안을 구분한다. 확신이 없는 지적은 "불확실"로 표시한다.
````

- [ ] **Step 6: 자리표시자 검사를 돌려 통과하는지 확인한다**

Step 1과 같은 명령을 실행한다.
Expected: `placeholders OK`

- [ ] **Step 7: 커밋한다**

```bash
git add .claude/skills/textbook-to-md/references
git commit -m "feat: add textbook-to-md agent prompt templates

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: SKILL.md

**Files:**
- Create: `.claude/skills/textbook-to-md/SKILL.md`

**Interfaces:**
- Consumes:
  - Task 5의 템플릿 4개와 자리표시자 집합
  - Task 1–3의 도구 CLI
  - Task 4의 보고서 경로
- Produces: 스킬 진입점. frontmatter는 `name: textbook-to-md`다.

- [ ] **Step 1: 스킬 검사를 먼저 돌려 실패하는지 확인한다**

```bash
python3 - <<'EOF'
import re, pathlib, yaml
root = pathlib.Path(".claude/skills/textbook-to-md")
text = (root / "SKILL.md").read_text(encoding="utf-8")
fm = yaml.safe_load(text.split("---")[1])
assert fm["name"] == "textbook-to-md", fm
assert 0 < len(fm["description"]) <= 1024, len(fm["description"])
used = set()
for p in (root / "references").glob("*.md"):
    used |= set(re.findall(r"<<([A-Z_]+)>>", p.read_text(encoding="utf-8")))
documented = set(re.findall(r"`<<([A-Z_]+)>>`", text))
assert used == documented, ("표에 없음", sorted(used - documented), "템플릿에 없음", sorted(documented - used))
for ref in set(re.findall(r"references/([a-z]+\.md)", text)):
    assert (root / "references" / ref).exists(), ref
for needle in ["verify_chapter.py", "make_index.py", "--recrop", "docs/superpowers/reports/ch", "opus",
               "worktree", "git log --oneline main..", "record review"]:
    assert needle in text, needle
print("skill OK")
EOF
```
Expected: FAIL (`FileNotFoundError`)

- [ ] **Step 2: SKILL.md를 쓴다**

`.claude/skills/textbook-to-md/SKILL.md`:

````markdown
---
name: textbook-to-md
description: 교과서/마이크로전자회로의 새 장 PDF(스캔본) 문제를 문제 1개당 md 1개로 변환한다. 0단계 조사, opus 작성과 독립 리뷰 파이프라인, 리뷰 반영, 인덱스, 장 단위 검증까지 한 번에 진행한다. 12장 문제 md로 변환해줘, N장 교과서 문제 변환, /textbook-to-md N 같은 요청에 쓴다.
---

# 교과서 문제 → MD 변환 (`textbook-to-md`)

Razavi 마이크로전자회로 `N장.pdf`의 예제, 연습문제, 장말문제를 FORMAT.md 형식의 md로 옮긴다. 9–11장(377문제)에서 검증한 절차다.

## 고정 규칙
- 형식과 판독 관례의 기준은 `교과서/마이크로전자회로/FORMAT.md` 하나다. 이 스킬은 형식을 다시 정의하지 않는다.
- 모든 서브에이전트는 **opus**로 띄운다(`model: opus`). 렌더링 검증(md → PNG)은 하지 않는다.
- 작성 에이전트는 한 번에 하나만 돌린다. git 인덱스와 figures.yaml을 공유하기 때문이다. 리뷰는 한 묶음 늦게 병렬로 돌린다.
- 추적하지 않는 파일(PDF, `STT/`, `강의노트/`)은 add하지 않는다. add할 때는 항상 경로를 명시한다.
- push, main 병합, worktree 삭제는 사용자에게 묻고 나서 한다.
- SPICE Problems는 범위 밖이다.

## 멈추고 묻는 경우 (이 셋뿐)
1. 0단계 조사에서 FORMAT이 다루지 않는 새 그림 유형이 나왔을 때. 표기 방법을 제안하고, 확인을 받으면 FORMAT.md의 해당 절(그림 유형이면 `## 본문 절` 5)에 먼저 추가해 커밋한다.
2. 마무리 검증이 실패했을 때. 오류 목록을 보여 주고 완료를 선언하지 않는다.
3. 병합, push, worktree 정리.

그 밖에는 묻지 않고 진행한다. 묶음마다 한 줄씩 진행 상황을 알린다.

## 절차

### 1. 입력과 전제
- 장 번호 `N`. 메인 checkout 루트를 `MAIN`이라 한다.
- `MAIN/교과서/마이크로전자회로/N장.pdf`가 없으면 중단하고 알린다.
- `git -C MAIN status --short | grep -v '^??'`가 비어 있어야 한다.
- 장마다 worktree를 하나씩 쓴다. 다른 장과 병렬로 진행할 수 있다. PDF는 심볼릭 링크로 넣고 절대 add하지 않는다.
  ```bash
  git -C MAIN worktree add "$(dirname MAIN)/$(basename MAIN)-chN" -b feat/chN-problem-md main
  ln -s MAIN/교과서/마이크로전자회로/N장.pdf "$(dirname MAIN)/$(basename MAIN)-chN/교과서/마이크로전자회로/N장.pdf"
  ```
  이후 모든 에이전트의 작업 루트(`<<REPO>>`)는 이 worktree(`WT`)다.

### 2. 재개 판단
`WT/교과서/마이크로전자회로/chN/`가 이미 있으면 처음부터 하지 않는다.
```bash
git -C WT log --oneline main.. --grep="chN"
ls WT/docs/superpowers/reports/chN/
```
세 가지로 어디까지 끝났는지 판단하고 그다음부터 잇는다.
- `add chN …` 커밋이 있으면 그 작성 묶음은 끝났다.
- `review-<묶음>.md`가 있으면 그 리뷰는 끝났다(추적 여부와 무관).
- `apply review fixes` / `record review` 커밋이 있으면 그 반영은 끝났다.

조사 결과가 scratchpad에 없으면 0단계를 다시 한다. 파일을 건드리지 않는 조사라서 안전하다.

### 3. 0단계 조사
1. `references/survey.md`의 자리표시자를 채워 `SCRATCH/survey-prompt-chN.md`로 쓴다. opus 에이전트 하나에 "이 파일을 읽고 그대로 따르라"고 맡긴다(포그라운드).
2. 결과 `SCRATCH/survey-chN.md`를 읽는다.
   - 새 그림 유형이 있으면 여기서 멈추고 묻는다(위 1번).
   - 묶음 계획을 확정한다. 12–18개씩, 예제와 연습문제를 먼저 예제 순으로, 장말문제는 PDF 페이지 경계로 나눈다. 이름은 A, B, C …
   - `WT/교과서/마이크로전자회로/chN/figures/figures.yaml`의 머리를 만든다. 첫 작성 에이전트가 함께 커밋한다.
     ```yaml
     # 그림 id → PDF 페이지(1부터)와 bbox [x0, y0, x1, y1] (PDF pt, 왼쪽 위 원점)
     # id 는 반드시 따옴표로 감싼다 ("N.30" 이 숫자 N.3 으로 바뀌는 것 방지)
     pdf: ../../N장.pdf
     dpi: 144
     figures:
     ```
3. 사용자에게 장 제목, 문제 수, 묶음 계획을 한 번 보여 주고, 묻지 않고 진행한다.

### 4. 공통 지침 파일
`references/common.md`를 채워 `SCRATCH/COMMON-chN.md`로 쓴다. `<<PAGE_MAP>>`에는 조사 결과의 쪽 대응 표, 예제 표, 장말문제 표와 목록을 그대로 붙인다.

### 5. 파이프라인
에이전트는 모두 opus로, 백그라운드로 띄운다. 프롬프트는 템플릿을 채운 파일을 `SCRATCH/`에 쓰고 "이 파일을 읽고 따르라"로 준다.

작성 k가 끝나면(첫 묶음은 바로) 다음 둘을 **동시에** 띄운다.
- **리뷰 k:** `references/reviewer.md`를 쓴다. 채울 값은 다음과 같다.
  - `<<TARGETS>>`: 묶음 k의 대상
  - `<<COMMIT>>`: 작성 k가 보고한 add 커밋
  - `<<FLAGS>>`: 작성 k가 보고한 "판독이 애매했던 곳"을 그대로 붙인다
  - `<<REPORT>>`: `docs/superpowers/reports/chN/review-<k>.md`
  - `<<PREV_FIX_COMMIT>>`: 작성 k의 1단계 커밋, 없으면 "없음"
- **작성 k+1:** `references/writer.md`를 쓴다.
  - 1단계는 리뷰 k−1의 보고서를 반영한다. 리뷰 k−1이 아직 안 끝났으면 끝날 때까지 기다렸다가 띄운다. 첫 두 묶음은 `<<PREV_REVIEW>>` = "없음"이다.
  - `<<BUSY_FILES>>`에는 리뷰 k의 대상 파일과 `<<PREV_FIX_COMMIT>>`이 고친 파일을 적는다.

마지막 작성 묶음 n이 끝나면 다음 순서로 마무리한다.
1. 리뷰 n과 **반영 n−1**을 동시에 띄운다. 반영 n−1은 `writer.md`에서 `<<TARGETS>>` = "없음", `<<PREV_BATCH>>` = n−1로 채운다.
2. 리뷰 n이 끝나면 **반영 n**을 띄운다(같은 방식).

묶음마다 사용자에게 한 줄씩 알린다. 내용은 작성 커밋, 리뷰 결과(사실 오류 수), 반영 커밋이다.

### 6. 마무리
1. 인덱스를 만들고 `docs: add chN problem index README`로 커밋한다.
   ```bash
   python3 교과서/마이크로전자회로/_tools/make_index.py 교과서/마이크로전자회로/chN "N장 <조사에서 읽은 장 제목>"
   ```
2. 검증을 돌린다. 모두 통과해야 완료다.
   ```bash
   python3 교과서/마이크로전자회로/_tools/verify_chapter.py 교과서/마이크로전자회로/chN --recrop
   for c in 교과서/마이크로전자회로/ch*/; do python3 교과서/마이크로전자회로/_tools/check_md.py "$c" | grep -c WARN; python3 교과서/마이크로전자회로/_tools/check_md.py "$c" | tail -1; done
   python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests
   ls docs/superpowers/reports/chN/
   git log --oneline main.. --grep="record review\|apply review fixes"
   ```
   - verify: 오류 0이어야 한다. INFO(연습문제가 없는 예제)는 원본에서 직접 확인해 보고에 적는다.
   - check_md: 모든 장이 오류 0, WARN 0이어야 한다.
   - 묶음마다 `review-<묶음>.md`가 있고, 그 보고서를 커밋한 반영 또는 기록 커밋이 있어야 한다.
3. 보고하고 병합·push·worktree 정리를 묻는다. 병합을 고르면 `git -C MAIN merge --ff-only feat/chN-problem-md`로 한다. main이 앞서 있으면 worktree에서 `git rebase main`을 한 뒤 fast-forward한다. worktree 삭제(`git worktree remove`)와 push는 따로 묻는다.

## 마무리 보고 형식
| 항목 | 결과 |
|---|---|
| 파일 수 | 예제 a, 연습문제 b, 장말문제 c, 합계 |
| 형식 검사 | `N개 파일, 오류 0개`, WARN 0 |
| 장 단위 검사 | 오류 0, INFO와 원본 확인 결과 |
| 그림 | 등록 수, 다시 크롭 일치 |
| 리뷰 | 묶음 수, 사실 오류 수와 반영 내용, 반영하지 않은 제안과 이유 |
| 원문 오식 | 인쇄대로 적은 곳 목록 |
| 브랜치 | worktree 경로, main 대비 커밋 수, push 안 함 |

## 자리표시자
템플릿의 `<<이름>>`을 아래 값으로 바꾼다. 경로는 절대 경로로 넣는다.

| 자리표시자 | 템플릿 | 값 |
|---|---|---|
| `<<N>>` | 전부 | 장 번호 (예: 12) |
| `<<REPO>>` | survey, common | worktree 절대 경로 |
| `<<PDF>>` | survey, common | `교과서/마이크로전자회로/N장.pdf` |
| `<<CH>>` | common | `교과서/마이크로전자회로/chN` |
| `<<SCRATCH>>` | survey, common | 세션 scratchpad 절대 경로 |
| `<<PAGE_MAP>>` | common | 조사 결과의 쪽 대응 표, 예제 표, 장말문제 표와 목록 |
| `<<COMMON>>` | writer, reviewer | `SCRATCH/COMMON-chN.md` 절대 경로 |
| `<<BATCH>>` | writer, reviewer | 이번 묶음 이름 |
| `<<TARGETS>>` | writer, reviewer | 대상 id 범위. 마무리 반영에서는 "없음" |
| `<<LOCATIONS>>` | writer | 조사 결과 중 이번 묶음의 위치 행 |
| `<<EXPECTED_TOTAL>>` | writer | 이 묶음을 마친 뒤 chN의 md 총수 |
| `<<BUSY_FILES>>` | writer | 지금 리뷰 중인 파일 |
| `<<PREV_BATCH>>` | writer | 반영할 리뷰의 묶음 이름 |
| `<<PREV_TARGETS>>` | writer | 그 묶음의 대상 id 범위 |
| `<<PREV_REVIEW>>` | writer | 그 보고서 경로 `docs/superpowers/reports/chN/review-<묶음>.md` 또는 "없음" |
| `<<COMMIT>>` | reviewer | 리뷰 대상 add 커밋 해시 |
| `<<FLAGS>>` | reviewer | 작성자가 보고한 판독이 애매했던 곳 |
| `<<REPORT>>` | reviewer | `docs/superpowers/reports/chN/review-<묶음>.md` |
| `<<PREV_FIX_COMMIT>>` | reviewer | 확인할 반영 커밋 해시 또는 "없음" |
````

- [ ] **Step 3: 스킬 검사를 돌려 통과하는지 확인한다**

Step 1과 같은 명령을 실행한다.
Expected: `skill OK`

- [ ] **Step 4: 전체 회귀 검사를 돌린다**

```bash
python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests 2>&1 | tail -1
for c in ch09 ch10 ch11; do python3 교과서/마이크로전자회로/_tools/verify_chapter.py 교과서/마이크로전자회로/$c --recrop | tail -1; done
git status --short | grep -v '^??'
```
Expected:
- 테스트: `OK`
- verify: 세 장 모두 `오류 0개` (ch11은 `참고 1개`)
- 마지막 명령: 출력이 비어 있어야 한다. SKILL.md는 아직 add하지 않아 `??`로만 보이므로 걸러지고, 그 밖에 커밋하지 않은 변경이 없어야 한다.

- [ ] **Step 5: 커밋한다**

```bash
git add .claude/skills/textbook-to-md/SKILL.md
git commit -m "feat: add textbook-to-md skill for chapter conversion

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 6: 사용자 확인** (병합하지 않는다)

브랜치 `feat/textbook-to-md-skill`의 커밋 목록(`git log --oneline main..`)을 보여 준다. main 병합과 push 여부는 사용자에게 묻는다.
