# `/ec2-interactive` v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `/ec2-interactive` 스킬을 `ec2-review-pack` 네이티브 SVG 회로도 하네스·경량 복소수 MNA 솔버·3대 아키타입(`probe`, `bench`, `approx`)·Playwright 레이아웃 자동 검증(`0.6em` 라벨 간격·오버플로)으로 개편하고, 가장 최근 복습팩(`복습노트/1120/`)에 아키타입별 3개 자료를 발행·연결해 End-to-End 검증한다.

**Architecture:** 기존 3D `<canvas>`·`<x-dc>` 런타임(`dc-runtime.js`, `template.dc.html`, `harness.cjs`)을 제거하고 표준 HTML/SVG/JS 런타임(`lab-template.html`, `mna.js`, `lab-runtime.js`)으로 교체한다. 주제 소스는 `.assets/자료_인터렉티브_NN_<이름>/lab.js`로 저장하고 `build.cjs`가 단일 독립 HTML(`인터렉티브_NN_<이름>.html`)로 번들링하며, `resolve.cjs`·`save.cjs`·`link-notes.cjs`의 탐색·배타 저장·노트 연결 계약과 `workbook/vendor_route.py`·`layout_probe.py` 오프라인 검증 체계를 그대로 연결한다.

**Tech Stack:** Node.js `>= 20` (`node:test`, zero npm dependencies), vanilla ES2022 + inline SVG + KaTeX `0.16.11` + Pretendard `1.3.9`, Python 3 + Playwright (`workbook/browser_runtime.py`, `workbook/vendor_route.py`).

**Spec:** [docs/superpowers/specs/2026-11-21-ec2-interactive-v2-design.md](../specs/2026-11-21-ec2-interactive-v2-design.md)

## Global Constraints
- Node.js `>= 20`, Python 3 + Playwright 환경에서 오프라인으로 모든 테스트와 브라우저 프로브가 통과해야 한다.
- 발행 HTML의 외부 리소스는 아래 4개 CDN URL만 허용한다(`workbook/vendor_route.py` 사본 매핑과 일치):
  - `https://cdn.jsdelivr.net/npm/pretendard@1.3.9/dist/web/static/pretendard.css`
  - `https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css`
  - `https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js`
  - `https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js`
- SVG 회로도 클래스는 `ec2-review-pack/assets/note-template.html`과 동일하게 `.fig-ink`, `.fig-accent`, `.fig-danger`, `.fig-dot`, `.fig-text`, `.fig-math`, `.fig-muted`, `.sym`, `data-node-color="blue"|"red"`만 사용한다. 하드코딩 hex 색을 마크업에 직접 쓰지 않는다.
- SVG 수식은 `NOTATION-01` native `<text class="fig-text fig-math">` + `<tspan baseline-shift="sub" font-size="78%">`를 사용한다(평문 `V_out`/`g_m`·SVG 내 `$...$` 금지). 회로 배치는 `CIRCUIT-02`(입력 왼쪽, 출력·시험원 오른쪽)를 따른다.
- 모든 모드·대표 상태·배지 활성 상태에서 `1440×900`·`375×812`, `light`/`dark` 모두 콘솔 오류 0건, 가로 스크롤 0px, `overflow <= 1px`, SVG `label_gaps >= 0.6em`을 만족해야 한다.
- 기존 `복습노트/1014/인터렉티브_01~03`은 수정하지 않으며 `resolve.cjs`·`save.cjs`·`link-notes.cjs`가 레거시 파일을 안전하게 인식·건너뛰어야 한다.
- 정리노트 연결은 문맥 안내 문단(`data-ec2-interactive`) 외 원문 바이트·동반 MD·PDF·그림 SHA-256을 변경하지 않는다.

## Review Focus
1. **특이 회로(전압원 직접 단락 또는 부동 노드)** — `bench`에서 학생이 의도치 않게 전압원을 접지에 단락하거나 부동 노드를 만들었을 때 `mna.js`가 `NaN`/`Infinity`를 뱉지 않고 `{ ok: false, singular: true, reason }`을 반환해야 한다. *(Task 1 테스트 고정)*
2. **키보드 접근성 및 `<1024px` 모바일 서랍 상호작용** — SVG의 `data-port`/`data-elem` 클릭 요소가 `tabindex="0"` + `Enter`/`Space`로 조작되고, 모바일 서랍이 한 번에 하나만 열리며 `Escape`로 닫혀야 한다. *(Task 2 테스트 고정)*
3. **번들러 스크립트 탈출(`</script>`) 및 SVG 평문 첨자 누락** — `lab.js` 문자열 안에 `</script>`가 포함돼도 `build.cjs`가 깨진 HTML을 만들지 않아야 하고, `check.cjs`가 SVG `<text>` 안의 평문 `V_out`·`g_m`·`$...$`를 확실히 차단해야 한다. *(Task 3 테스트 고정)*
4. **동적 배지 활성 상태의 도선 겹침 및 모바일 넘침** — 정적 초기 화면에서는 통과하던 SVG가 `+Δv` 도미노 배지나 `bench` 포트 칩이 켜졌을 때 도선과 `< 0.6em`으로 겹치거나 `375px` 뷰포트에서 넘치는 결함을 `probe_interactive.py`가 실제로 잡아내야 한다. *(Task 4 테스트 고정)*
5. **`1120` 기존 위젯과 겹치지 않는 노트 연결 및 바이트 보존** — `link-notes.cjs` 적용 후 `복습노트/1120/정리노트_1120_Nonideal_IO_Feedback.html`에서 `data-ec2-interactive` 문단만 제거하면 원문과 byte-equivalent여야 하고, 재실행 시 `changed: false`, 동반 MD·PDF·그림 SHA-256이 불변이어야 한다. *(Task 8 검증 고정)*

---

## File Structure Map

