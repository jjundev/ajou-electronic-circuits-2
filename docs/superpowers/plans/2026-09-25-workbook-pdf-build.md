# 문제 md → 문제지·답안지 PDF 빌드 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 교과서·기출 문제 md를 문제집 템플릿 두 개(문제지·답안지)의 JSON으로 바꿔 PDF를 만드는 생성기 `workbook/build_workbook.py`를 만든다. md에는 문제집용 선택 절 `## 원문`·`## 힌트`·`## 풀이`를 추가하고, 모든 장과 기출의 PDF를 만들어 커밋한다.

**Architecture:** md가 원본이고 JSON은 빌드 산출물이다. `check_md.py`에 절 나누기와 새 절 검사를 추가하고, `workbook/`의 모듈이 이를 가져다 쓴다. 모듈 흐름은 `mdsub`(md 하위 문법 → HTML) → `problem`(md 한 개 → 필드) → `assemble`(대상 → JSON) → `render`(템플릿 주입 → Playwright + 설치된 Chrome → PDF)이다. `build_workbook.py`는 CLI다.

**Tech Stack:** Python 3.14 (Homebrew), PyYAML, PyMuPDF(`fitz`, 테스트에서 PNG·PDF 확인용), Playwright for Python(`channel="chrome"`), 표준 라이브러리 `unittest`(pytest는 없음).

**Spec:** `docs/superpowers/specs/2026-09-25-workbook-pdf-build-design.md`

## Global Constraints

- `MAIN` = `/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2` (메인 checkout)
- `WT` = `/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2-pdf` (작업 worktree, 브랜치 `feat/workbook-pdf`). 이미 있는 워크트리 `전자회로2-workbook`(브랜치 `workbook-template`, 옛 v3 템플릿)은 건드리지 않는다.
- Task 0 이후 모든 명령은 `WT`에서 실행한다. 빌드에 쓰는 PNG, md, README는 모두 git이 추적하므로 심볼릭 링크는 필요 없다.
- **템플릿 원본:** `/Users/hyunjun_macbook_pro/Downloads/template_problem.html`, `/Users/hyunjun_macbook_pro/Downloads/template_answer.html` (최종본)
- **git add:** 추적하지 않는 파일(`STT/`, `강의노트/`, `교과서/**/*.pdf`)은 절대 add하지 않는다. `git add -A`, `git add .`는 쓰지 않고 항상 경로를 명시한다.
- **커밋 메시지:** 마지막 줄은 빈 줄 뒤 `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`이다.
- **push, main 병합, worktree 삭제**는 사용자에게 묻고 나서 한다.
- **코드 스타일:** 기존 `교과서/마이크로전자회로/_tools/*.py`를 따른다. 모듈 docstring에 용도·사용법을 적고, CLI는 `main(argv)`가 종료 코드(0 성공, 1 오류, 2 사용법)를 돌려주며, 메시지는 한국어다.
- **문제 md는 이번에 고치지 않는다** (ch09–ch11, 기출 22개). 내용 작업(원문 OCR, 힌트, 풀이)은 범위 밖이다.
- **테스트 명령:**
  - 교과서 도구: `python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests` — 지금 79개가 통과하고, Task 1 뒤에는 93개가 통과해야 한다.
  - 기출 도구: `python3 -m unittest discover -s from_the_past/md/_tools/tests` — 65개가 계속 통과해야 한다.
  - 생성기: `python3 -m unittest discover -s workbook/tests`
- **의존성:** 새로 설치하는 것은 playwright 하나뿐이다: `pip3 install --user --break-system-packages playwright`(PyYAML과 같은 설치 방식). `playwright install`(브라우저 다운로드)은 하지 않고 설치된 Google Chrome을 쓴다.
- **렌더링에는 인터넷이 필요하다** (템플릿이 CDN에서 Pretendard와 KaTeX를 받음).
- **산출물:** `workbook/pdf/*.pdf`는 커밋한다. `workbook/build/`는 gitignore한다.

## Review Focus

1. **수식 속 `<`, `&`, 그리고 데이터 속 `</script>`:** `$a < b$`는 PDF에 그대로 보여야 한다. JSON에 `</script>`나 `<!--`가 있어도 템플릿 스크립트가 끊기면 안 된다. → Task 3 `test_math_kept_and_escaped`, Task 6 `test_script_end_in_data_is_escaped`
2. **수식을 품은 작성자 표시, 수식 속 괄호:** `(크기 $|A_v| = 5$로 해석, 원문에 없음)`은 지워져야 한다. `$f(x)$`나 수식 안의 `(원문에 없음)`은 그대로 남아야 한다. `(E10.09, 원문 표기 …)`처럼 지우는 대상이 아닌 괄호도 남아야 한다. → Task 4 `test_strip_markers`
3. **문제 그림이 없는 문제의 `- 회로:` 줄:** 그림이 없으면 이 줄이 유일한 회로 정보다. 지우면 안 된다. → Task 4 `test_circuit_line_kept_without_figure`
4. **같은 그림 id가 여러 줄인 frontmatter:** 패널별로 나뉜 `role: problem` 두 줄은 이미지 하나로, `role: answer`는 빼야 한다(E9.07 `"9.13"` 같은 경우). → Task 4 `test_problem_role_only_and_dedup`
5. **NFD로 된 기출 폴더 이름:** macOS에서 받은 `2023-1_기말`이 NFD여도 대상이 찾아지고, 파일 이름과 제목은 NFC여야 한다. → Task 5 `test_nfd_exam_name`

---

## File Structure

```
workbook/
  README.md                 # 사용법, 결과 위치, 미리보기, 테스트 (Task 7)
  paths.py                  # 저장소 경로 + 기존 도구 import 경로 (Task 2)
  mdsub.py                  # md 하위 문법 → HTML (Task 3)
  problem.py                # 문제 md 한 개 → 제목·html·그림·힌트·풀이 (Task 4)
  assemble.py               # 대상(장·기출·id) → 문제 목록 → 문제집 JSON (Task 5)
  render.py                 # 템플릿 주입 + Playwright PDF (Task 6)
  build_workbook.py         # CLI (Task 7)
  templates/problem.html    # Downloads 최종본 + 자리표시자 + 기출 지원 (Task 2)
  templates/answer.html
  templates/sample-problem.json, sample-answer.json   # 템플릿에서 뺀 샘플 (Task 2)
  tests/test_templates.py, test_mdsub.py, test_problem.py, test_assemble.py, test_render.py, test_build.py
  pdf/                      # 커밋하는 PDF (Task 8)
  build/                    # 중간 산출물, .gitignore (Task 7)
교과서/마이크로전자회로/_tools/check_md.py        # split_sections, split_subsections, check_workbook_sections (Task 1)
교과서/마이크로전자회로/_tools/tests/test_check_md.py
교과서/마이크로전자회로/FORMAT.md                  # '문제집용 절' (Task 1)
from_the_past/md/FORMAT-EXAM.md                    # 한 줄 추가 (Task 1)
.gitignore                                          # workbook/build/ (Task 7)
```

---

### Task 0: worktree와 설계 문서

**Files:**
- Move: `docs/superpowers/specs/2026-09-25-workbook-pdf-build-design.md`, `docs/superpowers/plans/2026-09-25-workbook-pdf-build.md` (MAIN → WT)

- [ ] **Step 1: 메인 checkout 상태를 확인한다**

```bash
cd "/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2"
git status --short | grep -v '^??'
git status --short
```
Expected: 첫 명령은 출력이 없다. 둘째 명령에는 이 계획과 spec 두 파일만 `??`로 나온다(`docs/superpowers/`가 폴더 단위로 보일 수도 있다).

- [ ] **Step 2: worktree를 만들고 설계 문서를 옮긴다**

```bash
MAIN="/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2"
WT="/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2-pdf"
git -C "$MAIN" worktree add "$WT" -b feat/workbook-pdf main
mv "$MAIN/docs/superpowers/specs/2026-09-25-workbook-pdf-build-design.md" "$WT/docs/superpowers/specs/"
mv "$MAIN/docs/superpowers/plans/2026-09-25-workbook-pdf-build.md" "$WT/docs/superpowers/plans/"
ls "$WT/교과서/마이크로전자회로/ch09/figures/fig9-43.png" /Users/hyunjun_macbook_pro/Downloads/template_problem.html /Users/hyunjun_macbook_pro/Downloads/template_answer.html
```
Expected: `ls`가 세 파일을 모두 보여 준다.

- [ ] **Step 3: 커밋한다**

```bash
cd "/Users/hyunjun_macbook_pro/Documents/Univ/전자회로2-pdf"
git add docs/superpowers/specs/2026-09-25-workbook-pdf-build-design.md docs/superpowers/plans/2026-09-25-workbook-pdf-build.md
git commit -m "docs: add workbook pdf build design and plan

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 1: `check_md` — 절 나누기와 문제집용 절 검사

**Files:**
- Modify: `교과서/마이크로전자회로/_tools/check_md.py` (상수는 `NO_CIRCUIT_RE` 줄 아래에, 함수는 `def check_body` 바로 위에 추가하고, `check_body` 끝에 한 줄을 추가)
- Modify: `교과서/마이크로전자회로/_tools/tests/test_check_md.py` (끝에 클래스 추가)
- Modify: `교과서/마이크로전자회로/FORMAT.md` (`## 수식` 앞에 절 추가)
- Modify: `from_the_past/md/FORMAT-EXAM.md:44` 다음 줄

**Interfaces:**
- Produces (Task 4가 가져다 씀):
  - `split_sections(body: str) -> list[tuple[str, str]]` — `## ` 절 (제목, 내용). 첫 `## ` 앞은 버린다. 내용은 앞뒤 줄바꿈을 뗀다.
  - `split_subsections(text: str) -> list[tuple[str, str]]` — `### ` 소절. 첫 `### ` 앞에 글이 있으면 `("", 글)`이 맨 앞에 온다.
  - `check_workbook_sections(body: str) -> list[str]` — 오류 메시지 목록
  - `HINT_FORMULA_RE` — `^> 띠: \$([^$]+)\$$`, group(1)이 LaTeX
  - `check_body(...)`는 이제 `check_workbook_sections` 오류도 돌려준다.

- [ ] **Step 1: 실패하는 테스트를 쓴다**

`test_check_md.py`의 import 줄 아래에 다음을 추가한다.

```python
from check_md import check_workbook_sections, split_sections, split_subsections  # noqa: E402
```

파일 끝(`if __name__ == "__main__":`가 있으면 그 위)에 다음을 추가한다.

