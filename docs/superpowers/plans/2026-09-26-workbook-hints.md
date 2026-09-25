# 문제집 힌트 채우기 (`## 힌트`) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 교과서 377문제와 기출 22문제를 모두 검토해, 힌트가 필요한 문제(약 25~40%)에만 핵심 아이디어 힌트를 `## 힌트`로 넣는다. 그 뒤 쪽 넘침 없이 PDF 14개를 다시 만들어 커밋한다.

**Architecture:** 코드 작업은 둘이다.
- `check_md.py`: 힌트 절 검사를 강화한다(띠 줄 경계, 이름표 길이, 개수).
- `workbook/source_pages.py`: `next`/`missing`에 `--ledger` 옵션을 더해, 판정 원장을 기준으로 배치와 남은 것을 낸다.

나머지는 내용 작업이다. opus 작성자가 15문제씩 풀어 보고 판정하며, 독립 opus 리뷰어가 배치마다 검토한다. ch09 워크트리에서 도구와 파일럿을 끝내 main에 병합한다. 그 뒤 ch10, ch11, 기출 워크트리를 병렬로 돌리고, 마지막에 ch09 브랜치로 모아 PDF를 다시 만든다.

**Tech Stack:** Python 3.14 (Homebrew), PyYAML, PyMuPDF(`fitz`), 표준 라이브러리 `unittest`(pytest 없음), 생성기 `workbook/build_workbook.py`(Playwright + 설치된 Chrome), Agent 도구(subagent, model `opus`).

**Spec:** `docs/superpowers/specs/2026-09-26-workbook-hints-design.md`

## Global Constraints