```
.agents/skills/ec2-interactive/
├── SKILL.md                           # Modify (Task 5) — v2 0~9단계 파이프라인
├── assets/
│   ├── mna.js                         # Create (Task 1) — 경량 복소수 소신호 MNA 솔버
│   ├── lab-template.html              # Create (Task 2) — 3단 셸 + ec2-review-pack SVG CSS + KaTeX
│   └── lab-runtime.js                 # Create (Task 2) — EC2Lab.mount + 3대 아키타입 + __EC2_LAB__
├── references/
│   ├── lab-api.md                     # Create (Task 5) — lab.js 스키마, 5종 data-* 훅, mna API
│   ├── example-lab.js                 # Create (Task 3) — 최소 정상 참조 lab.js (테스트/문서 겸용)
│   ├── design.md                      # Modify (Task 5) — SVG/KaTeX/3아키타입 화면 규칙
│   ├── topic-selection.md             # Modify (Task 5) — 아키타입 적합도 및 기존 위젯 차별 기준
│   ├── circuit-verification.md        # Modify (Task 5) — MNA+해석식 독립 검산 계약
│   └── note-links.md                  # Keep untouched
├── scripts/
│   ├── resolve.cjs                    # Keep untouched (1014 레거시 호환 유지)
│   ├── link-notes.cjs                 # Keep untouched
│   ├── build.cjs                      # Modify (Task 3) — lab.js → 단일 독립 HTML 번들러
│   ├── check.cjs                      # Modify (Task 3) — 스키마·DOM 훅·첨자·끝값/오조립 검사기
│   ├── steps.cjs                      # Modify (Task 3) — 모드·단계·포트 조합 덤프
│   ├── save.cjs                       # Modify (Task 3) — lab.js 복사 + wx 배타 저장(canvas.json 제거)
│   └── probe_interactive.py           # Create (Task 4) — 오프라인 Playwright + layout_probe 전 상태 검사
└── tests/
    ├── mna.test.cjs                   # Create (Task 1)
    ├── runtime.test.cjs               # Create (Task 2)
    ├── build.test.cjs                 # Modify (Task 3)
    ├── check.test.cjs                 # Modify (Task 3)
    ├── steps.test.cjs                 # Modify (Task 3)
    ├── save.test.cjs                  # Modify (Task 3)
    ├── test_probe_interactive.py      # Create (Task 4)
    ├── skill.test.cjs                 # Modify (Task 5)
    ├── resolve.test.cjs               # Keep untouched
    └── link-notes.test.cjs            # Keep untouched
```

*(Task 5에서 삭제되는 3D 레거시: `assets/dc-runtime.js`, `assets/template.dc.html`, `scripts/harness.cjs`, `scripts/frequency-model.cjs`, `scripts/frequency-topics.cjs`, `scripts/make-frequency-example.cjs`, `references/scene-api.md`, `references/example-frequency-response.dc.html`, `tests/frequency-model.test.cjs`, `tests/frequency-topics.test.cjs`, `tests/template.test.cjs`.)*

---

### Task 1: 경량 복소수 소신호 MNA 솔버 (`assets/mna.js`)

**Files:**
- Create: `.agents/skills/ec2-interactive/assets/mna.js`
- Test: `.agents/skills/ec2-interactive/tests/mna.test.cjs`

**Interfaces:**
- Consumes: 없음 (순수 표준 JS, 브라우저 전역 `globalThis.EC2MNA`와 Node `module.exports` 동시 노출).
- Produces:
  - `solveCircuit(netlist, options?)`
    - `netlist`: `{ ground?: string, elements: Array<{ id: string, type: 'R'|'C'|'L'|'vccs'|'vsrc'|'isrc'|'short'|'open', n1: string, n2: string, value?: number, gm?: number, cp?: string, cn?: string }> }` (`ground` 기본 `'0'`).
    - `options`: `{ freqHz?: number }` (기본 `0`; `freqHz === 0`일 때 `C`는 개방 `Y=0`, `L`은 단락 `0 V` 전압원으로 처리).
    - 반환:
      - 정상: `{ ok: true, singular: false, nodes: Record<string, { re: number, im: number, mag: number, phaseDeg: number }>, branches: Record<string, { re: number, im: number, mag: number, phaseDeg: number }> }` (`branches[id]`는 `n1 → n2` 방향 전류).
      - 특이행렬/오류: `{ ok: false, singular: true, reason: string }`.

- [ ] **Step 1: 실패 테스트 작성 (`tests/mna.test.cjs`)**

