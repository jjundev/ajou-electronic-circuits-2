# v2 인터랙티브 실험실 API 계약 (`lab.js` & `mna.js`)

주제 하나는 CommonJS 모듈(`module.exports = spec`)로 작성한 `lab.js` 한 파일이다. 실행 예제는 `references/example-lab.js`, 공통 셸과 런타임은 `assets/lab-template.html`·`assets/lab-runtime.js`, 경량 소신호 MNA 솔버는 `assets/mna.js`에 있다.

검증 및 빌드 명령:
- 계약 검사: `node scripts/check.cjs <lab.js>` (`ok` 및 종료 코드 `0`, 결함 시 코드별 줄 출력 및 종료 `1`, 사용법 오류 종료 `2`)
- 상태 스냅샷: `node scripts/steps.cjs <lab.js>` (`buildProbeStates` 전 상태의 타일·노드·진단 출력)
- 단일 HTML 빌드: `node scripts/build.cjs <lab.js> <out.html>`

## `check.cjs` 검사 코드

| 코드 | 의미 |
|---|---|
| `LOAD_ERROR` | `lab.js` 파일 없음, 문법 오류, 또는 객체 export 실패 |
| `EXTERNAL_URL` | 허용된 4개 CDN과 표준 SVG `xmlns` 외 외부 `http(s)://` URL 포함 |
| `SCHEMA_INVALID` | `id`, `title`, `archetype`, `modes`, `evaluate`, `predict`, `params`, `steps`, `presets` 스키마 위반 또는 `<svg>` 인라인 4-숫자 `viewBox` 누락 |
| `MISTAKES_INVALID` | `mistakes.<modeKey>`가 길이 3 배열이 아니거나 `title`/`text`가 비어 있음 |
| `HEX_IN_SVG` | SVG 마크업 안 직접 `#rgb`/`#rrggbb` 색상 지정 (`url(#id)`와 HTML 엔티티 제외) |
| `SVG_TEXT_NOTATION` | SVG `<text>` 안 평문 밑줄 첨자(`V_out`) 또는 LaTeX(`$...$`, `\(...\)`) 사용 |
| `HOOK_MISSING` | `ports`·`elems`·`causalSteps` 선언 또는 `evaluate()` 반환 키(`nodes`/`branches`/`elems`/`ports`)에 대응하는 SVG `data-*` 훅 누락 |
| `EVAL_THROW` | 대표 상태 또는 파라미터 끝값 조합에서 `evaluate()` 예외 발생 또는 비객체 반환 |
| `EVAL_NON_FINITE` | `nodes`, `branches`, `tiles`, `plotData`에 `NaN`/`Infinity` 값 또는 문자열 포함, 혹은 `bench` 외 아키타입에서 `diagnosis.singular: true` 반환 |

## `lab.js` 스키마 (`spec`)

```js
module.exports = {
  id: 'example-voltage-divider',      // 필수: 고유 문자열
  title: '전압 분배기 동작 프로브',       // 필수: 상단 바·<title> 제목
  archetype: 'probe',                 // 필수: 'probe' | 'bench' | 'approx'
  modes: [/* Mode, ... */],           // 필수: 1개 이상
  predict: {                          // 선택: 부드러운 1초 예측 카드
    prompt: '질문 ($...$ 가능)',
    options: [{ id: 'a', label: '보기 1' }, { id: 'b', label: '보기 2' }],
    answerId: 'a',
    explain: '선택 직후 보여 줄 한두 문장 해설',
  },
  params: [/* Param, ... */],         // 선택: 슬라이더 목록
  ports: [/* Port, ... */],           // 선택: 종단/연결 포트(또는 Mode.ports)
  elems: [/* Elem, ... */],           // 선택: 토글 소자(또는 Mode.elems)
  initialDisabledElems: [],           // 선택: 초기 비활성 소자 id 배열
  causalSteps: [/* CausalStep */],    // 선택: 인과 맥동 단계(또는 Mode.causalSteps)
  presets: [/* Preset, ... */],       // 선택: 대표 설정(또는 Mode.presets)
  steps: [/* Step, ... */],           // 선택: 단계별 살펴보기
  toggles: [['labels', '노드 배지', true]], // 선택: 보기 토글('labels'가 배지 표시 제어)
  mistakes: {                         // 필수: 모드 key마다 정확히 3개
    modeKey: [{ title: '오개념 제목', text: '교정 설명' }, /* ...3개 */],
  },
  evaluate(state, mna) {              // 필수: 순수 상태 평가 함수
    return { /* EvalResult */ };
  },
};
```

