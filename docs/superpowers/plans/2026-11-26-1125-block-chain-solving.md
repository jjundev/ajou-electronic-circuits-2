# 1125 정리노트 풀이 방식 전환 및 개인 풀이 명세 갱신 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `복습노트/1125/정리노트_1125_Analog_Filters.html`의 예제 III·IV(C-V·C-C 귀환) 본문을 연쇄 이득 곱·로딩 치환·테브난 변환·부하 기준 접지 연결·직접 기호 전류 분배 중심으로 자연스럽게 교체하고, 동반 `.assets` MD·SVG 동기화 및 개인 풀이 명세(`.claude/skills/ec2-review-pack/references/solution-style.md`) 등록과 근거 기록까지 완료한다.

**Architecture:** 기존 단일 HTML 정리노트의 2·3장(`#s1`, `#s2`)과 5장 요약 표(`#s4-cheatsheet`) 내부 텍스트·수식·인라인 SVG만 제자리에서 수정하고, 기존 파이프라인(`check_html.py`, `html2md.py --check`, `layout_probe.py`)으로 동반 마크다운·독립 SVG·레이아웃을 검증한다. 이어서 개인 풀이 명세는 기존 13개 규칙 ID(`UNIT-01`~`FREQ-01`)를 그대로 유지한 채 상위 우선순위와 관련 규칙 본문만 확장하고 `docs/learning/solution-style-updates/`에 추적 기록을 남긴다.

**Tech Stack:** Static HTML5 + KaTeX + Inline SVG (Pretendard 600), Python 3 (`check_html.py`, `html2md.py`, `layout_probe.py`, `workbook/learning_style.py`), pytest.

**Spec:** 대화에서 `/grill-yourself`로 확정된 설계(`#1=C`, `#5=A` 확정, 나머지 `#2~#4, #6~#9` 확정).

## Global Constraints

- 메타 표현 금지: "내가 필기한 풀이", "필기 방식", "다른 풀이" 같은 메타 문구나 별도 보충 박스를 넣지 않고 정식 본문 설명 자체를 자연스럽게 교체한다.
- 기존 토픽 `id` 불변: `#why-circuit`, `#s1-cv-ideal`, `#s1-cv-open`, `#s1-cv-io`, `#s1-cv-closed`, `#s2-cc-break`, `#s2-cc-gain`, `#s2-cc-io`, `#s2-cc-closed`, `#s4-cheatsheet` 앵커 ID를 바꾸지 않는다.
- 기존 인터랙티브 위젯 2종(`#widget-s1-cv-closed`, `#widget-ccio`), 교수님 말씀·꼭 기억해요·확인 질문 구조, 1장(`#s0`)·4장(`#s3`) 본문은 보존한다.
- SVG 표기 규격(`NOTATION-01`, `CIRCUIT-02`): 생성·수정 SVG 라벨은 `<text class="fig-text fig-math">`와 `<tspan baseline-shift="sub" font-size="78%">`로 Pretendard 600 정체를 유지하고, 일반 라벨은 도선과 최소 `0.6em`, 회로 위치 기호(`fig-loc` `㉠㉡㉢㉣`)는 최소 `0.25em` 간격을 둔다.
- 위치 기호 짝(`check_html.py:401-405`): 각 토픽의 `figure.circuit` 안 `.fig-loc` 집합과 본문 `.loc` 집합이 정확히 일치해야 한다.
- 수학적 정확성(`CORRECT-01`): 1125 필기 4쪽 메모에서 빠진 PMOS $M_2$의 음수 부호는 보정해 $I^*=-g_{m2}V_X$와 $A_{I,open}<0$, $KA_{I,open}>0$을 유지한다.
- 제외 파일 불변: `확인문제_1125_Analog_Filters.html`, `문제설명_1125_Analog_Filters.html`, `복습문제_1125_Analog_Filters-*.pdf`, 과거 발행물의 검토 승인·해시는 수정하지 않는다.
- `solution-style.md` 시작 SHA-256은 `87746aa5d127893bd5f5ce10a8804d44f3e05bd687c93664e050289b2ff3945a`이며, 기존 13개 규칙 ID(`UNIT-01`, `CALC-01`, `CALC-02`, `CIRCUIT-01`, `CIRCUIT-02`, `GAIN-01`, `DEGEN-01`, `SCALE-01`, `BIAS-01`, `NOTATION-01`, `EXPLAIN-01`, `CORRECT-01`, `FREQ-01`)를 추가·삭제·개명하지 않는다.

## Review Focus