```js
const test = require('node:test');
const assert = require('node:assert/strict');
const { solveCircuit } = require('../assets/mna.js');

const approx = (a, b, tol = 1e-4) => assert.ok(Math.abs(a - b) <= tol, `${a} != ${b}`);

test('resistive divider and branch current sign (n1 -> n2)', () => {
  const r = solveCircuit({
    elements: [
      { id: 'vs', type: 'vsrc', n1: 'in', n2: '0', value: 4 },
      { id: 'r1', type: 'R', n1: 'in', n2: 'mid', value: 3000 },
      { id: 'r2', type: 'R', n1: 'mid', n2: '0', value: 1000 },
    ],
  });
  assert.equal(r.ok, true);
  approx(r.nodes.mid.re, 1.0);
  approx(r.branches.r1.re, 1e-3, 1e-7);
});

test('RC low-pass at pole frequency has -3.0103 dB and -45 deg', () => {
  const R = 1000, C = 1e-6, fp = 1 / (2 * Math.PI * R * C);
  const r = solveCircuit({
    elements: [
      { id: 'vs', type: 'vsrc', n1: 'in', n2: '0', value: 1 },
      { id: 'r1', type: 'R', n1: 'in', n2: 'out', value: R },
      { id: 'c1', type: 'C', n1: 'out', n2: '0', value: C },
    ],
  }, { freqHz: fp });
  assert.equal(r.ok, true);
  approx(20 * Math.log10(r.nodes.out.mag), -3.0103, 1e-3);
  approx(r.nodes.out.phaseDeg, -45, 1e-2);
});

test('Example I CG V-V closed loop matches 8/3 exactly', () => {
  const r = solveCircuit({
    elements: [
      { id: 'vin', type: 'vsrc', n1: 's', n2: '0', value: 1 },
      { id: 'gm1', type: 'vccs', cp: 'g', cn: 's', n1: 'out', n2: 's', gm: 4e-3 },
      { id: 'rd', type: 'R', n1: 'out', n2: '0', value: 4000 },
      { id: 'r1', type: 'R', n1: 'out', n2: 'g', value: 3000 },
      { id: 'r2', type: 'R', n1: 'g', n2: '0', value: 1000 },
    ],
  });
  assert.equal(r.ok, true);
  approx(r.nodes.out.re, 8 / 3, 1e-4);
  approx(r.nodes.g.re, 2 / 3, 1e-4);
});

test('short/open switches and singular circuit diagnostics (Review Focus #1)', () => {
  const shorted = solveCircuit({
    elements: [
      { id: 'vs', type: 'vsrc', n1: 'a', n2: '0', value: 1 },
      { id: 'bad', type: 'short', n1: 'a', n2: '0' },
    ],
  });
  assert.equal(shorted.ok, false);
  assert.equal(shorted.singular, true);
  assert.ok(shorted.reason.length > 0);

  const floating = solveCircuit({
    elements: [
      { id: 'r1', type: 'R', n1: 'x', n2: 'y', value: 1000 },
      { id: 'op', type: 'open', n1: 'x', n2: '0' },
    ],
  });
  assert.equal(floating.ok, false);
  assert.equal(floating.singular, true);
});
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `node --test .agents/skills/ec2-interactive/tests/mna.test.cjs`
Expected: FAIL (`Cannot find module '../assets/mna.js'`)

- [ ] **Step 3: `assets/mna.js` 구현**

`.agents/skills/ec2-interactive/assets/mna.js`에 복소수 산술(`cAdd`, `cSub`, `cMul`, `cDiv`, `cAbs`), 스탬프 조립(`R`, `C`, `L`, `vccs`, `vsrc`, `isrc`, `short`, `open`), 부분 피벗팅 복소수 가우스 소거법(`|pivot| < 1e-14`일 때 `{ ok: false, singular: true, reason }` 반환)을 구현한다. UMD 래퍼로 브라우저 `globalThis.EC2MNA = { solveCircuit }`과 CommonJS `module.exports = { solveCircuit }`을 모두 노출한다.

- [ ] **Step 4: 테스트 통과 확인**

Run: `node --test .agents/skills/ec2-interactive/tests/mna.test.cjs`
Expected: PASS (4/4)

- [ ] **Step 5: 체크포인트 확인**

`git status`로 `.agents/skills/ec2-interactive/assets/mna.js`, `tests/mna.test.cjs` 외 불필요한 변경이 없음을 확인한다(커밋은 사용자 요청 시에만 수행).

---

### Task 2: SVG 하네스 템플릿 및 3대 아키타입 런타임 (`assets/lab-template.html`, `assets/lab-runtime.js`)

**Files:**
- Create: `.agents/skills/ec2-interactive/assets/lab-template.html`
- Create: `.agents/skills/ec2-interactive/assets/lab-runtime.js`
- Test: `.agents/skills/ec2-interactive/tests/runtime.test.cjs`

**Interfaces:**
- Consumes: `EC2MNA.solveCircuit` (Task 1).
- Produces:
  - `assets/lab-template.html`: 자리표시 `__TITLE__`, `__SOURCE_COMMENT__`, `__MNA_SCRIPT__`, `__RUNTIME_SCRIPT__`, `__LAB_SCRIPT__`.
  - `assets/lab-runtime.js`:
    - `createInitialState(spec) -> LabState` (`{ mode, step, params, disabledElems, ports, causalStep, predictChoice, predictDismissed, toggles, theme, drawer, leftOpen, rightOpen }`)
    - `reduceState(spec, state, action) -> LabState` (순수 리듀서: `SET_MODE`, `PICK_STEP`, `SET_PARAM`, `APPLY_PRESET`, `TOGGLE_ELEM`, `SET_PORT`, `PULSE_CAUSAL`, `ANSWER_PREDICT`, `DISMISS_PREDICT`, `TOGGLE_OPT`, `SET_THEME`, `TOGGLE_PANEL`, `CLOSE_DRAWER`)
    - `buildProbeStates(spec) -> Array<{ label, state }>` (기본 상태 + 모든 모드 + 모든 단계 + `probe` 마지막 박자 + `bench` 대표 오조립 1개/정답 1개 + `approx` 각 소자 OFF)
    - `mount(spec, rootEl, deps?) -> LabController` (`window.__EC2_LAB__`에 동일 컨트롤러 등록: `getState`, `setMode`, `pickStep`, `setParam`, `toggleElem`, `setPort`, `pulseCausal`, `answerPredict`, `dismissPredict`, `setTheme`, `applyProbeState(state)`, `listProbeStates()`).

- [ ] **Step 1: 실패 테스트 작성 (`tests/runtime.test.cjs`)**

```js
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { createInitialState, reduceState, buildProbeStates } = require('../assets/lab-runtime.js');

const tpl = fs.readFileSync(path.join(__dirname, '..', 'assets', 'lab-template.html'), 'utf8');

test('lab-template.html matches ec2-review-pack CDN URLs and SVG CSS classes', () => {
  for (const needle of [
    'https://cdn.jsdelivr.net/npm/pretendard@1.3.9/dist/web/static/pretendard.css',
    'https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css',
    'https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js',
    'https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js',
    '.fig-ink', '.fig-accent', '.fig-danger', '.fig-dot', '.fig-text', '.fig-math',
    'data-node-color="blue"', 'data-node-color="red"',
    '__TITLE__', '__MNA_SCRIPT__', '__RUNTIME_SCRIPT__', '__LAB_SCRIPT__',
  ]) {
    assert.ok(tpl.includes(needle), `missing ${needle}`);
  }
});

test('soft predict card can be dismissed without locking controls, and drawer Escape closes (Review Focus #2)', () => {
  const spec = {
    id: 'demo', title: '데모', archetype: 'probe',
    modes: [{ key: 'a', label: '기본', svg: '<svg viewBox="0 0 100 100"></svg>', ariaLabel: '회로' }],
    predict: { prompt: '출력?', options: [{ id: 'up', label: '상승' }], answerId: 'up', explain: '이유' },
    params: [{ key: 'vin', label: 'v_in', min: -10, max: 10, step: 1, unit: 'mV', def: 5 }],
    causalSteps: [{ id: 1, label: '1단계' }, { id: 2, label: '2단계' }],
    mistakes: { a: [{ title: '1', text: 'a' }, { title: '2', text: 'b' }, { title: '3', text: 'c' }] },
    evaluate: () => ({ tiles: [{ label: 'V', val: '1 V' }] }),
  };
  let st = createInitialState(spec);
  assert.equal(st.predictDismissed, false);
  st = reduceState(spec, st, { type: 'SET_PARAM', key: 'vin', value: 8 });
  assert.equal(st.params.vin, 8); // 예측 미완료여도 조작 잠기지 않음
  st = reduceState(spec, st, { type: 'DISMISS_PREDICT' });
  assert.equal(st.predictDismissed, true);
  st = reduceState(spec, st, { type: 'TOGGLE_PANEL', side: 'left', narrow: true });
  assert.equal(st.drawer, 'left');
  st = reduceState(spec, st, { type: 'CLOSE_DRAWER' });
  assert.equal(st.drawer, null);
  assert.ok(buildProbeStates(spec).some((p) => p.state.causalStep === 2));
});