### `Mode`·조작·단계 정의
- `Mode`: `{ key, label, svg, ariaLabel, ports?, elems?, causalSteps?, presets? }`
  - `svg`는 `<svg viewBox="x y w h" ...>...</svg>` 인라인 문자열이어야 하며 `w > 0, h > 0`인 4-숫자 `viewBox`가 필요하다.
  - `params`, `ports`, `elems`, `causalSteps`, `presets`, `toggles` 항목에 `mode: 'k'` 또는 `modes: ['k1', 'k2']`를 주면 해당 모드에만 노출된다. `ports`·`elems`·`causalSteps`·`presets`는 `Mode` 객체 안에 직접 두어도 된다.
- `Param`: `{ key, label, min, max, step?, unit?, def?, scale?: 'linear'|'log', format?(val) }` (`scale: 'log'`는 `0 < min < max` 필수).
- `Port`: `{ id, label, options: [{ id, label, shortLabel? }], def?, answer?, badOption? }`
  - `steps.cjs`와 `probe_interactive.py`가 사용하는 `buildProbeStates()`는 `answer`(또는 `correct`)로 정답 조립 상태를, 다른 옵션(있다면 `badOption` 우선)으로 대표 오조립 상태를 자동 생성한다.
- `Elem`: `{ id, label }` 또는 문자열 `id`.
- `CausalStep`: `{ id, label, detail? }` (`id` 생략 시 1부터 시작).
- `Preset`: `{ id, label, mode?, params?, ports?, disabledElems?, causalStep? }`.
- `Step`: `{ mode?, title, who?, text?, params?, ports?, disabledElems?, causalStep? }`.
- `toggles`: `[[key, label, def], ...]` 또는 `[{ key, label, def, mode? }]` 또는 `{ [modeKey]: [...] }`.

### `evaluate(state, mna)` 입출력
- `state`: `{ mode, step, params, disabledElems, ports, causalStep, predictChoice, predictDismissed, toggles, theme, drawer, leftOpen, rightOpen, focusNode }`
- 반환 `EvalResult`:
  - `tiles`: `[{ label, val }]` (3개일 때 `.tiles.three` 3열 그리드).
  - `diagnosis`: `{ kind: 'ok'|'warn'|'bad'|'info', title?, text, singular? }` 또는 문자열.
  - `formula` / `equations`: KaTeX 문자열(`$$...$$`) 또는 `{ name?, tex }` (단일·배열).
  - `summary`: 오른쪽 패널 「지금 일어나는 일」 문장(인라인 `$...$` 가능).
  - `nodes`: `{ [nodeId]: { v?, val?, unit?, text?, badge?, dir?: 'up'|'down'|'↑'|'↓', hot?, bad?, dim? } }`.
  - `branches`: `{ [branchId]: true | { hot?, active?, bad?, dim?, dir?: 'fwd'|'rev'|1|-1 } }`.
  - `elems`: `{ [elemId]: { hot?, bad?, dim? } }`.
  - `ports`: `{ [portId]: { hot?, ok?, bad?, badge?, text? } }` (포트 배지는 SVG에 해당 `data-badge-for` 슬롯이 있을 때만 표시).
  - `plotData`: `{ title?, ariaLabel?, xLabel?, yLabel?, xScale?: 'linear'|'log', xMin?, xMax?, yMin?, yMax?, exact: [[x,y],...], approx?: [[x,y],...], exactLabel?, approxLabel?, marker?: [x,y], approxMarker?: [x,y], errPct?: number, thresholdPct?: number }` (`thresholdPct` 기본 `10`).

## 5종 SVG `data-*` 훅과 배지 배치

| 훅 속성 | 필수 조건 | 런타임 동작 |
|---|---|---|
| `data-node="<id>"` | `evaluate().nodes[id]` 반환 시 필수 | 클릭 시 `FOCUS_NODE` 토글, `hot`/`bad`/`dim`에 따라 `.is-hot`/`.is-bad`/`.is-dim` 적용 및 배지 갱신 |
| `data-branch="<id>"` | `evaluate().branches[id]` 반환 시 필수 | `.is-hot`/`.is-bad`/`.is-dim`/`.is-rev`, `data-dir="fwd"\|"rev"` 적용 |
| `data-elem="<id>"` | `elems` 선언 또는 `evaluate().elems[id]` 반환 시 필수 | `role="button"`, `tabindex="0"`, `aria-pressed` 부여; 클릭/`Enter`/`Space`로 `TOGGLE_ELEM`, 비활성 시 `.is-off` |
| `data-port="<id>"` | `ports` 선언 또는 `evaluate().ports[id]` 반환 시 필수 | `role="button"`, `tabindex="0"`, `aria-haspopup="menu"`, `aria-expanded` 부여; 클릭/`Enter`/`Space`로 `.port-popover` 열기, 하위 `[data-port-view="<optId>"]` 전환 및 `.port-chip` 텍스트 갱신 |
| `data-causal-step="<n>"` | `causalSteps`의 모든 `id`에 대해 필수(쉼표 복수 예: `"1,2"`) | 현재 단계 `.is-hot`, 이전 단계 `.is-done`, 나머지 `.is-dim` 적용 |

