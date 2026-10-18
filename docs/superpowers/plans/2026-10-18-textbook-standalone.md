# 교과서 문제 standalone화 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 감사에서 고른 71개 교과서 문제 md를, 문제지에 보이는 부분(원문·조건·구할 것·문제 그림)만으로 풀 수 있게 고친다.

**Architecture:** 각 파일의 `## 상속·참조`(문제지에 안 나옴)에 있는 식·값·정의·앞 문제 결과 중 필요한 최소한을 `## 조건`에 bullet로 **복사**한다. check_md.py에 "조건·구할 것이 상속·참조를 가리키면 오류" 규칙을 더하고 FORMAT.md에 규칙을 적는다. 장마다 검사 → PDF 재생성 → 커밋.

**Tech Stack:** Markdown + LaTeX(KaTeX), Python 3 검사 도구(`교과서/마이크로전자회로/_tools`), 문제집 생성기(`workbook/`, Playwright + Chrome).

**Spec:** `docs/superpowers/specs/2026-10-18-textbook-standalone-design.md` — 파일별 무엇을 넣을지는 `docs/superpowers/reports/2026-10-18-standalone-audit.md`의 `수정` 칸.

## Global Constraints

- 고치는 절은 `## 조건`뿐. `## 원문`, `## 구할 것` 문구, frontmatter, `## 상속·참조`, 넷리스트는 그대로 둔다 (상속·참조는 복사 원천일 뿐, 지우지 않음)
- 새 bullet 형식 (줄 끝 표시는 괄호 하나, 괄호 안에 괄호 금지):
  - 식: `- 식 (9.12): $…$ (본문 식, 원문에 없음)`
  - 기호 정의: `- $\Delta V_{in,max}$: <정의> (본문 정의, 원문에 없음)`
  - 앞 문제 결과: `- 문제 10.46의 결과: $G_m = …$ (원문에 없음)`
  - 본문 회로: `- 참고 회로 (본문 Fig 9.22(a)): <글 설명> (원문에 없음)` — **`- 회로:`로 시작하지 않는다** (문제 그림이 있는 파일에서 PDF에서 빠짐)
  - 앞 문제 가정: `- 문제 9.40에서 이어받는 가정: … (원문에 없음)`
- 새 bullet은 조건에서 그 식·문제·기호를 처음 언급하는 bullet 바로 다음에 둔다
- 조건에 있는 "(아래 상속·참조)" 문구는 지우고 그 자리에 내용을 적는다
- 도구로 쓰는 식·정의는 식까지 준다. 유도 자체가 과제면(P11.26) 결과식과 정의만, 유도 과정은 안 준다
- 해당 문제 자신의 답이나 풀이 단계를 조건에 넣지 않는다
- 식은 같은 파일 `## 상속·참조`의 LaTeX를 그대로 옮긴다. 상속·참조에 없는 P10.78은 `ch10/장말문제/P10.77.md`의 `## 풀이`, P11.52는 `ch11/장말문제/P11.09.md`·`P11.10.md`의 `## 풀이`에서 가져온다
- 쪽이 넘치면(OVERFLOW) 그 파일의 새 bullet에서 설명을 지우고 식만 남긴다. 템플릿은 건드리지 않는다
- 커밋 메시지 끝: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

## Review Focus

1. 새 bullet을 `- 회로:`로 시작 → 문제 그림이 있는 파일에서 PDF에서 조용히 사라짐. 기대: 참고 회로 설명이 문제지에 보임 (Task 6 Step 1 스크립트가 잡음)
2. 표시 괄호 안에 괄호(`(본문 식 (9.12), 원문에 없음)`) → "원문에 없음"이 PDF에 그대로 보임. 기대: 표시가 지워짐 (Task 6 Step 1이 잡음)
3. 식을 추가해 쪽 넘침 → 문제지 한 쪽에 안 들어감. 기대: OVERFLOW 0 (각 장 Task의 build 단계)
4. LaTeX 오타 → KaTeX 렌더 실패. 기대: build 종료 코드 0 (각 장 Task의 build 단계)
5. 골든 샘플 P9.09 조건 변경 → workbook 테스트 실패. 기대: 샘플 갱신 후 통과 (Task 2 Step 4)

---