- `MAIN` = `/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2` (메인 checkout, 브랜치 `main`, 시작 시점 `34113ec`)
- 워크트리 `WT09`, `WT10`, `WT11`, `WTEX` = `$MAIN/.claude/worktrees/hints-{ch09,ch10,ch11,exams}`, 브랜치 `claude/hints-{ch09,ch10,ch11,exams}`.
- 다른 세션의 워크트리 `.claude/worktrees/past-exam-tool-minor-fixes-04332f`와 `feat/ch09~11-problem-md` 브랜치는 건드리지 않는다.
- `SCRATCH` = 실행하는 세션의 scratchpad 경로. 페이지 이미지와 풀이 메모는 `$SCRATCH/hints/<라벨>/<배치>/`에 둔다. 저장소 안에는 두지 않는다. 셸 상태가 유지되지 않으므로 셸 명령마다 `export SCRATCH=<경로>`와 `WT09=…` 같은 변수를 다시 정의한다.
- **git add:** 항상 경로를 명시한다. `git add -A`, `git add .`는 쓰지 않는다.
- **커밋 메시지:** 마지막 줄은 빈 줄 뒤 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`이다.
- **push는 하지 않는다.** main 병합과 워크트리 삭제는 그때마다 사용자에게 묻는다.
- **PDF:** Task 7 전까지 `workbook/pdf/*.pdf`를 다시 만들거나 커밋하지 않는다. 빌드할 때는 항상 `--pdf-dir workbook/build/pdf`를 준다(`workbook/build/`는 gitignore).
- **힌트 규칙**(스펙 '힌트 작성 규칙'과 같다. FORMAT.md에도 Task 1에서 적는다)
  - **넣을 때**: 공식 대입만으로는 바로 풀리지 않는 경우에만 넣는다.
    - 회로를 다른 모양으로 다시 보기: 반회로, 가운데 노드에서 본 저항, 퇴화 저항으로 보기, 알려진 구조로 알아보기
    - 어느 노드에서 무엇을 들여다볼지
    - 무시해도 되는 소자
    - 대칭이나 가상 접지 알아보기
  - **넣지 않을 때**: 값 대입으로 끝나는 문제, 예제를 바로 되풀이하는 문제, 정의를 묻는 문제. 억지로 만들지 않는다. 목표는 전체의 약 25~40%이고 배치마다 맞추는 할당량은 아니다.
  - **개수**: 문제당 1개가 기본이고 최대 2개다. 2개면 풀이 순서대로 둔다.
  - **이름표**(`### ` 뒤)는 문제지 띠에 그대로 보인다. 24자 이내(`check_md`가 셈)의 명령형 또는 명사구로 쓴다.
  - **본문**은 `- ` 목록 1~3줄로, 그렇게 볼 수 있는 이유를 쓴다. 수치 답, 최종 식, 중간 계산 값은 쓰지 않는다.
  - **`> 띠:` 식**: 기본으로 쓰지 않는다. 식 자체가 아이디어일 때만 예외로 쓰고, 쓴 이유를 원장 이유 칸에 적는다.
  - **예제 이어받기**만으로는 힌트가 아니다(이미 `## 조건`에 있음). 보는 법이 핵심일 때만 넣는다.
  - **예제와 기출**도 같은 기준이다.
  - **위치**: `## 힌트`는 파일 맨 끝에 둔다(빈 줄 하나 뒤). `## 풀이`는 아직 없다. md의 다른 부분은 고치지 않는다.
- **판정 원장:** 라벨마다 하나씩 `docs/superpowers/reports/<라벨>/hints-ledger.md`를 둔다. 줄 형식은 `- <id> | 힌트 <1|2> | <이유>` 또는 `- <id> | 없음 | <이유>`다. 첫 줄은 `# 힌트 판정 원장 — <라벨>`이다.
- **리뷰 보고서:** `docs/superpowers/reports/<라벨>/hint-<배치 글자>.md`
- **테스트 명령과 기대 개수**
  - 교과서 도구 `python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests`: 지금 100개, Task 1 뒤 105개.
  - 기출 도구 `python3 -m unittest discover -s from_the_past/md/_tools/tests`: 65개, 변하지 않는다.
  - 생성기 `python3 -m unittest discover -s workbook/tests`: 지금 80개, Task 2 뒤 86개, Task 7에서 템플릿을 고치면 87개.
- **서브에이전트:** 작성자와 리뷰어 모두 `Agent`(subagent_type `general-purpose`, model `opus`)로 띄운다. 워크트리 하나에 작성자는 한 번에 한 명뿐이다. 같은 git index와 같은 원장을 쓰기 때문이다.

## Review Focus

1. **수식이 든 이름표를 길이 검사가 잘못 막음:** `$C_{\mu}$를 밀러로 입력과 출력에 나눈다`는 글자 수로는 26자지만 띠에 보이는 글자는 19자다. 통과해야 한다. → Task 1 `test_hint_label_math_counts_visible_chars`
2. **목록 아래 들여쓴 `> 띠:` 줄이 조용히 사라짐:** `hints()`는 들여쓴 줄을 띠 식으로 보지 않고 본문에 둔다. 검사기가 막아야 한다. → Task 1 `test_indented_strip_line_rejected`
3. **원장에는 "힌트 1"인데 md에 힌트 절을 빠뜨림:** 원장만 보면 완료로 보인다. `missing --ledger`가 `MISMATCH`와 종료 코드 1을 내야 한다. → Task 2 `test_main_missing_reports_mismatch`
4. **원장 줄의 오타:** 예를 들어 `| 아마 |`가 조용히 무시되면 그 문제는 판정이 안 된 채로 남거나 두 번 판정된다. `ERROR` 줄이 나와야 한다. → Task 2 `test_bad_line_raises`, `test_duplicate_id_raises`
5. **첫 배치에서 원장 파일이 아직 없음:** traceback이 아니라 "판정 0개"로 다뤄 모든 md를 내야 한다. → Task 2 `test_missing_ledger_file_is_empty`

---

## 절차 B — 배치 반복 (Task 3–6에서 오케스트레이터가 실행)

오케스트레이터는 이 계획을 실행하는 메인 세션이다. 가지고 다니는 값은 다음과 같다.
- 워크트리 `WT`
- 폴더 `F` (예: `교과서/마이크로전자회로/ch10`)
- 라벨 `L` (예: `ch10`)
- 원장 `LEDGER` = `docs/superpowers/reports/L/hints-ledger.md`
- 배치 글자 (A, B, C…)

1. `cd WT && python3 workbook/source_pages.py next F --ledger LEDGER --size 15`로 다음 배치의 md 경로 목록을 얻는다. 목록이 비었으면 6으로 간다.
2. 반영하지 않은 리뷰 보고서 목록을 모은다. 대상은 `docs/superpowers/reports/L/hint-<글자>.md` 가운데 끝난 것(`.part`가 아닌 것)이면서 아직 반영 커밋이 없는 것이다.
3. **부록 W**의 작성자 지시에 값을 채워 작성자 subagent를 foreground로 띄운다. 끝나면 받는 것:
   - 커밋 해시
   - 힌트를 넣은 id와 이름표 목록
   - 판정이 애매했던 곳
   - OVERFLOW 줄
4. **부록 R**의 리뷰어 지시에 3의 결과를 넣어 리뷰어 subagent를 background로 띄운다.
5. 배치 글자를 하나 올리고 1로 돌아간다. 리뷰가 끝나기를 기다리지 않는다.
6. 모든 리뷰어가 끝날 때까지 기다린다. 반영하지 않은 보고서가 남았으면 부록 W를 "반영만" 모드(대상 "없음")로 한 번 더 띄운다.
7. **완료 검사 C**를 돌린다.

### 완료 검사 C (교과서 장 `chNN`)
```bash
cd WT
python3 workbook/source_pages.py missing 교과서/마이크로전자회로/chNN --ledger docs/superpowers/reports/chNN/hints-ledger.md   # 종료 코드 0, "판정 없음: 0개", MISMATCH 없음
python3 교과서/마이크로전자회로/_tools/check_md.py 교과서/마이크로전자회로/chNN   # 오류 0
python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests 2>&1 | tail -1   # OK
python3 -m unittest discover -s from_the_past/md/_tools/tests 2>&1 | tail -1          # OK
python3 -m unittest discover -s workbook/tests 2>&1 | tail -1                         # OK
grep -c "| 힌트" docs/superpowers/reports/chNN/hints-ledger.md; grep -c "^- " docs/superpowers/reports/chNN/hints-ledger.md   # 힌트 비율
python3 workbook/build_workbook.py chNN --pdf-dir workbook/build/pdf 2> $SCRATCH/overflow-chNN.txt; grep OVERFLOW $SCRATCH/overflow-chNN.txt
```
- 앞의 다섯 명령은 모두 성공해야 한다.
- 힌트 비율이 15% 밑이거나 50% 위면 오케스트레이터 메모에 남기고 Task 7 보고에 넣는다. 재작업하지는 않는다.
- OVERFLOW 줄은 실패로 보지 않는다. 목록만 기록하고 Task 7에서 처리한다.
- 기출은 네 시험 폴더마다 `missing … --ledger docs/superpowers/reports/exams/hints-ledger.md`를 돌린다. 검사는 `python3 from_the_past/md/_tools/check_exam.py <폴더>`, 빌드는 `build_workbook.py <시험 폴더 이름>`이다.

---

### Task 0: 준비 — ch09 워크트리와 설계 문서

**Files:**
- Move: `$MAIN/docs/superpowers/specs/2026-09-26-workbook-hints-design.md`, `$MAIN/docs/superpowers/plans/2026-09-26-workbook-hints.md` → `WT09`의 같은 경로. 두 파일은 지금 MAIN에서 추적되지 않는 상태다.

- [ ] **Step 1: 워크트리 만들기**

```bash
cd /Users/hyunjun_macbook_pro/Documents/Univ/전자회로2
git status --short                      # 설계 문서 두 개(??)만 보여야 한다
git worktree add .claude/worktrees/hints-ch09 -b claude/hints-ch09 main
```

- [ ] **Step 2: 설계 문서를 워크트리로 옮겨 커밋**

```bash
MAIN=/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2; WT09=$MAIN/.claude/worktrees/hints-ch09
mv "$MAIN/docs/superpowers/specs/2026-09-26-workbook-hints-design.md" "$WT09/docs/superpowers/specs/"
mv "$MAIN/docs/superpowers/plans/2026-09-26-workbook-hints.md" "$WT09/docs/superpowers/plans/"
cd "$WT09"
git add docs/superpowers/specs/2026-09-26-workbook-hints-design.md docs/superpowers/plans/2026-09-26-workbook-hints.md
git commit -m "docs: add workbook hints design and plan

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 3: 기준 테스트 확인**

```bash
cd "$WT09"
python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests 2>&1 | grep ^Ran   # Ran 100
python3 -m unittest discover -s from_the_past/md/_tools/tests 2>&1 | grep ^Ran          # Ran 65
python3 -m unittest discover -s workbook/tests 2>&1 | grep ^Ran                         # Ran 80
```

---

### Task 1: `check_md`의 힌트 검사 강화와 FORMAT.md 규칙

**Files:**
- Modify: `교과서/마이크로전자회로/_tools/check_md.py` (상수는 44–51행 근처, `check_workbook_sections`는 100–136행)
- Modify: `교과서/마이크로전자회로/FORMAT.md` ('문제집용 절', 149–167행)
- Test: `교과서/마이크로전자회로/_tools/tests/test_check_md.py` (`TestWorkbookSections`, `test_bad_formula_line` 뒤)

**Interfaces:**
- Consumes: 기존 `HINT_FORMULA_RE`, `split_subsections`
- Produces:
  - `check_md.HINT_LABEL_MAX = 24`, `check_md.HINT_MAX = 2`
  - `check_md.hint_label_length(label: str) -> int`
  - `check_md.check_hint(label: str, text: str) -> list[str]`
  - `check_workbook_sections`가 새 오류를 낸다. 기출 검사기도 `check_body`를 거쳐 같은 검사를 받는다.

- [ ] **Step 1: 실패하는 테스트 작성** — `test_bad_formula_line` 바로 뒤에 추가한다.

```python
    def test_two_strip_lines_rejected(self):
        self.assert_error(WB_BASE + "\n## 힌트\n### 식\n> 띠: $a$\n> 띠: $b$\n- x\n", "하나만")

    def test_indented_strip_line_rejected(self):
        self.assert_error(WB_BASE + "\n## 힌트\n### 반회로\n- 대칭\n  > 띠: $R = r_O$\n", "들여 쓰지")

    def test_hint_label_too_long_rejected(self):
        self.assert_error(WB_BASE + "\n## 힌트\n### " + "가" * 25 + "\n- x\n", "24자까지")

    def test_hint_label_math_counts_visible_chars(self):
        body = WB_BASE + "\n## 힌트\n### $C_{\\mu}$를 밀러로 입력과 출력에 나눈다\n- x\n"
        self.assertEqual(check_workbook_sections(body), [])
        self.assertEqual(hint_label_length("$C_{\\mu}$를 밀러로 입력과 출력에 나눈다"), 19)
        self.assertEqual(hint_label_length("$I = 1\\ \\text{mA}$"), 5)

    def test_three_hints_rejected(self):
        self.assert_error(WB_BASE + "\n## 힌트\n### 가\n- x\n### 나\n- y\n### 다\n- z\n", "2개까지")
```

그리고 파일 위쪽 import 줄(11행)을 다음처럼 바꾼다.

```python
from check_md import check_workbook_sections, hint_label_length, split_sections, split_subsections  # noqa: E402
```

- [ ] **Step 2: 실패 확인**

Run: `python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests 2>&1 | tail -3`
Expected: `ImportError: cannot import name 'hint_label_length'`

- [ ] **Step 3: 구현**

`check_md.py`에서 `import sys` 뒤에 `import unicodedata`를 추가한다. `HINT_FORMULA_RE = …` 줄 바로 뒤에 다음을 추가한다.

```python
HINT_STRIP_PREFIX = "> 띠:"
HINT_LABEL_MAX = 24     # 이름표는 문제지 Hint 띠(24mm, 7.5pt)에 그대로 보인다. 3줄쯤
HINT_MAX = 2
LABEL_MATH_RE = re.compile(r"\$([^$]+)\$")
TEX_WRAPPER_RE = re.compile(r"\\(text|mathrm|left|right)\b")
TEX_COMMAND_RE = re.compile(r"\\[A-Za-z]+")
TEX_MARKUP_RE = re.compile(r"[{}_^\\\s]")
```

`check_original` 뒤에 두 함수를 추가한다.

```python
def hint_label_length(label):
    """띠에 보이는 글자 수. 수식 안은 \\mu 같은 명령을 한 글자로, \\text 같은 감싸개와 중괄호·첨자 기호·공백은 0으로 센다."""
    def visible(m):
        tex = TEX_WRAPPER_RE.sub("", m.group(1))
        return TEX_MARKUP_RE.sub("", TEX_COMMAND_RE.sub("x", tex))
    return len(unicodedata.normalize("NFC", LABEL_MATH_RE.sub(visible, label)))


def check_hint(label, text):
    """## 힌트의 ### 소절 하나: 띠 식 줄은 소절당 하나, 들여 쓰지 않고, 이름표는 HINT_LABEL_MAX자까지."""
    errors = []
    strips = [line for line in text.splitlines() if line.lstrip().startswith(HINT_STRIP_PREFIX)]
    for line in strips:
        if line != line.lstrip():
            errors.append(f"## 힌트 / ### {label}: 띠 식 줄은 들여 쓰지 않음 ({line.strip()!r})")
        elif not HINT_FORMULA_RE.match(line.rstrip()):
            errors.append(f"## 힌트 / ### {label}: 띠 식 줄은 '> 띠: $<LaTeX>$' 형식 ({line.strip()!r})")
    if len(strips) > 1:
        errors.append(f"## 힌트 / ### {label}: 띠 식 줄은 소절에 하나만 ({len(strips)}개)")
    n = hint_label_length(label)
    if n > HINT_LABEL_MAX:
        errors.append(f"## 힌트 / ### {label}: 이름표는 {HINT_LABEL_MAX}자까지 (지금 {n}자) — 문제지 띠에 그대로 보임")
    return errors
```

`check_workbook_sections`의 소절 반복 부분을 다음처럼 바꾼다. 원래 코드는 `for label, text in subs:`부터 `if name == "풀이":` 앞까지다.

```python
        for label, text in subs:
            if label and not text.strip():
                errors.append(f"## {name} / ### {label}: 내용 없음")
            if name == "힌트" and label:
                errors += check_hint(label, text)
        if name == "힌트":
            count = sum(1 for label, _ in subs if label)
            if count > HINT_MAX:
                errors.append(f"## 힌트: 힌트는 {HINT_MAX}개까지 (지금 {count}개)")
```

- [ ] **Step 4: 통과 확인**

Run: `python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests 2>&1 | tail -1` → `OK` (105개)
Run: `python3 -m unittest discover -s from_the_past/md/_tools/tests 2>&1 | tail -1` → `OK` (65개)
Run: `python3 -m unittest discover -s workbook/tests 2>&1 | tail -1` → `OK` (80개)
Run: `for c in ch09 ch10 ch11; do python3 교과서/마이크로전자회로/_tools/check_md.py 교과서/마이크로전자회로/$c | tail -1; done` → 세 장 모두 오류 0 (아직 힌트가 없으므로 변화 없음)

- [ ] **Step 5: FORMAT.md 규칙** — '문제집용 절' 표의 `## 힌트` 행을 다음으로 바꾼다.

```markdown
| `## 힌트` | 본문 끝 (`## 풀이`보다 앞) | 힌트 하나 = `### <이름표>` 소절, 문제당 2개까지. 이름표는 문제지 Hint 띠에 그대로 보이므로 24자 이내(수식은 보이는 글자로 셈). 소절 안에 `> 띠: $<LaTeX>$` 줄(소절당 하나, 들여 쓰지 않음)을 두면 띠에 이름표 대신 그 식이 보인다(예외로만 씀). 나머지 줄은 답안지 Hint 쪽 본문이다 |
```

예시 블록의 `## 힌트` 부분 네 줄(`## 힌트`부터 `- 바이폴라 캐스코드의 출력 저항`까지)을 다음으로 바꾼다.

```markdown
## 힌트
### $Q_1$ 위에서 보면 퇴화 CE
- $Q_2$와 이상적인 $I_1$은 $Q_1$ 이미터에 달린 저항 $r_{O2} \parallel r_{\pi 1}$ 하나로 볼 수 있다
```

`- 쓸 수 있는 문법: …` bullet 바로 앞에 다음 bullet을 추가한다.

```markdown
- 힌트는 공식이 아니라 핵심 아이디어다. 공식은 학생이 이미 안다고 본다.
  - 넣을 때: 공식 대입만으로는 바로 풀리지 않을 때. 회로를 다른 모양으로 다시 보기(반회로, 가운데 노드에서 본 저항, 퇴화 저항, 알려진 구조), 어느 노드에서 무엇을 들여다볼지, 무시해도 되는 소자, 대칭이나 가상 접지.
  - 넣지 않을 때: 값 대입으로 끝나는 문제, 예제를 바로 되풀이하는 문제, 정의를 묻는 문제. 억지로 만들지 않는다. 예제에서 값을 이어받는 것은 `## 조건`에 이미 있으므로 힌트가 아니다.
  - 이름표는 24자 이내의 명령형 또는 명사구(예: `꼬리 노드는 AC 접지`). 본문은 `- ` 목록 1~3줄로 그렇게 볼 수 있는 이유를 쓰고, 수치 답·최종 식·중간 계산 값은 쓰지 않는다.
  - `> 띠:` 식은 식 자체가 아이디어일 때만 쓴다. 식이 있으면 띠가 24mm에서 50mm로 넓어진다.
```

- [ ] **Step 6: 커밋**

```bash
git add 교과서/마이크로전자회로/_tools/check_md.py 교과서/마이크로전자회로/_tools/tests/test_check_md.py 교과서/마이크로전자회로/FORMAT.md
git commit -m "feat(check_md): tighten hint section checks and document hint rules

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: `source_pages.py`에 판정 원장 옵션 `--ledger`

**Files:**
- Modify: `workbook/source_pages.py` (docstring, `import` 줄, `pending`, `parse_args`, `main`)
- Modify: `workbook/README.md` ('원문 옮기기 도구' 절)
- Test: `workbook/tests/test_source_pages.py` (`write_md` 도우미, 새 클래스 `TestLedger`)

**Interfaces:**
- Consumes: `check_md.split_sections`, `check_md.split_subsections`
- Produces:
  - `source_pages.read_ledger(path) -> dict[str, int]`: id → 힌트 개수, 없음은 0. 파일이 없으면 `{}`. 형식 오류와 중복 id는 `SourceError`.
  - `source_pages.pending(folder, ledger=None) -> list[Path]`: ledger가 None이면 지금처럼 원문 기준, dict면 원장에 없는 id.
  - `source_pages.hint_count(body: str) -> int`
  - `source_pages.ledger_mismatches(folder, ledger) -> list[str]`: `"MISMATCH <id>: 원장 N개, md M개"`
  - CLI: `next <폴더> [--size N] [--ledger 파일]`, `missing <폴더> [--ledger 파일]`. `--ledger`를 주면 `missing`은 남은 md와 MISMATCH 줄을 stdout에, `판정 없음: N개`를 stderr에 낸다. 둘 중 하나라도 있으면 종료 코드 1이다.

- [ ] **Step 1: 실패하는 테스트 작성**

`write_md` 도우미에 `tail` 인자를 더한다(기존 호출은 그대로 동작한다).

```python
def write_md(path, pid, kind, page, original=False, extra="", tail=""):
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "# 장말문제 9.1 — 제목\n\n" + ("## 원문\nText.\n\n" if original else "") + "## 조건\n- a\n" + tail
    path.write_text(f"---\nid: {pid}\nkind: {kind}\npdf_page: {page}\n{extra}---\n{body}", encoding="utf-8")
    return path
```

import 줄을 다음처럼 바꾼다.

```python
from source_pages import SourceError, main, pending, read_ledger, render, source_pdf  # noqa: E402
```

`class TestRender(Base):` 바로 앞에 추가한다.

```python
class TestLedger(Base):
    def ledger(self, text):
        path = self.root / "hints-ledger.md"
        path.write_text(text, encoding="utf-8")
        return path

    def test_pending_skips_judged_ids(self):
        write_md(self.ch / "예제/E9.01.md", "E9.01", "예제", 1, original=True)
        write_md(self.ch / "예제/E9.02.md", "E9.02", "예제", 2, original=True)
        ledger = read_ledger(self.ledger("# 힌트 판정 원장 — ch09\n\n- E9.01 | 없음 | 대입만\n"))
        self.assertEqual(ledger, {"E9.01": 0})
        self.assertEqual([p.name for p in pending(self.ch, ledger)], ["E9.02.md"])

    def test_missing_ledger_file_is_empty(self):
        self.assertEqual(read_ledger(self.root / "none.md"), {})

    def test_bad_line_raises(self):
        with self.assertRaises(SourceError):
            read_ledger(self.ledger("- E9.01 | 아마 | 모름\n"))

    def test_duplicate_id_raises(self):
        with self.assertRaises(SourceError):
            read_ledger(self.ledger("- E9.01 | 없음 | a\n- E9.01 | 힌트 1 | b\n"))

    def test_main_missing_reports_mismatch(self):
        write_md(self.ch / "예제/E9.01.md", "E9.01", "예제", 1, original=True,
                 tail="\n## 힌트\n### 반회로로 본다\n- 대칭\n")
        write_md(self.ch / "예제/E9.02.md", "E9.02", "예제", 2, original=True)
        path = self.ledger("- E9.01 | 힌트 1 | 대칭\n- E9.02 | 힌트 1 | 절을 빠뜨림\n")
        code, out, err = run(["missing", str(self.ch), "--ledger", str(path)])
        self.assertEqual(code, 1)
        self.assertIn("MISMATCH E9.02: 원장 1개, md 0개", out)
        self.assertNotIn("E9.01", out)
        self.assertIn("판정 없음: 0개", err)

    def test_main_next_with_ledger(self):
        for i in range(1, 4):
            write_md(self.ch / f"장말문제/P9.0{i}.md", f"P9.0{i}", "장말문제", i, original=True)
        path = self.ledger("- P9.01 | 없음 | 대입만\n")
        code, out, _ = run(["next", str(self.ch), "--ledger", str(path), "--size", "5"])
        self.assertEqual(code, 0)
        self.assertEqual([Path(line).name for line in out.splitlines()], ["P9.02.md", "P9.03.md"])
```

- [ ] **Step 2: 실패 확인**

Run: `python3 -m unittest workbook/tests/test_source_pages.py 2>&1 | tail -3`
Expected: `ImportError: cannot import name 'read_ledger'`

- [ ] **Step 3: 구현**

import 줄을 바꾼다.

```python
from check_md import split_frontmatter, split_sections, split_subsections
```

`TEXT_MIN = …` 줄 뒤에 추가한다.

```python
LEDGER_LINE_RE = re.compile(r"^- (\S+) \| (없음|힌트 ([12])) \| \S.*$")
```

`pending`을 다음으로 바꾸고, 바로 뒤에 새 함수 세 개를 둔다.

```python
def pending(folder, ledger=None):
    """할 일이 남은 md를 (source, pdf_page, id) 순으로. 같은 쪽의 예제·연습문제가 이어진다.
    ledger가 None이면 원문이 없는 md, 판정 원장(dict)이면 원장에 판정이 없는 md."""
    keyed = []
    for md in problem_mds(folder):
        meta, body = read_md(md)
        if ledger is None:
            if any(title == "원문" for title, _ in split_sections(body)):
                continue
        elif str(meta["id"]) in ledger:
            continue
        keyed.append(((str(meta.get("source", "")), int(meta["pdf_page"]), str(meta["id"])), md))
    return [md for _, md in sorted(keyed)]


def read_ledger(path):
    """힌트 판정 원장 → {id: 힌트 개수(없음 = 0)}. 파일이 없으면 빈 원장. '- '로 시작하지 않는 줄은 무시한다."""
    path = Path(path)
    if not path.exists():
        return {}
    ledger = {}
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.startswith("- "):
            continue
        m = LEDGER_LINE_RE.match(line.rstrip())
        if not m:
            raise SourceError(f"{path}:{n}: 원장 줄 형식은 '- <id> | 힌트 <1|2> | <이유>' 또는 '- <id> | 없음 | <이유>'")
        pid = m.group(1)
        if pid in ledger:
            raise SourceError(f"{path}:{n}: {pid} 판정이 두 번 있음")
        ledger[pid] = int(m.group(3) or 0)
    return ledger


def hint_count(body):
    """## 힌트의 ### 소절 수. 절이 없으면 0."""
    text = next((c for t, c in split_sections(body) if t == "힌트"), "")
    return sum(1 for label, _ in split_subsections(text) if label)


def ledger_mismatches(folder, ledger):
    """원장의 힌트 개수와 md의 ### 소절 수가 다른 문제."""
    out = []
    for md in problem_mds(folder):
        meta, body = read_md(md)
        pid = str(meta["id"])
        if pid in ledger and hint_count(body) != ledger[pid]:
            out.append(f"MISMATCH {pid}: 원장 {ledger[pid]}개, md {hint_count(body)}개")
    return out
```

`parse_args`에서 `nxt`와 `mis`에 옵션을 더한다.

```python
    nxt.add_argument("--ledger", type=Path, help="힌트 판정 원장. 주면 원장에 없는 md를 낸다")
```
```python
    mis.add_argument("--ledger", type=Path, help="힌트 판정 원장. 주면 판정 없는 md와 MISMATCH를 낸다")
```

`main`의 `try` 안 `if args.cmd == "next": … elif args.cmd == "missing": …` 부분을 다음으로 바꾼다. `else:`(render)는 그대로 둔다.

```python
        if args.cmd in ("next", "missing"):
            ledger = read_ledger(args.ledger) if args.ledger else None
            left = pending(args.folder, ledger)
        if args.cmd == "next":
            for md in left[:args.size]:
                print(md)
        elif args.cmd == "missing":
            bad = ledger_mismatches(args.folder, ledger) if ledger is not None else []
            for line in [str(md) for md in left] + bad:
                print(line)
            what = "판정 없음" if ledger is not None else "원문 없음"
            print(f"{what}: {len(left)}개", file=sys.stderr)
            return 1 if left or bad else 0
```

모듈 docstring의 사용법 두 줄을 바꾼다.

```
  python3 workbook/source_pages.py next <폴더> [--size 10] [--ledger 원장]   원문 없는(원장을 주면 판정 없는) md를 (원본, pdf_page, id) 순으로 N개
  python3 workbook/source_pages.py missing <폴더> [--ledger 원장]            남은 md 목록(+ 원장과 힌트 수가 다른 MISMATCH). 하나라도 있으면 종료 코드 1
```

- [ ] **Step 4: 통과 확인**

Run: `python3 -m unittest discover -s workbook/tests 2>&1 | tail -1` → `OK` (86개)
Run: `python3 workbook/source_pages.py next 교과서/마이크로전자회로/ch09 --ledger docs/superpowers/reports/ch09/hints-ledger.md --size 3` → ch09 md 경로 3개 (원장이 아직 없으므로 처음 3개)
Run: `python3 workbook/source_pages.py missing 교과서/마이크로전자회로/ch09; echo $?` → `원문 없음: 0개`, `0` (옵션이 없을 때는 동작이 그대로)

- [ ] **Step 5: README** — `workbook/README.md` '원문 옮기기 도구' 절의 코드 블록 끝에 두 줄을 더하고, 블록 뒤에 설명 한 줄을 둔다.

```bash
python3 workbook/source_pages.py next 교과서/마이크로전자회로/ch10 --ledger docs/superpowers/reports/ch10/hints-ledger.md --size 15   # 힌트 판정 안 된 md
python3 workbook/source_pages.py missing 교과서/마이크로전자회로/ch10 --ledger docs/superpowers/reports/ch10/hints-ledger.md          # 남은 것 + MISMATCH
```
```markdown
힌트 판정 원장의 줄 형식은 `- <id> | 힌트 <1|2> | <이유>` 또는 `- <id> | 없음 | <이유>`다. 힌트는 없어도 되는 절이라, 검토가 끝났는지는 md가 아니라 원장으로 판단한다.
```

- [ ] **Step 6: 커밋**

```bash
git add workbook/source_pages.py workbook/tests/test_source_pages.py workbook/README.md
git commit -m "feat(workbook): track hint judgments with a ledger in source_pages

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: 파일럿 — ch09 15문제, main 병합

**Files:**
- Modify (힌트를 넣을 때만): `교과서/마이크로전자회로/ch09/**/*.md` 가운데 `next --ledger`가 처음 낸 15개
- Create: `docs/superpowers/reports/ch09/hints-ledger.md`, `docs/superpowers/reports/ch09/hint-A.md`

**Interfaces:**
- Consumes: Task 1의 `check_hint`(check_md에서 호출됨), Task 2의 `next/missing --ledger`
- Produces: main에 병합된 도구와 파일럿 결과. Task 4–6 워크트리는 이 main에서 만든다.

- [ ] **Step 1: 대상 얻기**

```bash
cd "$WT09"; python3 workbook/source_pages.py next 교과서/마이크로전자회로/ch09 --ledger docs/superpowers/reports/ch09/hints-ledger.md --size 15
```
- [ ] **Step 2: 작성자 파견** — 부록 W를 채워 foreground로 띄운다. 값은 WT=`WT09`, L=`ch09`, 배치=`A`, 대상=Step 1의 15개, 반영할 보고서=없음이다.
- [ ] **Step 3: 리뷰어 파견** — 부록 R을 채운다. 파일럿에서는 **foreground**로 띄우고 기다린다.
- [ ] **Step 4: 반영** — 부록 W를 "반영만" 모드로 띄운다(대상 없음, 반영할 보고서=`hint-A.md`).
- [ ] **Step 5: 검사와 빌드**

```bash
cd "$WT09"
python3 교과서/마이크로전자회로/_tools/check_md.py 교과서/마이크로전자회로/ch09 | tail -1
python3 workbook/source_pages.py missing 교과서/마이크로전자회로/ch09 --ledger docs/superpowers/reports/ch09/hints-ledger.md > $SCRATCH/left.txt; grep MISMATCH $SCRATCH/left.txt   # 비어야 함
IDS=$(grep "| 힌트" docs/superpowers/reports/ch09/hints-ledger.md | sed -E 's/^- ([^ ]+) .*/\1/' | paste -sd, -)
python3 workbook/build_workbook.py --ids "$IDS" --name 힌트-파일럿 --pdf-dir workbook/build/pdf 2>&1 | tail -5
```
Expected: 검사 오류가 0이고 MISMATCH가 없다. OVERFLOW 줄이 있으면 id를 기록한다. 실패로 보지 않는다. 힌트 id가 하나도 없으면 빌드를 건너뛰고, Step 7에서 판정 기준이 너무 엄격한지 사용자에게 묻는다.

- [ ] **Step 6: 눈으로 확인** — 문제지와 답안지를 PNG로 그린다. `--name`이 NFC로 바뀌지 않는 문제가 있으므로, 이름이 다르면 `ls workbook/build/pdf`로 실제 이름을 찾는다.

```bash
python3 - <<'EOF'
import fitz, os, glob
out = os.environ.get("SCRATCH", "/tmp") + "/hint-pilot"
os.makedirs(out, exist_ok=True)
for pdf in glob.glob("workbook/build/pdf/*파일럿-*.pdf"):
    with fitz.open(pdf) as d:
        tag = "q" if pdf.endswith("문제.pdf") else "a"
        for i in range(d.page_count):
            d[i].get_pixmap(dpi=80).save(f"{out}/{tag}{i+1:02d}.png")
