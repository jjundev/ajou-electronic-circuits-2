# 0918 전류 미러 식 비례식 표기 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 0918 복습노트에서 전류 미러 복사 식을 비례식 `I_copy : I_REF = (W/L)_1 : (W/L)_REF`로 바꾸고, 바로 아래에 대입용 분수형을 한 줄 덧붙인다.

**Architecture:** 정리노트는 HTML이 원본이다. HTML을 고친 다음 `html2md.py`가 `.assets/` md를 다시 만든다(직접 고치지 않는다). 문제설명은 해시로 검증되는 발행물이다. 그래서 `ec2-problem-explain`의 rerender → 조각 수정 → build/check → 재검토 → publish 절차로만 바꾼다.

**Tech Stack:** 정적 HTML + KaTeX 0.16.11 auto-render, Python 3 스크립트(`ec2-review-pack/scripts/check_html.py`, `html2md.py`, `ec2-problem-explain/scripts/epe_cli.py`)

**Spec:** 이 대화에서 확정한 설계("전류 미러 공식을 비례식으로 바꾸기", 결정 #1–#7). 핵심은 아래 Global Constraints에 그대로 옮겼다.

## Global Constraints

- 항 순서는 언제나 **복사 쪽 : 기준 쪽**이다. 예: `I_{copy} : I_{REF} = (W/L)_1 : (W/L)_{REF}`
- 비례식이 주 식이다. 분수형은 바로 뒤에 보조 줄 하나로 둔다. 형태는 `<p class="eq-sub">$\Rightarrow\ I_{copy}=\dfrac{(W/L)_1}{(W/L)_{REF}}\,I_{REF}$</p>` (#6=비례식 + 분수 한 줄)
- `.eq-sub` CSS는 한 규칙만 둔다: 작은 글씨(`var(--fs-label)`), 흐린 색(`var(--ink-2)`), 위 여백 `var(--s1)`
- λ 식: `I_{copy} : I_{REF} = (W/L)_1(1+\lambda V_{DS1}) : (W/L)_{REF}(1+\lambda V_{DS,REF})`
- 두 번 복사(NMOS→PMOS)는 비례식 두 줄(`I_{N1} : I_{REF} = …`, `I_{P1} : I_{N1} = …`)로 쓰고, 보조 줄에는 곱한 분수형 결과 하나를 둔다
- β 보정식 `I_{copy}=I_{REF}/(1+2/β)`(html:1249)는 그대로 둔다
- 범위: 정리노트 HTML(+ 다시 만든 md), 문제설명 1군데(#7). 복습문제 PDF와 SVG 그림은 건드리지 않는다
- `교과서/`, `workbook/`은 건드리지 않는다. 독립화 워크트리 브랜치와 파일이 겹치지 않게 하기 위해서다

## Review Focus

1. **표 셀 안 보조 줄** — 공식표(html:1679–1683)의 `<br>` + 인라인 수식이 html2md 변환 뒤 GFM 표를 깨면 안 된다. Task 1 Step 6의 `--check`와 md 표 행 수 확인으로 막는다.
2. **KaTeX 렌더 오류** — `:`나 `\Rightarrow`가 들어간 식에 빨간 오류 글자가 없어야 한다. Task 1 Step 7의 `.katex-error` 개수 0으로 확인한다.
3. **좁은 화면 넘침** — λ 비례식은 길어서 모바일(375px)에서 가로로 넘칠 수 있다. `.katex-display`가 이미 `overflow-x: auto`라 스크롤로 처리되는지 Task 1 Step 7에서 본다.
4. **본문 문장과 식의 어긋남** — "두 식을 나누면"(549, 679행) 뒤 결과가 비례식으로 바뀌어도 문장이 그대로 자연스러운지 확인한다. 어색하면 "두 식의 비를 쓰면"으로 바꾼다.
5. **다크 모드 대비** — `.eq-sub`의 `--ink-2`가 다크 테마에서도 읽혀야 한다. Task 1 Step 7에서 테마 토글로 본다.

---

### Task 1: 정리노트 비례식 변환

**Files:**
- Modify: `복습노트/0918/정리노트_0918_Current_Mirrors.html`. CSS는 262–266행 근처 `.eq-list` 규칙 옆에 둔다. 식이 있는 줄은 398, 435, 549, 565, 679, 721, 884, 917, 965, 1070, 1087, 1088, 1158, 1179, 1258, 1518, 1519, 1532, 1533, 1679, 1680, 1683이다.
- Regenerate (직접 수정 금지): `복습노트/0918/.assets/정리노트_0918_Current_Mirrors.md`
- Test: 아래 Step 1의 검사 명령

**Interfaces:**
- Produces: CSS 클래스 `.eq-sub`(Task 2에서는 쓰지 않음)

- [ ] **Step 1: 실패하는 검사 작성**

분수형 미러 식이 `eq-sub` 보조 줄 밖에 남아 있으면 실패하는 검사다. scratchpad에 `check_ratio.py`로 저장한다.

```python
import re, sys
html = open(sys.argv[1], encoding="utf-8").read()
FRAC = re.compile(r"d?frac\{(\(W/L\)|I_\{S)")
bad = [i+1 for i, line in enumerate(html.splitlines())
       if FRAC.search(line) and 'class="eq-sub"' not in line]
ratio = len(re.findall(r"I_\{copy\}\s*:\s*I_\{REF\}", html))
print("bare fractions at lines:", bad, "| ratio forms:", ratio)
sys.exit(1 if bad or ratio < 15 else 0)
```

- [ ] **Step 2: 실패 확인**

Run: `python check_ratio.py 복습노트/0918/정리노트_0918_Current_Mirrors.html`
Expected: 종료 코드 1, `bare fractions at lines: [398, 435, …]`

- [ ] **Step 3: `.eq-sub` CSS 한 규칙 추가**

Global Constraints의 값으로 추가한다.

- [ ] **Step 4: 22곳을 비례식 + 보조 줄로 교체**

설계의 교체 규칙 표를 따른다. 섹션별로는 이렇다.
- MOS 기본: 398, 435, 549, 565, 884, 917, 1679
- PMOS: 965, 1087
- λ: 679, 721, 1680
- 두 번 복사: 1070, 1088
- BJT: 1158, 1179, 1258, 1683
- NPN/PNP 연쇄: 1518, 1519, 1532, 1533

`eq-list` 항목에서는 보조 줄 `<p class="eq-sub">`를 같은 `<li>` 안에 둔다. 표 셀에서는 `<br>` 뒤에 `<span class="eq-sub">$…$</span>`로 둔다. 인라인 문장(965, 1258)은 비례식만 쓰고 분수형을 붙이지 않는다. 같은 식의 보조 줄이 바로 위 섹션 요약에 이미 있다. 보조 줄 마크업은 모두 같은 줄에 둬서 Step 1 검사가 줄 단위로 판정할 수 있게 한다.

- [ ] **Step 5: 검사 통과 확인**

Run: `python check_ratio.py 복습노트/0918/정리노트_0918_Current_Mirrors.html`
Expected: `bare fractions at lines: [] | ratio forms: N`(N ≥ 15), 종료 코드 0

- [ ] **Step 6: 구조 검사와 md 다시 만들기**

Run: `python .claude/skills/ec2-review-pack/scripts/check_html.py 복습노트/0918/정리노트_0918_Current_Mirrors.html`
Expected: `OK`

Run: `python .claude/skills/ec2-review-pack/scripts/html2md.py 복습노트/0918/정리노트_0918_Current_Mirrors.html --check`
Expected: `OK`. `.assets/` md와 `fig-why.svg`가 다시 만들어진다. 그다음 md 1211–1215행 근처 공식표가 한 행씩 그대로인지(셀이 쪼개지지 않았는지) 눈으로 확인한다.

- [ ] **Step 7: 브라우저 확인**

내장 브라우저로 HTML을 연다. 아래 JS 결과가 `0`이어야 한다.

`document.querySelectorAll('.katex-error').length`

같은 화면에서 데스크톱과 모바일(375px), 라이트와 다크를 바꿔 가며 확인한다. λ 식이 페이지 가로 스크롤 없이 식 상자 안에서만 스크롤되는지, `.eq-sub`가 읽히는지 본다. 확인한 뒤 viewport는 desktop으로 되돌린다.

- [ ] **Step 8: 커밋**

```bash
git add "복습노트/0918/정리노트_0918_Current_Mirrors.html" "복습노트/0918/.assets/정리노트_0918_Current_Mirrors.md" "복습노트/0918/.assets/figures_0918"
git commit -m "docs(0918): write mirror copy formulas as proportions"
```

---

### Task 2: 문제설명 첫 줄 비례식 변환

**Files:**
- Modify (RUN 안의 조각): `<RUN>/…/fragments/p3.html`. 원본은 `복습노트/0918/.assets/자료_문제설명_0918_Current_Mirrors/fragments/p3.html:3`이다.
- Republished by `epe_cli publish`: `복습노트/0918/문제설명_0918_Current_Mirrors.html`, `.assets/문제설명_0918_Current_Mirrors.md`, `.assets/자료_문제설명_0918_Current_Mirrors/`(manifest·validation 해시 포함)

**Interfaces:**
- Consumes: 없음(Task 1과 독립)

- [ ] **Step 1: 새 RUN으로 rerender**

Run: `python .claude/skills/ec2-problem-explain/scripts/epe_cli.py rerender --repo "<저장소 절대경로>" --target 0918 --run "<scratchpad>/epe-0918-ratio"`
Expected: 종료 코드 0, RUN에 fragments·stage가 생긴다

- [ ] **Step 2: 실패 확인**

Run: `grep -c 'frac{(W/L)_{I1}}' "<RUN>/…/fragments/p3.html"`
Expected: `1`

- [ ] **Step 3: p3 조각의 식 한 줄 교체**

새 식:
`$$(W/L)_{I1} : (W/L)_{REF} = 0.2 : 0.3,\qquad (W/L)_{I2} : (W/L)_{REF} = 0.5 : 0.3$$`

바로 앞 문장 "필요한 비를 써요"는 그대로 둔다. 분수형 보조 줄은 넣지 않는다. 이 식은 이미 크기 비 자체라 대입할 분수형이 따로 없다.

- [ ] **Step 4: build·check 통과 확인**

Run: `python .claude/skills/ec2-problem-explain/scripts/epe_cli.py build --run "<RUN>"` → 이어서 `check --run "<RUN>"`
Expected: 둘 다 종료 코드 0

- [ ] **Step 5: 네 검토 다시 수행**

조각이 바뀌었으므로 `ec2-problem-explain/SKILL.md`의 "레이아웃만 바뀐 기존 발행분 재발행" 규칙에 따라 content·independent·source_visual·browser를 실제로 다시 수행한다. 범위는 p3 문항이고, 나머지는 SKILL 규칙이 허용하는 만큼만 재사용한다. 기대 결과는 네 항목 모두 `pass`다. 하나라도 pass가 아니면 publish하지 않고 멈춰서 보고한다.

- [ ] **Step 6: publish와 결과 확인**

Run: `python .claude/skills/ec2-problem-explain/scripts/epe_cli.py publish --run "<RUN>"`
Expected: 종료 코드 0. 이어서 `grep -c '0.2 : 0.3' 복습노트/0918/문제설명_0918_Current_Mirrors.html`이 `1` 이상이다.

- [ ] **Step 7: 커밋**

```bash
git add "복습노트/0918/문제설명_0918_Current_Mirrors.html" "복습노트/0918/.assets/문제설명_0918_Current_Mirrors.md" "복습노트/0918/.assets/자료_문제설명_0918_Current_Mirrors"
git commit -m "docs(0918): write problem 3 size ratio as a proportion"
```