### Task 1: check_md 규칙 + FORMAT.md

**Files:**
- Modify: `교과서/마이크로전자회로/_tools/check_md.py` (`check_body`, 174행 근처 절 누락 검사 바로 뒤)
- Modify: `교과서/마이크로전자회로/FORMAT.md` (`## 본문 절` 4번 `## 상속·참조` 항목, `**원문에 없는 보충:**` 목록)
- Test: `교과서/마이크로전자회로/_tools/tests/test_check_md.py`

**Interfaces:**
- Produces: `check_body`가 내는 오류 문자열 `f"## {name}: '상속·참조'를 가리키지 않음 (문제지에 나오지 않음) — 필요한 내용을 조건에 적음"` (`name`은 `조건` 또는 `구할 것`)

- [ ] **Step 1: 실패하는 테스트 작성** — `test_check_md.py`에 클래스 추가

```python
class HiddenSectionReferenceTest(unittest.TestCase):
    def run_check(self, text):
        with tempfile.TemporaryDirectory() as t:
            ch = make_chapter(Path(t), {"예제/E9.01.md": text})
            return check_file(ch / "예제/E9.01.md", ch)

    def test_conditions_pointing_to_ref_section_is_error(self):
        text = VALID_MD.replace("- I_C = 1 mA", "- I_C = 1 mA\n- 나머지 조건은 예제 9.1과 같음 (아래 상속·참조)")
        errors, _ = self.run_check(text)
        self.assertTrue(any(e.startswith("## 조건:") and "상속·참조" in e for e in errors), errors)

    def test_ask_pointing_to_ref_section_is_error(self):
        text = VALID_MD.replace("- R_out", "- R_out (상속·참조의 요구)")
        errors, _ = self.run_check(text)
        self.assertTrue(any(e.startswith("## 구할 것:") and "상속·참조" in e for e in errors), errors)

    def test_ref_section_itself_is_ok(self):
        text = VALID_MD.replace("## 회로 — Fig 9.2(a)", "## 상속·참조\n- 예제 9.1 값\n\n## 회로 — Fig 9.2(a)")
        errors, _ = self.run_check(text)
        self.assertEqual(errors, [])
```

- [ ] **Step 2: 실패 확인**

Run: `python3 -m unittest 교과서/마이크로전자회로/_tools/tests/test_check_md.py -k HiddenSection -v` (cwd 저장소 루트)
Expected: 앞의 두 테스트 FAIL, `test_ref_section_itself_is_ok` PASS

- [ ] **Step 3: `check_body`에 규칙 구현** — `split_sections(body)`로 `조건`, `구할 것` 절 내용을 보고 `"상속·참조"`가 들어 있으면 Interfaces의 오류 문자열을 추가

- [ ] **Step 4: 통과 확인**

Run: `python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests`
Expected: 전부 OK

- [ ] **Step 5: 기출 검사가 안 깨지는지 확인** (`check_body`를 `from_the_past/md/_tools/check_exam.py:143`도 씀)

Run: `for d in from_the_past/md/20*/; do python3 from_the_past/md/_tools/check_exam.py "$d"; done` (`_tools` 폴더는 제외)
Expected: 이 변경 전과 같은 결과 (새 "상속·참조" 오류 없음 — 사전 조사에서 기출 0건)

- [ ] **Step 6: FORMAT.md 수정**
  - `## 상속·참조` 항목 첫 하위 bullet로: `- 이 절은 문제지에 나오지 않는다. 학생이 풀 때 필요한 식·값·정의·앞 문제 결과는 \`## 조건\`에도 적는다 (아래 '원문에 없는 보충' 형식). 조건·구할 것에서 이 절을 가리키지 않는다 (\`check_md.py\`가 막음)`
  - `**원문에 없는 보충:**` 목록 끝에 Global Constraints의 새 bullet 형식 다섯 줄과 "`- 회로:`로 시작하지 않음" 한 줄을 옮겨 적는다

- [ ] **Step 7: 커밋**

