const tex = String.raw;
const ground = (x, y) => `<g class="sym"><path class="fig-ink" d="M${x - 10} ${y}h20 m-16 5h12 m-9 5h6"/></g>`;
const svg = `<svg viewBox="0 0 430 292" role="img">
  <path class="fig-ink" d="M36 82h36m48 0h30m82 0h23m43 0h96"/>
  <circle class="fig-dot" data-node="in" data-node-color="blue" cx="36" cy="82" r="4"/>
  <circle class="fig-dot" data-node="err" data-node-color="blue" cx="134" cy="82" r="4"/>
  <circle class="fig-dot" data-node="out" data-node-color="red" cx="394" cy="82" r="4"/>
  <text class="fig-text fig-math" data-node-color="blue" x="36" y="62" text-anchor="middle">v<tspan baseline-shift="sub" font-size="78%">in</tspan></text>
  <text class="fig-text fig-math" data-node-color="blue" x="134" y="62" text-anchor="middle">v<tspan baseline-shift="sub" font-size="78%">1</tspan></text>
  <text class="fig-text fig-math" data-node-color="red" x="394" y="62" text-anchor="middle">v<tspan baseline-shift="sub" font-size="78%">out</tspan></text>
  <g class="sym">
    <circle class="fig-ink" cx="96" cy="82" r="24"/>
    <path class="fig-ink" d="M81 82h10m-5-5v10m5 10h10"/>
  </g>
  <rect class="fig-ink" x="150" y="61" width="82" height="42" rx="6"/>
  <text class="fig-text fig-math" x="191" y="87" text-anchor="middle">A<tspan baseline-shift="sub" font-size="78%">0</tspan></text>
  <g class="sym"><path class="fig-ink" d="M255 82h5l4-6 7 12 7-12 7 12 7-12 5 6h1"/></g>
  <text class="fig-text fig-math" x="277" y="60" text-anchor="middle">R<tspan baseline-shift="sub" font-size="78%">out</tspan></text>
  <path class="fig-ink" d="M394 82v154H254m-62 0H96V106"/>
  <rect class="fig-ink" x="192" y="218" width="62" height="36" rx="6"/>
  <text class="fig-text fig-math" x="223" y="241" text-anchor="middle">K</text>
  <text class="fig-text fig-math" x="139" y="218" text-anchor="middle">v<tspan baseline-shift="sub" font-size="78%">F</tspan></text>
  <path class="fig-ink" d="M154 236l7-4m-7 4 7 4"/>
  <g data-elem="load">
    <path class="fig-ink" d="M323 82v47m0 44v23"/>
    <g class="sym"><path class="fig-ink" d="M323 129v5l-6 4 12 7-12 7 12 7-6 4v10"/></g>
    <circle class="fig-dot" cx="323" cy="82" r="3"/>
    ${ground(323, 196)}
    <text class="fig-text fig-math" x="343" y="150">R<tspan baseline-shift="sub" font-size="78%">L</tspan></text>
  </g>
  <g data-badges>
    <g data-badge-for="in" transform="translate(38,26)"/>
    <g data-badge-for="err" transform="translate(134,26)"/>
    <g data-badge-for="out" transform="translate(386,26)"/>
  </g>
</svg>`;

function solve(mna, gain, k, loadOn) {
  const elements = [
    { id: 'vin', type: 'vsrc', n1: 'in', n2: '0', value: 1e-3 },
    { id: 'vf', type: 'R', n1: 'f', n2: '0', value: 1000 },
    { id: 'sense', type: 'vccs', n1: '0', n2: 'f', cp: 'out', cn: '0', gm: k / 1000 },
    // Exact Norton equivalent of A₀·(v_in − v_F) in series with 1 kΩ.
    { id: 'rout', type: 'R', n1: 'out', n2: '0', value: 1000 },
    { id: 'a0', type: 'vccs', n1: '0', n2: 'out', cp: 'in', cn: 'f', gm: gain / 1000 },
  ];
  if (loadOn) elements.push({ id: 'load', type: 'R', n1: 'out', n2: '0', value: 100 });
  const answer = mna.solveCircuit({ elements });
  if (!answer.ok) throw new Error(answer.reason);
  return {
    gain: answer.nodes.out.re / answer.nodes.in.re,
    outMv: 1000 * answer.nodes.out.re,
    errMv: 1000 * (answer.nodes.in.re - answer.nodes.f.re),
  };
}