### 노드 배지 배치 규칙
SVG 최상단 여백에 정적 배지 슬롯을 직접 두는 것을 기본으로 한다:
```xml
<g data-badges>
  <g data-badge-for="in" transform="translate(60, 32)"></g>
  <g data-badge-for="out" transform="translate(220, 32)"></g>
</g>
```
런타임(`syncBadges`)은 각 슬롯 안에 `<rect class="lab-badge-bg" data-badge-bg="1" y="-11" height="22" rx="6">`와 `<text class="lab-badge-text" x="0" y="4" text-anchor="middle">`를 그린다. 슬롯이 없으면 `data-node` 요소의 `cx, cy - 22`(또는 `x, y - 18`)에 자동 배지(`data-auto-badge="1"`)를 추가하지만, 도선과 `0.6em` 미만으로 겹치면 `probe_interactive.py`가 실패하므로 도선에서 떨어진 위치에 정적 슬롯을 배치한다.

## `assets/mna.js` (`EC2MNA.solveCircuit`) API

```js
const res = mna.solveCircuit({ ground: '0', elements: [/* ... */] }, { freqHz: 0 });
```
- `netlist.ground`: 기준 노드 이름(생략 시 `'0'`).
- `options.freqHz`: `0` 이상 유한 숫자(생략 시 `0`, DC 해석). AC에서는 $\omega = 2\pi f$로 커패시터 어드미턴스 $j\omega C$, 인덕터 어드미턴스 $1/(j\omega L)$ 스탬프를 적용하며, `freqHz === 0` 또는 `L === 0`인 인덕터는 0 V 이상적 단락(분기 변수)으로 처리한다.
- 지원 소자 8종(`id` 고유 문자열, `n1`, `n2` 필수):
  - `R`: `{ id, type: 'R', n1, n2, value }` (`value > 0`, Ω)
  - `C`: `{ id, type: 'C', n1, n2, value }` (`value >= 0`, F)
  - `L`: `{ id, type: 'L', n1, n2, value }` (`value >= 0`, H)
  - `vccs`: `{ id, type: 'vccs', n1, n2, cp, cn, gm }` — 전류 `I(n1 → n2) = gm · (V(cp) - V(cn))`
  - `vsrc`: `{ id, type: 'vsrc', n1, n2, value }` (`value`는 실수 또는 `{ re, im }`) — `V(n1) - V(n2) = value`
  - `isrc`: `{ id, type: 'isrc', n1, n2, value }` (`value`는 실수 또는 `{ re, im }`) — `n1 → n2` 방향 전류 `value`
  - `short`: `{ id, type: 'short', n1, n2 }` — `V(n1) - V(n2) = 0`
  - `open`: `{ id, type: 'open', n1, n2 }` — 스탬프 없음, 분기 전류 0
- 반환값:
  - 정상: `{ ok: true, singular: false, nodes: { [node]: Phasor }, branches: { [elemId]: Phasor } }` (`Phasor = { re, im, mag, phaseDeg }`, 모든 가지 전류는 `n1 → n2` 기준)
  - 특이/오류: `{ ok: false, singular: true, reason: string }` (전압원 단락, 부유 노드, 잘못된 소자 스펙 등)

## 3대 아키타입 계약 (`probe`, `bench`, `approx`)

| 아키타입 | 목적과 핵심 조작 | 필수·권장 요소 | `singular: true` 허용 |
|---|---|---|---|
| `probe` | 입력 변화가 전류·노드 전압·출력으로 전파되는 인과 추적 | `params` + `causalSteps` + `nodes`/`branches` + `data-badges` | 금지 |
| `bench` | 포트 종단·시험 회로 조립과 오조립 원인 진단 | `ports` (`def`, `answer`, `badOption`) + SVG `data-port` + `.port-chip` | 허용(`diagnosis.singular: true`) |
| `approx` | 이상적 근사식과 기생·로딩 포함 정확식 비교 및 근사 붕괴 조건 확인 | `elems` (`data-elem`) + `params` + `plotData` (`exact`, `approx`, `errPct`) | 금지 |

## 런타임 제어 API (`window.__EC2_LAB__`)

`assets/lab-runtime.js`는 마운트 시 `window.__EC2_LAB__`에 `getState`, `setMode`, `pickStep`, `setParam`, `applyPreset`, `toggleElem`, `setPort`, `pulseCausal`, `answerPredict`, `dismissPredict`, `setTheme`, `togglePanel`, `closeDrawer`, `renderMath`, `listProbeStates`, `applyProbeState`, `destroy`를 노출한다. `scripts/probe_interactive.py`는 `listProbeStates()`, `applyProbeState(st)`, `setTheme(t)`를 호출해 전 상태를 자동 검사한다.