```bash
git add 교과서/마이크로전자회로/_tools/check_md.py 교과서/마이크로전자회로/_tools/tests/test_check_md.py 교과서/마이크로전자회로/FORMAT.md docs/superpowers/specs/2026-10-18-textbook-standalone-design.md docs/superpowers/plans/2026-10-18-textbook-standalone.md docs/superpowers/reports/2026-10-18-standalone-audit.md
git commit -m "feat(check_md): reject 조건/구할 것 pointing to hidden 상속·참조"
```
(이 시점에 `check_md.py ch10`은 P10.42·P10.56·P10.69·P10.76에서 새 오류를 낸다 — Task 4에서 해소)

---

### Task 2: ch09 22개

**Files:**
- Modify (필수 13): `ch09/예제/E9.02.md`, `E9.16.md`, `ch09/연습문제/X9.02.md`, `ch09/장말문제/P9.09.md`, `P9.13.md`, `P9.21.md`, `P9.26.md`, `P9.28.md`, `P9.35.md`, `P9.36.md`, `P9.37.md`, `P9.41.md`, `P9.45.md`
- Modify (권장 9): `ch09/연습문제/X9.07.md`, `ch09/장말문제/P9.06.md`, `P9.18.md`, `P9.30.md`, `P9.31.md`, `P9.38.md`, `P9.39.md`, `P9.43.md`, `P9.57.md`
- Modify: `workbook/templates/sample-problem.json` (P9.09 `html.conditions`만)
- Modify: `workbook/pdf/ch09-문제.pdf`, `workbook/pdf/ch09-답안.pdf` (재생성)

(경로 앞 `교과서/마이크로전자회로/` 생략)

**Interfaces:**
- Consumes: Task 1의 check_md 규칙

- [ ] **Step 1: 필수 13개 조건 수정** — 감사 보고서 각 행의 `수정` 칸대로, Global Constraints 형식으로. 특이 사항:
  - E9.16: 폴로어 구조(본문 Fig 9.32)를 `- 참고 회로 (본문 Fig 9.32):` 글 설명으로. Fig 9.33은 answer 그림이라 문제 그림으로 넣지 않음
  - P9.21, P9.28, P9.35–P9.37: 문제 그림이 없으므로 식 bullet + 참고 회로 bullet 둘 다
  - P9.41, P9.45: `- 문제 9.40에서 이어받는 가정:` / `- 문제 9.44에서 이어받는 가정:`
- [ ] **Step 2: 권장 9개 조건 수정** — 같은 방식. X9.07은 `- $G_m$: …` 정의 bullet
- [ ] **Step 3: 검사**

Run: `python3 교과서/마이크로전자회로/_tools/check_md.py 교과서/마이크로전자회로/ch09 && python3 교과서/마이크로전자회로/_tools/verify_chapter.py 교과서/마이크로전자회로/ch09`
Expected: 오류 0

- [ ] **Step 4: 골든 샘플 갱신** — P9.09는 `workbook/tests/test_assemble.py:18` `CONDITIONS_UNEDITED`에 있음. `sample-problem.json`에서 id `P9.09` 항목의 `html.conditions`만 새로 빌드한 값으로 바꾼다 (다른 키·다른 문제는 그대로):

```bash
python3 -c "import sys,json; sys.path.insert(0,'workbook'); from assemble import ids_selection,build_data; print(json.dumps(build_data(ids_selection(['P9.09'],'x'),'problems')['problems'][0]['html']['conditions'],ensure_ascii=False))"
```
Run: `python3 -m unittest discover -s workbook/tests`
Expected: OK

- [ ] **Step 5: PDF 재생성**

Run: `python3 workbook/build_workbook.py ch09`
Expected: 종료 코드 0, `OVERFLOW` 줄 없음. 넘치면 Global Constraints대로 줄이고 다시

- [ ] **Step 6: 커밋**

```bash
git add 교과서/마이크로전자회로/ch09 workbook/templates/sample-problem.json workbook/pdf/ch09-문제.pdf workbook/pdf/ch09-답안.pdf
git commit -m "fix(ch09): make 22 problems standalone by restating referenced eqs/conditions"
```

---

### Task 3: ch10·ch11 예제·연습문제 19개