1. **모바일(375px) display 수식 가로 넘침**: `#s1-cv-ideal`/`#s1-cv-open`의 3인자 연쇄 곱 식이나 `#s2-cc-gain`의 테브난·분배 식이 한 줄로 길어져 `375px` 폭에서 `.katex-display` overflow가 발생하면 안 된다 → Task 1·2에서 긴 식을 단계별 행 또는 `aligned`로 줄바꿈하고, Task 3의 `layout_probe.py --widths 1280,375`로 `overflow` 0건을 검증한다.
2. **SVG 라벨–도선 간격(`< 0.6em`) 및 `㉠㉡㉢㉣` 불일치**: `fig-circuit-s1-cv-ideal`에 `V_out`, `fig-circuit-s2-cc-gain`에 `I*`/`I'`, `fig-circuit-s2-cc-k`에 `I_out`/`I_F`를 넣을 때 도선과 겹치거나 `.fig-loc`↔`.loc` 짝이 깨지면 안 된다 → Task 1·2에서 `check_html.py` 통과를 확인하고, Task 3의 `layout_probe.py`로 `label_gaps` 0건을 검증한다.
3. **PMOS 둘째 단 부호 누락으로 인한 음의 귀환 모순**: `#s2-cc-gain`에서 $I^*=-g_{m2}V_X$의 `-`가 빠지면 $A_{I,open}>0$이 되어 `#s2-cc-closed`의 $K<0 \Rightarrow KA_{I,open}>0$ 설명과 모순된다 → Task 2에서 본문·수식·예시 수치(`-46.07`) 일치 검증, Task 4 `CORRECT-01`에 보정 근거 기록.
4. **내부 앵커 깨짐 및 구 문구("전류 분배 두 번") 잔존**: `#s2-cc-gain` 제목을 바꿀 때 `id="s2-cc-gain"`이 바뀌면 `확인문제_1125_Analog_Filters.html` 링크가 깨지고, `#why-circuit`·`#s2-cc-closed`·`#s4-cheatsheet`의 링크 텍스트나 표에 구 문구가 남으면 본문과 충돌한다 → Task 2에서 4곳 일괄 동기화 후 `grep` 및 `check_html.py`(정리노트+확인문제 동시 검사)로 검증.
5. **`solution-style.md` 규칙 ID 오염·상대 링크 오기·미관련 파일 변경**: 새 `### NAME-01` 헤더를 만들거나 상대 링크 경로가 틀리면 `workbook/learning_style.py` 또는 문서 추적이 깨진다 → Task 4에서 `read_style(Path('.'))` 13개 ID 검증, `pytest workbook/tests/test_learning_style.py -q`, 상대 링크 실존 확인, `git status`로 변경 파일 집합 확인.

---

## File Structure

- Modify: `복습노트/1125/정리노트_1125_Analog_Filters.html` — 예제 III(`#s1`)·예제 IV(`#s2`)·링크(`#why-circuit`)·요약 표(`#s4-cheatsheet`)의 본문·수식·인라인 SVG 교체
- Regenerate: `복습노트/1125/.assets/정리노트_1125_Analog_Filters.md` 및 `복습노트/1125/.assets/figures_1125/*.svg` — `html2md.py`로 HTML과 1:1 동기화
- Modify: `.claude/skills/ec2-review-pack/references/solution-style.md` — 기존 13규칙 ID 유지, 상위 우선순위 및 `CIRCUIT-01`/`CIRCUIT-02`/`GAIN-01`/`DEGEN-01`/`NOTATION-01`/`CORRECT-01` 확장
- Create: `docs/learning/solution-style-updates/2026-11-26-block-chain-solving.md` — 1125 필기 5쪽 관찰·비교표·확정 선호·대수 동치 검산·전후 SHA-256 기록

---

### Task 1: 예제 III (C-V 귀환) 본문·수식·SVG 전환

**Files:**
- Modify: `복습노트/1125/정리노트_1125_Analog_Filters.html:498-553`

**Interfaces:**
- Consumes: 기존 `#s1` 토픽 ID(`s1-cv-ideal`, `s1-cv-open`, `s1-cv-io`, `s1-cv-closed`), 기존 수치 예시($g_{m1}=2\ \mathrm{mS}$, $R_D=5\ \mathrm{k\Omega}$, $g_{m2}=4\ \mathrm{mS}$, $R_L=0.5\ \mathrm{k\Omega}$, $R_M=1\ \mathrm{k\Omega}$), 기존 위젯 `#widget-s1-cv-closed`
- Produces: 연쇄 이득 곱·$R_L\to(R_L+R_M)$ 치환·레이저 기준 접지 연결 직렬 판정·폐루프 배율 관점이 반영된 `#s1` 4개 토픽과 갱신된 SVG(`fig-circuit-s1-cv-ideal`, `fig-s1-cv-series`, 필요 시 `fig-circuit-s1-cv-open`)