```python
WB_BASE = """# 연습문제 9.1 — 제목

## 조건
- a

## 구할 것
- b

## 회로 — 없음 (글 문제)
"""
WB_ORIGINAL = "## 원문\nRepeat Example 9.1.\n\n"
WB_HINTS = "\n## 힌트\n### 식 9.5\n> 띠: $R = r_O$\n- 캐스코드\n"
WB_SOLUTION = "\n## 풀이\n### 소신호\n- $g_m$\n### 답\n$R \\approx 1$\n"


def wb_body(original=True, hints=True, solution=True):
    head, rest = WB_BASE.split("\n\n", 1)
    body = head + "\n\n" + (WB_ORIGINAL if original else "") + rest
    return body + (WB_HINTS if hints else "") + (WB_SOLUTION if solution else "")


class TestWorkbookSections(unittest.TestCase):
    def assert_error(self, body, fragment):
        errors = check_workbook_sections(body)
        self.assertTrue(any(fragment in e for e in errors), errors)

    def test_valid_all_sections(self):
        self.assertEqual(check_workbook_sections(wb_body()), [])

    def test_valid_without_workbook_sections(self):
        self.assertEqual(check_workbook_sections(wb_body(False, False, False)), [])

    def test_original_must_be_first(self):
        self.assert_error(WB_BASE.replace("## 구할 것", WB_ORIGINAL + "## 구할 것"), "## 원문")

    def test_hint_after_solution_rejected(self):
        self.assert_error(WB_BASE + WB_SOLUTION + WB_HINTS, "## 힌트, ## 풀이")

    def test_section_after_hints_rejected(self):
        self.assert_error(WB_BASE + WB_HINTS + "\n## 상속·참조\n- x\n", "## 힌트, ## 풀이")

    def test_empty_section_rejected(self):
        self.assert_error(WB_BASE + "\n## 힌트\n", "비어 있음")

    def test_solution_must_end_with_answer(self):
        self.assert_error(WB_BASE + "\n## 풀이\n### 소신호\n- x\n", "### 답")

    def test_two_answers_rejected(self):
        self.assert_error(WB_BASE + "\n## 풀이\n### 답\n- x\n### 답\n- y\n", "### 답")

    def test_subsection_without_body(self):
        self.assert_error(WB_BASE + "\n## 힌트\n### 식 9.5\n### 식 9.7\n- y\n", "### 식 9.5: 내용 없음")

    def test_text_before_first_subsection(self):
        self.assert_error(WB_BASE + "\n## 풀이\n먼저\n### 답\n- x\n", "첫 ### 소절 앞")

    def test_bad_formula_line(self):
        self.assert_error(WB_BASE + "\n## 힌트\n### 식\n> 띠: R = r_O\n- x\n", "띠 식 줄")

    def test_duplicate_section(self):
        self.assert_error(WB_BASE + WB_HINTS + WB_HINTS, "두 번")

    def test_split_sections_and_subsections(self):
        self.assertEqual(split_sections(wb_body())[0], ("원문", "Repeat Example 9.1."))
        self.assertEqual(split_subsections("앞\n### a\nx\n### b\ny"), [("", "앞"), ("a", "x"), ("b", "y")])

    def test_check_body_reports_workbook_errors(self):
        errors = check_body(WB_BASE + "\n## 풀이\n### 소신호\n- x\n", Path("X9.01.md"), "연습문제")
        self.assertTrue(any("### 답" in e for e in errors), errors)
```

- [ ] **Step 2: 실패를 확인한다**

Run: `python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests 2>&1 | tail -3`
Expected: `ImportError: cannot import name 'check_workbook_sections'` 때문에 test_check_md 모듈이 실패한다.

- [ ] **Step 3: `check_md.py`를 구현한다**

`NO_CIRCUIT_RE = …` 줄 바로 아래에 다음을 추가한다.

```python
SECTION_RE = re.compile(r"^## (.+)$", re.MULTILINE)
SUBSECTION_RE = re.compile(r"^### (.+)$", re.MULTILINE)
HINT_FORMULA_RE = re.compile(r"^> 띠: \$([^$]+)\$$")
WORKBOOK_SECTIONS = ("원문", "힌트", "풀이")
WORKBOOK_TAIL = ("힌트", "풀이")
```

`def check_body(` 바로 위에 다음을 추가한다.

```python
def split_sections(body):
    """본문을 '## ' 절로 나눈다 → [(제목, 내용)]. 첫 '## ' 앞(H1)은 버린다. 문제집 생성기(workbook/)도 쓴다."""
    ms = list(SECTION_RE.finditer(body))
    ends = [m.start() for m in ms[1:]] + [len(body)]
    return [(m.group(1).strip(), body[m.end():end].strip("\n")) for m, end in zip(ms, ends)]


def split_subsections(text):
    """절 내용을 '### ' 소절로 나눈다 → [(제목, 내용)]. 첫 '### ' 앞에 글이 있으면 ("", 글)을 맨 앞에 둔다."""
    ms = list(SUBSECTION_RE.finditer(text))
    head = text[:ms[0].start()] if ms else text
    out = [("", head.strip("\n"))] if head.strip() else []
    ends = [m.start() for m in ms[1:]] + [len(text)]
    out += [(m.group(1).strip(), text[m.end():end].strip("\n")) for m, end in zip(ms, ends)]
    return out


def check_workbook_sections(body):
    """문제집용 선택 절(## 원문, ## 힌트, ## 풀이)의 위치와 모양. 규칙은 FORMAT.md '문제집용 절'."""
    errors = []
    sections = split_sections(body)
    titles = [t for t, _ in sections]
    for name in WORKBOOK_SECTIONS:
        if titles.count(name) > 1:
            errors.append(f"## {name} 절이 두 번 이상 있음")
    if "원문" in titles and titles[0] != "원문":
        errors.append("## 원문 은 H1 바로 다음 첫 절이어야 함")
    tail = [t for t in titles if t in WORKBOOK_TAIL]
    if tail and titles[-len(tail):] != [t for t in WORKBOOK_TAIL if t in tail]:
        errors.append("## 힌트, ## 풀이 는 이 순서로 본문 맨 끝에 둠")
    content = {t: c for t, c in reversed(sections)}     # 같은 제목이 여럿이면 첫 절
    for name in WORKBOOK_SECTIONS:
        if name in content and not content[name].strip():
            errors.append(f"## {name} 절이 비어 있음")
    for name in WORKBOOK_TAIL:
        if not content.get(name, "").strip():
            continue
        subs = split_subsections(content[name])
        if subs[0][0] == "":
            errors.append(f"## {name}: 첫 ### 소절 앞에 글이 있음")
        for label, text in subs:
            if label and not text.strip():
                errors.append(f"## {name} / ### {label}: 내용 없음")
            if name == "힌트":
                for line in text.splitlines():
                    if line.startswith("> 띠:") and not HINT_FORMULA_RE.match(line.rstrip()):
                        errors.append(f"## 힌트 / ### {label}: 띠 식 줄은 '> 띠: $<LaTeX>$' 형식 ({line.strip()!r})")
        if name == "풀이":
            labels = [label for label, _ in subs if label]
            if not labels or labels[-1] != "답" or labels.count("답") > 1:
                errors.append("## 풀이: 마지막 소절 하나만 ### 답 이어야 함")
    return errors
```

`check_body` 끝부분을 이렇게 바꾼다.

```python
    for link in IMAGE_RE.findall(body):
        if not (path.parent / link).exists():
            errors.append(f"이미지 없음: {link}")
    errors += check_workbook_sections(body)
    return errors
```

- [ ] **Step 4: 테스트가 통과하는지 확인한다**

Run: `python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests 2>&1 | tail -3 && python3 -m unittest discover -s from_the_past/md/_tools/tests 2>&1 | tail -3`
Expected: `Ran 93 tests … OK`, `Ran 65 tests … OK`

- [ ] **Step 5: 실제 md가 계속 통과하는지 확인한다**

```bash
for ch in ch09 ch10 ch11; do python3 교과서/마이크로전자회로/_tools/check_md.py 교과서/마이크로전자회로/$ch | tail -1; done
for ex in 2021-1_중간 2021-1_기말 2023-1_중간 2023-1_기말; do python3 from_the_past/md/_tools/check_exam.py from_the_past/md/$ex | tail -1; done
```
Expected: 일곱 줄 모두 오류 0개.

- [ ] **Step 6: FORMAT.md에 '문제집용 절'을 추가한다**

`교과서/마이크로전자회로/FORMAT.md`의 `## 수식` 줄 바로 앞에 다음을 넣는다(뒤에 빈 줄 하나).

````markdown
## 문제집용 절 (선택)
문제지·답안지 PDF(`workbook/`)에 쓰는 절이다. 없어도 된다. 있으면 `check_md.py`가 위치와 모양을 검사한다. 기출도 같다.

| 절 | 위치 | 내용 |
|---|---|---|
| `## 원문` | H1 바로 다음 (첫 절) | 인쇄된 문제 문장을 글자 그대로 옮긴다. 문단은 빈 줄로 나누고 수식은 `$…$`로 쓴다. 소문항 (a)(b)…도 원문 그대로 |
| `## 힌트` | 본문 끝 (`## 풀이`보다 앞) | 힌트 하나 = `### <이름표>` 소절. 소절 안에 `> 띠: $<LaTeX>$` 줄을 두면(선택) 문제 쪽 Hint 띠에 이름표 대신 그 식이 보인다. 나머지 줄은 답안지 Hint 쪽 본문이다 |
| `## 풀이` | 본문 맨 끝 | 단계 하나 = `### <이름표>` 소절. 마지막 소절 하나만 `### 답` |

```markdown
## 힌트
### 식 9.5
> 띠: $R_{out} = [1 + g_{m1}(r_{O2} \parallel r_{\pi 1})] r_{O1} + r_{O2} \parallel r_{\pi 1}$
- 바이폴라 캐스코드의 출력 저항

## 풀이
### 소신호 파라미터
- $g_{m1} = I_{C1}/V_T$
### 답
$R_{out} \approx 490\ \text{k}\Omega$
```
- 쓸 수 있는 문법: `- ` 목록(2칸 들여쓰기로 한 단계), 목록 아래 들여쓴 이어지는 줄, 일반 문단(빈 줄로 나눔), `**굵게**`, `$…$`, `$$…$$`. 표, 코드 블록, 이미지는 PDF에 나오지 않는다.
- PDF에서는 `## 조건`의 `- 회로:` 줄(문제 그림이 있을 때만)과 `(원문에 없음)`, `(원문의 …)`, `(보조 출처: …)` 표시가 빠진다. md에서는 지우지 않는다.
- 예제에 `## 풀이`가 없으면 답안지 답 칸에 `## 답 (검증용)`의 글(`### 정답 회로`, 코드 블록, `> 참고:`는 뺌)이 들어간다.
````

- [ ] **Step 7: FORMAT-EXAM.md에 한 줄을 추가한다**

`from_the_past/md/FORMAT-EXAM.md`에서 ``- `## 답` 절은 두지 않는다(풀이는 이번 범위 밖).`` 줄 바로 아래에 다음을 넣는다.

```markdown
- 문제집용 절 `## 원문`, `## 힌트`는 교과서 FORMAT.md의 '문제집용 절'을 그대로 따른다. `## 풀이`는 아직 쓰지 않는다(풀이 작업에서 정함).
```

- [ ] **Step 8: 커밋한다**

```bash
git add 교과서/마이크로전자회로/_tools/check_md.py 교과서/마이크로전자회로/_tools/tests/test_check_md.py 교과서/마이크로전자회로/FORMAT.md from_the_past/md/FORMAT-EXAM.md
git commit -m "feat: add workbook sections (원문, 힌트, 풀이) to md format and checker

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: 템플릿 설치와 기출 지원

**Files:**
- Create: `workbook/paths.py`
- Create: `workbook/templates/problem.html`, `workbook/templates/answer.html` (Downloads에서 복사해 수정)
- Create: `workbook/templates/sample-problem.json`, `workbook/templates/sample-answer.json`
- Test: `workbook/tests/test_templates.py`

**Interfaces:**
- Produces: `paths.ROOT`, `paths.TEXTBOOK`, `paths.EXAMS`, `paths.WORKBOOK`, `paths.TEMPLATES` (모두 `Path`). `import paths`를 하면 `교과서/마이크로전자회로/_tools`와 `from_the_past/md/_tools`가 `sys.path`에 들어간다.
- 템플릿 계약: `<script type="application/json" id="workbook-data">__WORKBOOK_DATA__</script>`가 한 곳에만 있다. 문제 항목의 `kind: "기출"`, `book_page: null`, `original_lang`을 받는다.

- [ ] **Step 1: `paths.py`와 실패하는 테스트를 쓴다**

`workbook/paths.py`:

```python
"""문제집 생성기의 저장소 경로. import하면 기존 도구 폴더(check_md, crop_figures, crop_exam)를 sys.path에 넣는다."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXTBOOK = ROOT / "교과서" / "마이크로전자회로"
EXAMS = ROOT / "from_the_past" / "md"
WORKBOOK = ROOT / "workbook"
TEMPLATES = WORKBOOK / "templates"

for _tools in (TEXTBOOK / "_tools", EXAMS / "_tools"):
    if str(_tools) not in sys.path:
        sys.path.insert(0, str(_tools))
```

`workbook/tests/test_templates.py`:

