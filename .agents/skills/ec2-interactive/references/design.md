# v2 전자회로 화면·SVG 설계 규칙

기준 구현은 `references/example-lab.js`, 공통 셸과 스타일 토큰은 `assets/lab-template.html`이다. 레이아웃·수식·SVG 간격 자동 검증은 `scripts/probe_interactive.py`가 수행한다.

## 1. 네이티브 SVG 규약 (`CIRCUIT-02` 일치)

- **허용 색상·선 클래스만 사용 (하드코딩 hex 금지):**
  - `.fig-ink`: 일반 도선·소자 윤곽 (`stroke: currentColor; fill: none; stroke-width: 2`).
  - `.fig-accent`: 현재 강조 경로·기준 신호선 (`stroke: var(--accent); fill: none; stroke-width: 2.5`).
  - `.fig-danger`: 오류·단락·경고 경로 (`stroke: var(--danger); fill: none; stroke-width: 2.5`).
  - `.fig-dot`: 전기적 접합점·노드 점 (`fill: var(--accent)`). 채움은 점·도형에만 쓰고 윤곽선은 선 클래스로 그린다.
  - `.fig-text`: 소자 이름·값·단위 (`fill: currentColor; font-size: 13px`).
  - `.fig-math`: 수식 기호 글자 (`Pretendard`, 600 정체).
  - `.fig-muted`: 보조 설명·축 눈금 (`fill: var(--ink-2); font-size: 12px`).
  - `.sym` (또는 `data-symbol`): 저항·커패시터·접지·전류원·트랜지스터 같은 기호 그룹. `probe_interactive.py`가 `label_gaps` 검사에서 심볼 내부 선분을 제외하므로 표준 기호를 반드시 `.sym`으로 감싼다.
- **노드 색 대응:** 중요 노드의 `.fig-dot`과 대응 `<text class="fig-text fig-math">`에 `data-node-color="blue"` 또는 `data-node-color="red"`를 짝지어 넣는다.
- **첨자·기호 표기:** SVG `<text>` 안에 `_` 밑줄(`V_out`)이나 LaTeX(`$g_m$`, `\(v_o\)`)을 쓰면 `scripts/check.cjs`가 `SVG_TEXT_NOTATION`으로 차단한다. 아래첨자는 `<tspan baseline-shift="sub" font-size="78%">out</tspan>`, 위첨자는 `baseline-shift="super"`, 특수 기호는 유니코드(`Ω`, `μ`, `π`, `‖`)를 쓴다.
- **제로 하드코딩 hex:** SVG 문자열 안에 `#rrggbb`/`#rgb`를 넣으면 `HEX_IN_SVG` 오류가 난다(`url(#id)` 마커 참조 제외). 라이트·다크 전환이 CSS 변수로 자동 동작하도록 클래스만 사용한다.
- **회로 가독성 (`CIRCUIT-02`):** 전기적 연결(접합점 `.fig-dot`), 종속원 화살표 방향, AC 접지, 입출력 노드, 기준 전위를 명확히 그리고 물리 배치가 전기적 연결로 오해되지 않게 간격을 둔다.

## 2. 허용 CDN 4종과 KaTeX 수식

`assets/lab-template.html`과 `scripts/build.cjs`가 허용하는 외부 URL은 아래 4개뿐이며, `check.cjs`(`EXTERNAL_URL`)와 `probe_interactive.py`(`blocked_requests`)가 이외 URL을 차단한다:
1. `https://cdn.jsdelivr.net/npm/pretendard@1.3.9/dist/web/static/pretendard.css`
2. `https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css`
3. `https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js`
4. `https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js`

- HTML 패널(`predict`, `formula`, `equations`, `summary`, `diagnosis`, `mistakes`)에서는 KaTeX(`$...$`, `$$...$$`)를 사용한다.
- 디스플레이 수식(`$$...$$`)이 긴 경우 `.katex-display`가 가로 스크롤로 감싸지만, `.formula-box`·`.panel-right` 바깥으로 넘치지 않게 `aligned`로 적절히 줄바꿈한다. 미렌더 `$` 잔존이나 `.katex-error`가 없어야 한다.

## 3. 3단 셸과 예측 카드

- **상단 바(`.topbar`):** 좌측 서랍 토글(`data-drawer-btn="left"`) · 제목(`.brand`, 640px 이하 자동 숨김) · 모드 선택(`.seg`, 2개 이상일 때만 표시) · 테마 토글(`.theme-toggle`, `od-theme` 저장) · 우측 서랍 토글(`data-drawer-btn="right"`).
- **왼쪽 조작 패널(`.panel-left`):** 보기 옵션 → `+Δv` 인과 도미노 → 포트 종단 조립 → 소자 포함 여부 → 소자·입력 값 슬라이더 → 대표 설정 → 단계별 살펴보기.
- **중앙 실험 무대(`.stage`):**
  - `.lab-stage-wrap` / `.lab-stage`: 메인 회로 SVG와 `.port-popover` 종단 메뉴.
  - `.plot-slot` (`plotData` 비교 그래프): 정확식 실선(`.fig-accent`)과 근사식 점선(`.fig-ink` `stroke-dasharray: 6 4`), 오차 배지(`.err-badge`)를 표시한다.
- **오른쪽 설명 패널(`.panel-right`):** 수치 요약(`.tiles`) → 회로 진단(`.diagnosis`) → 핵심 수식(`.formula-box`) → 지금 일어나는 일(`.summary-box`) → 「꼭 기억해요」(`.sec.warn`, 모드별 정확히 3개).
- **예측 카드(`.predict-slot`):** 넓은 화면에서 설명 패널이 열려 있으면 맨 위에 배치한다. `1024px` 미만이거나 설명 패널이 닫혀 있으면 회로 위에서 ‘예측해 보기’로 시작한다. 답을 고르면 ‘회로에서 확인’으로 모델을 조작하고 관측값과 이유를 표시한다. ‘바로 실험하기’를 누르면 카드를 접고 현재 회로 상태를 유지한다. 포트·모드·소자·슬라이더는 예측을 시작하기 전에도 조작할 수 있다. 여러 모드가 있으면 해당 조건에서 의미 있는 질문만 노출한다.

## 4. 반응형·간격·접근성·문체

- **뷰포트 및 테마:** `1440×900` 데스크톱과 `375×812` 모바일, `light`·`dark` 테마 전 조합에서 `horizontal_scroll_px <= 1`과 `overflow` 0건을 만족해야 한다.
- **모바일 단일 서랍(`<= 1023.98px`):** 한 번에 왼쪽 또는 오른쪽 서랍 하나만 열리며(`data-drawer="left"|"right"|"none"`), 스크림 클릭 또는 `Escape` 키로 닫힌다.
- **SVG 라벨 여백(`0.6em` `label_gaps`):** 일반 `<text>`와 배지 텍스트가 심볼 밖 도선과 `0.6em` 미만으로 닿거나 겹치지 않아야 한다. 정적 `<g data-badges><g data-badge-for="...">` 좌표를 도선 밖 여백에 잡는다.
- **키보드 및 터치:** `data-port`·`data-elem`은 `Enter`/`Space`로 활성화되고, 포트 팝오버·모바일 서랍은 `Escape`로 닫힌다. 모든 버튼·인터랙티브 컨트롤은 `44px` 이상(`--tap: 44px`)을 유지하고 `aria-pressed`·`aria-expanded`·`aria-label`을 갖춘다.
- **문체:** 해요체로 한 문장에 한 가지만 쓴다. 수업 밖 해석·보충에는 `(교과서 보충)`을 표시한다.