module.exports = {
  id: 'ec2-1113-loaded-voltage-feedback',
  title: '출력 부하와 1/K 근사',
  archetype: 'approx',
  modes: [{ key: 'vv', label: '전압–전압 귀환', svg, ariaLabel: '차동 전압 이득 블록과 직렬 출력 저항, 병렬 출력 부하, 이상적인 전압 감지 및 반송 블록' }],
  predict: {
    prompt: '개루프 이득이 100이고 귀환 계수 K가 0.1입니다. 출력에 100 Ω 부하를 달면 1/K 근사의 오차는 어떻게 될까요?',
    options: [{ id: 'larger', label: '오차가 커진다' }, { id: 'same', label: '오차가 같다' }, { id: 'smaller', label: '오차가 작아진다' }],
    answerId: 'larger',
    explain: '출력 저항과 부하가 전압을 나눠 가지므로, 같은 입력 오차에서 감지되는 출력 전압이 작아집니다. 유효 루프 이득도 낮아져 이득이 1/K에서 멀어집니다.',
    check: {
      before: { params: { gain: 100, k: 0.1 }, disabledElems: ['load'] },
      after: { params: { gain: 100, k: 0.1 }, disabledElems: [] },
      tiles: ['exact', 'error'],
    },
  },
  params: [
    { key: 'gain', label: '무부하 개루프 이득 A₀', min: 2, max: 10000, def: 100, scale: 'log', unit: 'V/V' },
    { key: 'k', label: '귀환 계수 K', min: 0.05, max: 0.5, def: 0.1, step: 0.01 },
  ],
  elems: [{ id: 'load', label: '출력 부하 100 Ω 연결' }],
  initialDisabledElems: ['load'],
  presets: [
    { id: 'open', label: '무부하 · A₀ = 100', params: { gain: 100, k: 0.1 }, disabledElems: ['load'] },
    { id: 'loaded', label: '부하 연결 · A₀ = 100', params: { gain: 100, k: 0.1 }, disabledElems: [] },
    { id: 'recovered', label: '부하 연결 · A₀ = 10,000', params: { gain: 10000, k: 0.1 }, disabledElems: [] },
  ],
  steps: [
    { title: '무부하 기준 읽기', text: '점선 1/K와 실선의 차이를 읽어요.', params: { gain: 100, k: 0.1 }, disabledElems: ['load'] },
    { title: '부하를 달아 보기', text: '개루프 이득과 K를 그대로 두고 곡선과 오차가 어떻게 바뀌는지 확인해요.', params: { gain: 100, k: 0.1 }, disabledElems: [] },
    { title: '개루프 이득 높이기', text: '부하가 연결된 상태에서 실선이 점선에 다가가는지 확인해요.', params: { gain: 10000, k: 0.1 }, disabledElems: [] },
  ],
  toggles: [['labels', '노드 배지', true]],
  mistakes: {
    vv: [
      { title: '개루프 이득이 크면 언제나 근사가 맞는다?', text: '부하를 포함한 유효 루프 이득이 충분히 커야 합니다.' },
      { title: '감지 블록이 이상적이므로 출력 부하도 무시한다?', text: '감지 블록은 전류를 끌어가지 않지만, 외부 부하에는 전류가 흐릅니다.' },
      { title: '1/K에 가까워지면 K도 변한 것이다?', text: 'K는 감지 전압의 비율입니다. 현재 곡선과 점선의 차이는 유한한 루프 이득에서 생깁니다.' },
    ],
  },
  evaluate(state, mna) {
    const { gain, k } = state.params;
    const loadOn = !state.disabledElems.includes('load');
    const result = solve(mna, gain, k, loadOn);
    const approximation = 1 / k;
    const error = 100 * (approximation - result.gain) / approximation;
    const effectiveGain = gain / (loadOn ? 11 : 1);
    const curve = Array.from({ length: 33 }, (_, index) => {
      const a = 2 * 5000 ** (index / 32);
      return [a, solve(mna, a, k, loadOn).gain];
    });
    const badge = (mv) => ({ badge: `${mv.toFixed(mv < 0.1 ? 3 : 2)} mV` });

    return {
      tiles: [
        { id: 'exact', label: '폐루프 이득', val: `${result.gain.toFixed(3)} V/V` },
        { id: 'loop', label: '유효 루프 이득', val: (effectiveGain * k).toFixed(3) },
        { id: 'error', label: '근사 오차 (1/K 기준)', val: `${error.toFixed(2)}%` },
      ],
      nodes: { in: badge(1), err: badge(result.errMv), out: badge(result.outMv) },
      elems: { load: { hot: loadOn } },
      diagnosis: {
        kind: error > 10 ? 'warn' : 'ok',
        title: error > 10 ? '근사 오차 10% 초과' : '근사 오차 10% 이하',
        text: loadOn
          ? tex`100 Ω 부하가 1 kΩ 출력 저항과 분압을 이루어 유효 개루프 이득은 $A_0/11$입니다.`
          : tex`출력이 개방되어 유효 개루프 이득은 $A_0$입니다.`,
      },
      equations: [
        tex`$$v_1=v_{\mathrm{in}}-Kv_{\mathrm{out}}$$`,
        tex`$$A_{\mathrm{cl}}=\frac{A_{\mathrm{eff}}}{1+KA_{\mathrm{eff}}}$$`,
      ],
      summary: '(교과서 보충) 입력은 1 mV입니다. 선형 저주파 증폭기와 이상적인 전압 감지·반송을 사용해 외부 부하의 영향만 비교합니다.',
      plotData: {
        title: '개루프 이득에 따른 폐루프 이득',
        xLabel: '무부하 개루프 이득 A₀',
        yLabel: '폐루프 이득 (V/V)',
        xScale: 'log', xMin: 2, xMax: 10000, yMin: 0,
        exact: curve,
        approx: [[2, approximation], [10000, approximation]],
        exactLabel: '회로 해석', approxLabel: '1/K 근사',
        marker: [gain, result.gain], approxMarker: [gain, approximation],
        errPct: error, thresholdPct: 10,
      },
    };
  },
};