```python
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import TEMPLATES  # noqa: E402

PLACEHOLDER = "__WORKBOOK_DATA__"


def read(name):
    return (TEMPLATES / name).read_text(encoding="utf-8")


class TestTemplates(unittest.TestCase):
    def test_placeholder_once(self):
        for name in ("problem.html", "answer.html"):
            with self.subTest(name=name):
                t = read(name)
                self.assertEqual(t.count(PLACEHOLDER), 1)
                self.assertIn(f'id="workbook-data">{PLACEHOLDER}</script>', t)

    def test_samples_extracted(self):
        for name, mode in (("sample-problem.json", "problems"), ("sample-answer.json", "answers")):
            with self.subTest(name=name):
                data = json.loads(read(name))
                self.assertEqual(data["meta"]["mode"], mode)
                self.assertEqual(len(data["problems"]), 12)

    def test_exam_kind_supported(self):
        for name in ("problem.html", "answer.html"):
            with self.subTest(name=name):
                t = read(name)
                self.assertIn("--kind-exam: #7A4FA0;", t)
                self.assertIn('[data-kind="exam"]', t)
                self.assertIn("'기출': 'exam'", t)
                self.assertIn("p.book_page != null", t)
                self.assertNotIn("p.${p.book_page} · ${n}", t)

    def test_original_lang_from_data(self):
        self.assertIn("p.original_lang || 'en'", read("problem.html"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 실패를 확인한다**

Run: `python3 -m unittest discover -s workbook/tests 2>&1 | tail -3`
Expected: `FileNotFoundError`(templates 없음)로 FAILED(errors=4)

- [ ] **Step 3: 템플릿을 복사하고 샘플을 빼낸다**

```bash
mkdir -p workbook/templates
cp /Users/hyunjun_macbook_pro/Downloads/template_problem.html workbook/templates/problem.html
cp /Users/hyunjun_macbook_pro/Downloads/template_answer.html workbook/templates/answer.html
python3 - <<'EOF'
import json
import re
from pathlib import Path

T = Path("workbook/templates")
PAT = re.compile(r'(<script type="application/json" id="workbook-data">)(.*?)(</script>)', re.S)
for name, sample in (("problem.html", "sample-problem.json"), ("answer.html", "sample-answer.json")):
    path = T / name
    t = path.read_text(encoding="utf-8")
    m = PAT.search(t)
    assert m and len(PAT.findall(t)) == 1, name
    data = json.loads(m.group(2))
    (T / sample).write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    path.write_text(t[:m.start(2)] + "__WORKBOOK_DATA__" + t[m.end(2):], encoding="utf-8")
    print(name, "→", sample, len(data["problems"]))
EOF
```
Expected: `problem.html → sample-problem.json 12`, `answer.html → sample-answer.json 12`

- [ ] **Step 4: 기출 지원을 위한 최소 수정을 한다**

```bash
python3 - <<'EOF'
from pathlib import Path

T = Path("workbook/templates")
EDITS = [
    ("  --kind-problem: #C0622B;    /* 장말문제 */\n",
     "  --kind-problem: #C0622B;    /* 장말문제 */\n  --kind-exam: #7A4FA0;       /* 기출 */\n"),
    ('[data-kind="problem"]  { --kind: var(--kind-problem); }\n',
     '[data-kind="problem"]  { --kind: var(--kind-problem); }\n[data-kind="exam"]     { --kind: var(--kind-exam); }\n'),
    ("const KIND_SLUG = { '예제': 'example', '연습문제': 'exercise', '장말문제': 'problem' };",
     "const KIND_SLUG = { '예제': 'example', '연습문제': 'exercise', '장말문제': 'problem', '기출': 'exam' };"),
    ("  meta.append(txt('span', 'head-info', `${p.section} · p.${p.book_page} · ${n} / ${total}`));",
     "  const info = [p.section, p.book_page != null ? `p.${p.book_page}` : '', `${n} / ${total}`];\n"
     "  meta.append(txt('span', 'head-info', info.filter(Boolean).join(' · ')));"),
]
PROBLEM_ONLY = [
    ("  if (p.html.original) panel.append(block('문제 원문', p.html.original, 'original', 'en'));   // 영어 원문은 맨 처음",
     "  if (p.html.original) panel.append(block('문제 원문', p.html.original, 'original', p.original_lang || 'en'));   // 원문은 맨 처음"),
]
for name in ("problem.html", "answer.html"):
    path = T / name
    t = path.read_text(encoding="utf-8")
    for old, new in EDITS + (PROBLEM_ONLY if name == "problem.html" else []):
        assert t.count(old) == 1, (name, old)
        t = t.replace(old, new)
    path.write_text(t, encoding="utf-8")
    print("수정:", name)
EOF
```
Expected: `수정: problem.html`, `수정: answer.html` (AssertionError가 나면 멈추고 해당 줄을 템플릿에서 찾아 공백을 확인한다)

- [ ] **Step 5: 테스트가 통과하는지 확인한다**

Run: `python3 -m unittest discover -s workbook/tests 2>&1 | tail -3`
Expected: `Ran 4 tests … OK`

- [ ] **Step 6: 커밋한다**

```bash
git add workbook/paths.py workbook/templates/problem.html workbook/templates/answer.html workbook/templates/sample-problem.json workbook/templates/sample-answer.json workbook/tests/test_templates.py
git commit -m "feat(workbook): install final templates with data placeholder and exam support

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: `mdsub.py` — md 하위 문법 → HTML

**Files:**
- Create: `workbook/mdsub.py`
- Test: `workbook/tests/test_mdsub.py`

**Interfaces:**
- Produces:
  - `inline(text: str) -> str` — 한 줄. 수식 밖만 `**굵게**` 처리, `& < >`는 안팎 모두 이스케이프
  - `to_html(md: str) -> str` — 목록·문단 블록. 빈 입력이면 `""`
  - `answer_html(md: str) -> str` — 비어 있지 않은 줄이 하나면 (`- `를 뗀) `inline`, 여러 줄이면 `to_html`

- [ ] **Step 1: 실패하는 테스트를 쓴다**

`workbook/tests/test_mdsub.py`:

```python
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mdsub import answer_html, to_html  # noqa: E402


class TestToHtml(unittest.TestCase):
    def test_flat_list(self):
        self.assertEqual(to_html("- a\n- b"), "<ul><li>a</li><li>b</li></ul>")

    def test_nested_list(self):
        self.assertEqual(to_html("- a\n  - b\n  - c\n- d"),
                         "<ul><li>a<ul><li>b</li><li>c</li></ul></li><li>d</li></ul>")

    def test_nested_list_closed_at_end(self):
        self.assertEqual(to_html("- a\n  - b"), "<ul><li>a<ul><li>b</li></ul></li></ul>")

    def test_skipped_indent_is_one_level(self):
        self.assertEqual(to_html("- a\n    - b"), "<ul><li>a<ul><li>b</li></ul></li></ul>")

    def test_continuation_lines_join_item(self):
        md = "- 특성:\n  $$I_D = \\gamma V^3$$\n  $\\gamma$는 계수\n- 다음"
        self.assertEqual(to_html(md),
                         "<ul><li>특성: $$I_D = \\gamma V^3$$ $\\gamma$는 계수</li><li>다음</li></ul>")

    def test_paragraphs(self):
        self.assertEqual(to_html("첫 줄\n이어짐\n\n둘째"), "<p>첫 줄 이어짐</p><p>둘째</p>")

    def test_math_kept_and_escaped(self):
        self.assertEqual(to_html(r"- $a_{1} < b \\ c$ & d"),
                         r"<ul><li>$a_{1} &lt; b \\ c$ &amp; d</li></ul>")

    def test_bold_outside_math_only(self):
        self.assertEqual(to_html("**굵게** $**x**$"), "<p><b>굵게</b> $**x**$</p>")

    def test_empty(self):
        self.assertEqual(to_html(""), "")
        self.assertEqual(to_html("\n\n"), "")


class TestAnswerHtml(unittest.TestCase):
    def test_single_bullet_is_inline(self):
        self.assertEqual(answer_html("- $R \\approx 1$ (식 9.10)\n"), "$R \\approx 1$ (식 9.10)")

    def test_single_line_is_inline(self):
        self.assertEqual(answer_html("$R$"), "$R$")

    def test_many_lines_use_blocks(self):
        self.assertEqual(answer_html("- a\n- b"), "<ul><li>a</li><li>b</li></ul>")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 실패를 확인한다**

Run: `python3 -m unittest discover -s workbook/tests 2>&1 | tail -3`
Expected: `ModuleNotFoundError: No module named 'mdsub'`

- [ ] **Step 3: 구현한다**

`workbook/mdsub.py`:

```python
"""문제 md의 하위 문법 → HTML (문제집 템플릿의 html 필드용).

다루는 문법 (FORMAT.md의 조건·구할 것·원문·힌트·풀이 본문에서 쓰는 것만):
- `- ` 목록. 2칸 들여쓰기마다 한 단계 깊어진다
- 목록 항목 아래 들여쓴 목록 아닌 줄(`  $$…$$`, `  설명`)은 그 항목에 공백으로 이어 붙인다
- 들여쓰지 않은 일반 줄은 문단(<p>)이고, 빈 줄이 블록을 나눈다
- `**굵게**` → <b> (수식 밖만)
수식($…$, $$…$$)은 그대로 둔다(템플릿의 KaTeX auto-render가 그림). & < > 는 수식 안팎 모두
이스케이프한다. KaTeX는 텍스트 노드를 읽으므로 수식 안의 &lt; 도 < 로 읽힌다.
"""
import html
import re

MATH_RE = re.compile(r"\$\$.+?\$\$|\$[^$]+?\$", re.DOTALL)
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
ITEM_RE = re.compile(r"^( *)- (.*)$")


def _plain(text):
    return BOLD_RE.sub(r"<b>\1</b>", html.escape(text, quote=False))


def inline(text):
    """한 줄 글 → HTML 조각."""
    out, last = [], 0
    for m in MATH_RE.finditer(text):
        out.append(_plain(text[last:m.start()]))
        out.append(html.escape(m.group(0), quote=False))
        last = m.end()
    out.append(_plain(text[last:]))
    return "".join(out)


def _render_list(items):
    out, depth = [], -1
    for level, text in items:
        level = min(level, depth + 1)          # 들여쓰기를 두 단계 이상 건너뛰어도 한 단계만 깊어진다
        if level > depth:
            out.append("<ul>")
        else:
            out.append("</li>" + "</ul></li>" * (depth - level))
        out.append("<li>" + inline(text))
        depth = level
    out.append("</li>" + "</ul></li>" * depth + "</ul>")
    return "".join(out)


