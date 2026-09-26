# 문제집 풀이 (④) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 399문제 md에 `## 풀이`를 쓰고 검산해, 답안지 PDF에 단계별 풀이와 답이 나오게 한다.

**Architecture:** 풀이 절차와 내용 규칙을 프로젝트 스킬 `.claude/skills/workbook-solution/`에 둔다(`SKILL.md` + `references/{rules,writer,reviewer,lessons}.md`). 오케스트레이터(이 계획을 실행하는 메인 세션)는 스킬의 배치 루프를 돌리고, 장마다 워크트리 하나에서 opus 작성자(한 번에 한 명)와 배치별 opus 리뷰어(background, 독립 풀이)를 띄운다. 진행은 `source_pages.py --section 풀이`로 추적한다.

**Tech Stack:** Python 3 표준 라이브러리 + PyMuPDF(`fitz`), unittest, playwright + Google Chrome(PDF 렌더), Claude Code 스킬과 Agent.

**Spec:** `docs/superpowers/specs/2026-09-26-workbook-solutions-design.md`

## Global Constraints

- `MAIN` = `/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2` (브랜치 `main`, 시작 시점 `d6756e2`).
- 워크트리 `WT09`, `WT10`, `WT11`, `WTEX` = `$MAIN/.claude/worktrees/sol-{ch09,ch10,ch11,exams}`, 브랜치 `claude/sol-{ch09,ch10,ch11,exams}`.
- 다른 세션의 워크트리 `.claude/worktrees/past-exam-tool-minor-fixes-04332f`, `.claude/worktrees/magical-wright-a2d529`와 `feat/ch09~11-problem-md` 브랜치는 건드리지 않는다.
- `SCRATCH` = 실행하는 세션의 scratchpad 절대 경로. 페이지 이미지, 검산 스크립트, 채운 지시문은 `$SCRATCH/sol/…`에 둔다. 저장소 안에는 두지 않는다. 셸 상태가 유지되지 않으므로 명령마다 `MAIN=…`, `WT09=…`, `SCRATCH=…`를 다시 정의한다.
- **git add:** 항상 경로를 명시한다. `git add -A`, `git add .`는 쓰지 않는다.
- **커밋 메시지:** 마지막 줄은 빈 줄 뒤 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`이다.
- **push는 하지 않는다.** main 병합, 워크트리 삭제는 그때마다 사용자에게 묻는다.
- **PDF:** Task 6 전까지 `workbook/pdf/*.pdf`를 다시 만들거나 커밋하지 않는다. 빌드할 때는 항상 `--pdf-dir workbook/build/pdf`를 준다.
- **풀이 규칙**의 유일한 기준은 `.claude/skills/workbook-solution/references/rules.md`다(Task 3에서 만든다). 확정 규칙:
  - 단계 3~5개(최대 6), 마지막 `### 답`. 단계마다 식 → 값 대입 → 결과(유효숫자 3자리, 단위).
  - 축퇴 출력 저항은 처음부터 $[1 + g_m(R_E \parallel r_\pi)]\, r_O$, $(1 + g_m R_S)\, r_O$. 뒤 항 `+R_E∥r_π`, `+R_S`는 쓰지 않는다.
  - 예제도 새로 쓰고 `## 답 (검증용)`과 대조한다.
- **배치:** 교과서 10문제, 기출은 시험 폴더 하나. 순서는 장마다 예제 → 연습문제 → 장말문제, 기출은 2021-1_중간 → 2021-1_기말 → 2023-1_중간 → 2023-1_기말.
- **서브에이전트:** 작성자와 리뷰어 모두 `Agent`(subagent_type `general-purpose`, model `opus`). 워크트리 하나에 작성자는 한 번에 한 명.
- **스킬 수정:** 오케스트레이터만 한다. Task 4 병합 전에는 `WT09`에서, 병합 뒤에는 `MAIN`(main)에서만 커밋한다.
- **테스트 명령과 기대 개수**
  - 교과서 도구 `python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests`: 129개, 변하지 않는다.
  - 기출 도구 `python3 -m unittest discover -s from_the_past/md/_tools/tests`: 지금 70개, Task 2 뒤 71개.
  - 생성기 `python3 -m unittest discover -s workbook/tests`: 지금 91개, Task 1 뒤 96개.

## Review Focus

1. **기출 md에 `## 풀이`와 `### 답`을 넣으면 `check_exam`이 "답 절" 오류로 막을까:** `ANSWER_RE = ^## 답`은 `### 답`과 맞지 않아야 한다. 통과해야 한다. → Task 2 `test_solution_section_allowed`
2. **`--section` 인자가 NFD로 들어옴:** 터미널이나 파일 이름에서 붙여 넣은 `풀이`가 NFD면 argparse `choices`에서 떨어진다. NFC로 바꿔 받아야 한다. → Task 1 `test_section_argument_nfd_accepted`
3. **힌트 원장과 풀이 추적을 섞어 씀:** `--ledger`와 `--section 풀이`를 같이 주면 조용히 원장 기준으로 동작하면 안 된다. `ERROR`와 종료 코드 2. → Task 1 `test_section_with_ledger_is_error`
4. **종류 폴더(`ch09/예제`)를 대상으로 줌:** 스킬은 예제 → 연습 → 장말 순서로 하위 폴더를 넘긴다. 하위 폴더에서도 목록이 나와야 한다. → Task 1 `test_pending_on_kind_subfolder`
5. **스킬 템플릿과 자리표시자 표가 어긋남:** 템플릿에 표에 없는 `<<X>>`가 있으면 에이전트가 채워지지 않은 지시를 받는다. → Task 3 Step 1의 자리표시자 대조 검사

---

### Task 0: 준비 — 옛 워크트리 정리, ch09 워크트리, 설계 문서

**Files:**
- Move: `$MAIN/docs/superpowers/specs/2026-09-26-workbook-solutions-design.md`, `$MAIN/docs/superpowers/plans/2026-09-26-workbook-solutions.md` → `WT09`의 같은 경로. 두 파일은 지금 MAIN에서 추적되지 않는다.

- [ ] **Step 1: 옛 힌트 워크트리 정리 (사용자에게 묻고 나서)** — 묻는다: "`hints-{ch09,ch10,ch11,exams}` 워크트리 4개와 `claude/hints-*` 브랜치는 모두 main에 병합됐습니다. 지울까요? ch09 워크트리의 추적되지 않는 `progress.md`도 함께 사라집니다." 승인을 받으면 실행한다. 거절하면 건너뛴다.

```bash
MAIN=/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2; cd "$MAIN"
for x in ch09 ch10 ch11 exams; do git merge-base --is-ancestor claude/hints-$x main && echo "병합됨 $x"; done   # 4줄
for x in ch09 ch10 ch11 exams; do git worktree remove --force .claude/worktrees/hints-$x && git branch -d claude/hints-$x; done
git worktree list
```
`--force`는 추적되지 않는 `progress.md`와 `__pycache__` 때문에 필요하다. `git branch -d`(소문자)는 병합되지 않은 브랜치를 지우지 않으므로 안전장치가 된다.

- [ ] **Step 2: 워크트리 만들기와 설계 문서 커밋**

```bash
MAIN=/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2; cd "$MAIN"
git status --short        # 설계 문서 두 개(??)만
git worktree add .claude/worktrees/sol-ch09 -b claude/sol-ch09 main
WT09=$MAIN/.claude/worktrees/sol-ch09
mv docs/superpowers/specs/2026-09-26-workbook-solutions-design.md "$WT09/docs/superpowers/specs/"
mv docs/superpowers/plans/2026-09-26-workbook-solutions.md "$WT09/docs/superpowers/plans/"
cd "$WT09"
git add docs/superpowers/specs/2026-09-26-workbook-solutions-design.md docs/superpowers/plans/2026-09-26-workbook-solutions.md
git commit -m "docs: add workbook solutions design and plan

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 3: 기준 테스트**

```bash
cd /Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/.claude/worktrees/sol-ch09
python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests 2>&1 | grep ^Ran   # Ran 129
python3 -m unittest discover -s from_the_past/md/_tools/tests 2>&1 | grep ^Ran          # Ran 70
python3 -m unittest discover -s workbook/tests 2>&1 | grep ^Ran                         # Ran 91
```

---

### Task 1: `source_pages.py --section`

**Files:**
- Modify: `workbook/source_pages.py` (docstring 1–11, `pending` 48–61, `parse_args` 141–155, `main` 158–172)
- Modify: `workbook/README.md` ('원문 옮기기 도구' 절)
- Test: `workbook/tests/test_source_pages.py`

**Interfaces:**
- Produces:
  - `pending(folder, ledger=None, section="원문") -> list[Path]`: `ledger`가 None이면 `## <section>` 절이 없는 md를 (source, pdf_page, id) 순으로.
  - CLI `next|missing <폴더> --section {원문,풀이}`. `missing`의 stderr 끝 줄은 `<section> 없음: N개`(원장을 주면 `판정 없음: N개`).
  - `--ledger`와 `--section 풀이`를 함께 주면 stderr `ERROR …`, 종료 코드 2.

- [ ] **Step 1: 실패하는 테스트** — `test_source_pages.py` 맨 위 import에 `import unicodedata`를 더하고, `class TestRender(Base):` 앞에 다음 클래스를 넣는다.

```python
class TestSection(Base):
    SOL = "\n## 풀이\n### 소신호 파라미터\n- $g_m = 1$\n### 답\n- 1\n"

    def test_pending_section_skips_solved(self):
        write_md(self.ch / "예제/E9.01.md", "E9.01", "예제", 1, original=True, tail=self.SOL)
        write_md(self.ch / "예제/E9.02.md", "E9.02", "예제", 2, original=True)
        self.assertEqual([p.name for p in pending(self.ch, section="풀이")], ["E9.02.md"])
        self.assertEqual(pending(self.ch), [])

    def test_pending_on_kind_subfolder(self):
        write_md(self.ch / "예제/E9.01.md", "E9.01", "예제", 1, original=True)
        write_md(self.ch / "장말문제/P9.01.md", "P9.01", "장말문제", 1, original=True)
        self.assertEqual([p.name for p in pending(self.ch / "예제", section="풀이")], ["E9.01.md"])

    def test_main_missing_section(self):
        write_md(self.ch / "예제/E9.01.md", "E9.01", "예제", 1, original=True)
        code, out, err = run(["missing", str(self.ch), "--section", "풀이"])
        self.assertEqual(code, 1)
        self.assertIn("E9.01.md", out)
        self.assertIn("풀이 없음: 1개", err)
        write_md(self.ch / "예제/E9.01.md", "E9.01", "예제", 1, original=True, tail=self.SOL)
        self.assertEqual(run(["missing", str(self.ch), "--section", "풀이"])[0], 0)

    def test_section_argument_nfd_accepted(self):
        write_md(self.ch / "예제/E9.01.md", "E9.01", "예제", 1, original=True)
        code, out, _ = run(["next", str(self.ch), "--section", unicodedata.normalize("NFD", "풀이")])
        self.assertEqual(code, 0)
        self.assertEqual([Path(line).name for line in out.splitlines()], ["E9.01.md"])

    def test_section_with_ledger_is_error(self):
        write_md(self.ch / "예제/E9.01.md", "E9.01", "예제", 1, original=True)
        ledger = self.root / "hints-ledger.md"
        ledger.write_text("- E9.01 | 없음 | 대입만\n", encoding="utf-8")
        code, _, err = run(["next", str(self.ch), "--section", "풀이", "--ledger", str(ledger)])
        self.assertEqual(code, 2)
        self.assertIn("ERROR", err)
```

- [ ] **Step 2: 실패 확인**

Run: `cd $WT09 && python3 -m unittest workbook/tests/test_source_pages.py 2>&1 | tail -3`
Expected: `FAILED (errors=…)`. `pending()`에 `section` 인자가 없어서 TypeError, CLI 테스트는 argparse의 `unrecognized arguments`로 SystemExit가 난다.

- [ ] **Step 3: 구현** — `workbook/source_pages.py`를 다음처럼 고친다.

docstring의 사용법 두 줄을 바꾼다:
```python
  python3 workbook/source_pages.py next <폴더> [--size 10] [--section 원문|풀이] [--ledger 원장]
      그 절이 없는(원장을 주면 판정 없는) md를 (원본, pdf_page, id) 순으로 N개. 기본 절은 원문
  python3 workbook/source_pages.py missing <폴더> [--section 원문|풀이] [--ledger 원장]
      남은 md 목록(+ 원장과 힌트 수가 다른 MISMATCH). 하나라도 있으면 종료 코드 1
```
그리고 `<폴더>` 설명 줄 뒤에 한 줄을 더한다:
```python
<폴더>는 종류 하위 폴더(ch09/예제)도 된다. --ledger는 힌트 판정용이라 --section 풀이와 함께 쓰지 않는다.
```

import에 `import unicodedata`를 더하고, `LEDGER_LINE_RE` 아래에 둔다:
```python
SECTIONS = ("원문", "풀이")


def nfc(text):
    return unicodedata.normalize("NFC", text)
```

`pending`을 바꾼다:
```python
def pending(folder, ledger=None, section="원문"):
    """할 일이 남은 md를 (source, pdf_page, id) 순으로. 같은 쪽의 예제·연습문제가 이어진다.
    ledger가 None이면 section 절(원문, 풀이)이 없는 md, 판정 원장(dict)이면 원장에 판정이 없는 md."""
    keyed = []
    for md in problem_mds(folder):
        meta, body = read_md(md)
        if ledger is None:
            if any(title == section for title, _ in split_sections(body)):
                continue
        elif str(meta["id"]) in ledger:
            continue
        keyed.append(((str(meta.get("source", "")), int(meta["pdf_page"]), str(meta["id"])), md))
    return [md for _, md in sorted(keyed)]
```

`parse_args`에서 `nxt.add_argument("--ledger", …)` 줄 뒤와 `mis.add_argument("--ledger", …)` 줄 뒤에 각각 넣는다:
```python
    nxt.add_argument("--section", type=nfc, choices=SECTIONS, default="원문", help="이 절이 없는 md를 낸다")
```
```python
    mis.add_argument("--section", type=nfc, choices=SECTIONS, default="원문", help="이 절이 없는 md를 낸다")
```

`main`의 `next`/`missing` 부분을 바꾼다:
```python
        if args.cmd in ("next", "missing"):
            if args.ledger and args.section != "원문":
                print("ERROR --ledger는 힌트 판정용이라 --section과 함께 쓰지 않음", file=sys.stderr)
                return 2
            ledger = read_ledger(args.ledger) if args.ledger else None
            left = pending(args.folder, ledger, args.section)
```
```python
            what = "판정 없음" if ledger is not None else f"{args.section} 없음"
```

- [ ] **Step 4: 통과 확인**

Run: `cd $WT09 && python3 -m unittest discover -s workbook/tests 2>&1 | tail -3`
Expected: `Ran 96 tests` … `OK`

실제 폴더로 확인:
```bash
cd $WT09
python3 workbook/source_pages.py next 교과서/마이크로전자회로/ch09/예제 --section 풀이 --size 3      # E9.xx 3줄
python3 workbook/source_pages.py missing 교과서/마이크로전자회로/ch09 --section 풀이 >/dev/null; echo $?   # 풀이 없음: 110개, 1
python3 workbook/source_pages.py missing 교과서/마이크로전자회로/ch09 >/dev/null; echo $?                  # 원문 없음: 0개, 0
```

- [ ] **Step 5: README** — `workbook/README.md` '원문 옮기기 도구' 절의 코드 블록 끝에 두 줄을 더한다.

```bash
python3 workbook/source_pages.py next 교과서/마이크로전자회로/ch09/예제 --section 풀이 --size 10   # 풀이 없는 md (종류 하위 폴더도 됨)
python3 workbook/source_pages.py missing 교과서/마이크로전자회로/ch09 --section 풀이              # 풀이 남은 것
```

- [ ] **Step 6: 커밋**

```bash
cd $WT09
git add workbook/source_pages.py workbook/tests/test_source_pages.py workbook/README.md
git commit -m "feat(workbook): track missing sections with source_pages --section

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: 기출에 `## 풀이` 허용과 FORMAT 문서

**Files:**
- Modify: `from_the_past/md/FORMAT-EXAM.md:44-45`
- Modify: `from_the_past/md/_tools/check_exam.py:144`
- Modify: `교과서/마이크로전자회로/FORMAT.md:180` 뒤
- Test: `from_the_past/md/_tools/tests/test_check_exam.py`

**Interfaces:**
- Consumes: 없음
- Produces: 기출 md의 `## 풀이`가 `check_exam`을 통과한다는 보장(Task 5의 기출 배치가 쓴다).

- [ ] **Step 1: 고정 테스트** — `test_check_exam.py`의 `test_answer_section_rejected` 뒤에 넣는다.

```python
    def test_solution_section_allowed(self):
        solution = "\n## 풀이\n### (1) 소신호 파라미터\n- $g_m = 1\\ \\text{mS}$\n### 답\n- (1) $1\\ \\text{k}\\Omega$\n"
        self.assertEqual(self.check(VALID_Q2 + solution), ([], []))
```

- [ ] **Step 2: 실행**

Run: `cd $WT09 && python3 -m unittest from_the_past/md/_tools/tests/test_check_exam.py 2>&1 | tail -3`
Expected: `OK`. 이미 통과하는 고정 테스트다(`ANSWER_RE`가 `### 답`과 맞지 않음). 실패하면 멈추고 `ANSWER_RE`를 보고한다.

- [ ] **Step 3: 오류 문구** — `check_exam.py:144`를 바꾼다.

```python
        errors.append("기출에는 답 절을 두지 않음 (풀이와 답은 ## 풀이에 씀, FORMAT-EXAM.md)")
```

- [ ] **Step 4: FORMAT-EXAM.md** — 44행을 바꾼다.

old: ``- `## 답` 절은 두지 않는다(풀이는 이번 범위 밖).``
new: ``- `## 답` 절은 두지 않는다. 풀이와 답은 `## 풀이`(마지막 소절 `### 답`)에 쓴다.``

45행 앞부분을 바꾼다.

old: ``- 문제집용 절 `## 원문`, `## 힌트`는 교과서 FORMAT.md의 '문제집용 절'을 그대로 따른다. `## 풀이`는 아직 쓰지 않는다(풀이 작업에서 정함).``
new: ``- 문제집용 절 `## 원문`, `## 힌트`, `## 풀이`는 교과서 FORMAT.md의 '문제집용 절'을 그대로 따른다. 풀이 내용 규칙은 `.claude/skills/workbook-solution/references/rules.md`에 있다.``

(45행의 나머지 문장 "원문은 인쇄된 글자만 옮기고…"는 그대로 둔다.)

- [ ] **Step 5: FORMAT.md** — 180행("예제에 `## 풀이`가 없으면 …") 뒤에 한 줄을 넣는다.

```markdown
- `## 풀이`의 내용(단계 구성, 식 → 대입 → 값, 근사 관례, 예제 대조, 조건이 모자랄 때)은 `.claude/skills/workbook-solution/references/rules.md`가 정한다. 이 문서는 모양만 정한다.
```

- [ ] **Step 6: 테스트와 검사**

```bash
cd $WT09
python3 -m unittest discover -s from_the_past/md/_tools/tests 2>&1 | grep ^Ran           # Ran 71
python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests 2>&1 | tail -1       # OK
for e in 2021-1_중간 2021-1_기말 2023-1_중간 2023-1_기말; do python3 from_the_past/md/_tools/check_exam.py from_the_past/md/$e | tail -1; done   # 오류 0
```

- [ ] **Step 7: 커밋**

```bash
git add from_the_past/md/FORMAT-EXAM.md from_the_past/md/_tools/check_exam.py from_the_past/md/_tools/tests/test_check_exam.py 교과서/마이크로전자회로/FORMAT.md
git commit -m "docs: allow ## 풀이 in exam md and point to the solution rules

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: 스킬 `workbook-solution`

**Files:**
- Create: `.claude/skills/workbook-solution/SKILL.md`
- Create: `.claude/skills/workbook-solution/references/rules.md`
- Create: `.claude/skills/workbook-solution/references/writer.md`
- Create: `.claude/skills/workbook-solution/references/reviewer.md`
- Create: `.claude/skills/workbook-solution/references/lessons.md`
- Delete (저장소 밖): 메모리 `~/.claude/projects/-Users-hyunjun-macbook-pro-Documents-Univ-----2/memory/workbook-solution-degeneration-rout.md`와 `MEMORY.md`의 그 줄

**Interfaces:**
- Consumes: Task 1의 `next/missing --section 풀이`, Task 2의 기출 `## 풀이` 허용
- Produces: 오케스트레이터가 따르는 `SKILL.md` 절차와, 에이전트 지시 템플릿의 자리표시자 11개 `LABEL, BATCH, WT, SKILL, REPORTS, TARGETS, PAGES, CHECK_CMD, COMMIT, FLAGS, REPORT`

- [ ] **Step 1: 실패하는 구조 검사** — 이 검사를 `$SCRATCH/sol/check_skill.py`로 저장한다.

```python
import re, sys
from pathlib import Path

d = Path(sys.argv[1]) / ".claude/skills/workbook-solution"
skill = (d / "SKILL.md").read_text(encoding="utf-8")
assert skill.startswith("---\nname: workbook-solution\ndescription: "), "frontmatter"
table = set(re.findall(r"^\| `<<(\w+)>>`", skill, re.M))
used = set()
for t in ("writer.md", "reviewer.md"):
    used |= set(re.findall(r"<<(\w+)>>", (d / "references" / t).read_text(encoding="utf-8")))
for f in ("rules.md", "lessons.md"):
    assert (d / "references" / f).is_file(), f
    assert "<<" not in (d / "references" / f).read_text(encoding="utf-8"), f"{f}에 자리표시자"
print("표에 없음:", sorted(used - table))
print("쓰이지 않음:", sorted(table - used))
assert used == table
print("OK", len(table))
```

Run: `python3 $SCRATCH/sol/check_skill.py $WT09`
Expected: `FileNotFoundError` (SKILL.md가 아직 없음)

- [ ] **Step 2: `SKILL.md`**

````markdown
---
name: workbook-solution
description: 문제집 md(교과서 ch09–11, 기출)의 `## 풀이`를 작성자·리뷰어 배치로 쓰고 독립 풀이로 검산한다. "풀이 써줘", "chNN 풀이 채워", 특정 문제 풀이 다시 쓰기, /workbook-solution <라벨> 같은 요청에 쓴다.
---

# 문제집 풀이 (`workbook-solution`)

문제 md 끝에 `## 풀이`를 쓴다. 작성자가 풀고 모든 수치를 **검산**해서 쓰고, 리뷰어가 **독립 풀이**로 다시 풀어 대조한다.

## 고정 규칙
- 풀이 내용의 기준은 `references/rules.md` 하나다. 모양(`### 소절`, 마지막 `### 답`)은 `교과서/마이크로전자회로/FORMAT.md` '문제집용 절'과 `check_md.py`가 정한다.
- 서브에이전트는 모두 `Agent`(subagent_type `general-purpose`, model `opus`)로 띄운다. 프롬프트는 템플릿을 채운 파일을 `SCRATCH/sol/<라벨>/`에 쓰고 "이 파일을 읽고 그대로 따르라"로 준다.
- 워크트리 하나에 작성자는 한 번에 한 명이다(git index 공유). 리뷰어는 배치마다 background로 띄우고 기다리지 않는다.
- 스킬 파일은 `<<SKILL>>` 경로(병합 뒤에는 main checkout)에서 읽게 한다. 스킬 수정은 오케스트레이터만 하고 main에서 커밋한다.
- `git add`는 경로를 명시한다. 커밋 끝에 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. push, main 병합, 워크트리 삭제는 사용자에게 묻는다.
- 작업 중 빌드는 `--pdf-dir workbook/build/pdf`. `workbook/pdf/`는 모든 라벨을 모은 뒤 한 번만 다시 만든다.

## 멈추고 묻는 경우 (이 셋뿐)
1. 리뷰가 `rules.md` 자체를 바꿔야 할 문제를 찾았을 때. 바꿀 문장과 이미 쓴 풀이에 소급할지를 함께 묻는다.
2. 완료 검사가 실패했을 때.
3. 병합, push, 워크트리 정리.

그 밖에는 묻지 않고 진행하고, 배치마다 한 줄씩 알린다(작성 커밋, 리뷰 [높음] 수, 반영 커밋).

## 절차

### 1. 입력과 워크트리
- 라벨 `L`: `ch09` | `ch10` | `ch11` | `exams`. 특정 id만 다시 쓸 때는 그 id 목록이 대상이고 배치 하나로 끝낸다.
- 폴더 순서 `F…`
  - 교과서: `교과서/마이크로전자회로/L/예제` → `…/연습문제` → `…/장말문제`
  - 기출: `from_the_past/md/2021-1_중간` → `2021-1_기말` → `2023-1_중간` → `2023-1_기말` (폴더 하나가 배치 하나)
- 워크트리 `WT` = `MAIN/.claude/worktrees/sol-L`, 브랜치 `claude/sol-L`. 없으면 만든다.
  ```bash
  git -C MAIN worktree add .claude/worktrees/sol-L -b claude/sol-L main
  ```
- 완료 기준: `git -C WT status --short`가 비어 있다(재개라면 2로).

### 2. 재개 판단
- 남은 문제: 폴더마다 `python3 workbook/source_pages.py missing <F> --section 풀이`.
- 끝난 리뷰: `docs/superpowers/reports/L/sol-<X>.md`. `.part`만 있으면 끊긴 리뷰다. `.part`를 지우고 그 배치 리뷰를 다시 띄운다.
- 반영 안 된 리뷰: `git -C WT log --oneline -1 -- <보고서>`가 비어 있는 보고서.
- 다음 배치 글자: `git -C WT log --oneline main.. --grep="solutions batch"`의 마지막 글자 다음.

### 3. 배치 루프
1. 대상: WT에서 `python3 workbook/source_pages.py next <현재 F> --section 풀이 --size 10`(기출은 `--size 20`). 비었으면 다음 폴더로, 모든 폴더가 비었으면 4로.
2. 작성자: `references/writer.md`를 채워 띄운다. `<<REPORTS>>`에는 끝났고(`.part` 아님) 아직 반영 안 된 보고서를 모두 넣는다. 끝나면 최종 메시지에서 커밋 해시, 애매한 곳, 조건 문제를 받는다.
3. 리뷰어: `references/reviewer.md`를 채워 background로 띄운다. `<<FLAGS>>`에는 작성자의 애매한 곳과 조건 문제를 그대로 붙인다. 작성자의 답 요약은 넣지 않는다(독립 풀이를 흐리지 않게).
4. 배치 글자를 올리고 1로.
5. 교훈: 리뷰에 [높음]이 있거나 같은 지적이 두 배치 이상 나오면, 그 교훈 한 줄을 `references/lessons.md`에 더해 main에서 `docs(skill): add solution lesson`으로 커밋한다. 규칙 자체를 바꿔야 하면 멈추고 묻는다.

### 4. 마무리
1. 모든 리뷰어가 끝나기를 기다린다. 반영 안 된 보고서가 있으면 작성자를 "반영만" 모드(`<<TARGETS>>` = 없음)로 띄운다.
2. 완료 검사. 모두 통과해야 완료다.
   ```bash
   cd WT
   for f in <F…>; do python3 workbook/source_pages.py missing "$f" --section 풀이 >/dev/null || echo "남음 $f"; done
   <<CHECK_CMD>>                                   # 교과서는 장 폴더, 기출은 시험 폴더마다. 오류 0
   python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests 2>&1 | tail -1
   python3 -m unittest discover -s from_the_past/md/_tools/tests 2>&1 | tail -1
   python3 -m unittest discover -s workbook/tests 2>&1 | tail -1
   python3 workbook/build_workbook.py <L 또는 시험 폴더 이름> --pdf-dir workbook/build/pdf 2>&1 | grep -E "OVERFLOW|ERROR"   # 비어야 함
   ls docs/superpowers/reports/L/*.part 2>/dev/null                                                                     # 비어야 함
   for r in docs/superpowers/reports/L/sol-*.md; do git log --oneline -1 -- "$r" | grep -q . || echo "미반영 $r"; done  # 비어야 함
   ```
3. 보고하고 병합을 묻는다. 병합은 WT에서 `git rebase main` 뒤 `git -C MAIN merge --ff-only claude/sol-L`. 먼저 `git -C MAIN branch --show-current`가 `main`인지 확인한다.

## 마무리 보고 형식
| 항목 | 결과 |
|---|---|
| 풀이 수 | 예제 a, 연습문제 b, 장말문제 c (기출은 시험별) |
| 검사 | check 오류 0, 테스트 3묶음 OK, OVERFLOW 0 |
| 리뷰 | 배치 수, [높음] 지적 수와 유형, 반영하지 않은 지적과 이유 |
| 예제 대조 | 교재 값과 다른 예제 목록과 이유 |
| 조건 수정 | 고친 문제 목록 |
| 브랜치 | 워크트리, main 대비 커밋 수, push 안 함 |

## 자리표시자
경로는 절대 경로로 넣는다.

| 자리표시자 | 템플릿 | 값 |
|---|---|---|
| `<<LABEL>>` | writer, reviewer | `ch09` · `ch10` · `ch11` · `exams` |
| `<<BATCH>>` | writer, reviewer | 배치 글자 (A, B, …) |
| `<<WT>>` | writer, reviewer | 워크트리 절대 경로 |
| `<<SKILL>>` | writer, reviewer | 스킬 폴더 절대 경로. 파일럿 병합 전에는 `WT09/.claude/skills/workbook-solution`, 뒤에는 `MAIN/.claude/skills/workbook-solution` |
| `<<REPORTS>>` | writer | 반영할 보고서 경로들 또는 "없음" |
| `<<TARGETS>>` | writer, reviewer | 대상 md 경로들 또는 "없음"(반영만) |
| `<<PAGES>>` | writer, reviewer | `SCRATCH/sol/<라벨>/<배치>` |
| `<<CHECK_CMD>>` | writer, reviewer | 교과서 `python3 교과서/마이크로전자회로/_tools/check_md.py 교과서/마이크로전자회로/<장>`, 기출 `python3 from_the_past/md/_tools/check_exam.py <시험 폴더>` |
| `<<COMMIT>>` | reviewer | 작성자의 `add … solutions batch` 커밋 해시 |
| `<<FLAGS>>` | reviewer | 작성자가 보고한 애매한 곳과 조건 문제 |
| `<<REPORT>>` | reviewer | `docs/superpowers/reports/<라벨>/sol-<배치>.md` |
````

(주: 4-2의 `<<CHECK_CMD>>`는 오케스트레이터가 직접 치는 명령이라 자리를 표시했다. 구조 검사는 writer·reviewer 템플릿만 대조한다.)

- [ ] **Step 3: `references/rules.md`**

````markdown
# 풀이 규칙

`## 풀이` 내용의 기준이다. 모양(`### 소절`, 마지막 `### 답`)은 FORMAT.md '문제집용 절'이 정하고 `check_md.py`가 막는다.

독자는 이 문제집으로 공부하는 학생이다. 답안지 한 쪽에 문제 원문, 조건, 구할 것, 문제 그림, 풀이, 답이 함께 보인다. `## 상속·참조`와 `## 회로` 넷리스트, 답 그림은 보이지 않는다.

## 구조
- 단계 하나 = `### <이름표>` 소절, 한 가지를 구한다. 3~5개가 기본이고 6개까지. 마지막은 `### 답`.
- 이름표는 그 단계가 구하는 것을 20자 안팎 명사구로 쓴다. 예: `소신호 파라미터`, `절반 회로의 출력 저항`.
- 소문항이 있으면 이름표 앞에 번호를 붙인다. 교과서 `(a) `, 기출 `(1) `. 소문항마다 적어도 한 단계.

## 단계 본문
- `- ` 목록 1~4줄. 한 줄은 식 → 값 대입 → 결과다.
  - 예: `- $g_{m1} = I_{C1}/V_T = 1\ \text{mA}/26\ \text{mV} = 38.5\ \text{mS}$`
- 결과는 유효숫자 3자리에 단위를 붙인다. 기호로 답하는 문제는 대입 없이 식만 쓴다.
- 앞 단계의 값은 기호로 부른다. 계산은 반올림 전 값으로 한다(검산 스크립트 그대로).
- 근사는 쓰는 줄에 조건과 함께 적는다. 예: `($r_O \gg R_E$이므로)`.
- 회로를 다르게 보는 줄(절반 회로, 가상 접지, 퇴화로 보기)에는 왜 그렇게 볼 수 있는지 한 줄을 붙인다.
- 문법: `- ` 목록(2칸 들여쓰기로 한 단계), `$…$`, `$$…$$`, `**굵게**`. 표, 코드 블록, 이미지는 쓰지 않는다.

## 수업 관례
- 축퇴 출력 저항은 처음부터 짧은 식으로 쓴다.
  - 바이폴라 $R_{out} \approx [1 + g_m(R_E \parallel r_\pi)]\, r_O$
  - MOS $R_{out} \approx (1 + g_m R_S)\, r_O$
  - 교재 식 (9.1)·(9.3)의 뒤 항 $+R_E \parallel r_\pi$, $+R_S$는 쓰지 않는다. 적은 뒤 근사로 지우는 흐름도 쓰지 않는다.
- 조건에 없는 상수(예: $V_T = 26\ \text{mV}$)는 처음 쓰는 줄에 값을 밝힌다.

## 기호
- 문제지에 보이는 기호(원문, 조건, 구할 것, 문제 그림 라벨)는 그대로 쓴다. 그 밖의 기호는 처음 쓸 때 정의한다. 예: `$Q_1$ 컬렉터에서 본 저항 $R_X$`.
- 답 그림에만 있는 이름(예: $Q_F$)은 쓰지 않는다.

## 힌트와 잇기
- `## 힌트`가 있으면 그 아이디어를 쓰는 단계를 둔다. 답안지의 풀이 칸과 Hint 쪽은 따로 읽히므로, 그 단계 안에서 이유를 한 줄로 다시 적는다. "힌트 1 참고" 같은 참조는 쓰지 않는다.

## `### 답`
- `## 구할 것`의 항목 순서대로 `- ` 한 줄씩. 수치는 값과 단위, 기호 답은 최종 식. 소문항은 `- (a) …`.
- 설명을 묻는 항목은 한두 문장.

## 예제
- 교재 풀이의 흐름을 따르고, 최종 값을 `## 답 (검증용)`과 대조한다.
- 수업 관례 때문에 생기는 2% 미만의 차이는 적지 않는다.
- 그보다 크게 다르면 계산으로 다시 확인한다. 교재 쪽 오류면 그 단계 끝에 `- 교재 값 <값>과 다름: <이유 한 줄>`을 적는다.

## 조건이 모자라거나 틀릴 때
- 문제지에 인쇄된 것만으로 풀리지 않으면(값 누락, 사양 충돌, 원문 오식) 첫 단계 첫 줄에 `- <무엇>을 <값>으로 가정한다 (<까닭>)`를 두고 푼다. `## 조건`은 이 배치에서 고치지 않고 보고한다. 리뷰가 확인하면 다음 반영 커밋에서 조건을 고치고 이 줄을 지운다.
- 조건에 따라 답이 갈리면(출력 단락과 개방 등) 어느 경우인지 밝힌다. 원문이 정하지 않았으면 두 경우를 모두 적는다.

## 분량
- 한 문제의 풀이는 답안지 한 쪽에 들어가야 한다. 단계 본문을 합쳐 약 1300자가 기준이다.
- 빌드가 OVERFLOW를 내면 템플릿은 두고 풀이를 줄인다. 뻔한 대입 줄을 합치고 설명 줄을 줄인다. 결과가 이어지지 않게 단계를 빼지는 않는다.
````

- [ ] **Step 4: `references/writer.md`**

````markdown
# 풀이 작성 — <<LABEL>> 배치 <<BATCH>>

당신은 작성 에이전트다. 작업 폴더는 <<WT>>이고 모든 명령은 여기서 실행한다(cd <<WT>>).
먼저 읽는다: <<SKILL>>/references/rules.md, <<SKILL>>/references/lessons.md, 교과서/마이크로전자회로/FORMAT.md의 '문제집용 절'. 기출이면 from_the_past/md/FORMAT-EXAM.md도 읽는다.

## 0. 리뷰 반영 (반영할 보고서: <<REPORTS>>, "없음"이면 건너뜀)
- 지적마다 직접 다시 계산해 판단한다. 동의하면 고치고, 동의하지 않으면 고치지 않고 이유를 최종 메시지에 적는다.
- 조건 문제 지적을 받아들이면 `## 조건`·`## 구할 것`을 고친다(원문에 없는 보충은 FORMAT.md대로 `(원문에 없음)`). 그리고 풀이 첫 단계의 가정 줄을 지운다.
- 검사(3)를 돌린다.
- 조건을 고쳤으면 그 md만 먼저 커밋한다: git commit -m "docs(<<LABEL>>): fix 조건 for <ids>"
- 나머지와 보고서를 커밋한다: git commit -m "docs(<<LABEL>>): apply review fixes to solutions batch <보고서 글자들>". 고친 것이 없어도 보고서는 커밋한다.

## 1. 대상 (<<TARGETS>>, "없음"이면 4의 최종 메시지로)
md마다 다음을 한다.
- md 전체를 읽는다: 원문, 조건, 구할 것, 회로 넷리스트와 단자·배치 설명, 상속·참조, 답 (검증용), 힌트.
- 이미지 줄(![Fig …](…png))이 가리키는 그림을 Read로 연다(md 기준 상대 경로).
- 원본 쪽이 필요하면 python3 workbook/source_pages.py render <md> --out <<PAGES>> 로 그려 본다.
- 푼다. 모든 수치를 **검산**한다: <<PAGES>>/calc-<id>.py에 식을 적어 python3로 돌리고, 풀이의 숫자는 그 출력에서 옮긴다. 검산 파일은 md에 넣지 않는다.
- 예제는 rules.md '예제'대로 `## 답 (검증용)`과 대조한다.

## 2. 쓰기
- rules.md를 따른다. `## 풀이`는 파일 맨 끝(`## 힌트`가 있으면 그 뒤)에 빈 줄 하나를 두고 붙인다.
- md의 다른 절은 고치지 않는다. 조건 문제는 rules.md '조건이 모자라거나 틀릴 때'대로 한다.

## 3. 검사
<<CHECK_CMD>>
python3 workbook/build_workbook.py --ids <대상 id들, 쉼표로> --name 풀이-<<LABEL>>-<<BATCH>> --pdf-dir workbook/build/pdf 2>&1 | grep -E "OVERFLOW|ERROR"
검사 오류가 0이고 빌드 출력이 빌 때까지 고친다. OVERFLOW는 rules.md '분량'대로 줄인다.

## 4. 커밋
git add <대상 md 경로들>
git commit -m "docs(<<LABEL>>): add solutions batch <<BATCH>> (<첫 id>–<끝 id>)" (끝에 빈 줄 + Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>)
git add에는 경로를 명시한다(-A나 . 금지). push하지 않는다.

## 최종 메시지
- 커밋 해시(조건 수정, 반영, 배치 커밋)
- 예제 대조: "<id> — 일치 | 다름 (교재 <값>, 계산 <값>, <이유>)" (예제가 없으면 생략)
- 애매한 곳: "<id> — <무엇을 어떻게 해석·가정했는지>" (없으면 "없음")
- 조건 문제: "<id> — <무엇이 모자라거나 틀린지, 둔 가정>" (없으면 "없음")
- 반영하지 않은 지적과 이유
````

- [ ] **Step 5: `references/reviewer.md`**

````markdown
# 풀이 리뷰 — <<LABEL>> 배치 <<BATCH>>

당신은 리뷰 에이전트다. 작업 폴더는 <<WT>>다. 먼저 <<SKILL>>/references/rules.md와 <<SKILL>>/references/lessons.md를 읽는다.

- 대상: <<TARGETS>> (커밋 <<COMMIT>>)
- 작성자가 애매하다고 한 곳과 조건 문제 (특히 독립적으로 판단):
<<FLAGS>>

## 원칙
- 추적되는 파일을 고치지 않고 git 상태도 바꾸지 않는다. 만드는 파일은 보고서 <<REPORT>> 하나뿐이다(폴더가 없으면 만든다). <<REPORT>>.part에 쓰고, 다 마친 뒤 mv <<REPORT>>.part <<REPORT>> 한다.
- **독립 풀이**가 먼저다. 대상마다 git show <<COMMIT>>^:<경로> 로 풀이가 없는 버전을 읽고, 그림을 보고, 직접 푼다. 수치는 <<PAGES>>/review/calc-<id>.py로 python3에서 계산한다. 모든 대상의 값을 표로 적은 뒤에야 git show <<COMMIT>> 으로 작성자의 풀이를 연다.
- 대조할 것:
  1. 최종 값: 독립 풀이와 상대 2% 안인가. 기호 답은 식이 같은가.
  2. 물리: 모델, 동작 영역, 근사 조건, 단락·개방 조건이 맞는가.
  3. 단계: 식 → 대입 → 결과가 맞고, 앞 단계 값과 이어지는가.
  4. rules.md: 기호, 수업 관례(축퇴 짧은 식), 단계 수와 분량, 답 순서, 힌트와 잇기.
  5. 예제: `## 답 (검증용)`과 맞는가. 다르면 메모가 있고 그 계산이 맞는가.
  6. 조건: 문제지에 인쇄된 것만으로 풀리는가. 가정 줄이 있으면 그 가정이 타당한가.
- 형식 검사를 한 번 돌린다: <<CHECK_CMD>>

## 보고서
# 풀이 리뷰 <<BATCH>> — 커밋 <<COMMIT>>

방법: <독립 풀이 여부, 본 그림과 원본 쪽, 형식 검사 결과>

## 독립 풀이 값
| id | 항목 | 리뷰어 | 작성자 | 일치 |

## 작성자가 애매하다고 한 곳 — 독립 판단
- <id>: 동의 | 반대 (<이유>)

### <id> — OK | 수정 필요 | 조건 문제
- [높음|중간|낮음] <대조 항목 번호>: <지적> → <고칠 내용>

[높음]은 틀린 값, 틀린 물리, 인쇄된 조건만으로 풀 수 없는 문제다. [낮음]은 표현 제안이다. 확신이 없으면 "불확실"로 표시한다. 최종 메시지에는 수정 필요와 조건 문제의 개수, [높음] 목록을 요약한다.
````

- [ ] **Step 6: `references/lessons.md`**

````markdown
# 풀이 교훈

배치 리뷰에서 나온, 규칙으로 올리기에는 좁은 교훈과 참고 값이다. 오케스트레이터만 더한다. 한 줄씩, 끝에 출처를 괄호로 적는다. 규칙이 되면 rules.md로 옮기고 여기서 지운다.

## 기출 해석
- 2021-1 중간 Q4(1) "Common-mode 이득"은 단일 출력으로 푼다. (힌트 리뷰)
- 2023-1 중간 Q3 (1)은 출력 단락과 개방에서 전류 분배가 다르다. 원문이 정하지 않았으므로 두 경우를 적는다. (힌트 리뷰)

## 힌트 리뷰에서 구한 값 (검산 대조용, 풀이에 그대로 옮기지 말고 다시 계산)
- X10.25: $R_1 \approx 1.7\ \text{k}\Omega$
- P10.91: 원문의 "minimum λ"는 허용 최대 λ이고 약 $0.235\ \text{V}^{-1}$
- P11.26: $\omega_T = g_m/\sqrt{C_\pi(C_\pi + 2C_\mu)}$
- E11.21: $C_{SB} = 100\ \text{fF}$로 식 (11.114)의 $b = 8.35 \times 10^{-11}\ \text{s}$, 대역폭 약 3.45 GHz. 교재의 $5.8 \times 10^{-11}\ \text{s}$는 오식
````

- [ ] **Step 7: 구조 검사 통과**

Run: `python3 $SCRATCH/sol/check_skill.py $WT09`
Expected: `표에 없음: []`, `쓰이지 않음: []`, `OK 11`

- [ ] **Step 8: 메모리 정리** — 축퇴 규칙이 `rules.md`로 옮겨졌으므로 임시 메모리를 지운다.

```bash
M=/Users/hyunjun_macbook_pro/.claude/projects/-Users-hyunjun-macbook-pro-Documents-Univ-----2/memory
rm "$M/workbook-solution-degeneration-rout.md"
grep -v 'workbook-solution-degeneration-rout.md' "$M/MEMORY.md" > "$M/MEMORY.md.new" && mv "$M/MEMORY.md.new" "$M/MEMORY.md"
cat "$M/MEMORY.md"   # 두 줄
```

- [ ] **Step 9: 커밋**

```bash
cd $WT09
git add .claude/skills/workbook-solution/SKILL.md .claude/skills/workbook-solution/references/rules.md .claude/skills/workbook-solution/references/writer.md .claude/skills/workbook-solution/references/reviewer.md .claude/skills/workbook-solution/references/lessons.md
git commit -m "feat(skill): add workbook-solution skill

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: 파일럿 — ch09 예제 10문제, 규칙 확정, main 병합

**Files:**
- Modify: `교과서/마이크로전자회로/ch09/예제/*.md` 가운데 `next --section 풀이`가 처음 낸 10개
- Create: `docs/superpowers/reports/ch09/sol-A.md`
- Modify (사용자가 규칙을 바꿀 때만): `.claude/skills/workbook-solution/references/rules.md`

**Interfaces:**
- Consumes: Task 1–3 전부. 스킬 `SKILL.md` 절차 3을 배치 하나만 돌린다. `<<SKILL>>` = `$WT09/.claude/skills/workbook-solution`.
- Produces: main에 병합된 도구, 스킬, 파일럿 풀이. Task 5 워크트리는 이 main에서 만든다.

- [ ] **Step 1: 대상**

```bash
cd $WT09; python3 workbook/source_pages.py next 교과서/마이크로전자회로/ch09/예제 --section 풀이 --size 10
```

- [ ] **Step 2: 작성자** — `SKILL.md` 절차 3-2대로 `writer.md`를 채워 `$SCRATCH/sol/ch09/A-writer.md`에 쓰고 띄운다(foreground). 값: LABEL=`ch09`, BATCH=`A`, WT=`$WT09`, SKILL=`$WT09/.claude/skills/workbook-solution`, REPORTS=없음, TARGETS=Step 1의 10개, PAGES=`$SCRATCH/sol/ch09/A`, CHECK_CMD=`python3 교과서/마이크로전자회로/_tools/check_md.py 교과서/마이크로전자회로/ch09`.
- [ ] **Step 3: 리뷰어** — `reviewer.md`를 채워 `$SCRATCH/sol/ch09/A-reviewer.md`에 쓰고 띄운다. 파일럿에서는 **foreground**로 기다린다. REPORT=`docs/superpowers/reports/ch09/sol-A.md`.
- [ ] **Step 4: 반영** — `writer.md`를 "반영만" 모드(TARGETS=없음, REPORTS=`docs/superpowers/reports/ch09/sol-A.md`)로 띄운다.
- [ ] **Step 5: 검사, 빌드, 눈으로 확인**

```bash
cd $WT09
python3 교과서/마이크로전자회로/_tools/check_md.py 교과서/마이크로전자회로/ch09 | tail -1                 # 오류 0
IDS=$(git -c core.quotepath=false diff --name-only main -- 교과서/마이크로전자회로/ch09/예제 | xargs -n1 basename | sed 's/\.md$//' | paste -sd, -)
python3 workbook/build_workbook.py --ids "$IDS" --name 풀이-파일럿 --pdf-dir workbook/build/pdf 2>&1 | grep -E "OVERFLOW|ERROR"   # 비어야 함
SCRATCH=<scratchpad 절대 경로> python3 - <<'EOF'
import fitz, os, glob
out = os.environ["SCRATCH"] + "/sol/pilot-png"
os.makedirs(out, exist_ok=True)
for pdf in glob.glob("workbook/build/pdf/*파일럿-답안.pdf"):
    with fitz.open(pdf) as d:
        for i in range(d.page_count):
            d[i].get_pixmap(dpi=80).save(f"{out}/a{i+1:02d}.png")
print(out)
EOF
```
`--name`이 NFC로 바뀌지 않는 문제가 있으므로 glob이 비면 `ls workbook/build/pdf`로 실제 이름을 찾는다. PNG를 Read로 열어 확인한다: 단계 번호와 이름표, 식 → 대입 → 값 줄이 KaTeX로 그려졌고, `답` 상자에 구할 것 순서로 값이 있고, "넘침" 표시가 없다.

- [ ] **Step 6: 사용자 확인** — 보여 준다.
  - 답안지 PNG 두세 장(단계가 가장 많은 문제 포함)
  - 예제 대조 결과(일치/다름 목록)
  - 리뷰 A의 [높음]·[중간] 지적 요약과 반영 결과
  - 규칙을 바꿀 만한 점이 보였다면 그 제안

  묻는다: "풀이의 깊이와 모양이 원하시는 것과 맞나요? 바꿀 규칙이 있으면 말씀해 주세요. 맞으면 `claude/sol-ch09`를 main에 병합하고 ch10·ch11·기출 워크트리를 열어 병렬로 진행합니다."
  사용자가 규칙을 바꾸면: `rules.md`(와 Global Constraints의 확정 규칙)를 고쳐 `docs(skill): …`로 커밋하고, 파일럿 10문제를 "반영만" 모드 작성자에게 새 규칙으로 다시 쓰게 한 뒤 Step 5–6을 되풀이한다.

- [ ] **Step 7: 병합** (사용자가 승인한 뒤)

```bash
MAIN=/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2
test "$(git -C $MAIN branch --show-current)" = main && git -C $MAIN merge --ff-only claude/sol-ch09
```

---

### Task 5: 확장 — ch09 나머지, ch10, ch11, 기출 병렬

**Files:**
- Modify: `교과서/마이크로전자회로/{ch09,ch10,ch11}/{예제,연습문제,장말문제}/*.md`, `from_the_past/md/*/Q*.md`
- Create: `docs/superpowers/reports/{ch09,ch10,ch11,exams}/sol-*.md`
- Modify (교훈이 생길 때만, main에서): `.claude/skills/workbook-solution/references/lessons.md`

**Interfaces:**
- Consumes: main의 스킬. 이제 `<<SKILL>>` = `$MAIN/.claude/skills/workbook-solution`.
- Produces: 브랜치 `claude/sol-{ch09,ch10,ch11,exams}`의 풀이. Task 6이 모은다.

- [ ] **Step 1: 워크트리**

```bash
cd /Users/hyunjun_macbook_pro/Documents/Univ/전자회로2
for x in ch10 ch11 exams; do git worktree add .claude/worktrees/sol-$x -b claude/sol-$x main; done
git worktree list
```
- [ ] **Step 2: 네 라벨을 번갈아 돌린다** — 라벨마다 `SKILL.md` 절차 1–4(마무리의 병합 질문은 빼고)를 돌린다. 작성자는 background로 띄우고, 한 워크트리의 작성자가 끝나면 그 워크트리의 리뷰어와 다음 작성자를 띄운다. 배치 글자와 예상 배치 수:
  - ch09: `B`부터, 예제 11 + 연습문제 21 + 장말문제 68 → 약 11배치
  - ch10: `A`부터, 29 + 29 + 93 → 약 16배치
  - ch11: `A`부터, 29 + 28 + 59 → 약 12배치
  - exams: `A`=2021-1_중간(5), `B`=2021-1_기말(7), `C`=2023-1_중간(4), `D`=2023-1_기말(6)
- [ ] **Step 3: 교훈과 규칙** — `SKILL.md` 절차 3-5대로. 교훈 커밋은 MAIN에서:

```bash
cd /Users/hyunjun_macbook_pro/Documents/Univ/전자회로2
git add .claude/skills/workbook-solution/references/lessons.md
git commit -m "docs(skill): add solution lesson

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```
- [ ] **Step 4: 라벨마다 완료 검사** — `SKILL.md` 절차 4-2를 통과시킨다. 실패하면 멈추고 보고한다.

---

### Task 6: 통합 — 모으기, PDF 다시 만들기, 병합

**Files:**
- Modify: `workbook/pdf/*.pdf` (14개)

**Interfaces:**
- Consumes: 브랜치 `claude/sol-{ch09,ch10,ch11,exams}`, main의 교훈 커밋

- [ ] **Step 1: ch09 브랜치로 모으기** — 다른 파일만 건드렸으므로 충돌은 예상하지 않는다. 충돌이 나면 멈추고 보고한다.

```bash
MAIN=/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2
git -C "$MAIN/.claude/worktrees/sol-ch09" rebase main
for x in ch10 ch11 exams; do
  git -C "$MAIN/.claude/worktrees/sol-$x" rebase claude/sol-ch09 &&
  git -C "$MAIN/.claude/worktrees/sol-ch09" merge --ff-only claude/sol-$x || break
done
```

- [ ] **Step 2: 전체 검사** (`WT09`)

```bash
cd $WT09
for c in ch09 ch10 ch11; do
  python3 workbook/source_pages.py missing 교과서/마이크로전자회로/$c --section 풀이 >/dev/null || echo "남음 $c"
  python3 교과서/마이크로전자회로/_tools/check_md.py 교과서/마이크로전자회로/$c | tail -1
done
for e in 2021-1_중간 2021-1_기말 2023-1_중간 2023-1_기말; do
  python3 workbook/source_pages.py missing from_the_past/md/$e --section 풀이 >/dev/null || echo "남음 $e"
  python3 from_the_past/md/_tools/check_exam.py from_the_past/md/$e | tail -1
done
python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests 2>&1 | tail -1   # OK (129)
python3 -m unittest discover -s from_the_past/md/_tools/tests 2>&1 | tail -1          # OK (71)
python3 -m unittest discover -s workbook/tests 2>&1 | tail -1                         # OK (96)
python3 $SCRATCH/sol/check_skill.py $WT09                                             # OK 11
```
Expected: "남음"이 없고 검사 오류가 0이다.

- [ ] **Step 3: 전체 빌드**

```bash
python3 workbook/build_workbook.py --all 2> $SCRATCH/sol/build-all.txt; echo "exit $?"; grep -E "OVERFLOW|ERROR" $SCRATCH/sol/build-all.txt
```
Expected: `exit 0`, 출력 없음. OVERFLOW가 있으면 멈추고 넘친 id와 PNG(Task 4 Step 5 방식)를 보여 준다. 대응은 그 풀이를 `rules.md` '분량'대로 줄이는 것이고, 템플릿은 고치지 않는다.

- [ ] **Step 4: PDF 확인과 커밋** — 장마다 답안지 몇 쪽을 PNG로 그려 확인한 뒤 커밋한다.

```bash
git status --short workbook/pdf     # M 14개
git add workbook/pdf/*.pdf
git commit -m "build: regenerate pdfs with solutions

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
du -sh /Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/.git
```

- [ ] **Step 5: 사용자 확인 후 main 병합과 정리** — `SKILL.md`의 마무리 보고 형식으로 라벨별 결과와 `.git` 크기를 보고하고 묻는다: "`claude/sol-ch09`를 main에 ff-merge하고, 워크트리 4개와 브랜치를 지울까요?" 승인 뒤 실행한다.

```bash
cd /Users/hyunjun_macbook_pro/Documents/Univ/전자회로2
test "$(git branch --show-current)" = main && git merge --ff-only claude/sol-ch09
for x in ch09 ch10 ch11 exams; do git worktree remove .claude/worktrees/sol-$x && git branch -d claude/sol-$x; done
git worktree list
```