print(out)
EOF
```
PNG를 Read로 열어 네 가지를 확인한다.
1. 문제지 띠에 이름표가 3줄 안에 들어오고 잘리지 않는다.
2. 이름표 속 수식이 KaTeX로 그려졌다.
3. 답안지 Hint 쪽에 본문 목록이 나온다.
4. 힌트가 없는 문제에는 띠가 없다.

- [ ] **Step 7: 사용자 확인** — 다음을 보여 준다.
  - 원장 전체(15줄)
  - 띠가 보이는 문제지 PNG 한 장과 답안지 Hint 쪽 PNG 한 장
  - 리뷰 A의 지적 수와 주요 유형
  - OVERFLOW 목록

  그리고 묻는다: "힌트의 결(핵심 아이디어인지, 양과 길이)이 원하시는 것과 맞나요? 맞으면 `claude/hints-ch09`를 main에 ff-merge하고 ch10·ch11·기출 워크트리를 열어 병렬로 진행합니다."
  사용자가 기준을 바꾸면 먼저 스펙, Global Constraints, FORMAT.md, 부록 W·R을 고친다. 그다음 파일럿 15개를 새 기준으로 다시 작성한다. 원장 줄도 고치고 별도 커밋으로 남긴다.
- [ ] **Step 8: 병합** (사용자가 승인한 뒤)

```bash
git -C /Users/hyunjun_macbook_pro/Documents/Univ/전자회로2 merge --ff-only claude/hints-ch09
```

---

### Task 4: ch09 나머지 95문제

**Files:**
- Modify: `교과서/마이크로전자회로/ch09/{예제,연습문제,장말문제}/*.md` 가운데 힌트를 넣는 것
- Modify: `docs/superpowers/reports/ch09/hints-ledger.md`
- Create: `docs/superpowers/reports/ch09/hint-B.md`, `hint-C.md`, …

**Interfaces:**
- Consumes: Task 2의 `next/missing --ledger`, main에 병합된 Task 3
- Produces: `claude/hints-ch09`에 ch09 110개의 판정. Task 7이 이 브랜치로 모은다.

- [ ] **Step 1:** `WT09`에서 절차 B를 돌린다. F=`교과서/마이크로전자회로/ch09`, L=`ch09`, 첫 배치 글자는 `B`다. 약 7배치다.
- [ ] **Step 2:** 완료 검사 C(ch09)를 통과시키고, 힌트 비율과 OVERFLOW 목록을 기록한다.

### Task 5: ch10 151문제

**Files:**
- Modify: `교과서/마이크로전자회로/ch10/{예제,연습문제,장말문제}/*.md` 가운데 힌트를 넣는 것
- Create: `docs/superpowers/reports/ch10/hints-ledger.md`, `hint-A.md` …

**Interfaces:**
- Consumes: main(Task 3 병합 뒤)의 `source_pages.py --ledger`, `check_md.check_hint`
- Produces: `claude/hints-ch10`

- [ ] **Step 1: 워크트리**

```bash
cd /Users/hyunjun_macbook_pro/Documents/Univ/전자회로2
git worktree add .claude/worktrees/hints-ch10 -b claude/hints-ch10 main
```
- [ ] **Step 2:** `WT10`에서 절차 B를 돌린다. F=`교과서/마이크로전자회로/ch10`, L=`ch10`, 첫 배치 글자는 `A`다. 약 11배치다.
- [ ] **Step 3:** 완료 검사 C(ch10)를 통과시키고, 힌트 비율과 OVERFLOW 목록을 기록한다.

### Task 6: ch11 116문제와 기출 22문제

두 워크트리를 병렬로 돌린다. 오케스트레이터는 Task 5와 함께 세 워크트리의 절차 B를 번갈아 진행한다.

**Files:**
- Modify: `교과서/마이크로전자회로/ch11/**/*.md`, `from_the_past/md/{2021-1_중간,2021-1_기말,2023-1_중간,2023-1_기말}/Q*.md` 가운데 힌트를 넣는 것
- Create: `docs/superpowers/reports/ch11/hints-ledger.md`, `hint-A.md` …, `docs/superpowers/reports/exams/hints-ledger.md`, `hint-A.md` … `hint-D.md`
  - ch11 보고서 이름: 기존 `review-*.md`, `original-*.md`와 겹치지 않는다.

**Interfaces:**
- Consumes: main(Task 3 병합 뒤)의 `source_pages.py --ledger`, `check_md.check_hint`(`check_exam`이 `check_body`로 호출)
- Produces: `claude/hints-ch11`, `claude/hints-exams`

- [ ] **Step 1: 워크트리**

```bash
cd /Users/hyunjun_macbook_pro/Documents/Univ/전자회로2
git worktree add .claude/worktrees/hints-ch11 -b claude/hints-ch11 main
git worktree add .claude/worktrees/hints-exams -b claude/hints-exams main
```
- [ ] **Step 2:** `WT11`에서 절차 B를 돌린다. F=`교과서/마이크로전자회로/ch11`, L=`ch11`, 첫 배치 글자는 `A`다. 약 8배치다.
- [ ] **Step 3:** `WTEX`에서 시험 폴더마다 배치 하나로 절차 B를 돌린다. L=`exams`이고, 원장은 `docs/superpowers/reports/exams/hints-ledger.md` 하나를 함께 쓴다.
  - 배치 글자: A=`from_the_past/md/2021-1_중간`, B=`2021-1_기말`, C=`2023-1_중간`, D=`2023-1_기말`
  - 부록 W의 '기출' 항목을 켠다.
- [ ] **Step 4:** 완료 검사 C(ch11, 기출판)를 통과시킨다.

```bash
cd "$WTEX"
for e in 2021-1_중간 2021-1_기말 2023-1_중간 2023-1_기말; do
  python3 workbook/source_pages.py missing from_the_past/md/$e --ledger docs/superpowers/reports/exams/hints-ledger.md > /dev/null || echo "남음 $e"
  python3 from_the_past/md/_tools/check_exam.py from_the_past/md/$e | tail -1
  python3 workbook/build_workbook.py $e --pdf-dir workbook/build/pdf 2>&1 | grep OVERFLOW