**Files:**
- Modify (필수 7): `ch10/예제/E10.17.md`, `E10.20.md`, `E10.21.md`, `E10.27.md`, `ch10/연습문제/X10.17.md`, `X10.20.md`, `X10.27.md`
- Modify (권장 12): `ch10/예제/E10.04.md`, `E10.08.md`, `E10.19.md`, `E10.28.md`, `ch10/연습문제/X10.04.md`, `X10.08.md`, `X10.21.md`, `X10.28.md`, `ch11/예제/E11.21.md`, `E11.25.md`, `ch11/연습문제/X11.14.md`, `X11.25.md`
- Modify: `workbook/pdf/ch10-*.pdf`, `workbook/pdf/ch11-*.pdf`

- [ ] **Step 1: 필수 7개 수정.** 특이 사항:
  - E10.17, X10.17: 예제 10.16 설계값($V_{DD} = 1.8\ \text{V}$, 출력 CM $1.6\ \text{V}$, $R_D = 360\ \Omega$, $I_{SS} = 1.11\ \text{mA}$)을 `- 예제 10.16의 설계:` bullet로
  - E10.20, X10.20: `- $\Delta V_{in,max}$:` 정의 bullet
  - E10.27, X10.27: `- $A_{CM-DM}$:` 정의 bullet (공통 모드 입력 변화 → 차동 출력 이득)
- [ ] **Step 2: 권장 12개 수정.** E10.04/08/19, X10.04/08, E11.21은 "본문 Fig N"을 `- 참고 회로 (본문 Fig N):` 글 설명으로. E11.25, X11.25는 `- 예제 11.18의 결과:` (이득 $22\ \text{dB}$, $-3\ \text{dB}$ 대역폭 약 $250\ \text{MHz}$, 극점 위치 — E11.18.md `## 답 (검증용)`·`## 풀이`에서 그대로)
- [ ] **Step 3: 검사** — `check_md.py`와 `verify_chapter.py`를 ch10, ch11에 실행. Expected: ch11 오류 0, ch10은 P10.42·P10.56·P10.69·P10.76의 "상속·참조" 오류 4건만 (Task 4에서 해소)
- [ ] **Step 4: PDF 재생성** — `python3 workbook/build_workbook.py ch10` / `ch11`. Expected: 종료 코드 0, OVERFLOW 없음
- [ ] **Step 5: 커밋** — `fix(ch10,ch11): make 19 examples/exercises standalone`

---

### Task 4: ch10 장말문제 17개

**Files:**
- Modify (필수 11): `ch10/장말문제/P10.19.md`, `P10.20.md`, `P10.21.md`, `P10.22.md`, `P10.42.md`, `P10.43.md`, `P10.45.md`, `P10.46.md`, `P10.48.md`, `P10.65.md`, `P10.84.md`
- Modify (권장 6): `P10.27.md`, `P10.28.md`, `P10.56.md`, `P10.69.md`, `P10.76.md`, `P10.78.md`
- Modify: `workbook/pdf/ch10-*.pdf`

- [ ] **Step 1: 필수 11개 수정.** 특이 사항:
  - P10.20, P10.22, P10.43, P10.45, P10.46, P10.48: 문제 그림이 없으므로 식 bullet + `- 참고 회로 (본문 Fig 10.14 또는 10.31):` 글 설명
  - P10.42: "(아래 상속·참조)" 문구를 예제 10.16 사양(이득 $5$, 전력 $2\ \text{mW}$, 출력 CM $\ge 1.6\ \text{V}$, $\mu_n C_{ox} = 100\ \mu\text{A/V}^2$, $\lambda = 0$)으로 바꿈. 예제 10.16의 풀이 단계($I_{SS}$, $R_D$, $W/L$ 값)는 넣지 않음 — 이 문제의 풀이 경로
  - P10.48: `- 문제 10.46의 결과:` $G_m$ 식 (P10.46.md `## 풀이` `### 답`)
- [ ] **Step 2: 권장 6개 수정.** P10.56, P10.69, P10.76은 "(아래 상속·참조)"를 내용으로 바꿈. P10.78은 `- 문제 10.77의 결과:` (P10.77.md `## 풀이` `### 답`의 $R_{out}$)
- [ ] **Step 3: 검사** — `check_md.py`·`verify_chapter.py` ch10. Expected: 오류 0
- [ ] **Step 4: PDF 재생성** — `python3 workbook/build_workbook.py ch10`. Expected: 종료 코드 0, OVERFLOW 없음
- [ ] **Step 5: 커밋** — `fix(ch10): make 17 end-of-chapter problems standalone`