def to_html(md):
    """md 조각 → HTML. 빈 입력이면 빈 문자열."""
    blocks = []                                # ["ul", [[level, text], …]] | ["p", [줄, …]] | None(빈 줄)
    for raw in md.splitlines():
        line = raw.rstrip()
        cur = blocks[-1] if blocks else None
        if not line.strip():
            blocks.append(None)
            continue
        m = ITEM_RE.match(line)
        if m:
            if not (cur and cur[0] == "ul"):
                cur = ["ul", []]
                blocks.append(cur)
            cur[1].append([len(m.group(1)) // 2, m.group(2)])
        elif line.startswith(" ") and cur and cur[0] == "ul":
            cur[1][-1][1] += " " + line.strip()
        else:
            if not (cur and cur[0] == "p"):
                cur = ["p", []]
                blocks.append(cur)
            cur[1].append(line.strip())
    return "".join(_render_list(b[1]) if b[0] == "ul" else f"<p>{inline(' '.join(b[1]))}</p>"
                   for b in blocks if b)


def answer_html(md):
    """답 칸용. 비어 있지 않은 줄이 하나면(목록 한 개 포함) 태그 없이 글만, 여러 줄이면 to_html."""
    lines = [line for line in md.strip().splitlines() if line.strip()]
    if len(lines) == 1:
        return inline(re.sub(r"^- ", "", lines[0].strip()))
    return to_html(md)
```

- [ ] **Step 4: 테스트가 통과하는지 확인한다**

Run: `python3 -m unittest discover -s workbook/tests 2>&1 | tail -3`
Expected: `Ran 16 tests … OK`

- [ ] **Step 5: 커밋한다**

```bash
git add workbook/mdsub.py workbook/tests/test_mdsub.py
git commit -m "feat(workbook): convert md subset (lists, paragraphs, math) to html

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: `problem.py` — 문제 md 한 개 → 필드

**Files:**
- Create: `workbook/problem.py`
- Test: `workbook/tests/test_problem.py`

**Interfaces:**
- Consumes:
  - `check_md`: `split_frontmatter, split_sections, split_subsections, check_workbook_sections, HINT_FORMULA_RE` (Task 1)
  - `crop_figures.figure_filename("9.2") -> "fig9-02.png"`, `crop_exam.figure_filename("Q1") -> "fig-Q1.png"`
  - `mdsub.inline, to_html, answer_html` (Task 3)
- Produces (Task 5가 씀):
  - `class ProblemError(Exception)`
  - `@dataclass Problem(path: Path, meta: dict, sections: list[tuple[str, str]], title: str)`. 속성 `.id -> str`, `.is_exam -> bool`, `.figures_dir -> Path`, 메서드 `.section(name) -> str | None`
  - `load_problem(path) -> Problem` — frontmatter·H1·문제집용 절이 잘못되면 `ProblemError`
  - `strip_markers(md) -> str`, `drop_circuit_lines(md) -> str`, `example_answer_md(text) -> str`
  - `problem_figure_ids(p) -> list[str]`
  - `html_fields(p) -> dict` — `conditions`, `ask`, 그리고 `## 원문`이 있으면 `original`
  - `figures(p) -> list[dict]` — `{"src", "w_mm", "h_mm"}`, 파일이 없으면 `ProblemError`
  - `hints(p) -> list[dict]` — `{"label", "html"}`에 `"formula"`는 있을 때만
  - `solution(p) -> dict | None` — `{"steps": [{"label", "html"}], "answer"}`
  - `exam_info(exam_dir: Path) -> dict` — `exam.yaml` 내용 (캐시)

- [ ] **Step 1: 실패하는 테스트를 쓴다**

`workbook/tests/test_problem.py`:

```python
import sys
import tempfile
import unittest
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import TEXTBOOK  # noqa: E402
from problem import (ProblemError, drop_circuit_lines, example_answer_md, exam_info,  # noqa: E402
                     figures, hints, html_fields, load_problem, solution, strip_markers)

FIGS = ('  - {id: "9.2", role: problem, panels: [a]}\n'
        '  - {id: "9.2", role: problem, panels: [b]}\n'
        '  - {id: "9.13", role: answer, panels: []}\n')

BODY = r"""
## 조건
- 회로: Fig 9.2(a) 바이폴라 캐스코드 전류원
  - 회로 아래 설명 줄
- $Q_1$, $Q_2$ 모두 $I_C = 1\ \text{mA}$ (원문에 없음)

## 구할 것
- 출력 저항 $R_{out}$ (괄호 안은 원문에 없음)

## 회로 — 없음 (테스트)

## 답 (검증용)
- $R_{out} \approx 328.9\ \text{k}\Omega$ (식 9.10)
> 참고: 무시

### 정답 회로 — Fig 9.3
- 무시
"""

EXAM_MD = r"""---
id: 2023-1_기말-Q1
kind: 기출
exam: "2023-1 기말고사"
number: "1"
points: 20
source: "../../2023-1/23-1 기말/기말고사.pdf"
pdf_page: 1
source_lang: ko
figures:
  - {id: "Q1", role: problem, panels: [a, b]}
textbook_chapters: [10, 11]
depends_on: []
refs: []
---
# 기출 2023-1 기말 1 — Miller 정리로 구하는 극점

## 조건
- 회로: 그림 (a), (b)
- $\lambda = 0$ (보조 출처: 손정리 노트)

## 구할 것
- (1) 극점

## 회로 — 없음 (테스트)
"""


def textbook_md(pid="E9.01", kind="예제", figures=FIGS, original="", extra=""):
    chapter, num = pid[1:].split(".")
    number = f"{int(chapter)}.{int(num)}"
    fig_yaml = "figures:\n" + figures if figures else "figures: []\n"
    return ("---\n"
            f"id: {pid}\nkind: {kind}\nnumber: \"{number}\"\n"
            "section: \"9.1.1 전류원으로서의 캐스코드\"\nbook_page: 451\npdf_page: 2\nsource_lang: en\n"
            + fig_yaml
            + "depends_on: []\nrefs: []\n---\n"
            f"# {kind} {number} — 바이폴라 캐스코드 전류원의 출력 저항\n"
            + ("\n" + original if original else "")
            + BODY + extra)


def make_png(path, w, h):
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, w, h), False)
    pix.set_rect(pix.irect, (255, 255, 255))
    pix.save(str(path))


class ProblemCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        fig_dir = self.root / "ch09" / "figures"
        fig_dir.mkdir(parents=True)
        (fig_dir / "figures.yaml").write_text("dpi: 144\nfigures: {}\n", encoding="utf-8")
        make_png(fig_dir / "fig9-02.png", 200, 182)

    def tearDown(self):
        self._tmp.cleanup()

    def load(self, text, pid="E9.01", kind="예제"):
        path = self.root / "ch09" / kind / f"{pid}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return load_problem(path)


class TestLoad(ProblemCase):
    def test_title_and_id(self):
        p = self.load(textbook_md())
        self.assertEqual(p.id, "E9.01")
        self.assertEqual(p.title, "바이폴라 캐스코드 전류원의 출력 저항")
        self.assertFalse(p.is_exam)

    def test_missing_h1_raises(self):
        with self.assertRaisesRegex(ProblemError, "H1"):
            self.load(textbook_md().replace("# 예제 9.1 — ", "예제 9.1 "))

    def test_invalid_workbook_section_raises(self):
        with self.assertRaisesRegex(ProblemError, "### 답"):
            self.load(textbook_md(extra="\n## 풀이\n### 단계\n- x\n"))

    def test_real_file(self):
        p = load_problem(TEXTBOOK / "ch09" / "예제" / "E9.01.md")
        self.assertEqual(p.title, "바이폴라 캐스코드 전류원의 출력 저항")


class TestHtmlFields(ProblemCase):
    def test_circuit_line_dropped_when_problem_has_figure(self):
        f = html_fields(self.load(textbook_md()))
        self.assertEqual(f["conditions"], r"<ul><li>$Q_1$, $Q_2$ 모두 $I_C = 1\ \text{mA}$</li></ul>")
        self.assertEqual(f["ask"], r"<ul><li>출력 저항 $R_{out}$</li></ul>")

    def test_circuit_line_kept_without_figure(self):
        f = html_fields(self.load(textbook_md(figures="")))
        self.assertEqual(f["conditions"],
                         r"<ul><li>회로: Fig 9.2(a) 바이폴라 캐스코드 전류원<ul><li>회로 아래 설명 줄</li></ul></li>"
                         r"<li>$Q_1$, $Q_2$ 모두 $I_C = 1\ \text{mA}$</li></ul>")

    def test_original_optional(self):
        self.assertNotIn("original", html_fields(self.load(textbook_md())))
        p = self.load(textbook_md(original="## 원문\nRepeat Example 9.1 if $I_1 < 1$.\n"))
        self.assertEqual(html_fields(p)["original"], "<p>Repeat Example 9.1 if $I_1 &lt; 1$.</p>")

    def test_strip_markers(self):
        cases = [
            ("가정 (원문에 없음)", "가정"),
            ("메모 (원문의 메모)", "메모"),
            ("값 (보조 출처: 손정리 노트)", "값"),
            ('설계 (원문에 없음, 원문은 "설계하라"만 적음)', "설계"),
            ("이득 (크기 $|A_v| = 5$로 해석, 원문에 없음)", "이득"),
            ("$f(x)$ 가정 (원문에 없음)", "$f(x)$ 가정"),
            ("$\\text{(원문에 없음)}$", "$\\text{(원문에 없음)}$"),
            ('예제 (E10.09, 원문 표기 "Example 10-9")', '예제 (E10.09, 원문 표기 "Example 10-9")'),
            ("a (원문에 없음)\nb", "a\nb"),
        ]
        for src, want in cases:
            with self.subTest(src=src):
                self.assertEqual(strip_markers(src), want)

    def test_drop_circuit_lines(self):
        self.assertEqual(drop_circuit_lines("- 회로: Fig 1\n  - 설명\n  이어짐\n- 값\n  - 하위"), "- 값\n  - 하위")


class TestFigures(ProblemCase):
    def test_problem_role_only_and_dedup(self):
        figs = figures(self.load(textbook_md()))
        self.assertEqual(len(figs), 1)
        self.assertEqual((figs[0]["w_mm"], figs[0]["h_mm"]), (35.3, 32.1))
        self.assertTrue(figs[0]["src"].startswith("data:image/png;base64,iVBOR"))

    def test_missing_figure_file_raises(self):
        (self.root / "ch09" / "figures" / "fig9-02.png").unlink()
        with self.assertRaisesRegex(ProblemError, "그림 파일 없음"):
            figures(self.load(textbook_md()))


class TestHintsAndSolution(ProblemCase):
    def test_hints(self):
        extra = "\n## 힌트\n### 식 9.5\n> 띠: $R = r_O$\n- 캐스코드\n### 참고\n- $a < b$\n"
        self.assertEqual(hints(self.load(textbook_md(extra=extra))), [
            {"label": "식 9.5", "html": "<ul><li>캐스코드</li></ul>", "formula": "R = r_O"},
            {"label": "참고", "html": "<ul><li>$a &lt; b$</li></ul>"},
        ])

    def test_no_hints(self):
        self.assertEqual(hints(self.load(textbook_md())), [])

    def test_solution_section(self):
        extra = "\n## 풀이\n### $g_m$ 계산\n- $g_m = 1/26$\n### 답\n$R \\approx 1$\n"
        self.assertEqual(solution(self.load(textbook_md(extra=extra))), {
            "steps": [{"label": "$g_m$ 계산", "html": "<ul><li>$g_m = 1/26$</li></ul>"}],
            "answer": "$R \\approx 1$",
        })

    def test_example_answer_fallback(self):
        self.assertEqual(solution(self.load(textbook_md())),
                         {"steps": [], "answer": r"$R_{out} \approx 328.9\ \text{k}\Omega$ (식 9.10)"})

    def test_non_example_without_solution_is_none(self):
        p = self.load(textbook_md(pid="X9.01", kind="연습문제"), pid="X9.01", kind="연습문제")
        self.assertIsNone(solution(p))

    def test_example_answer_md_stops_at_subsection_and_code(self):
        self.assertEqual(example_answer_md("- a\n> 참고: b\n\n### 정답 회로\n- c\n"), "- a")
        self.assertEqual(example_answer_md("- a\n```spice\nQ1 a b c npn\n```\n"), "- a")


class TestExam(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        exam_dir = Path(self._tmp.name) / "2023-1_기말"
        (exam_dir / "figures").mkdir(parents=True)
        (exam_dir / "exam.yaml").write_text('exam: "2023-1 기말고사"\n', encoding="utf-8")
        (exam_dir / "figures" / "figures.yaml").write_text("dpi: 144\nfigures: {}\n", encoding="utf-8")
        make_png(exam_dir / "figures" / "fig-Q1.png", 144, 72)
        (exam_dir / "Q1.md").write_text(EXAM_MD, encoding="utf-8")
        self.p = load_problem(exam_dir / "Q1.md")

    def tearDown(self):
        self._tmp.cleanup()

    def test_exam_problem(self):
        self.assertTrue(self.p.is_exam)
        self.assertEqual(self.p.title, "Miller 정리로 구하는 극점")
        self.assertEqual(exam_info(self.p.path.parent)["exam"], "2023-1 기말고사")
        self.assertEqual([(f["w_mm"], f["h_mm"]) for f in figures(self.p)], [(25.4, 12.7)])
        self.assertEqual(html_fields(self.p)["conditions"], r"<ul><li>$\lambda = 0$</li></ul>")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 실패를 확인한다**

Run: `python3 -m unittest discover -s workbook/tests 2>&1 | tail -3`
Expected: `ModuleNotFoundError: No module named 'problem'`

- [ ] **Step 3: 구현한다**

`workbook/problem.py`:

```python
"""문제 md 한 개 → 문제집 JSON 항목의 재료 (제목, html 절, 그림, 힌트, 풀이).

교과서(FORMAT.md)와 기출(FORMAT-EXAM.md) md를 모두 읽는다. 문제집용 절 규칙은 FORMAT.md '문제집용 절'.
"""
import base64
import re
import struct
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

import paths  # noqa: F401  (기존 도구 import 경로 설정)
from check_md import (HINT_FORMULA_RE, check_workbook_sections, split_frontmatter,
                      split_sections, split_subsections)
from crop_exam import figure_filename as exam_figure_filename
from crop_figures import figure_filename as textbook_figure_filename
from mdsub import answer_html, inline, to_html

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MATH_RE = re.compile(r"\$\$.+?\$\$|\$[^$]+?\$", re.DOTALL)
# 작성자 보충 표시: 한 줄 안의 (…) 가운데 안쪽 괄호가 없고 이 말이 든 것
MARKER_RE = re.compile(r"[ \t]*\([^()\n]*(?:원문에 없음|원문의 |보조 출처)[^()\n]*\)")
MASK_RE = re.compile(r"\x00(\d+)\x00")
REQUIRED_KEYS = ("id", "kind", "number")


class ProblemError(Exception):
    pass


@dataclass
class Problem:
    path: Path
    meta: dict
    sections: list      # [(제목, 내용)]
    title: str

    @property
    def id(self):
        return str(self.meta["id"])

    @property
    def is_exam(self):
        return self.meta["kind"] == "기출"

    @property
    def figures_dir(self):
        return self.path.parent / "figures" if self.is_exam else self.path.parent.parent / "figures"

    def section(self, name):
        """제목이 name인 첫 절의 내용. 없으면 None."""
        return next((c for t, c in self.sections if t == name), None)


def load_problem(path):
    path = Path(path)
    try:
        meta, body = split_frontmatter(path.read_text(encoding="utf-8"))
    except (ValueError, yaml.YAMLError) as e:
        raise ProblemError(str(e)) from e
    missing = [k for k in REQUIRED_KEYS if k not in meta]
    if missing:
        raise ProblemError(f"frontmatter 키 누락: {', '.join(missing)}")
    errors = check_workbook_sections(body)
    if errors:
        raise ProblemError("; ".join(errors))
    h1 = next((line for line in body.splitlines() if line.startswith("# ")), None)
    if not h1 or " — " not in h1:
        raise ProblemError("H1 '# <종류> <번호> — <제목>' 없음")
    return Problem(path, meta, split_sections(body), h1.split(" — ", 1)[1].strip())


@lru_cache(maxsize=None)
def exam_info(exam_dir):
    return yaml.safe_load((Path(exam_dir) / "exam.yaml").read_text(encoding="utf-8")) or {}


def strip_markers(md):
    """작성자 보충 표시를 지운다. 수식을 먼저 가려 두므로 수식 안은 그대로이고, 수식을 품은 표시도 지워진다."""
    maths = []

    def mask(m):
        maths.append(m.group(0))
        return f"\x00{len(maths) - 1}\x00"

    masked = MARKER_RE.sub("", MATH_RE.sub(mask, md))
    return MASK_RE.sub(lambda m: maths[int(m.group(1))], masked)


def drop_circuit_lines(md):
    """'- 회로:' 줄과 그 아래 들여쓴 줄을 뺀다 (문제 그림이 PDF에 함께 나오므로)."""
    out, skipping = [], False
    for line in md.splitlines():
        if line.startswith("- 회로:"):
            skipping = True
            continue
        if skipping and line.startswith(" "):
            continue
        skipping = False
        out.append(line)
    return "\n".join(out)


def example_answer_md(text):
    """'## 답 (검증용)'에서 답 글만: '### ' 소절이나 코드 블록 앞까지, '> ' 메모 줄은 뺀다."""
    keep = []
    for line in text.splitlines():
        if line.startswith("### ") or line.startswith("```"):
            break
        if not line.startswith("> "):
            keep.append(line)
    return "\n".join(keep).strip()


def problem_figure_ids(p):
    ids = []
    for fig in p.meta.get("figures") or []:
        fig_id = str(fig.get("id"))
        if fig.get("role") == "problem" and fig_id not in ids:
            ids.append(fig_id)
    return ids


def html_fields(p):
    fields = {}
    original = p.section("원문")
    if original is not None:
        fields["original"] = to_html(original)
    conditions = p.section("조건") or ""
    if problem_figure_ids(p):
        conditions = drop_circuit_lines(conditions)
    fields["conditions"] = to_html(strip_markers(conditions))
    fields["ask"] = to_html(strip_markers(p.section("구할 것") or ""))
    return fields


@lru_cache(maxsize=None)
def _figures_dpi(fig_dir):
    spec = yaml.safe_load((fig_dir / "figures.yaml").read_text(encoding="utf-8")) or {}
    return spec.get("dpi", 144)


def png_size(data):
    if data[:8] != PNG_SIGNATURE:
        raise ProblemError("PNG 파일이 아님")
    return struct.unpack(">II", data[16:24])


def figures(p):
    """문제 그림(role: problem)을 base64 data URI와 인쇄 크기(mm)로. mm = 픽셀 / dpi × 25.4."""
    name = exam_figure_filename if p.is_exam else textbook_figure_filename
    out = []
    for fig_id in problem_figure_ids(p):
        png = p.figures_dir / name(fig_id)
        if not png.exists():
            raise ProblemError(f"그림 파일 없음: {png}")
        try:
            dpi = _figures_dpi(p.figures_dir)
        except FileNotFoundError as e:
            raise ProblemError(f"figures.yaml 없음: {p.figures_dir}") from e
        data = png.read_bytes()
        w, h = png_size(data)
        out.append({"src": "data:image/png;base64," + base64.b64encode(data).decode("ascii"),
                    "w_mm": round(w / dpi * 25.4, 1), "h_mm": round(h / dpi * 25.4, 1)})
    return out


def hints(p):
    text = p.section("힌트")
    if not text:
        return []
    out = []
    for label, body in split_subsections(text):
        formula, lines = None, []
        for line in body.splitlines():
            m = HINT_FORMULA_RE.match(line.rstrip())
            if m:
                formula = m.group(1).strip()
            else:
                lines.append(line)
        hint = {"label": inline(label), "html": to_html("\n".join(lines))}
        if formula:
            hint["formula"] = formula
        out.append(hint)
    return out


def solution(p):
    """'## 풀이'가 있으면 단계와 답. 없고 예제면 '## 답 (검증용)'의 답만. 둘 다 없으면 None."""
    text = p.section("풀이")
    if text:
        subs = split_subsections(text)
        return {"steps": [{"label": inline(label), "html": to_html(body)} for label, body in subs[:-1]],
                "answer": answer_html(subs[-1][1])}
    if p.meta["kind"] == "예제":
        answer = p.section("답 (검증용)")
        if answer:
            return {"steps": [], "answer": answer_html(strip_markers(example_answer_md(answer)))}
    return None
```

- [ ] **Step 4: 테스트가 통과하는지 확인한다**

Run: `python3 -m unittest discover -s workbook/tests 2>&1 | tail -3`
Expected: `Ran 34 tests … OK`

- [ ] **Step 5: 커밋한다**

```bash
git add workbook/problem.py workbook/tests/test_problem.py
git commit -m "feat(workbook): read one problem md into workbook fields

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: `assemble.py` — 대상 → 문제집 JSON

**Files:**
- Create: `workbook/assemble.py`
- Test: `workbook/tests/test_assemble.py`

**Interfaces:**
- Consumes: `paths.TEXTBOOK, EXAMS`, `problem.*` (Task 4), `workbook/templates/sample-*.json` (Task 2)
- Produces (Task 6·7이 씀):
  - `MODE_SUFFIX = {"problems": "문제", "answers": "답안"}`
  - `class BuildError(Exception)` — `.errors: list[str]`
  - `@dataclass Selection(name: str, title: str, chapter: int, paths: list[Path])`
  - `chapter_selection(ch: int)`, `exam_selection(dir_name: str)`, `ids_selection(ids: list[str], name: str)`, `resolve_target(target: str)`, `all_selections()` — 대상이 없으면 `KeyError(메시지)`, id 오류는 `BuildError`
  - `entry(p, in_file: set[str], mode: str) -> dict`, `build_data(sel, mode) -> dict` (`{"meta", "problems"}`)

- [ ] **Step 1: 실패하는 테스트를 쓴다**

`workbook/tests/test_assemble.py`:

```python
import json
import sys
import tempfile
import unicodedata
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from assemble import (BuildError, Selection, all_selections, build_data, chapter_selection,  # noqa: E402
                      exam_selection, ids_selection, resolve_target)
from paths import TEMPLATES  # noqa: E402

SAMPLE_IDS = ["P9.05", "X9.13", "P11.39", "X11.01", "E9.01", "E11.18",
              "X9.16", "P9.07", "E11.01", "P10.32", "P9.09", "E9.07"]
MECHANICAL = ["id", "kind", "number", "title", "section", "book_page", "difficulty", "sol",
              "depends_on", "figures"]
CONDITIONS_UNEDITED = {"E9.01", "E11.18", "P9.07", "P10.32", "P9.09", "E9.07"}   # 샘플이 손대지 않은 조건
ASK_EDITED = {"P9.05", "P10.32"}                                                 # 샘플이 손댄 구할 것


def sample(name):
    data = json.loads((TEMPLATES / name).read_text(encoding="utf-8"))
    return data["meta"], {p["id"]: p for p in data["problems"]}


class TestGolden(unittest.TestCase):
    """템플릿 샘플(12문제)을 md에서 다시 만들어 기계적인 필드를 비교한다."""

    @classmethod
    def setUpClass(cls):
        sel = ids_selection(SAMPLE_IDS, "샘플")
        cls.data = build_data(sel, "problems")
        cls.built = {p["id"]: p for p in cls.data["problems"]}
        cls.meta, cls.sample = sample("sample-problem.json")
        cls.answers = build_data(sel, "answers")

    def test_meta_matches_sample(self):
        self.assertEqual(self.data["meta"], self.meta)
        self.assertEqual(self.answers["meta"], sample("sample-answer.json")[0])

    def test_order_follows_ids(self):
        self.assertEqual([p["id"] for p in self.data["problems"]], SAMPLE_IDS)

    def test_mechanical_fields_match_sample(self):
        for pid in SAMPLE_IDS:
            for key in MECHANICAL:
                with self.subTest(pid=pid, key=key):
                    self.assertEqual(self.built[pid][key], self.sample[pid][key])

    def test_conditions_match_where_sample_is_unedited(self):
        for pid in CONDITIONS_UNEDITED:
            with self.subTest(pid=pid):
                self.assertEqual(self.built[pid]["html"]["conditions"], self.sample[pid]["html"]["conditions"])

    def test_ask_matches_where_sample_is_unedited(self):
        for pid in set(SAMPLE_IDS) - ASK_EDITED:
            with self.subTest(pid=pid):
                self.assertEqual(self.built[pid]["html"]["ask"], self.sample[pid]["html"]["ask"])


class TestSelections(unittest.TestCase):
    def test_chapter_book_order(self):
        sel = chapter_selection(9)
        ids = [p.stem for p in sel.paths]
        self.assertEqual((sel.name, sel.title, sel.chapter), ("ch09", "9장 캐스코드 단과 전류 거울", 9))
        self.assertEqual(ids[:4], ["E9.01", "X9.01", "E9.02", "X9.02"])
        self.assertEqual(len(ids), 110)
        first_p = next(i for i, x in enumerate(ids) if x.startswith("P"))
        self.assertTrue(all(x.startswith("P") for x in ids[first_p:]))

    def test_exam_selection(self):
        sel = exam_selection("2021-1_기말")
        self.assertEqual([p.stem for p in sel.paths], [f"Q{n}" for n in range(1, 8)])
        self.assertEqual((sel.name, sel.title, sel.chapter), ("2021-1_기말", "2021-1 기말고사", 0))

    def test_nfd_exam_name(self):
        nfd = unicodedata.normalize("NFD", "2023-1_기말")
        self.assertEqual(exam_selection(nfd).name, "2023-1_기말")
        self.assertEqual(resolve_target(nfd).title, "2023-1 기말고사")

    def test_resolve_target_chapter(self):
        self.assertEqual(resolve_target("ch10").chapter, 10)

    def test_unknown_target(self):
        for target in ("ch99", "2099-1_기말", "foo"):
            with self.subTest(target=target), self.assertRaises(KeyError):
                resolve_target(target)

    def test_ids_selection_errors(self):
        with self.assertRaises(BuildError) as cm:
            ids_selection(["Z1", "P9.99"], "t")
        self.assertEqual(len(cm.exception.errors), 2)

    def test_all_selections(self):
        self.assertEqual([s.name for s in all_selections()],
                         ["ch09", "ch10", "ch11", "2021-1_기말", "2021-1_중간", "2023-1_기말", "2023-1_중간"])


class TestEntries(unittest.TestCase):
    def test_in_file(self):
        alone = build_data(ids_selection(["P9.05"], "t"), "problems")["problems"][0]
        self.assertEqual(alone["depends_on"], [{"id": "E9.01", "in_file": False}])
        both = build_data(ids_selection(["E9.01", "P9.05"], "t"), "problems")["problems"][1]
        self.assertEqual(both["depends_on"], [{"id": "E9.01", "in_file": True}])

    def test_answers_mode(self):
        data = build_data(ids_selection(["E9.01", "P9.05"], "t"), "answers")
        self.assertEqual(data["meta"]["title"], "t 답안")
        e901, p905 = data["problems"]
        self.assertEqual(e901["solution"], {
            "steps": [], "answer": r"$R_{out} \approx 328.9\ \text{k}\Omega$ ($V_T \approx 26\ \text{mV}$, 식 9.10)"})
        self.assertNotIn("solution", p905)
        self.assertTrue(all("original" not in p["html"] for p in data["problems"]))

    def test_exam_entry(self):
        e = build_data(ids_selection(["2023-1_기말-Q1"], "t"), "problems")["problems"][0]
        self.assertEqual((e["kind"], e["number"], e["section"], e["book_page"], e["difficulty"], e["original_lang"]),
                         ("기출", "1", "2023-1 기말고사 · 20점", None, None, "ko"))
        self.assertEqual(len(e["figures"]), 1)

    def test_build_errors_collected(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = []
            for name in ("a.md", "b.md"):
                path = Path(tmp) / name
                path.write_text('---\nid: E9.01\nkind: 예제\nnumber: "9.1"\n---\n본문만\n', encoding="utf-8")
                bad.append(path)
            with self.assertRaises(BuildError) as cm:
                build_data(Selection("bad", "bad", 0, bad), "problems")
        self.assertEqual(len(cm.exception.errors), 2)
        self.assertIn("a.md", cm.exception.errors[0])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 실패를 확인한다**

Run: `python3 -m unittest discover -s workbook/tests 2>&1 | tail -3`
Expected: `ModuleNotFoundError: No module named 'assemble'`

- [ ] **Step 3: 구현한다**

`workbook/assemble.py`:

```python
"""대상(교과서 장, 기출 회차, id 목록) → 문제 md 목록 → 문제집 JSON ({"meta", "problems"}).

JSON 모양은 workbook/templates/*.html 의 #workbook-data 계약(샘플: templates/sample-*.json)을 따른다.
"""
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from paths import EXAMS, TEXTBOOK
from problem import ProblemError, exam_info, figures, hints, html_fields, load_problem, solution

TEXTBOOK_ID_RE = re.compile(r"^([EXP])(\d+)\.(\d{2})$")
EXAM_ID_RE = re.compile(r"^(\d{4}-[12]_(?:중간|기말))-Q([1-9]\d*)$")
EXAM_DIR_RE = re.compile(r"^\d{4}-[12]_(?:중간|기말)$")
EXAM_FILE_RE = re.compile(r"^Q([1-9]\d*)\.md$")
CHAPTER_RE = re.compile(r"^ch(\d{2})$")
KIND_DIR = {"E": "예제", "X": "연습문제", "P": "장말문제"}
MODE_SUFFIX = {"problems": "문제", "answers": "답안"}


class BuildError(Exception):
    def __init__(self, errors):
        super().__init__("\n".join(errors))
        self.errors = errors


@dataclass
class Selection:
    name: str        # 파일 이름 앞부분 (ch09, 2023-1_기말, --name 값)
    title: str       # 문제지 meta.title (답안지는 뒤에 " 답안")
    chapter: int     # 장 번호, 장이 아니면 0
    paths: list


def nfc(s):
    return unicodedata.normalize("NFC", s)


def _book_order(path):
    """예제·연습문제를 번호순으로 섞고(E9.01, X9.01, E9.02 …) 장말문제를 뒤에 둔다."""
    m = TEXTBOOK_ID_RE.match(path.stem)
    kind, number = m.group(1), int(m.group(3))
    return (1, number, 0) if kind == "P" else (0, number, 0 if kind == "E" else 1)


def chapter_selection(ch):
    ch_dir = TEXTBOOK / f"ch{ch:02d}"
    if not ch_dir.is_dir():
        raise KeyError(f"장 폴더 없음: {ch_dir}")
    md_paths = sorted((p for kind in KIND_DIR.values() for p in (ch_dir / kind).glob("*.md")), key=_book_order)
    first = (ch_dir / "README.md").read_text(encoding="utf-8").splitlines()[0]
    title = first.removeprefix("# ").removesuffix(" — 문제 인덱스")
    return Selection(f"ch{ch:02d}", title, ch, md_paths)


def exam_selection(dir_name):
    name = nfc(dir_name)
    exam_dir = EXAMS / name
    if not EXAM_DIR_RE.match(name) or not exam_dir.is_dir():
        raise KeyError(f"기출 폴더 없음: {exam_dir}")
    numbered = [(int(m.group(1)), p) for p in exam_dir.glob("*.md") if (m := EXAM_FILE_RE.match(nfc(p.name)))]
    return Selection(name, exam_info(exam_dir)["exam"], 0, [p for _, p in sorted(numbered)])


def ids_selection(ids, name):
    md_paths, errors = [], []
    for raw in ids:
        pid = nfc(raw.strip())
        if m := TEXTBOOK_ID_RE.match(pid):
            path = TEXTBOOK / f"ch{int(m.group(2)):02d}" / KIND_DIR[m.group(1)] / f"{pid}.md"
        elif m := EXAM_ID_RE.match(pid):
            path = EXAMS / m.group(1) / f"Q{m.group(2)}.md"
        else:
            errors.append(f"id 형식 오류: {pid!r} (예: P9.05, 2023-1_기말-Q1)")
            continue
        if path.exists():
            md_paths.append(path)
        else:
            errors.append(f"문제 파일 없음: {path}")
    if errors:
        raise BuildError(errors)
    return Selection(name, name, 0, md_paths)


def resolve_target(target):
    target = nfc(target)
    if m := CHAPTER_RE.match(target):
        return chapter_selection(int(m.group(1)))
    return exam_selection(target)


def all_selections():
    chapters = sorted(int(m.group(1)) for d in TEXTBOOK.iterdir() if d.is_dir() and (m := CHAPTER_RE.match(d.name)))
    exams = sorted(nfc(d.name) for d in EXAMS.iterdir() if d.is_dir() and EXAM_DIR_RE.match(nfc(d.name)))
    return [chapter_selection(c) for c in chapters] + [exam_selection(e) for e in exams]


def entry(p, in_file, mode):
    m = p.meta
    chapter_end = m["kind"] == "장말문제"
    e = {
        "id": p.id,
        "kind": m["kind"],
        "number": str(m["number"]),
        "title": p.title,
        "section": f'{exam_info(p.path.parent)["exam"]} · {m["points"]}점' if p.is_exam else m["section"],
        "book_page": None if p.is_exam else m["book_page"],
        "difficulty": m.get("difficulty") if chapter_end else None,
        "sol": m.get("sol") if chapter_end else None,
        "original_lang": m.get("source_lang", "en"),
        "depends_on": [{"id": str(d), "in_file": str(d) in in_file} for d in m.get("depends_on") or []],
        "html": html_fields(p),
        "figures": figures(p),
        "hints": hints(p),
    }
    if mode == "answers":
        e["html"].pop("original", None)
        sol = solution(p)
        if sol is not None:
            e["solution"] = sol
    return e


def build_data(sel, mode):
    if mode not in MODE_SUFFIX:
        raise ValueError(f"mode 는 {list(MODE_SUFFIX)} 중 하나: {mode!r}")
    problems, errors = [], []
    for path in sel.paths:
        try:
            problems.append(load_problem(path))
        except ProblemError as e:
            errors.append(f"{path}: {e}")
    in_file = {p.id for p in problems}
    entries = []
    for p in problems:
        try:
            entries.append(entry(p, in_file, mode))
        except ProblemError as e:
            errors.append(f"{p.path}: {e}")
        except KeyError as e:
            errors.append(f"{p.path}: frontmatter 키 누락: {e.args[0]}")
    if errors:
        raise BuildError(errors)
    title = sel.title + (" 답안" if mode == "answers" else "")
    return {"meta": {"mode": mode, "title": title, "chapter": sel.chapter, "total": len(entries)},
            "problems": entries}
```

- [ ] **Step 4: 테스트가 통과하는지 확인한다**

Run: `python3 -m unittest discover -s workbook/tests 2>&1 | tail -3`
Expected: `Ran 50 tests … OK`. 골든 비교가 틀리면 샘플이 아니라 구현을 고친다. 샘플의 기계적인 필드는 md·PNG와 모두 같다는 것을 설계 단계에서 확인했다.

- [ ] **Step 5: 커밋한다**

```bash
git add workbook/assemble.py workbook/tests/test_assemble.py
git commit -m "feat(workbook): assemble workbook json for chapters, exams and id lists

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: `render.py` — 템플릿 주입과 PDF 렌더링

**Files:**
- Create: `workbook/render.py`
- Test: `workbook/tests/test_render.py`

**Interfaces:**
- Consumes: `paths.TEMPLATES`, 테스트에서 `assemble.build_data, ids_selection`
- Produces (Task 7이 씀):
  - `PLACEHOLDER = "__WORKBOOK_DATA__"`, `class RenderError(Exception)`
  - `load_template(mode: str) -> str` — `"problems"` → problem.html, `"answers"` → answer.html
  - `inject(template: str, data: dict) -> str`
  - `render_pdf(html_path: Path, pdf_path: Path, timeout_ms=120_000) -> list[str]` — 넘친 쪽 id 목록

- [ ] **Step 1: playwright를 설치한다**

```bash
pip3 install --user --break-system-packages playwright
python3 -c "import playwright; print('playwright', playwright.__version__)"
```
Expected: 버전이 출력된다(설계 때 dry-run은 1.63.0). `playwright install`은 실행하지 않는다.

- [ ] **Step 2: 실패하는 테스트를 쓴다**

`workbook/tests/test_render.py`:

```python
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from assemble import build_data, ids_selection  # noqa: E402
from render import PLACEHOLDER, RenderError, inject, load_template, render_pdf  # noqa: E402

HAS_PLAYWRIGHT = importlib.util.find_spec("playwright") is not None
SMOKE_IDS = ["E9.01", "P9.05", "2023-1_기말-Q1"]


class TestInject(unittest.TestCase):
    def test_replaces_placeholder(self):
        out = inject(f'<script id="workbook-data">{PLACEHOLDER}</script>', {"a": 1})
        self.assertEqual(out, '<script id="workbook-data">{"a": 1}</script>')

    def test_script_end_in_data_is_escaped(self):
        data = {"html": "</script><!-- $a < b$"}
        out = inject(f"<script>{PLACEHOLDER}</script>", data)
        payload = out[len("<script>"):-len("</script>")]
        self.assertNotIn("<", payload)
        self.assertEqual(json.loads(payload), data)

    def test_template_without_placeholder_rejected(self):
        with self.assertRaisesRegex(RenderError, "자리표시자"):
            inject("<html></html>", {})

    def test_real_templates_accept_data(self):
        for mode in ("problems", "answers"):
            with self.subTest(mode=mode):
                self.assertNotIn(PLACEHOLDER, inject(load_template(mode), {"meta": {}, "problems": []}))


class TestRenderPdf(unittest.TestCase):
    def test_missing_playwright_message(self):
        with patch.dict(sys.modules, {"playwright": None, "playwright.sync_api": None}):
            with self.assertRaises(RenderError) as cm:
                render_pdf(Path("x.html"), Path("x.pdf"))
        self.assertIn("pip3 install", str(cm.exception))


@unittest.skipUnless(HAS_PLAYWRIGHT, "playwright 없음")
class TestRenderSmoke(unittest.TestCase):
    """교과서 예제·장말문제와 기출 하나를 실제 Chrome으로 그린다 (인터넷 필요)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def render(self, mode):
        data = build_data(ids_selection(SMOKE_IDS, "스모크"), mode)
        html_path = self.tmp / f"{mode}.html"
        html_path.write_text(inject(load_template(mode), data), encoding="utf-8")
        pdf_path = self.tmp / f"{mode}.pdf"
        return render_pdf(html_path, pdf_path), pdf_path

    def assert_pdf(self, mode):
        overflow, pdf_path = self.render(mode)
        self.assertEqual(overflow, [])
        with fitz.open(pdf_path) as doc:
            self.assertEqual(doc.page_count, 3)
            self.assertAlmostEqual(doc[0].rect.width, 841.89, delta=1)    # 297mm
            self.assertAlmostEqual(doc[0].rect.height, 595.28, delta=1)   # 210mm

    def test_problems_pdf(self):
        self.assert_pdf("problems")

    def test_answers_pdf(self):
        self.assert_pdf("answers")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: 실패를 확인한다**

Run: `python3 -m unittest discover -s workbook/tests 2>&1 | tail -3`
Expected: `ModuleNotFoundError: No module named 'render'`

- [ ] **Step 4: 구현한다**

`workbook/render.py`:

```python
"""문제집 JSON → 템플릿 HTML → PDF.

템플릿 계약(workbook/templates/*.html): #workbook-data 안의 자리표시자 __WORKBOOK_DATA__ 를 JSON으로 바꾼다.
템플릿은 다 그리면 html[data-ready]를 'true'(실패면 'error')로, body[data-overflow]를 넘친 쪽 id(쉼표)로 둔다.
PDF는 Playwright가 설치된 Google Chrome(channel="chrome")으로 만든다. 템플릿이 CDN 글꼴·KaTeX를 받으므로 인터넷이 필요하다.
"""
import json
from pathlib import Path

from paths import TEMPLATES

PLACEHOLDER = "__WORKBOOK_DATA__"
TEMPLATE_FILES = {"problems": "problem.html", "answers": "answer.html"}
INSTALL_HINT = "pip3 install --user --break-system-packages playwright"
VIEWPORT = {"width": 1400, "height": 1000}   # 화면 배율 1 (템플릿 screenZoom 기준 297mm ≈ 1123px)


class RenderError(Exception):
    pass


def load_template(mode):
    return (TEMPLATES / TEMPLATE_FILES[mode]).read_text(encoding="utf-8")


def inject(template, data):
    """자리표시자를 JSON으로 바꾼다. '<'를 \\u003c로 적어 </script>, <!-- 가 스크립트를 끊지 못하게 한다."""
    count = template.count(PLACEHOLDER)
    if count != 1:
        raise RenderError(f"템플릿의 자리표시자 {PLACEHOLDER} 가 {count}번 있음 (1번이어야 함)")
    payload = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
    return template.replace(PLACEHOLDER, payload)


def render_pdf(html_path, pdf_path, timeout_ms=120_000):
    """HTML을 Chrome으로 열어 다 그려지면 PDF로 저장하고, 넘친 쪽 id 목록을 돌려준다."""
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        raise RenderError(f"playwright가 없음. 설치: {INSTALL_HINT}") from e
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(channel="chrome")
            try:
                page = browser.new_page(viewport=VIEWPORT)
                page.goto(Path(html_path).resolve().as_uri())
                page.wait_for_function("document.documentElement.dataset.ready", timeout=timeout_ms)
                ready, overflow = page.evaluate(
                    "[document.documentElement.dataset.ready, document.body.dataset.overflow || '']")
                if ready != "true":
                    raise RenderError(f"템플릿이 데이터를 그리지 못함 (data-ready={ready!r}): {html_path}")
                page.pdf(path=str(pdf_path), prefer_css_page_size=True, print_background=True)
            finally:
                browser.close()
    except PlaywrightError as e:
        raise RenderError(f"Chrome 렌더링 실패 (Google Chrome 설치와 인터넷 연결 확인): {e}") from e
    return [x for x in overflow.split(",") if x]
```

- [ ] **Step 5: 테스트가 통과하는지 확인한다**

Run: `python3 -m unittest discover -s workbook/tests -v 2>&1 | tail -8`
Expected: `Ran 57 tests … OK`, 그리고 `TestRenderSmoke`의 두 테스트가 skipped가 아니라 ok로 나온다. 스모크가 실패하면 두 가지를 먼저 본다.
- 템플릿 JS 오류: 스모크 HTML을 `open`으로 열어 개발자 도구 콘솔을 확인한다.
- `data-ready='error'` 메시지

- [ ] **Step 6: 스모크 PDF를 눈으로 확인한다**

```bash
SMOKE=$(mktemp -d)
python3 - "$SMOKE" <<'EOF'
import sys
from pathlib import Path

sys.path.insert(0, "workbook")
import fitz
from assemble import build_data, ids_selection
from render import inject, load_template, render_pdf

out = Path(sys.argv[1])
for mode in ("problems", "answers"):
    data = build_data(ids_selection(["E9.01", "P9.05", "2023-1_기말-Q1"], "스모크"), mode)
    html = out / f"{mode}.html"
    html.write_text(inject(load_template(mode), data), encoding="utf-8")
    print(mode, "overflow:", render_pdf(html, out / f"{mode}.pdf"))
    with fitz.open(out / f"{mode}.pdf") as doc:
        for i, page in enumerate(doc):
            page.get_pixmap(dpi=60).save(out / f"{mode}-{i + 1}.png")
print(out)
EOF
```
출력된 폴더의 `problems-1.png`, `problems-3.png`, `answers-1.png`를 Read 도구로 본다. 확인할 것:
- `problems-1.png`(E9.01): 조건에 `회로:` 줄이 없고 그림이 있다. 헤더는 `9.1.1 … · p.451 · 1 / 3`이다.
- `problems-3.png`(기출 Q1): 종류 배지가 보라색 `기출`이다. 헤더는 `2023-1 기말고사 · 20점 · 3 / 3`이고 `p.`가 없다.
- `answers-1.png`: 답 칸에 `328.9 kΩ`이 수식으로 그려져 있다.

- [ ] **Step 7: 커밋한다**

```bash
git add workbook/render.py workbook/tests/test_render.py
git commit -m "feat(workbook): inject data into templates and print pdf with chrome

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: `build_workbook.py` CLI, README, .gitignore

**Files:**
- Create: `workbook/build_workbook.py`
- Create: `workbook/README.md`
- Modify: `.gitignore` (끝에 추가)
- Test: `workbook/tests/test_build.py`

**Interfaces:**
- Consumes: `assemble.MODE_SUFFIX, BuildError, all_selections, build_data, ids_selection, resolve_target, Selection`, `render.RenderError, inject, load_template, render_pdf`, `paths.WORKBOOK`
- Produces: `main(argv: list[str]) -> int`, 모듈 수준 함수 `selections(args)`, `render_pdf`(테스트에서 patch하는 이름)

- [ ] **Step 1: 실패하는 테스트를 쓴다**

`workbook/tests/test_build.py`:

```python
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_workbook  # noqa: E402
from assemble import Selection  # noqa: E402
from render import RenderError  # noqa: E402


class BuildCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.build = Path(self._tmp.name) / "build"
        self.pdf = Path(self._tmp.name) / "pdf"

    def tearDown(self):
        self._tmp.cleanup()

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = build_workbook.main(["build_workbook.py", *argv,
                                        "--build-dir", str(self.build), "--pdf-dir", str(self.pdf)])
        return code, out.getvalue(), err.getvalue()

    def read_json(self, name):
        return json.loads((self.build / name).read_text(encoding="utf-8"))


class TestJsonOnly(BuildCase):
    def test_ids(self):
        code, _, err = self.run_cli("--ids", "E9.01,P9.05", "--name", "t", "--json-only")
        self.assertEqual(code, 0, err)
        for name in ("t-문제.json", "t-문제.html", "t-답안.json", "t-답안.html"):
            self.assertTrue((self.build / name).exists(), name)
        self.assertEqual(self.read_json("t-문제.json")["meta"]["total"], 2)
        self.assertEqual(self.read_json("t-답안.json")["meta"]["title"], "t 답안")
        self.assertFalse(self.pdf.exists())

    def test_chapter(self):
        code, _, err = self.run_cli("ch09", "--json-only")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.read_json("ch09-문제.json")["meta"]["total"], 110)

    def test_all(self):
        code, _, err = self.run_cli("--all", "--json-only")
        self.assertEqual(code, 0, err)
        self.assertEqual(len(list(self.build.glob("*.json"))), 14)


class TestErrors(BuildCase):
    def test_unknown_target_exit_2(self):
        code, _, err = self.run_cli("ch99", "--json-only")
        self.assertEqual(code, 2)
        self.assertIn("ERROR", err)

    def test_bad_id_exit_2(self):
        code, _, err = self.run_cli("--ids", "Z1", "--name", "t", "--json-only")
        self.assertEqual(code, 2)
        self.assertIn("Z1", err)

    def test_target_required_exactly_once(self):
        for argv in ([], ["ch09", "--all"], ["--ids", "E9.01"]):
            with self.subTest(argv=argv), self.assertRaises(SystemExit):
                self.run_cli(*argv)

    def test_md_error_exit_1(self):
        broken = Path(self._tmp.name) / "E9.01.md"
        broken.write_text('---\nid: E9.01\nkind: 예제\nnumber: "9.1"\n---\n본문만\n', encoding="utf-8")
        with patch.object(build_workbook, "selections", return_value=[Selection("bad", "bad", 0, [broken])]):
            code, _, err = self.run_cli("ch09", "--json-only")
        self.assertEqual(code, 1)
        self.assertIn(str(broken), err)

    def test_overflow_exit_1(self):
        with patch.object(build_workbook, "render_pdf", return_value=["P9.05"]):
            code, _, err = self.run_cli("--ids", "E9.01,P9.05", "--name", "t")
        self.assertEqual(code, 1)
        self.assertIn("OVERFLOW t-문제: P9.05", err)
        self.assertIn("OVERFLOW t-답안: P9.05", err)

    def test_render_error_exit_1(self):
        with patch.object(build_workbook, "render_pdf", side_effect=RenderError("크롬 없음")):
            code, _, err = self.run_cli("--ids", "E9.01", "--name", "t")
        self.assertEqual(code, 1)
        self.assertIn("ERROR t: 크롬 없음", err)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 실패를 확인한다**

Run: `python3 -m unittest discover -s workbook/tests 2>&1 | tail -3`
Expected: `ModuleNotFoundError: No module named 'build_workbook'`

- [ ] **Step 3: 구현한다**

`workbook/build_workbook.py`:

```python
#!/usr/bin/env python3
"""문제 md → 문제지·답안지 PDF.

사용법:
  python3 workbook/build_workbook.py ch09                          # 교과서 장 하나 (책 순서)
  python3 workbook/build_workbook.py 2023-1_기말                   # 기출 회차 하나
  python3 workbook/build_workbook.py --ids P9.05,E9.01 --name 샘플  # 고른 문제 (적은 순서)
  python3 workbook/build_workbook.py --all                         # 모든 장과 기출
  옵션: --json-only (PDF 없이 JSON·HTML만), --pdf-dir, --build-dir

결과: workbook/pdf/<이름>-문제.pdf, <이름>-답안.pdf (커밋 대상)
      workbook/build/<이름>-문제.json, .html … (중간 산출물, git 무시)
종료 코드: 0 성공, 1 md 오류·렌더링 실패·쪽 넘침, 2 사용법·대상 오류
"""
import argparse
import json
import sys
from pathlib import Path

import paths
from assemble import MODE_SUFFIX, BuildError, all_selections, build_data, ids_selection, resolve_target
from render import RenderError, inject, load_template, render_pdf


def parse_args(argv):
    ap = argparse.ArgumentParser(prog="build_workbook.py", description="문제 md → 문제지·답안지 PDF")
    ap.add_argument("target", nargs="?", help="ch09 같은 장 폴더 또는 2023-1_기말 같은 기출 폴더")
    ap.add_argument("--ids", help="쉼표로 구분한 문제 id (예: P9.05,E9.01,2023-1_기말-Q1)")
    ap.add_argument("--name", help="--ids 묶음의 이름 (파일 이름과 제목)")
    ap.add_argument("--all", action="store_true", help="모든 장과 기출 회차")
    ap.add_argument("--json-only", action="store_true", help="PDF 없이 JSON·HTML만 만든다")
    ap.add_argument("--pdf-dir", type=Path, default=paths.WORKBOOK / "pdf")
    ap.add_argument("--build-dir", type=Path, default=paths.WORKBOOK / "build")
    args = ap.parse_args(argv[1:])
    if sum([bool(args.target), bool(args.ids), args.all]) != 1:
        ap.error("대상은 target, --ids, --all 중 하나만 준다")
    if args.ids and not args.name:
        ap.error("--ids 에는 --name 이 필요하다")
    return args


def selections(args):
    if args.all:
        return all_selections()
    if args.ids:
        return [ids_selection(args.ids.split(","), args.name)]
    return [resolve_target(args.target)]


def build_one(sel, args):
    """선택 하나를 문제지·답안지로 만든다. 넘친 쪽을 '<파일 이름>: <id>' 목록으로 돌려준다."""
    overflow = []
    for mode, suffix in MODE_SUFFIX.items():
        data = build_data(sel, mode)
        stem = f"{sel.name}-{suffix}"
        args.build_dir.mkdir(parents=True, exist_ok=True)
        (args.build_dir / f"{stem}.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        html_path = args.build_dir / f"{stem}.html"
        html_path.write_text(inject(load_template(mode), data), encoding="utf-8")
        print(html_path)
        if args.json_only:
            continue
        args.pdf_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = args.pdf_dir / f"{stem}.pdf"
        overflow += [f"{stem}: {x}" for x in render_pdf(html_path, pdf_path)]
        print(pdf_path)
    return overflow


def main(argv):
    args = parse_args(argv)
    try:
        sels = selections(args)
    except KeyError as e:
        print(f"ERROR {e.args[0]}", file=sys.stderr)
        return 2
    except BuildError as e:
        for msg in e.errors:
            print(f"ERROR {msg}", file=sys.stderr)
        return 2
    code, overflow = 0, []
    for sel in sels:
        try:
            overflow += build_one(sel, args)
        except BuildError as e:
            for msg in e.errors:
                print(f"ERROR {msg}", file=sys.stderr)
            code = 1
        except RenderError as e:
            print(f"ERROR {sel.name}: {e}", file=sys.stderr)
            code = 1
    for item in overflow:
        print(f"OVERFLOW {item}", file=sys.stderr)
    return 1 if overflow else code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```

- [ ] **Step 4: 테스트가 통과하는지 확인한다**

Run: `python3 -m unittest discover -s workbook/tests 2>&1 | tail -3`
Expected: `Ran 66 tests … OK`

- [ ] **Step 5: README와 .gitignore를 쓴다**

`.gitignore` 끝에 다음을 추가한다.

```
# 문제집 생성기 중간 산출물 (PDF는 workbook/pdf/에 커밋)
workbook/build/
```

`workbook/README.md`:

````markdown
# 문제집 PDF 생성기

문제 md(교과서 `교과서/마이크로전자회로/chNN`, 기출 `from_the_past/md/<회차>`)를 문제지·답안지 PDF로 만든다.
설계는 `docs/superpowers/specs/2026-09-25-workbook-pdf-build-design.md`에 있다.

## 준비
```bash
pip3 install --user --break-system-packages playwright
```
브라우저는 설치된 Google Chrome을 쓴다(`playwright install`은 하지 않는다). 빌드 중에 CDN에서 Pretendard와 KaTeX를 받으므로 인터넷이 필요하다.

## 사용법
```bash
python3 workbook/build_workbook.py ch09                                  # 교과서 장 (책 순서)
python3 workbook/build_workbook.py 2023-1_기말                           # 기출 회차
python3 workbook/build_workbook.py --ids P9.05,E9.01,2023-1_기말-Q1 --name 샘플
python3 workbook/build_workbook.py --all                                 # 모든 장과 기출
```
- `--json-only`: PDF 없이 JSON·HTML만 만든다.
- 결과:
  - `workbook/pdf/<이름>-문제.pdf`, `<이름>-답안.pdf` — 커밋한다. md를 고치면 다시 만들어 함께 커밋한다.
  - `workbook/build/` — JSON·HTML 중간 산출물. git이 무시한다.
- 종료 코드:
  - 0: 성공
  - 1: md 오류(`ERROR` 줄), 렌더링 실패, 쪽 넘침(`OVERFLOW <파일>: <id>` 줄. PDF는 남는다)
  - 2: 사용법·대상 오류

## md에서 PDF로 가는 것
| PDF | md |
|---|---|
| 문제 원문 | `## 원문` (없으면 블록을 숨김) |
| 조건 / 구할 것 | `## 조건` / `## 구할 것`. 문제 그림이 있으면 `- 회로:` 줄은 뺀다. `(원문에 없음)`·`(원문의 …)`·`(보조 출처: …)`도 뺀다 |
| 그림 | frontmatter `figures`의 `role: problem` 그림 (크기 = 픽셀 / dpi × 25.4 mm) |
| Hint 띠 / Hint 쪽 | `## 힌트`의 `### ` 소절 (`> 띠: $…$` 줄이 띠에 보인다) |
| 풀이 / 답 | `## 풀이`의 `### ` 소절, 마지막 `### 답`. 없고 예제면 `## 답 (검증용)` |

절 문법은 `교과서/마이크로전자회로/FORMAT.md`의 '문제집용 절'에 있다.

## 템플릿
- `templates/problem.html`, `templates/answer.html`. 데이터는 `<script id="workbook-data">` 안의 `__WORKBOOK_DATA__` 한 곳에 들어간다.
- 미리보기: `python3 -m http.server -d workbook/templates 8765`를 띄우고 http://localhost:8765/problem.html?data=sample-problem.json 을 연다. 답안지는 `answer.html?data=sample-answer.json`이다.
- 템플릿을 고친 뒤에는 아래 테스트(실제 Chrome 스모크 렌더링 포함)를 돌린다.

## 테스트
```bash
python3 -m unittest discover -s workbook/tests
```
````

- [ ] **Step 6: 실제 CLI로 JSON만 만들어 본다**

```bash
python3 workbook/build_workbook.py ch09 --json-only; echo "exit=$?"
git status --short
```
Expected: `exit=0`. `git status`에 `workbook/build/`가 나오지 않는다(무시됨).

- [ ] **Step 7: 커밋한다**

```bash
git add workbook/build_workbook.py workbook/README.md workbook/tests/test_build.py .gitignore
git commit -m "feat(workbook): add build_workbook cli, readme and ignore build outputs

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 8: 모든 PDF 생성과 커밋

**Files:**
- Create: `workbook/pdf/{ch09,ch10,ch11,2021-1_기말,2021-1_중간,2023-1_기말,2023-1_중간}-{문제,답안}.pdf` (14개)

- [ ] **Step 1: 전부 빌드한다**

```bash
python3 workbook/build_workbook.py --all; echo "exit=$?"
```
Expected: `exit=0`이고 `OVERFLOW`, `ERROR` 줄이 없다.
**넘침이나 오류가 있으면 여기서 멈춘다.** md와 템플릿은 고치지 않는다. 목록을 그대로 사용자에게 보고하고 지시를 기다린다(PDF도 커밋하지 않는다).

- [ ] **Step 2: 쪽 수와 크기를 확인한다**

```bash
python3 - <<'EOF'
from pathlib import Path
import fitz
for p in sorted(Path("workbook/pdf").glob("*.pdf")):
    with fitz.open(p) as d:
        print(f"{p.name}\t{d.page_count}쪽\t{p.stat().st_size / 1e6:.1f}MB")
EOF
```
Expected (지금은 힌트가 없어 답안지에 Hint 쪽이 없으므로 문제지와 답안지의 쪽 수가 같다):
| 이름 | 쪽 |
|---|---|
| ch09 | 110 |
| ch10 | 151 |
| ch11 | 116 |
| 2021-1_기말 | 7 |
| 2021-1_중간 | 5 |
| 2023-1_기말 | 6 |
| 2023-1_중간 | 4 |

파일 하나라도 50MB를 넘으면 멈추고 사용자에게 크기를 보고한다(GitHub의 파일당 한도는 100MB).

- [ ] **Step 3: 몇 쪽을 눈으로 확인한다**

```bash
SHOT=$(mktemp -d)
python3 - "$SHOT" <<'EOF'
import sys
from pathlib import Path
import fitz
out = Path(sys.argv[1])
for name, page in (("ch09-문제", 0), ("ch09-답안", 0), ("ch10-문제", 80), ("ch11-문제", 100), ("2023-1_기말-문제", 0)):
    with fitz.open(f"workbook/pdf/{name}.pdf") as d:
        d[page].get_pixmap(dpi=60).save(out / f"{name}-{page + 1}.png")
print(out)
EOF
```
출력된 폴더의 PNG 다섯 장을 Read 도구로 본다. 확인할 것:
- 수식이 KaTeX로 그려져 있다(`$`가 그대로 보이지 않는다).
- 그림이 보이고, 헤더의 종류 색·번호·쪽 표시가 맞다.
- 기출 쪽은 보라색 배지다.

이상이 있으면 멈추고 보고한다.

- [ ] **Step 4: 커밋한다**

```bash
git add workbook/pdf/*.pdf
git status --short
git commit -m "build: generate problem and answer pdfs for ch09-ch11 and past exams

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```
Expected: `git status`에 `workbook/pdf/`의 PDF 14개만 `A`로 나온다.

- [ ] **Step 5: 전체 테스트를 다시 돌린다**

```bash
python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests 2>&1 | tail -1
python3 -m unittest discover -s from_the_past/md/_tools/tests 2>&1 | tail -1
python3 -m unittest discover -s workbook/tests 2>&1 | tail -1
```
Expected: 세 줄 모두 `OK`(93, 65, 66개).

- [ ] **Step 6: 마무리를 사용자에게 묻는다**

main 병합 방식(ff-merge 또는 rebase+ff), push 여부, worktree 삭제 여부를 묻는다. 옛 템플릿 워크트리 `전자회로2-workbook`(브랜치 `workbook-template`)을 정리할지도 함께 묻는다. 이 계획에서는 그 워크트리를 쓰지 않았고, Downloads 최종본이 그것을 대신한다.