- [ ] **Step 1: `#s1-cv-ideal`([L499-L510](file:///Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/복습노트/1125/정리노트_1125_Analog_Filters.html#L499-L510))의 회로 SVG와 1·2단 유도 교체**

  - `fig-circuit-s1-cv-ideal`: $M_2$ 소스 노드(`cx="204" cy="100"` 또는 `R_L` 위쪽 접속점 `cx="204" cy="126"`)에 노드 점(`data-node="vout" data-node-color="blue"`)과 `V_out` 라벨(도선·`I_out`·`M_2`·`㉢`과 겹치지 않게 왼쪽 `x="192"` 부근, `text-anchor="end"`, 도선과 최소 `0.6em` 간격)을 추가하고 `aria-label`·`figcaption`에 $M_2$ 소스 노드 $V_{out}$을 자연스럽게 반영한다. `㉠㉡㉢` 마크는 그대로 유지한다.
  - 첫 단([L506](file:///Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/복습노트/1125/정리노트_1125_Analog_Filters.html#L506)): $I_{D1}=g_{m1}(0-V_{in})$, $V_X=-I_{D1}R_D$ 연립 단계를 제거하고, `㉠` 게이트가 접지된 공통 게이트 단의 기본 전압 이득 $\frac{V_X}{V_{in}}=g_{m1}R_D$(`㉡` 노드 $X$ 출력)를 바로 제시한다.
  - 둘째 단([L507](file:///Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/복습노트/1125/정리노트_1125_Analog_Filters.html#L507)): $I_{out}=g_{m2}(V_X-I_{out}R_L)$ 연립 전개를 제거하고, `㉢` 부하 $R_L$ 위쪽 소스 전압을 $V_{out}$으로 두어 연쇄 곱으로 전개한다(모바일 375px 넘침을 막기 위해 긴 식은 단계별 행 또는 `aligned`로 줄바꿈):
    1. $\frac{I_{out}}{V_{in}}=\frac{V_X}{V_{in}}\cdot\frac{I_{out}}{V_X}=\frac{V_X}{V_{in}}\cdot\frac{V_{out}}{V_X}\cdot\frac{1}{R_L}$ (부하 $R_L$에서 $I_{out}=V_{out}/R_L$)
    2. $\frac{V_{out}}{V_X}=\frac{R_L}{1/g_{m2}+R_L}$ (소스 팔로워의 전압 이득)
    3. $\begin{aligned}\frac{I_{out}}{V_{in}}&=(g_{m1}R_D)\cdot\frac{R_L}{1/g_{m2}+R_L}\cdot\frac{1}{R_L}\\&=\frac{g_{m1}R_D}{1/g_{m2}+R_L}\end{aligned}$ ($R_L$ 약분)
  - 페이지 요약(`.sum`)의 핵심 식은 기존 $\frac{V_X}{V_{in}}=g_{m1}R_D$와 $\frac{I_{out}}{V_X}=\frac{1}{1/g_{m2}+R_L}$(또는 $\frac{V_{out}}{V_X}$ 연계 설명)을 유지한다.

- [ ] **Step 2: `#s1-cv-open`([L512-L524](file:///Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/복습노트/1125/정리노트_1125_Analog_Filters.html#L512-L524))의 로딩 유도 교체**

  - 출력 쪽 복제([L520](file:///Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/복습노트/1125/정리노트_1125_Analog_Filters.html#L520)): $I_{out}=g_{m2}[V_X-I_{out}(R_L+R_M)]$을 처음부터 다시 세워 이항하는 4단계를 제거한다.
  - 대신 `㉡` 출력 쪽 복제 $R_M$이 $R_L$ 아래에 직렬로 붙어 `㉢` $M_2$ 소스에서 접지까지 총 저항이 $R_L$에서 $(R_L+R_M)$으로 바뀌므로, **이상적 식의 $R_L$ 자리에 $(R_L+R_M)$을 그대로 치환**하는 2~3단계로 전개한다:
    1. $R_L \to R_L+R_M$ (직렬 로딩 저항 반영, $I_{out}=V_{out}/(R_L+R_M)$)
    2. $\begin{aligned}\left.\frac{I_{out}}{V_{in}}\right|_{open}&=(g_{m1}R_D)\cdot\frac{R_L+R_M}{1/g_{m2}+R_L+R_M}\cdot\frac{1}{R_L+R_M}\\&=\frac{g_{m1}R_D}{R_L+R_M+1/g_{m2}}\end{aligned}$ ($(R_L+R_M)$ 약분)
  - 물리 직관("$R_M$이 직렬로 더해지면 소스 전압이 더 올라가 $V_{GS2}$와 전류가 줄어요")과 기존 교수님 말씀·꼭 기억해요·확인 질문·`㉠㉡㉢` 짝을 그대로 유지한다.

- [ ] **Step 3: `#s1-cv-io`([L526-L537](file:///Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/복습노트/1125/정리노트_1125_Analog_Filters.html#L526-L537))의 출력 임피던스 설명·ELI5 SVG 교체**

  - ELI5 문단([L527](file:///Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/복습노트/1125/정리노트_1125_Analog_Filters.html#L527))과 `fig-s1-cv-series`([L528](file:///Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/복습노트/1125/정리노트_1125_Analog_Filters.html#L528)): "레이저 양단에서 위로는 접지까지 $1/g_{m2}$, 아래로는 접지까지 $R_M$이 보이고, 두 접지는 같은 교류 접지라 한 선으로 이어지므로 둘은 직렬"이라는 설명과 세로 배치 도식(`접지 — 1/g_m2 (0.25 kΩ) — [레이저] — R_M (1 kΩ) — 접지` + 왼쪽에 위·아래 접지를 잇는 강조색 호 `같은 접지로 연결` + `직렬 합 1.25 kΩ`)으로 교체한다. `aria-label`과 `figcaption`도 새 그림에 맞춘다.
  - 출력 임피던스 본문([L532](file:///Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/복습노트/1125/정리노트_1125_Analog_Filters.html#L532)): `fig-circuit-s1-cv-rout`와 `㉢㉣`은 유지하되, $V_{S2}=I_X/g_{m2}$, $V_F=-I_XR_M$, $V_X=V_{S2}-V_F$ 노드 방정식 4단계를 제거하고, 레이저($R_L$) 자리 양단에서 위쪽(`㉢` $M_2$ 소스→접지: $1/g_{m2}$)과 아래쪽(`㉣` 출력 쪽 복제→접지: $R_M$)의 두 교류 접지가 하나로 연결되므로 곧바로 $R_{out,open}=1/g_{m2}+R_M$이 됨을 간결하게 설명한다.

- [ ] **Step 4: `#s1-cv-closed`([L545](file:///Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/복습노트/1125/정리노트_1125_Analog_Filters.html#L545))에 폐루프 배율 관점 정리 추가**

  - 세 폐루프 식 아래 설명에 "폐루프 이득은 개루프 이득의 $\frac{1}{1+K(I_{out}/V_{in})|_{open}}$배로 줄고, 입력과 출력 임피던스는 모두 $[1+K(I_{out}/V_{in})|_{open}]$배로 커져요"를 자연스럽게 반영한다. 기존 위젯·수치·예시는 그대로 유지한다.

- [ ] **Step 5: Task 1 검증 실행**

  Run:
  ```bash
  python3 .claude/skills/ec2-review-pack/scripts/check_html.py 복습노트/1125/정리노트_1125_Analog_Filters.html
  ! grep -nE "I_\{D1\}=g_\{m1\}|g_\{m2\}\(V_X-I_\{out\}|g_\{m2\}\[V_X-I_\{out\}|V_\{S2\}=I_X/g_\{m2\}|필기한|필기 방식" 복습노트/1125/정리노트_1125_Analog_Filters.html
  grep -nE "V_\{out\}/V_X|R_L\+R_M" 복습노트/1125/정리노트_1125_Analog_Filters.html | head -n 20
  ```
  Expected: `check_html.py` 출력 `OK`, 첫 `grep` 미일치(exit 0), 둘째 `grep`에서 새 연쇄/치환 식 확인.

- [ ] **Step 6: Commit**

  ```bash
  git add 복습노트/1125/정리노트_1125_Analog_Filters.html
  git commit -m "docs(1125): rewrite Ex. III C-V feedback note using chain gain, substitution, and ground-loop view"
  ```

---

### Task 2: 예제 IV (C-C 귀환) 본문·수식·SVG 전환 및 크로스 링크·치트시트 동기화

**Files:**
- Modify: `복습노트/1125/정리노트_1125_Analog_Filters.html:441,567-610,655`

**Interfaces:**
- Consumes: Task 1의 `#s1-cv-io` 접지 연결 직렬 설명 톤, 기존 `#s2` 토픽 ID(`s2-cc-break`, `s2-cc-gain`, `s2-cc-io`, `s2-cc-closed`), 기존 수치 예시($g_{m1}=2\ \mathrm{mS}$, $R_D=10\ \mathrm{k\Omega}$, $g_{m2}=5\ \mathrm{mS}$, $r_{O2}=50\ \mathrm{k\Omega}$, $R_L=1\ \mathrm{k\Omega}$, $R_F=10\ \mathrm{k\Omega}$, $R_M=1\ \mathrm{k\Omega}$, $A_{I,open}\approx-46.07$, $K=-1/11$)
- Produces: 입력 테브난 변환+CG 이득 및 출력 전류 분배($I^*=-g_{m2}V_X$) 중심의 `#s2-cc-gain`, 접지 연결 직렬 설명의 `#s2-cc-io`, $I_{out}, I_F$ 직접 기호의 `#s2-cc-closed`, 전면 동기화된 `#why-circuit` 링크 및 `#s4-cheatsheet` 표

- [ ] **Step 1: `#s2-cc-gain`([L567-L578](file:///Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/복습노트/1125/정리노트_1125_Analog_Filters.html#L567-L578)) 전면 동기화 (제목·ELI5·회로 SVG·본문·요약)**

  - `id="s2-cc-gain"`은 유지하고, 제목 `<h3>`을 `입력은 테브난 변환으로, 출력은 전류 분배로 구해요`(또는 동등한 간결 제목)로 교체한다.
  - ELI5 문단과 `fig-cc-gain-split`([L568](file:///Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/복습노트/1125/정리노트_1125_Analog_Filters.html#L568)): 기존 "전류 분배 두 번" 막대 그림을 2단계 흐름 도식으로 교체한다 — 1단계(입력): `I_in ‖ (R_F+R_M)` → 테브난 변환 `V_in = I_in(R_F+R_M)` + 직렬 `R_F+R_M` → CG 전압 이득으로 `V_X / I_in ≈ 9.57 kΩ`; 2단계(출력): `I* = -g_m2 V_X`가 `r_O2`(3.68 %)와 부하 경로(96.32 %)로 전류 분배 → `I_out / V_X ≈ -4.82 mS`. `aria-label`·`figcaption`도 새 그림에 맞춘다.
  - `fig-circuit-s2-cc-gain`([L569](file:///Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/복습노트/1125/정리노트_1125_Analog_Filters.html#L569)): 불필요한 `I_S1` 화살표를 정리하거나 유지 여부에 맞춰 본문과 일치시키고, `M_2` 드레인 분기(`㉢`)에 아래로 내려오는 드레인 소신호 전류 `I*`와 `r_O2`로 빠지는 전류 `I'` 화살표·라벨을 도선과 최소 `0.6em` 떨어지게 추가한다. 기존 `㉠㉡㉢`과 `figcaption`을 본문과 정확히 짝짓는다.
  - 숫자로 먼저 따라가요([L570](file:///Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/복습노트/1125/정리노트_1125_Analog_Filters.html#L570)): 입력 $1\ \mu\mathrm{A}$가 $R_F+R_M=11\ \mathrm{k\Omega}$와 만나 테브난 등가 전압 $V_{in}=11\ \mathrm{mV}$가 되고, 소스 저항 $11\ \mathrm{k\Omega}$가 붙은 CG 단 이득 $10/(0.5+11)\approx0.87$을 거쳐 $V_X\approx9.57\ \mathrm{mV}$, 이어서 둘째 단 전류 분배(96.32 %)로 $I_{out}\approx-46.07\ \mu\mathrm{A}$, 즉 $A_{I,open}\approx-46.07$이 됨을 일관되게 서술한다.
  - 첫 단([L571](file:///Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/복습노트/1125/정리노트_1125_Analog_Filters.html#L571)): 연쇄 분해 $\frac{I_{out}}{I_{in}}=\frac{V_X}{I_{in}}\cdot\frac{I_{out}}{V_X}$에서 출발해, `㉠` 입력 전류원 $I_{in}$과 병렬 $(R_F+R_M)$을 테브난 등가($V_{in}=I_{in}(R_F+R_M)$, 직렬 소스 저항 $R_F+R_M$)로 치환해 전개한다:
    1. $\frac{V_X}{I_{in}}=(R_F+R_M)\cdot\frac{V_X}{V_{in}}$ ($V_{in}=I_{in}(R_F+R_M)$)
    2. $\frac{V_X}{V_{in}}=\frac{R_D}{1/g_{m1}+(R_F+R_M)}$ (`㉡` 노드 $X$로 나가는 소스 저항 포함 CG 단 전압 이득)
    3. $\frac{V_X}{I_{in}}=\frac{(R_F+R_M)R_D}{R_F+R_M+1/g_{m1}}$ (예시 값 $\approx 9.57\ \mathrm{k\Omega}$)
  - 둘째 단([L572](file:///Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/복습노트/1125/정리노트_1125_Analog_Filters.html#L572)): `㉢` PMOS $M_2$의 소신호 드레인 전류 $I^*=-g_{m2}V_X$가 부하 경로($I_{out}$)와 $r_{O2}$ 가지($I'$)로 나뉘므로($I^*=I_{out}+I'$), 전류 분배로 전개한다:
    1. $I^*=I_{out}+I'=-g_{m2}V_X$ (PMOS라서 $V_X$가 오르면 아래 방향 전류가 줄어 음수)
    2. $I_{out}=I^*\cdot\frac{r_{O2}}{r_{O2}+R_L+(R_M\parallel R_F)}$
    3. $\frac{I_{out}}{V_X}=\frac{-g_{m2}r_{O2}}{r_{O2}+R_L+R_M\parallel R_F}$ (예시 값 $\approx -4.82\ \mathrm{mS}$)
  - 교수님 말씀([L574](file:///Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/복습노트/1125/정리노트_1125_Analog_Filters.html#L574))·확인 질문([L576](file:///Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/복습노트/1125/정리노트_1125_Analog_Filters.html#L576))·페이지 요약([L577](file:///Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/복습노트/1125/정리노트_1125_Analog_Filters.html#L577))을 새 첫 단·둘째 단 흐름에 맞춰 자연스럽게 정돈한다(예: 페이지 요약 핵심 식에 테브난+CG 첫 단과 둘째 단 전류 분배 반영).

- [ ] **Step 2: `#s2-cc-io`([L584](file:///Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/복습노트/1125/정리노트_1125_Analog_Filters.html#L584)) 출력 임피던스 설명 통일**

  - `fig-circuit-s2-cc-rout`와 `㉢㉣`은 유지하되, 레이저($R_L$) 양단에서 위로는 접지까지 `㉢` $r_{O2}$, 아래로는 접지까지 `㉣` $R_F \parallel R_M$이 보이고 두 접지가 같은 교류 접지로 이어지므로 직렬 합 $R_{out,open}=r_{O2}+R_F\parallel R_M$이 된다는 설명으로 `#s1-cv-io`와 톤을 맞춘다.

- [ ] **Step 3: `#s2-cc-closed`([L601-L603, L607](file:///Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/복습노트/1125/정리노트_1125_Analog_Filters.html#L601-L607))의 $K$ 기호 간소화 및 SVG 갱신**

  - `fig-circuit-s2-cc-k`([L601](file:///Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/복습노트/1125/정리노트_1125_Analog_Filters.html#L601)): 오른쪽 전류원 라벨을 `I_1` → `I_out`(위로 들어가게), 왼쪽 단락 가지 화살표 라벨을 `I_2` → `I_F`(오른쪽, 입력에서 빠지는 방향)로 교체한다. `I_out` 라벨이 viewBox 오른쪽 끝(`330`)에서 잘리지 않도록 필요 시 `viewBox` 너비 또는 좌표를 여유 있게 조정하고 `aria-label`·`figcaption`을 갱신한다.
  - $K$ 유도([L602](file:///Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/복습노트/1125/정리노트_1125_Analog_Filters.html#L602)): $I_{R_F}$ 단계를 빼고, `㉠` 감지 포트 $P$로 들어온 $I_{out}$이 `㉢` $R_M$과 `㉡` $R_F$로 전류 분배될 때 `I_F` 양의 방향과 반대로 흐르므로 곧바로 2단계로 쓴다:
    1. $I_F=-\frac{R_M}{R_F+R_M}I_{out}$
    2. $K=\frac{I_F}{I_{out}}=-\frac{R_M}{R_F+R_M}$
  - 슬라이드 60 그림의 $I_1$ 화살표 방향 주의 문장([L602](file:///Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/복습노트/1125/정리노트_1125_Analog_Filters.html#L602))과 꼭 기억해요([L607](file:///Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/복습노트/1125/정리노트_1125_Analog_Filters.html#L607))는 $I_{out}$·$I_F$ 기호와 모순되지 않게 정리한다.

- [ ] **Step 4: `#why-circuit`([L441](file:///Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/복습노트/1125/정리노트_1125_Analog_Filters.html#L441)), `#s2-cc-closed`([L603](file:///Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/복습노트/1125/정리노트_1125_Analog_Filters.html#L603)), `#s4-cheatsheet`([L655](file:///Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/복습노트/1125/정리노트_1125_Analog_Filters.html#L655)) 동기화**

  - `#why-circuit`과 `#s2-cc-closed`의 `<a href="#s2-cc-gain">...</a>` 링크 텍스트를 새 `#s2-cc-gain` 제목과 일치시킨다.
  - `#s4-cheatsheet` 표의 예제 IV 개루프 이득 칸을 `"테브난 변환+CG 이득과 출력 전류 분배의 곱, $A_{I,open}\lt0$"`으로 갱신한다.

- [ ] **Step 5: Task 2 검증 실행**

  Run:
  ```bash
  python3 .claude/skills/ec2-review-pack/scripts/check_html.py 복습노트/1125/정리노트_1125_Analog_Filters.html
  ! grep -nE "전류 분배 두 번|I_\{R_F\}|필기한|필기 방식" 복습노트/1125/정리노트_1125_Analog_Filters.html
  grep -nE 'id="s2-cc-gain"|-g_\{m2\}V_X|I\^\\\*=' 복습노트/1125/정리노트_1125_Analog_Filters.html
  ```
  Expected: `check_html.py` 출력 `OK`, 첫 `grep` 미일치(exit 0), 둘째 `grep`에서 `#s2-cc-gain` ID 유지 및 PMOS 음수 부호 `-g_{m2}V_X` 확인.

- [ ] **Step 6: Commit**

  ```bash
  git add 복습노트/1125/정리노트_1125_Analog_Filters.html
  git commit -m "docs(1125): rewrite Ex. IV C-C feedback note with Thevenin conversion, I* split, and direct I_F/I_out"
  ```

---

### Task 3: `.assets` 마크다운·독립 SVG 동기화 및 레이아웃·링크 전체 검증

**Files:**
- Regenerate: `복습노트/1125/.assets/정리노트_1125_Analog_Filters.md`
- Regenerate: `복습노트/1125/.assets/figures_1125/*.svg`
- Modify (결함 발견 시만): `복습노트/1125/정리노트_1125_Analog_Filters.html`

**Interfaces:**
- Consumes: Task 1·2가 완성한 `복습노트/1125/정리노트_1125_Analog_Filters.html`
- Produces: HTML과 1:1 일치하는 `.assets` MD·독립 SVG 및 `layout_probe.py` 0결함 확인

- [ ] **Step 1: `html2md.py --check`로 동반 MD와 독립 SVG 재생성 및 누락 검사**

  Run:
  ```bash
  python3 .claude/skills/ec2-review-pack/scripts/html2md.py 복습노트/1125/정리노트_1125_Analog_Filters.html --check
  ```
  Expected: exit 0 (수식·앵커·그림·링크 누락 없음).

- [ ] **Step 2: `layout_probe.py`로 데스크톱(1280px)·모바일(375px), 라이트·다크 모드 레이아웃 자동 측정**

  Run:
  ```bash
  python3 .claude/skills/ec2-review-pack/scripts/layout_probe.py 복습노트/1125/정리노트_1125_Analog_Filters.html --widths 1280,375 --themes light,dark --out /tmp/probe-1125.json
  ```
  Expected: exit 0 (`overflow`, `label_gaps`, `circuits` 결함 0건). 결함이 보고되면 `복습노트/1125/정리노트_1125_Analog_Filters.html`의 해당 수식 줄바꿈이나 SVG 좌표를 수정한 뒤 Step 1(`html2md.py --check`)과 Step 2(`layout_probe.py`)를 다시 통과시킨다.

- [ ] **Step 3: 정리노트 + 확인문제 교차 링크 및 정적 검사 실행**

  Run:
  ```bash
  python3 .claude/skills/ec2-review-pack/scripts/check_html.py 복습노트/1125/정리노트_1125_Analog_Filters.html 복습노트/1125/확인문제_1125_Analog_Filters.html
  rm -f /tmp/probe-1125.json
  ```
  Expected: `OK` (확인문제에서 정리노트 `#s1-*`/`#s2-*` 앵커로 가는 모든 링크 유효).

- [ ] **Step 4: Commit**

  ```bash
  git add 복습노트/1125/정리노트_1125_Analog_Filters.html 복습노트/1125/.assets/정리노트_1125_Analog_Filters.md 복습노트/1125/.assets/figures_1125/
  git commit -m "docs(1125): sync companion markdown and standalone SVGs after layout check"
  ```

---

### Task 4: 개인 풀이 명세(`solution-style.md`) 갱신 및 근거 기록 작성

**Files:**
- Modify: `.claude/skills/ec2-review-pack/references/solution-style.md:3,17-38,164-360,397-416,433-476,653-706`
- Create: `docs/learning/solution-style-updates/2026-11-26-block-chain-solving.md`
- Test: `workbook/tests/test_learning_style.py`

**Interfaces:**
- Consumes: `solution-style.md` 시작 SHA-256 `87746aa5d127893bd5f5ce10a8804d44f3e05bd687c93664e050289b2ff3945a`, 1125 필기 5쪽 관찰 결과, 사용자 확정(`#1=C`, `#5=A`)
- Produces: 기존 13규칙 ID를 유지한 갱신 `solution-style.md`와 상대 링크로 연결된 근거 기록 파일 `docs/learning/solution-style-updates/2026-11-26-block-chain-solving.md`

- [ ] **Step 1: 수정 직전 `solution-style.md` SHA-256 일치 확인**

  Run:
  ```bash
  shasum -a 256 .claude/skills/ec2-review-pack/references/solution-style.md
  ```
  Expected: `87746aa5d127893bd5f5ce10a8804d44f3e05bd687c93664e050289b2ff3945a` (다르면 중단하고 변경 충돌을 먼저 확인한다).

- [ ] **Step 2: `.claude/skills/ec2-review-pack/references/solution-style.md` 갱신 (기존 13개 `### NAME-01` ID 불변)**

  - 버전 기준일([L3](file:///Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/.claude/skills/ec2-review-pack/references/solution-style.md#L3)): `2026-11-26 (연쇄 이득 곱·테브난 변환·부하 기준 접지 연결 직렬 판정 반영)`으로 갱신한다.
  - `간결한 풀이의 우선순위`([L17-L38](file:///Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/.claude/skills/ec2-review-pack/references/solution-style.md#L17-L38)): 전류·전압 연립방정식을 새로 세워 이항·정리하기보다 중간 노드($V_X, V_{out}$) 기준 연쇄 이득 곱·알려진 기본 단 블록·직렬 로딩 치환($R_L\to R_L+R_M$)·전류 입력의 테브난 변환·부하 양단의 교류 접지 연결 직렬 판정을 우선한다는 원칙을 추가하고 `../../../../docs/learning/solution-style-updates/2026-11-26-block-chain-solving.md`로 상대 링크한다.
  - `CIRCUIT-01` & `CIRCUIT-02`: (a) 두 노드 사이 부하 양단의 출력 임피던스는 시험원 노드 방정식 대신 위·아래 접지까지 저항을 같은 교류 접지로 이어 직렬 합으로 바로 판정하는 규칙, (b) $I_{in}\parallel R_p$ 입력의 노턴→테브난 변환($V_{in}=I_{in}R_p$, 직렬 $R_p$, $R_p\cdot V_X/V_{in}$) 허용·우선 규칙을 반영한다.
  - `GAIN-01` & `DEGEN-01`: 다단 트랜스컨덕턴스·전류 이득($I_{out}/V_{in}$, $I_{out}/I_{in}$)에서 연립방정식 전개 대신 단별 전압 이득 연쇄 곱 + 옴의 법칙($1/R_L$) + 직렬 로딩 치환($R_L\to R_L+R_M$)을 우선 적용하고, `DEGEN-01` 제어 전압 식은 직접 블록 분해가 성립하지 않거나 축퇴 원리를 유도해야 하는 경우로 경계를 명시한다.
  - `NOTATION-01`: 귀환 계수 $K$ 유도에서 불필요한 임시 포트 변수($I_1, I_2, I_{R_F}$) 대신 원 회로의 감지·반송 기호($I_{out}, I_F$)를 직접 쓰는 표기 선호를 추가한다(원문 화살표가 반대일 때는 방향 정의 병기).
  - `CORRECT-01`: 1125 필기 4쪽의 PMOS $M_2$ 드레인 전류 $I^*=g_{m2}V_X$에서 생략된 음수 부호는 선호로 채택하지 않고 $I^*=-g_{m2}V_X$로 보정해 $A_{I,open}<0$, $KA_{I,open}>0$을 유지한다는 항목을 추가한다.
  - `변경 이력`: `2026-11-26` 항목을 추가한다.

- [ ] **Step 3: 근거 기록 `docs/learning/solution-style-updates/2026-11-26-block-chain-solving.md` 작성**

  - [2026-11-04-follower-impedance-form.md](file:///Users/hyunjun_macbook_pro/Documents/Univ/전자회로2/docs/learning/solution-style-updates/2026-11-04-follower-impedance-form.md) 형식을 따라 다음 항목을 기록한다:
    - 입력·시작 상태(1125 수업 필기 PDF 5쪽 시각 관찰 요약, 사용자 명시 선호, 변경 전 `solution-style.md` SHA-256)
    - 7열 비교표(`후보 ID | 파일·쪽수/영역 | 관찰 | 기존 규칙 ID | 분류 | 해석·범위 | 제안·근거`) — p1 연쇄 곱·로딩 치환, p2 부하 기준 접지 연결 직렬 판정, p3 폐루프 배율 관점, p4 테브난 변환+CG 이득 & $I^*=I_{out}+I'$ 전류 분배 & PMOS 음수 부호 보정, p5 직접 기호 $I_{out}, I_F$
    - 대수 동치 검산(연쇄 곱과 $I_{out}=g_{m2}(V_X-I_{out}R_L)$ 동치, 테브난 변환+CG 이득과 입력 전류 분배 동치)
    - 반영 내용(갱신한 기존 규칙 ID 목록, 신규 ID 미추가, 과거 산출물 검토 해시 미수정)
    - 검증 결과(변경 후 SHA-256, `read_style` 13규칙 확인, `pytest` 결과)

- [ ] **Step 4: 명세 계약·테스트·상대 링크·변경 범위 검증**

  Run:
  ```bash
  python3 -c "from pathlib import Path; from workbook.learning_style import read_style; s = read_style(Path('.')); assert len(s['rule_ids']) == 13, s['rule_ids']; print(len(s['rule_ids']), s['rule_ids'], s['sha256'])"
  pytest workbook/tests/test_learning_style.py -q
  python3 -c "from pathlib import Path; p = Path('.claude/skills/ec2-review-pack/references/solution-style.md'); target = (p.parent / '../../../../docs/learning/solution-style-updates/2026-11-26-block-chain-solving.md').resolve(); assert target.is_file(), target; print('LINK OK:', target)"
  git diff --check
  ```
  Expected: `13 ['UNIT-01', ..., 'FREQ-01'] <new-sha256>`, pytest 전체 통과(`passed`), `LINK OK`, `git diff --check` 출력 없음. (변경 후 SHA-256을 `2026-11-26-block-chain-solving.md`의 검증 절에 최종 기입한 뒤 `git diff --check` 재확인.)

- [ ] **Step 5: 제외 파일 불변 확인 및 Commit**

  Run:
  ```bash
  git status -s
  ```
  Expected: 변경된 파일은 `복습노트/1125/정리노트_1125_Analog_Filters.html`, `복습노트/1125/.assets/정리노트_1125_Analog_Filters.md`, `복습노트/1125/.assets/figures_1125/*.svg`, `.claude/skills/ec2-review-pack/references/solution-style.md`, `docs/learning/solution-style-updates/2026-11-26-block-chain-solving.md` (및 본 계획 파일)만 포함. `확인문제`·`문제설명`·PDF·과거 감사는 미변경.

  ```bash
  git add .claude/skills/ec2-review-pack/references/solution-style.md docs/learning/solution-style-updates/2026-11-26-block-chain-solving.md
  git commit -m "docs(style): record block-chain, Thevenin, and ground-loop solving preferences from 1125 notes"
  ```