---

### Task 5: ch11 장말문제 13개

**Files:**
- Modify (필수 11): `ch11/장말문제/P11.15.md`, `P11.26.md`, `P11.27.md`, `P11.28.md`, `P11.29.md`, `P11.30.md`, `P11.31.md`, `P11.32.md`, `P11.39.md`, `P11.40.md`, `P11.52.md`
- Modify (권장 2): `P11.41.md`, `P11.49.md`
- Modify: `workbook/pdf/ch11-*.pdf`

- [ ] **Step 1: 필수 11개 수정.** 특이 사항:
  - P11.26: 유도가 과제 → `- 식 (11.52):` 결과식 + `- $f_T$:` 정의(출력을 교류 접지했을 때 전류 이득이 1이 되는 주파수)만. 유도 과정은 넣지 않음
  - P11.27–P11.32: `- 식 (11.52): $2\pi f_T \approx g_m/C_\pi$` (MOS 쪽은 $C_{GS}$). P11.29–P11.32는 `- 식 (11.183) (문제 11.28의 결과):`와 `- 식 (11.184):`도
  - P11.39, P11.40: `- 식 (11.73)–(11.75):` 전달 함수 + 기호 대응 ($R_{Thev}$, $C_{in}$, $C_{XY}$, $C_{out}$, $R_L$)
  - P11.52: P11.9의 가정(채널 길이 변조와 다른 커패시턴스 무시)과 P11.10의 결과(전달 함수, 겹친 두 극점의 $-3\ \text{dB}$ 대역폭)를 P11.09.md·P11.10.md `## 풀이`에서
  - P11.39는 골든 샘플(`SAMPLE_IDS`)이지만 조건은 비교 대상이 아님 — 구할 것은 고치지 않는다
- [ ] **Step 2: 권장 2개 수정.** P11.41 `- 문제 11.40의 결과:`, P11.49 `- 참고 회로 (본문 Fig 11.50(a)):`
- [ ] **Step 3: 검사** — `check_md.py`·`verify_chapter.py` ch11, `python3 -m unittest discover -s workbook/tests`. Expected: 오류 0, OK
- [ ] **Step 4: PDF 재생성** — `python3 workbook/build_workbook.py ch11`. Expected: 종료 코드 0, OVERFLOW 없음
- [ ] **Step 5: 커밋** — `fix(ch11): make 13 end-of-chapter problems standalone`

---

### Task 6: 전체 검증

**Files:** 없음 (검증만. 실패하면 해당 장 Task로 돌아가 고치고 그 Task의 검사·build·커밋을 다시)

- [ ] **Step 1: 문제지에 보이는 글 확인** — 71개를 `--json-only`로 빌드하고 `problems[].html.conditions + ask`를 검사하는 일회성 스크립트(scratchpad, 커밋 안 함)를 돌린다:
  - 감사 보고서에서 유형에 EQ가 있는 행: `참조` 칸의 `식 9.12`마다 보이는 글에 `식 (9.12):`가 있어야 한다 (P11.39·P11.40은 `식 (11.73)`, P11.41은 `식 (11.80)`, `그림 …`·`문제 …` 항목은 건너뜀)
  - 71개 전부: 보이는 글에 `원문에 없음`, `상속·참조`가 없어야 한다 (Review Focus 1·2)
  - 새로 쓴 `- 참고 회로` bullet이 보이는 글에 남아 있어야 한다 (md에 `참고 회로`가 있으면 html에도 있음)

Run: `python3 workbook/build_workbook.py --ids <71개 id 쉼표> --name standalone-check --json-only` 후 스크립트 실행
Expected: 위반 0건

- [ ] **Step 2: 재감사** — 서브에이전트 하나에 `docs/superpowers/specs/2026-10-18-textbook-standalone-design.md`의 판정 기준(문제지에 보이는 것만으로 풀 수 있는가)과 71개 파일 목록을 주고 다시 판정. Expected: 필수·권장 0건. 남은 건은 해당 장 Task에서 고침
- [ ] **Step 3: 전체 테스트**

Run: `python3 -m unittest discover -s workbook/tests && python3 -m unittest discover -s 교과서/마이크로전자회로/_tools/tests`
Expected: OK