done
```

---

### Task 7: 통합 — 모으기, 쪽 넘침 처리, PDF 다시 만들기

**Files:**
- Modify (넘침이 있을 때만): `workbook/templates/problem.html:286-289`
- Test (넘침이 있을 때만): `workbook/tests/test_templates.py`
- Modify: `workbook/pdf/*.pdf` (14개)

**Interfaces:**
- Consumes: 브랜치 `claude/hints-{ch09,ch10,ch11,exams}`, 절차 B에서 모은 OVERFLOW 목록과 힌트 비율

- [ ] **Step 1: ch09 브랜치로 모으기** — 다른 파일만 건드렸으므로 충돌은 예상하지 않는다. 충돌이 나면 멈추고 보고한다.

```bash
MAIN=/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2
for x in ch10 ch11 exams; do
  git -C "$MAIN/.claude/worktrees/hints-$x" rebase claude/hints-ch09 &&
  git -C "$MAIN/.claude/worktrees/hints-ch09" merge --ff-only claude/hints-$x || break
done
```

- [ ] **Step 2: 전체 검사** (`WT09`)

```bash
cd "$WT09"
for c in ch09 ch10 ch11; do
  python3 workbook/source_pages.py missing 교과서/마이크로전자회로/$c --ledger docs/superpowers/reports/$c/hints-ledger.md >/dev/null || echo "남음 $c"
  python3 교과서/마이크로전자회로/_tools/check_md.py 교과서/마이크로전자회로/$c | tail -1
done
for e in 2021-1_중간 2021-1_기말 2023-1_중간 2023-1_기말; do
  python3 workbook/source_pages.py missing from_the_past/md/$e --ledger docs/superpowers/reports/exams/hints-ledger.md >/dev/null || echo "남음 $e"
  python3 from_the_past/md/_tools/check_exam.py from_the_past/md/$e | tail -1
done
python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests 2>&1 | tail -1   # OK (105)
python3 -m unittest discover -s from_the_past/md/_tools/tests 2>&1 | tail -1          # OK (65)
python3 -m unittest discover -s workbook/tests 2>&1 | tail -1                         # OK (86)
```
Expected: "남음"이 없고 검사 오류가 0이다.

- [ ] **Step 3: 전체 빌드**

```bash
python3 workbook/build_workbook.py --all 2> $SCRATCH/build-all.txt; echo "exit $?"; grep -E "OVERFLOW|ERROR" $SCRATCH/build-all.txt
```
`exit 0`이면 Step 8로 간다. OVERFLOW만 있으면 Step 4–7을 한다. ERROR가 있으면 멈추고 보고한다.

- [ ] **Step 4: 실패하는 테스트** (OVERFLOW가 있을 때만) — `workbook/tests/test_templates.py`의 `test_original_block_in_both_templates` 뒤에 추가한다.

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
Run: `python3 -m unittest discover -s workbook/tests 2>&1 | tail -1` → `OK` (87개)

- [ ] **Step 6: 다시 빌드** — Step 3 명령을 다시 돌린다. 아직 OVERFLOW가 있으면 **멈춘다.** 넘친 쪽 id와 PNG(Task 3 Step 6 방식)를 사용자에게 보여 주고 대응을 묻는다. 규칙 밖의 일이다. 예를 들어 그 문제의 힌트 본문을 줄이거나 `> 띠:` 식을 빼는 방법이 있다.
- [ ] **Step 7: 템플릿 커밋**

```bash
git add workbook/templates/problem.html workbook/tests/test_templates.py
git commit -m "fix(workbook): add a smaller font fit step for pages with hint strips

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 8: PDF 확인과 커밋** — 장마다 띠가 있는 문제지 쪽을 몇 개 PNG로 그려 확인한다(Task 3 Step 6 방식). 그다음 커밋한다.

```bash
git status --short workbook/pdf     # M 14개
git add workbook/pdf/*.pdf
git commit -m "build: regenerate pdfs with hints

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
du -sh /Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/.git
```

- [ ] **Step 9: 사용자 확인 후 main 병합과 정리** — 다음을 보고한다.
  - 라벨별 힌트 비율(힌트 문제 수 / 전체)
  - 리뷰 배치 수와 지적 합계
  - 템플릿 변경 여부
  - `.git` 크기

  그리고 묻는다: "`claude/hints-ch09`를 main에 ff-merge하고, 워크트리 4개와 브랜치를 지울까요?" 승인을 받은 뒤 실행한다.

```bash
cd /Users/hyunjun_macbook_pro/Documents/Univ/전자회로2
git merge --ff-only claude/hints-ch09
for x in ch09 ch10 ch11 exams; do git worktree remove .claude/worktrees/hints-$x && git branch -d claude/hints-$x; done
git worktree list
```

---

## 부록 W — 작성자 지시 (오케스트레이터가 `<<…>>`를 채워 Agent prompt로 보냄)

```
# 힌트 작성 — <<LABEL>> 배치 <<BATCH>>

당신은 작성 에이전트다. 작업 폴더는 <<WT>>이고 모든 명령은 여기서 실행한다(cd <<WT>>).
먼저 교과서/마이크로전자회로/FORMAT.md의 '문제집용 절'을 읽는다. 특히 "힌트는 공식이 아니라 핵심 아이디어다" 항목을 읽는다. 기출이면 from_the_past/md/FORMAT-EXAM.md도 읽는다.

목표: 학생이 막힐 만한 문제에만, "회로를 이렇게 보면 쉽게 풀린다"는 핵심 아이디어 하나를 준다. 공식은 학생이 이미 안다. 힌트가 필요 없는 문제에는 넣지 않는다. 전체 목표는 문제의 약 25~40%지만 배치마다 맞추는 할당량은 아니다.

## 0. 리뷰 반영 (반영할 보고서: <<REPORTS>>, "없음"이면 건너뜀)
- 보고서마다 지적을 하나씩 직접 판단한다. 동의하면 md와 원장을 고치고, 동의하지 않으면 고치지 않고 이유를 최종 메시지에 적는다.
- "넣어야 함" 지적을 받아들이면 원장 줄을 "힌트 N"으로 바꾼다. "빼야 함"이면 ## 힌트 절을 지우고 원장 줄을 "없음"으로 바꾼다.
- 검사(3)를 돌린다.
- git add <고친 md 경로들> <<LEDGER>> <보고서 경로들>
- git commit -m "docs: apply review fixes to <<LABEL>> hint batch <보고서 글자들>" (끝에 빈 줄 + Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>)
- 고친 것이 없어도 보고서는 커밋한다.

## 1. 대상 (<<TARGETS>>, "없음"이면 여기서 끝)
md마다 다음을 한다.
- md 전체를 읽는다: 원문, 조건, 구할 것, 회로 넷리스트와 단자·배치 설명, 상속·참조.
- md의 이미지 줄(![Fig …](../figures/…png))이 가리키는 그림을 Read로 열어 본다(경로는 md 기준 상대 경로).
- 예제면 ## 답 (검증용)을 읽는다. 교과서 풀이가 필요하면 python3 workbook/source_pages.py render <md> --out <<PAGES>> 로 원본 쪽을 그려 본다.
- 문제를 실제로 푼다. 계산 메모는 <<PAGES>>/notes-<id>.md에 적고, md에는 넣지 않는다.
- 풀면서 "학생이 막히는 지점"이 있었는지 판단한다.
  - 공식을 대입하면 끝나면 → 없음
  - 회로를 다르게 보는 순간이 있었다면 → 힌트 (예: 반회로, 가운데 노드에서 본 저항, 퇴화 저항, 알려진 구조로 알아보기, 어느 노드를 들여다볼지, 무시할 소자, 대칭·가상 접지)
<<EXAM_NOTES>>

## 2. 쓰기
- 힌트를 넣는 md: 파일 맨 끝에 빈 줄 하나를 두고 다음을 붙인다.
  ## 힌트
  ### <이름표: 24자 이내, 명령형 또는 명사구, 예 "꼬리 노드는 AC 접지">
  - <그렇게 볼 수 있는 이유, 1~3줄>
- 힌트는 문제당 1개가 기본, 최대 2개다. 2개면 풀이 순서대로 둔다.
- 이름표만 보고도 아이디어가 전달되어야 한다(문제지에는 이름표만 보인다).
- 금지:
  - 수치 답, 최종 식, 중간 계산 값
  - "식 (9.5)를 쓴다" 같은 공식 안내
  - 예제 값 이어받기만 적은 힌트
- "> 띠: $…$" 식 줄은 식 자체가 아이디어일 때만 예외로 쓴다. 쓸 때는 원장 이유 칸에 까닭을 적는다.
- md의 다른 곳은 고치지 않는다. 조건에서 오류를 발견하면 고치지 말고 최종 메시지에 적는다.
- 원장 <<LEDGER>>: 파일이 없으면 첫 줄을 "# 힌트 판정 원장 — <<LABEL>>"로, 그 뒤에 빈 줄을 두고 만든다. 대상마다 한 줄씩, 대상 순서대로 끝에 붙인다.
  - "- <id> | 힌트 <1|2> | <아이디어가 필요한 이유, 한 문장>"
  - "- <id> | 없음 | <필요 없는 이유, 한 문장>"

## 3. 검사
<<CHECK_CMD>>
python3 workbook/source_pages.py missing <<FOLDER>> --ledger <<LEDGER>> | grep MISMATCH    # 출력이 비어야 함
오류가 0이 될 때까지 고친다. 힌트를 넣은 문제가 있으면 빌드해서 넘침을 본다:
python3 workbook/build_workbook.py --ids <힌트 넣은 id들, 쉼표로> --name 힌트-<<LABEL>>-<<BATCH>> --pdf-dir workbook/build/pdf 2>&1 | grep -E "OVERFLOW|ERROR"
ERROR는 고친다. OVERFLOW는 고치지 말고 최종 메시지에 적는다.

## 4. 커밋
git add <힌트를 넣은 md 경로들> <<LEDGER>>
git commit -m "docs: add <<LABEL>> hints batch <<BATCH>> (<첫 id>–<끝 id>)" (끝에 빈 줄 + Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>)
git add에는 경로를 명시한다(-A나 . 금지). push하지 않는다.

## 최종 메시지
- 커밋 해시(반영 커밋, 배치 커밋)
- 힌트: "<id> — <이름표>" 한 줄씩, 그리고 "힌트 n / 대상 m"
- 판정이 애매했던 곳: "<id> — <넣음|안 넣음> — <망설인 이유>" 한 줄씩 (없으면 "없음")
- OVERFLOW 줄, 조건에서 발견한 오류, 반영하지 않은 리뷰 지적과 이유
```

채울 값:
- `<<LABEL>>`: `ch09`, `ch10`, `ch11`, `exams`
- `<<FOLDER>>`: 절차 B의 `F`
- `<<LEDGER>>`: `docs/superpowers/reports/<<LABEL>>/hints-ledger.md`
- `<<PAGES>>`: `$SCRATCH/hints/<<LABEL>>/<<BATCH>>` (절대 경로로 채움)
- `<<CHECK_CMD>>`
  - 교과서: `python3 교과서/마이크로전자회로/_tools/check_md.py 교과서/마이크로전자회로/chNN`
  - 기출: `python3 from_the_past/md/_tools/check_exam.py <시험 폴더>`
- `<<EXAM_NOTES>>`: 교과서면 빈 줄이다. 기출이면 아래 목록을 넣는다.
  - "기출 소문항 (1)(2)…가 여럿이면, 힌트는 가장 막히는 소문항 하나를 겨냥하고 이름표 앞에 '(2) '처럼 소문항 번호를 붙인다. 번호도 24자에 들어간다."
  - "기출 풀이는 없다. 원본 스캔의 손글씨는 참고하지 않는다."

## 부록 R — 리뷰어 지시

```
# 힌트 리뷰 — <<LABEL>> 배치 <<BATCH>>

당신은 리뷰 에이전트다. 작업 폴더는 <<WT>>다. 먼저 교과서/마이크로전자회로/FORMAT.md '문제집용 절'의 힌트 규칙을 읽는다.

- 대상: <<TARGETS>> (커밋 <<COMMIT>>)
- 작성자가 넣은 힌트: <<HINTS>>
- 작성자가 판정이 애매하다고 한 곳 (특히 독립적으로 판단):
<<FLAGS>>

## 원칙
- 추적되는 파일을 고치지 않고 git 상태도 바꾸지 않는다. 만드는 파일은 보고서 <<REPORT>> 하나뿐이다(폴더가 없으면 만든다).
- 보고서는 <<REPORT>>.part에 쓰고, 다 마친 뒤 mv <<REPORT>>.part <<REPORT>> 한다.
- 먼저 독립적으로 판단한다. 대상마다 git show <<COMMIT>>^:<경로> 로 힌트가 없는 버전을 읽고, 그림을 보고, 직접 풀어서 "막히는 지점이 있는가, 있다면 핵심 아이디어는 무엇인가"를 먼저 정한다. 메모는 <<PAGES>>/review-<<BATCH>>/에 둔다. 그다음 git show <<COMMIT>> 으로 작성자의 힌트와 원장 줄을 대조한다.
- 힌트가 있는 문제마다 확인할 것:
  1. 필요한가 — 공식 대입만으로 풀리는 문제에 넣지 않았는가
  2. 핵심 아이디어인가 — 공식 안내("식 x.y를 쓴다")나 조건 되풀이가 아닌가
  3. 물리적으로 맞는가 — 그렇게 보면 정말 풀리는가, 근사 조건이 맞는가
  4. 답을 누설하지 않는가 — 수치, 최종 식, 중간 값
  5. 이름표만으로 아이디어가 전달되는가(문제지에는 이름표만 보임), 24자 이내인가
  6. 본문이 "왜 그렇게 볼 수 있는지"를 1~3줄로 설명하는가
  7. "> 띠:" 식을 썼다면 식 자체가 아이디어인가
- "없음" 판정마다 확인할 것: 학생이 막힐 만한 지점이 정말 없는가. 있다고 보면 제안할 이름표와 함께 "넣어야 함"으로 지적한다.
- 형식 검사를 한 번 돌린다: <<CHECK_CMD>>

## 보고서
# 힌트 리뷰 <<BATCH>> — 커밋 <<COMMIT>> (<<TARGETS 요약>>)

방법: <독립 풀이 여부, 본 그림, 형식 검사 결과>
배치 힌트 비율: <n / m>

## 작성자가 애매하다고 한 곳 — 독립 판단
- <id>: 동의 | 반대 (<이유>)

### <id> — OK | 수정 필요 | 넣어야 함 | 빼야 함
- [높음|중간|낮음] <체크 항목 번호>: <지적> → <제안: 새 이름표/본문 또는 삭제>

[높음]은 틀린 물리, 답 누설, 명백히 필요한 힌트가 빠진 경우다. [낮음]은 표현 제안이다. 확신이 없으면 "불확실"로 표시한다. 최종 메시지에는 수정 필요, 넣어야 함, 빼야 함의 개수를 요약한다.
```

채울 값:
- `<<HINTS>>`: 작성자 최종 메시지의 "<id> — <이름표>" 목록
- `<<REPORT>>`: `docs/superpowers/reports/<<LABEL>>/hint-<<BATCH>>.md`
- 나머지는 부록 W와 같다.