test('runtime binds keyboard activation (Enter/Space) on data-port and data-elem hooks (Review Focus #2)', () => {
  const src = fs.readFileSync(path.join(__dirname, '..', 'assets', 'lab-runtime.js'), 'utf8');
  assert.match(src, /tabindex/);
  assert.match(src, /Enter/);
  assert.match(src, /Escape/);
});
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `node --test .agents/skills/ec2-interactive/tests/runtime.test.cjs`
Expected: FAIL (`Cannot find module '../assets/lab-runtime.js'`)

- [ ] **Step 3: `assets/lab-template.html` 작성**

`ec2-review-pack/assets/note-template.html`의 SVG CSS 토큰(`.fig-*`, `Pretendard 600`, `<tspan baseline-shift="sub">` 78%, `data-node-color="blue"|"red"`)과 기존 3단 레이아웃·라이트/다크 변수·스크롤바·`<1024px` 단일 서랍·44px 탭 타겟 스타일을 합친 템플릿을 작성한다. SVG 동적 상태 클래스(`.is-hot`, `.is-bad`, `.is-dim`, `.is-off`, `.port-chip`, `.lab-badge`), 상단 부드러운 예측 카드(`.predict-card`), 연동 SVG 플롯 영역(`.plot-wrap`)을 포함한다.

- [ ] **Step 4: `assets/lab-runtime.js` 구현**

순수 상태 함수(`createInitialState`, `reduceState`, `buildProbeStates`)와 DOM 마운터(`mount`)를 구현한다.
- 5종 SVG 훅 바인딩:
  - `data-node`: 클릭 포커스 + `<g data-badges>`의 선언 좌표(`data-badge-for`가 있으면 사용, 없으면 노드 위/아래 여유 위치)에 실시간 전압·`↑/↓` 배지 렌더(정적 `.sym` 내부 텍스트 미변경).
  - `data-branch`: 전류 방향·활성 점등(`.is-hot`/`.is-bad`).
  - `data-elem`: `role="button" tabindex="0"` + 클릭/`Enter`/`Space`로 `TOGGLE_ELEM` + `.is-off` 점선 표시.
  - `data-port`: `role="button" tabindex="0"` + 클릭/`Enter`/`Space`로 포트 선택 팔레트(또는 순환 선택) + `.port-chip` 라벨 갱신.
  - `data-causal-step`: 현재 `causalStep` 이하 단계 순차 점등 및 현재 단계 강조.
- 연동 SVG 그래프(`plotData: { xLabel, yLabel, exact: [[x,y]...], approx?: [[x,y]...], marker?: [x,y], errPct?, thresholdPct? }`)를 네이티브 SVG `<path class="fig-accent">`(실선 정확식) + `<path class="fig-ink" stroke-dasharray="6 4">`(점선 근사식)로 그린다.
- 우측 패널 수식에 `window.renderMathInElement`가 로드되어 있으면 KaTeX 자동 렌더를 호출한다.

- [ ] **Step 5: 테스트 통과 확인**

Run: `node --test .agents/skills/ec2-interactive/tests/runtime.test.cjs`
Expected: PASS (3/3)

---

### Task 3: 빌드·정적/실행 검사·단계 덤프·저장 파이프라인 (`build.cjs`, `check.cjs`, `steps.cjs`, `save.cjs`, `example-lab.js`)

**Files:**
- Create: `.agents/skills/ec2-interactive/references/example-lab.js`
- Modify: `.agents/skills/ec2-interactive/scripts/build.cjs`
- Modify: `.agents/skills/ec2-interactive/scripts/check.cjs`
- Modify: `.agents/skills/ec2-interactive/scripts/steps.cjs`
- Modify: `.agents/skills/ec2-interactive/scripts/save.cjs`
- Modify: `.agents/skills/ec2-interactive/tests/build.test.cjs`, `tests/check.test.cjs`, `tests/steps.test.cjs`, `tests/save.test.cjs`

**Interfaces:**
- Consumes: `assets/mna.js`, `assets/lab-template.html`, `assets/lab-runtime.js`, `scripts/resolve.cjs` (`nextNumber`).
- Produces:
  - `build.cjs`: `{ build(srcFile, outFile), loadLab(srcFile), titleOf(spec), ALLOWED_CDNS }` — CLI `node build.cjs <lab.js> <out.html>`.
  - `check.cjs`: `{ check(srcFile) }` → `{ ok, errors, details }` — CLI `node check.cjs <lab.js>` (`ok` exit 0 / 오류 코드별 1줄 exit 1).
  - `steps.cjs`: `{ stepsReport(srcFile) }` — CLI `node steps.cjs <lab.js>`.
  - `save.cjs`: `{ save({ src, dest, name }) }` → `{ nn, html, dir }` — CLI `node save.cjs <RUN/n/lab.js> <DEST> <name>`.

- [ ] **Step 1: 참조 예제 `references/example-lab.js` 및 실패 테스트 4종 작성**

`references/example-lab.js`는 1개 모드·`probe` 아키타입·`mna.js` 호출·`<tspan>` 첨자·5종 훅 규약을 준수하는 최소 저항분배기/CS 예제로 작성한다.
각 테스트 파일에 아래 핵심 어서션을 작성한다:
- `tests/build.test.cjs`:
  - `build(exampleLab, outHtml)` 결과가 `<!doctype html>`, `EC2MNA`, `EC2Lab`, 4개 허용 CDN URL을 포함하고 `canvas.json`을 생성하지 않음을 검증.
  - **Review Focus #3**: `lab.js` 문자열에 `</script>`가 들어있어도 빌드된 HTML에서 `<\/script>`로 안전 이스케이프되어 `<script>` 태그가 조기 종료되지 않음을 검증.
- `tests/check.test.cjs`:
  - `references/example-lab.js`는 `{ ok: true, errors: [] }` 통과.
  - 누락된 `data-node` 참조 → `HOOK_MISSING`, SVG `<text>` 안 평문 `V_out` 또는 `$g_m$` → `SVG_TEXT_NOTATION`(**Review Focus #3**), 마크업 hex `#2563eb` → `HEX_IN_SVG`, `mistakes` < 3개 → `MISTAKES_INVALID`, `evaluate()`의 `NaN` 반환 → `EVAL_NON_FINITE`, 허용 외 외부 URL → `EXTERNAL_URL` 오류 코드를 정확히 검출.
- `tests/steps.test.cjs`:
  - `stepsReport(exampleLab)`가 모드·단계·프리셋별 타일·진단 스냅샷을 반환하고 빈 배열이 아님을 검증.
- `tests/save.test.cjs`:
  - `save({ src: exampleLab, dest: tmpDir, name: '테스트 주제' })`가 `인터렉티브_01_테스트_주제.html`과 `.assets/자료_인터렉티브_01_테스트_주제/lab.js`를 생성(`canvas.json` 없음), 기존 `인터렉티브_01_*.html`이 있으면 `02`로 채번(기존 `1014` 레거시 호환), 쓰기 실패 시 롤백 검증.

- [ ] **Step 2: 테스트 실패 확인**

Run: `node --test .agents/skills/ec2-interactive/tests/build.test.cjs .agents/skills/ec2-interactive/tests/check.test.cjs .agents/skills/ec2-interactive/tests/steps.test.cjs .agents/skills/ec2-interactive/tests/save.test.cjs`
Expected: FAIL (기존 `.dc.html` 기반 스크립트와 불일치)

- [ ] **Step 3: `build.cjs`, `check.cjs`, `steps.cjs`, `save.cjs` v2 구현**

- `build.cjs`: `loadLab(srcFile)`로 검증 가능한 스펙 로드 후, `lab.js` 소스를 IIFE(`(function(module, exports){ ... })`)로 감싸고 모든 `</script`를 `<\/script`로 치환해 `lab-template.html`의 슬롯에 주입한다.
- `check.cjs`:
  - 스키마 검증(`id`, `title`, `archetype in ['probe','bench','approx']`, `modes >= 1`, `mistakes[mode].length === 3`, `predict` 옵션·정답 일치).
  - SVG 정적 검증: `viewBox`·`ariaLabel` 필수, `<text>` 내부 평문 밑줄 첨자(`/[A-Za-z]_[A-Za-z0-9]/`)·`$...$` 금지(`SVG_TEXT_NOTATION`), 인라인 hex 색 금지(`HEX_IN_SVG`), `spec`이 참조하는 `data-node`/`data-branch`/`data-elem`/`data-port`/`data-causal-step` ID가 해당 모드 SVG에 실제 존재(`HOOK_MISSING`).
  - 동적 실행 검증: `createInitialState` + `buildProbeStates` + 모든 파라미터 `min`/`max` 끝값에서 `spec.evaluate(state, EC2MNA)`를 실행해 예외·`NaN`·`Infinity` 부재 검증(`bench` 의도적 특이 진단은 `diagnosis.singular === true`일 때만 허용).
- `steps.cjs`: `buildProbeStates(spec)`를 순회하며 각 상태의 모드·라벨·타일·노드 수치·진단을 출력.
- `save.cjs`: `Main.dc.html`·`canvas.json` 대신 `lab.js`를 `.assets/자료_인터렉티브_NN_<이름>/lab.js`로 복사하고 `build.cjs`로 최상위 HTML을 `wx` 배타 생성.

- [ ] **Step 4: 테스트 통과 확인**

Run: `node --test .agents/skills/ec2-interactive/tests/build.test.cjs .agents/skills/ec2-interactive/tests/check.test.cjs .agents/skills/ec2-interactive/tests/steps.test.cjs .agents/skills/ec2-interactive/tests/save.test.cjs`
Expected: PASS (전체 통과)

---

### Task 4: 오프라인 Playwright 레이아웃·전 상태 자동 프로브 (`scripts/probe_interactive.py`)

**Files:**
- Create: `.agents/skills/ec2-interactive/scripts/probe_interactive.py`
- Test: `.agents/skills/ec2-interactive/tests/test_probe_interactive.py`

**Interfaces:**
- Consumes:
  - `workbook/browser_runtime.py` (`launch_chromium`, `install_render_routes`, `local_url`)
  - `workbook/vendor_route.py` (`resolve_asset`)
  - `ec2-review-pack/scripts/layout_probe.py`의 `GAP_EM = 0.6` 및 SVG 글리프-도선 거리·오버플로 측정 계약
  - `window.__EC2_LAB__.listProbeStates()`, `window.__EC2_LAB__.applyProbeState(state)`, `window.__EC2_LAB__.setTheme(theme)` (Task 2)
- Produces:
  - CLI: `python3 probe_interactive.py FILE.html [--widths 1440,375] [--themes light,dark] [--out probe.json]`
  - Exit code: `0` 결함 없음, `1` 결함 발견(`console_errors`/`page_errors`/`horizontal_scroll_px > 1`/`overflow`/`label_gaps`/`not katex_ok`), `2` 사용법·브라우저 오류.

- [ ] **Step 1: 실패 테스트 작성 (`tests/test_probe_interactive.py`)**

```python
import json, subprocess, sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
PROBE = SKILL / 'scripts' / 'probe_interactive.py'
BUILD = SKILL / 'scripts' / 'build.cjs'
EXAMPLE = SKILL / 'references' / 'example-lab.js'

def test_probe_passes_example_lab_across_desktop_and_mobile(tmp_path):
    html = tmp_path / 'example.html'
    out = tmp_path / 'probe.json'
    subprocess.run(['node', str(BUILD), str(EXAMPLE), str(html)], check=True)
    res = subprocess.run([sys.executable, str(PROBE), str(html), '--widths', '1440,375', '--themes', 'light,dark', '--out', str(out)], capture_output=True, text=True)
    assert res.returncode == 0, res.stdout + res.stderr
    data = json.loads(out.read_text(encoding='utf-8'))
    assert data['ok'] is True
    assert len(data['checks']) >= 4
    assert all(c['katex_ok'] and not c['label_gaps'] and not c['overflow'] and c['horizontal_scroll_px'] <= 1 for c in data['checks'])

def test_probe_catches_active_badge_wire_collision_and_mobile_overflow(tmp_path):
    """Review Focus #4: 정적 상태가 아닌 동적 배지가 도선에 0.6em 미만으로 겹치면 exit 1."""
    bad_lab = tmp_path / 'bad-lab.js'
    bad_lab.write_text(EXAMPLE.read_text(encoding='utf-8').replace('data-badge-for="out" transform="translate(220, 32)"', 'data-badge-for="out" transform="translate(150, 80)"'), encoding='utf-8')
    html = tmp_path / 'bad.html'
    out = tmp_path / 'bad-probe.json'
    subprocess.run(['node', str(BUILD), str(bad_lab), str(html)], check=True)
    res = subprocess.run([sys.executable, str(PROBE), str(html), '--widths', '1440,375', '--themes', 'light', '--out', str(out)], capture_output=True, text=True)
    assert res.returncode == 1
    data = json.loads(out.read_text(encoding='utf-8'))
    assert any(c['label_gaps'] for c in data['checks'])
```

- [ ] **Step 2: 테스트 실패 확인**

Run: `pytest .agents/skills/ec2-interactive/tests/test_probe_interactive.py -v`
Expected: FAIL (`probe_interactive.py` 없음)

- [ ] **Step 3: `scripts/probe_interactive.py` 구현**

`ec2-review-pack/scripts/layout_probe.py`의 측정 JS(`GAP_EM = 0.6`, `rectDistance`, `.sym`/`defs` 제외)를 기반으로 하되:
- `window.__EC2_LAB__.listProbeStates()`로 모든 대표 상태(초기·모드·도미노 배지 활성·포트 칩 활성·소자 OFF)를 순회하며 매 상태마다 `overflow`(우측 패널·KaTeX·테이블·모바일 서랍), `horizontal_scroll_px`, SVG `label_gaps`를 측정한다.
- `375` 뷰포트에서는 좌측·우측 서랍을 각각 연 상태도 검사하고 `Escape`로 닫힘을 확인한다.
- 오프라인 모드(`offline=True`)에서 `vendor_route.resolve_asset`으로 KaTeX·Pretendard를 제공하고 미등록 외부 요청은 실패 처리한다.

- [ ] **Step 4: 테스트 통과 확인**

Run: `pytest .agents/skills/ec2-interactive/tests/test_probe_interactive.py -v`
Expected: PASS (2/2)

---

### Task 5: 레거시 3D 정리 및 스킬 문서·테스트 스위트 완결

**Files:**
- Delete: `.agents/skills/ec2-interactive/assets/dc-runtime.js`, `assets/template.dc.html`, `scripts/harness.cjs`, `scripts/frequency-model.cjs`, `scripts/frequency-topics.cjs`, `scripts/make-frequency-example.cjs`, `references/scene-api.md`, `references/example-frequency-response.dc.html`, `tests/frequency-model.test.cjs`, `tests/frequency-topics.test.cjs`, `tests/template.test.cjs`
- Create: `.agents/skills/ec2-interactive/references/lab-api.md`
- Modify: `.agents/skills/ec2-interactive/SKILL.md`, `references/design.md`, `references/topic-selection.md`, `references/circuit-verification.md`, `tests/skill.test.cjs`

**Interfaces:**
- Consumes: Task 1–4의 모든 스크립트·자산·CLI 계약.
- Produces: v2 에이전트 지침(`SKILL.md`, `references/*.md`) 및 전체 회귀 테스트 스위트.

- [ ] **Step 1: `tests/skill.test.cjs`를 v2 계약에 맞게 먼저 갱신**

`SKILL.md`와 `references/`가 `lab-api.md`, `probe_interactive.py`, `mna.js`, 3대 아키타입(`probe`, `bench`, `approx`), `lab.js`, 4개 검증 게이트를 참조하고 삭제된 `Main.dc.html`·`template.dc.html`·`dc-runtime.js`·`canvas.json`을 참조하지 않음을 검증하는 테스트를 작성한다.

- [ ] **Step 2: 테스트 실패 확인**

Run: `node --test .agents/skills/ec2-interactive/tests/skill.test.cjs`
Expected: FAIL (구 `SKILL.md` 참조)

- [ ] **Step 3: 레거시 3D 파일 삭제 및 `SKILL.md`·`references/` 작성/갱신**

- `references/lab-api.md`: `lab.js` 스키마, 5종 `data-*` 훅, `mna.js` API, 3대 아키타입 계약, 배지 배치 규칙 문서화.
- `references/design.md`: 네이티브 SVG(`fig-*`, `data-node-color`, `<tspan>` 첨자), KaTeX, 3단 셸, 부드러운 1초 예측 카드, 라이트/다크·모바일 규칙으로 갱신.
- `references/topic-selection.md`: 아키타입(`probe`/`bench`/`approx`) 매핑 표 추가, 기존 정리노트 `.widget`이 단순 열람형일 때 능동 조작으로 확장하는 경우만 선정하고 단순 반복은 제외하도록 명시.
- `references/circuit-verification.md`: `mna.js` 계산 호출만으로 독립 검산 금지, 별도 해석식/복소수 전달함수/노드방정식으로 기본·대표·끝값·오조립 상태를 대조하는 계약 명시.
- `SKILL.md`: 0~9단계를 `lab.js` → `check.cjs`/`steps.cjs` → 독립 검산 → `build.cjs` + `probe_interactive.py` + 실제 브라우저 확인 → `save.cjs` → `link-notes.cjs` 흐름으로 간결하게 갱신.

- [ ] **Step 4: 전체 단위 테스트 및 레거시 `1014` 호환 검증**

Run:
```bash
node --test .agents/skills/ec2-interactive/tests/*.test.cjs
pytest .agents/skills/ec2-interactive/tests/test_probe_interactive.py -v
node .agents/skills/ec2-interactive/scripts/resolve.cjs "$(pwd)" 1014
node .agents/skills/ec2-interactive/scripts/resolve.cjs "$(pwd)" 1120
```
Expected: 모든 Node 테스트·pytest PASS, `resolve 1014`는 기존 3개(`인터렉티브_01~03`)와 `next: "04"` 반환, `resolve 1120`은 `next: "01"`과 `정리노트_1120_Nonideal_IO_Feedback.html` 반환.

---

### Task 6: `1120` 테스트 ① (`bench`) — 네 가지 귀환 복제 종단 직접 꽂아보기

**Files:**
- Create (in RUN → saved via `save.cjs`):
  - `복습노트/1120/인터렉티브_01_네_형태_귀환_복제_종단_조립.html`
  - `복습노트/1120/.assets/자료_인터렉티브_01_네_형태_귀환_복제_종단_조립/lab.js` (+ `brief.md`, `validation.json`)

**Interfaces:**
- Consumes: v2 스킬 파이프라인 (`check.cjs`, `steps.cjs`, `build.cjs`, `probe_interactive.py`, `save.cjs`), 원문 [정리노트_1120_Nonideal_IO_Feedback.html](file:///Users/hyunjun_macbook_pro/Documents/Univ/%EC%A0%84%EC%9E%90%ED%9A%8C%EB%A1%9C2/%EB%B3%B5%EC%8A%B5%EB%85%B8%ED%8A%B8/1120/%EC%A0%95%EB%A6%AC%EB%85%B8%ED%8A%B8_1120_Nonideal_IO_Feedback.html)의 `s0-four-terminations`, `s1-k-rules` 및 `fig-s0-recap-vv` / `widget-terminations-static-1..4` SVG 구조.
- Produces: 검증 통과·저장된 `1120` 1번 인터랙티브 HTML.

- [ ] **Step 1: `RUN` 준비 및 `brief.md` 작성**

`복습노트/1120/정리노트_1120_Nonideal_IO_Feedback.html`의 바이트 백업과 기존 `.assets/*.md`, `*.pdf`의 SHA-256을 `RUN`에 기록한다. `brief.md`에 4종 증폭기(V-V, V-C, C-V, C-C)의 이상적 입력/출력 임피던스(`V: ∞/0`, `I: 0/∞`), 감지 복제·반송 복제 남은 포트 정답, 오조립 시 로딩 왜곡 진단, 오개념 3개를 적는다.

- [ ] **Step 2: `bench` 아키타입 `lab.js` 작성**

4개 모드(`vv`, `vc`, `cv`, `cc`)마다 `data-port="sense-rem"`(감지 복제 남은 포트)과 `data-port="return-rem"`(반송 복제 남은 포트)에 `[단락/접지]`·`[개방]`을 꽂을 수 있게 구성하고, 하단에 테스트 저항 분배기/귀환망 `mna.js` 계산을 연결해 잘못 꽂았을 때 실제로 잘못 측정되는 로딩 임피던스를 수치와 `fig-danger` 경로로 표시한다.

- [ ] **Step 3: 기계 검사·독립 검산·오프라인 브라우저 프로브 실행**

Run:
```bash
node .agents/skills/ec2-interactive/scripts/check.cjs "$RUN/01/lab.js"
node .agents/skills/ec2-interactive/scripts/steps.cjs "$RUN/01/lab.js" > "$RUN/01/steps.txt"
node .agents/skills/ec2-interactive/scripts/build.cjs "$RUN/01/lab.js" "$RUN/01/preview.html"
python3 .agents/skills/ec2-interactive/scripts/probe_interactive.py "$RUN/01/preview.html" --out "$RUN/01/probe.json"
```
별도 독립 검토자(서브에이전트)에게 `lab.js`·`brief.md`·`steps.txt`·`1120` 원문을 전달해 4종 포트 종단 정답표(V-V: 감지 개방/반송 단락, V-C: 단락/단락, C-V: 개방/개방, C-C: 단락/개방) 및 오조립 진단을 독립 대조한다. `validation.json` 4게이트 `pass` 확인.

- [ ] **Step 4: `save.cjs`로 `복습노트/1120/`에 저장**

Run: `node .agents/skills/ec2-interactive/scripts/save.cjs "$RUN/01/lab.js" "$(pwd)/복습노트/1120" "네_형태_귀환_복제_종단_조립"`
Expected: `{"nn":"01", ...}` 출력, `brief.md`·`validation.json`을 출력 `dir`로 복사.

---

### Task 7: `1120` 테스트 ② (`probe`) — 예제 I CG 단 V-V 귀환 `+Δv` 인과와 분배기 로딩 프로브

**Files:**
- Create (in RUN → saved via `save.cjs`):
  - `복습노트/1120/인터렉티브_02_CG_VV_귀환_인과와_로딩.html`
  - `복습노트/1120/.assets/자료_인터렉티브_02_CG_VV_귀환_인과와_로딩/lab.js` (+ `brief.md`, `validation.json`)

**Interfaces:**
- Consumes: v2 스킬 파이프라인 + `mna.js`, 원문 `1120`의 `s2-vv-open`·`s2-vv-closed` 및 `fig-s2-vv-open` SVG 구조.
- Produces: 검증 통과·저장된 `1120` 2번 인터랙티브 HTML.

- [ ] **Step 1: `brief.md` 및 `probe` 아키타입 `lab.js` 작성**

- 수업 기본값: `g_m1 = 4 mS`, `R_D = 4 kΩ`, `R_1 = 3 kΩ`, `R_2 = 1 kΩ`, `v_in = +10 mV` (`-20..+20 mV` 연속 슬라이더 + `R_1+R_2` 크기 슬라이더).
- 4박자 `+Δv` 도미노(`data-causal-step="1..4"`): `v_in ↑` → `v_gs = v_g - v_in ↓` → `i_d ↓` → `v_out ↑` 및 분배기 `v_g = K v_out ↑`(부귀환 억제).
- 모드 2개: `closed`(실제 귀환 폐루프 `A_v,closed = 8/3 ≈ 2.67` vs 로딩 무시 오답 `16/5 = 3.20` 대조) / `open`(복제 달린 개루프 `R_out,open = 2 kΩ`, `A_v,open = 8`).
- `mna.js`로 모든 노드 전압(`v_in`, `v_g`, `v_out`)·가지 전류(`i_RD`, `i_div`, `i_D1`)를 계산해 SVG 배지에 표시한다.

- [ ] **Step 2: 기계 검사·독립 검산·브라우저 프로브 및 `save.cjs` 실행**

Run:
```bash
node .agents/skills/ec2-interactive/scripts/check.cjs "$RUN/02/lab.js"
node .agents/skills/ec2-interactive/scripts/steps.cjs "$RUN/02/lab.js" > "$RUN/02/steps.txt"
node .agents/skills/ec2-interactive/scripts/build.cjs "$RUN/02/lab.js" "$RUN/02/preview.html"
python3 .agents/skills/ec2-interactive/scripts/probe_interactive.py "$RUN/02/preview.html" --out "$RUN/02/probe.json"
```
독립 검토자가 별도 KCL로 기본값(`v_in=10 mV → v_out=26.67 mV, v_g=6.67 mV`, 개루프 `A_v,open=8`, 로딩 무시 `3.20`)과 끝값(`R_1+R_2` 최소/최대, `v_in=-20 mV`)을 검산한다. 4게이트 `pass` 후 `save.cjs` 실행(`nn: "02"`) 및 `brief.md`·`validation.json` 복사.

---

### Task 8: `1120` 테스트 ③ (`approx`) — 예제 II `R_F` 로딩·반송 부호 근사 탐색기 + `1120` 정리노트 연결 및 최종 검증

**Files:**
- Create (in RUN → saved via `save.cjs`):
  - `복습노트/1120/인터렉티브_03_CG_CS_RF_로딩과_반송_부호.html`
  - `복습노트/1120/.assets/자료_인터렉티브_03_CG_CS_RF_로딩과_반송_부호/lab.js` (+ `brief.md`, `validation.json`)
- Modify (via `link-notes.cjs` only):
  - `복습노트/1120/정리노트_1120_Nonideal_IO_Feedback.html` (`s0-four-terminations`, `s2-vv-open`, `s3-vc-sign`에 `data-ec2-interactive` 문맥 안내 3건만 추가)

**Interfaces:**
- Consumes: Task 6–7 저장 경로, `scripts/link-notes.cjs`, `scripts/probe_interactive.py`.
- Produces: `1120` 3번 인터랙티브 HTML + 연결·무결성 검증이 완료된 `복습노트/1120/정리노트_1120_Nonideal_IO_Feedback.html`.

- [ ] **Step 1: `brief.md` 및 `approx` 아키타입 `lab.js` 작성**

- 수업 기본값: `g_m1 = 10 mS`, `g_m2 = 10 mS`, `R_D1 = 5 kΩ`, `R_D2 = 2 kΩ`, `R_F = 10 kΩ` (`1..100 kΩ` 로그 슬라이더), `I_in = 1 μA`.
- 모드 2개:
  - `loading`: `fig-vc-open` 기반 SVG에서 `data-elem="rf-in"`·`data-elem="rf-out"`을 클릭해 ON/OFF 토글 + 연동 SVG 그래프에 **정확 폐루프(MNA)** vs **2포트 로딩 공식(`R_0/(1+KR_0)`)** vs **이상적 무로딩 근사** 비교 및 `10%` 붕괴 배지 표시.
  - `sign`: `fig-vc-k` 기반 SVG에서 감지 전압원 `V_1` 인가 시 실제 전류 방향 vs 양의 기준 화살표 `I_F` 반대 → `K = -1/R_F < 0` 부호 확인(`+ΔV_1` 펄스 포함).

- [ ] **Step 2: 기계 검사·독립 검산·브라우저 프로브 및 `save.cjs` 실행**

Run:
```bash
node .agents/skills/ec2-interactive/scripts/check.cjs "$RUN/03/lab.js"
node .agents/skills/ec2-interactive/scripts/steps.cjs "$RUN/03/lab.js" > "$RUN/03/steps.txt"
node .agents/skills/ec2-interactive/scripts/build.cjs "$RUN/03/lab.js" "$RUN/03/preview.html"
python3 .agents/skills/ec2-interactive/scripts/probe_interactive.py "$RUN/03/preview.html" --out "$RUN/03/probe.json"
```
독립 검토자가 별도 노드방정식으로 기본값(이상 개루프 `-100 kΩ`, 로딩 개루프 `-82.51 kΩ`, `R_in,open=99.01 Ω`, `R_out,open=1.67 kΩ`, `K=-0.1 mS`, `1+KR_0=9.25`, 폐루프 `-8.92 kΩ` vs MNA 정확 폐루프)과 끝값(`R_F=1 kΩ`, `100 kΩ`)을 검산한다. 4게이트 `pass` 후 `save.cjs` 실행(`nn: "03"`) 및 `brief.md`·`validation.json` 복사.

- [ ] **Step 3: `link-notes.cjs`로 `1120` 정리노트 연결 및 무결성 검증 (Review Focus #5)**

`RUN/note-links.json`에 3개 링크(`s0-four-terminations` → `01`, `s2-vv-open` → `02`, `s3-vc-sign` → `03`)를 작성하고 실행한다:
```bash
node .agents/skills/ec2-interactive/scripts/link-notes.cjs "$RUN/note-links.json" --dry-run
node .agents/skills/ec2-interactive/scripts/link-notes.cjs "$RUN/note-links.json"
node .agents/skills/ec2-interactive/scripts/link-notes.cjs "$RUN/note-links.json" # changed: false 확인
```
다음을 모두 검증한다:
1. 수정된 `정리노트_1120_Nonideal_IO_Feedback.html`에서 `data-ec2-interactive` 문단 3개를 제거한 바이트가 `RUN`의 원문 백업과 정확히 일치(byte-equivalent).
2. 기존 `복습노트/1120/`의 MD·PDF·그림 SHA-256이 `RUN` 백업과 100% 일치.
3. 저장된 `인터렉티브_01~03` HTML 각각에 `probe_interactive.py` 재실행(exit 0) 및 실제 브라우저에서 `정리노트_1120` 링크 3개 클릭 시 새 탭 열림·핵심 조작·콘솔 0오류 확인.

---

## Self-Review Check (Completed Inline)
- **Spec coverage**: 모든 확정 결정 `#0`–`#12`가 Task 1–8에 1:1 매핑됨(MNA Task 1, SVG 하네스·3아키타입·부드러운 예측 카드 Task 2, 번들·체크·스텝·세이브 Task 3, `probe_interactive.py` Task 4, 레거시 정리·문서 Task 5, `1120` 3종 발행·연결 Task 6–8, `1014` 미수정 보존 Task 5).
- **Type consistency**: `solveCircuit(netlist, options?)`, `createInitialState`/`reduceState`/`buildProbeStates`/`mount`, `window.__EC2_LAB__`, `check`/`build`/`stepsReport`/`save` 시그니처가 전 태스크에서 일치.
- **Review Focus**: 5개 실패 모드가 각각 Task 1, 2, 3, 4, 8의 명시적 테스트·검증 단계에 고정됨.
