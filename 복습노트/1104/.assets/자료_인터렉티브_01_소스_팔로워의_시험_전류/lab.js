const circuit = `<svg viewBox="0 0 390 245" role="img" aria-label="소스 팔로워의 출력 임피던스 시험 회로">
  <path class="fig-ink" d="M193 94H346"/>
  <g data-causal-step="3">
  <path class="fig-ink" d="M48 94H133M48 94V132M48 169V197"/>
  <g class="sym">
    <path class="fig-ink" d="M48 132v4l-7 4 14 5-14 5 14 5-14 5 7 4v5M36 197h24m-20 5h16m-12 5h8"/>
  </g>
  <text class="fig-text fig-math" x="19" y="154">R<tspan baseline-shift="sub" font-size="78%">S</tspan></text>
  </g>
  <g data-elem="cgs" data-branch="cgs" data-causal-step="3">
    <path class="fig-ink" d="M133 94H157M169 94H193"/>
    <g class="sym"><path class="fig-ink" d="M157 80v28m12-28v28"/></g>
    <text class="fig-text fig-math" x="163" y="131" text-anchor="middle">C<tspan baseline-shift="sub" font-size="78%">GS</tspan></text>
  </g>
  <g data-branch="gm" data-causal-step="2">
    <path class="fig-ink" d="M238 94V130M238 174V197"/>
    <g class="sym">
      <path class="fig-ink" d="M238 130l22 22-22 22-22-22zM238 141v22m-5-6 5 6 5-6M226 197h24m-20 5h16m-12 5h8"/>
    </g>
    <text class="fig-text fig-math" x="255" y="190">g<tspan baseline-shift="sub" font-size="78%">m</tspan>(v<tspan baseline-shift="sub" font-size="78%">x</tspan>−v<tspan baseline-shift="sub" font-size="78%">g</tspan>)</text>
  </g>
  <g data-causal-step="1">
    <path class="fig-ink" d="M346 94V134M346 170V197"/>
    <g class="sym">
      <circle class="fig-ink" cx="346" cy="152" r="18"/>
      <path class="fig-ink" d="M342 145h8m-4-4v8m-4 11h8M334 197h24m-20 5h16m-12 5h8"/>
    </g>
    <text class="fig-text fig-math" x="364" y="123">i<tspan baseline-shift="sub" font-size="78%">x</tspan> ↑</text>
  </g>
  <circle class="fig-dot" data-node="g" data-node-color="blue" cx="48" cy="94" r="4"/>
  <text class="fig-text fig-math" data-node="g" data-node-color="blue" x="48" y="71" text-anchor="middle">v<tspan baseline-shift="sub" font-size="78%">g</tspan></text>
  <circle class="fig-dot" data-node="x" data-node-color="red" cx="346" cy="94" r="4"/>
  <circle class="fig-dot" cx="238" cy="94" r="3.5"/>
  <text class="fig-text fig-math" data-node="x" data-node-color="red" x="346" y="71" text-anchor="middle">v<tspan baseline-shift="sub" font-size="78%">x</tspan></text>
  <text class="fig-muted" x="48" y="229" text-anchor="middle">입력 영점화</text>
  <text class="fig-muted" x="238" y="229" text-anchor="middle">드레인 AC 접지</text>
  <text class="fig-muted" x="346" y="229" text-anchor="middle">시험원 10 mV</text>
  <g data-badges>
    <g data-badge-for="g" transform="translate(50,30)"/>
    <g data-badge-for="x" transform="translate(339,30)"/>
  </g>
</svg>`;

const testVoltage = 0.01;
const defaultParams = { freq: 20, rs: 1000, gm: 10 };
const frequencies = Array.from({ length: 81 }, (_, index) => 30000 ** (index / 80));
const omegaText = (value) => `${value.toFixed(1)} Ω`;
const currentText = (amps) => `${(amps * 1e6).toFixed(1)} μA`;

module.exports = {
  id: 'ec2-1104-follower-current',
  title: '소스 팔로워의 시험 전류',
  archetype: 'approx',
  modes: [{ key: 'follower', label: '소스 팔로워', svg: circuit, ariaLabel: '소스 팔로워 출력 시험 회로' }],
  predict: {
    prompt: '앞단 저항이 $1/g_m$보다 클 때 주파수를 올리면 출력 임피던스의 크기는 어떻게 될까요?',
    options: [{ id: 'up', label: '커진다' }, { id: 'down', label: '작아진다' }, { id: 'flat', label: '그대로다' }],
    answerId: 'up',
    explain: '높은 주파수에서는 게이트가 소스를 따라 움직이고 시험 전류가 커패시터를 거쳐 앞단 저항으로 흐릅니다.',
  },
  params: [
    { key: 'freq', label: '시험 주파수', min: 1, max: 30000, scale: 'log', unit: 'MHz', def: defaultParams.freq },
    { key: 'rs', label: '앞단 저항 Rₛ', min: 50, max: 1500, step: 1, unit: 'Ω', def: defaultParams.rs },
    { key: 'gm', label: '트랜스컨덕턴스 gₘ', min: 2, max: 20, step: 0.5, unit: 'mS', def: defaultParams.gm },
  ],
  elems: [{ id: 'cgs', label: '게이트–소스 C (1 pF)' }],
  causalSteps: [
    { id: 1, label: '시험 전압을 건다', detail: '입력 독립 전압을 0으로 두고 출력에 10 mV의 교류 시험 전압을 겁니다.' },
    { id: 2, label: '제어 전류를 본다', detail: '게이트와 소스의 전압 차가 클수록 트랜지스터 가지의 교류 전류가 큽니다.' },
    { id: 3, label: '커패시터 전류를 본다', detail: '주파수가 올라가면 시험 전류가 게이트–소스 C를 지나 앞단 저항으로 더 많이 분배됩니다.' },
  ],
  presets: [
    { id: 'low', label: '저주파 · 1 MHz', params: { ...defaultParams, freq: 1 }, disabledElems: [] },
    { id: 'high', label: '고주파 · 30 GHz', params: { ...defaultParams, freq: 30000 }, disabledElems: [] },
    { id: 'equal', label: '경계 · Rₛ = 1/gₘ', params: { ...defaultParams, rs: 100, freq: 1000 }, disabledElems: [] },
  ],
  steps: [
    { title: '저주파에서 전류 비교', text: '게이트는 AC 접지에 가까워요. 시험 전류는 대부분 제어 전류 가지로 가요.', params: { ...defaultParams, freq: 1 }, disabledElems: [], causalStep: 2 },
    { title: '고주파에서 전류 비교', text: '게이트가 소스를 따라가요. 시험 전류는 대부분 앞단 저항으로 가요.', params: { ...defaultParams, freq: 30000 }, disabledElems: [], causalStep: 3 },
  ],
  mistakes: {
    follower: [
      { title: '출력 임피던스는 항상 1/gₘ', text: '$1/g_m$은 이 모델의 저주파 값입니다. $C_{GS}$가 켜져 있으면 고주파에서 $R_S$에 접근합니다.' },
      { title: '게이트와 소스의 전압이 비슷하면 커패시터 전류도 0', text: '전압 차는 줄지만 $|i_C|=2\\pi f C_{GS}|v_x-v_g|$입니다. 고주파에서 커패시터 전류는 $|v_x|/R_S$에 접근합니다.' },
      { title: '교류 가지 전류를 크기만 더하면 된다', text: '두 가지 전류에 위상 차가 있습니다. 시험 전류는 두 전류의 페이저 합입니다.' },
    ],
  },
  evaluate(state, mna) {
    const { freq, rs, gm: gmMilliSiemens } = state.params;
    const gm = gmMilliSiemens * 1e-3;
    const capOn = !state.disabledElems.includes('cgs');
    const elements = [
      { id: 'test', type: 'vsrc', n1: 'x', n2: '0', value: testVoltage },
      { id: 'rs', type: 'R', n1: 'g', n2: '0', value: rs },
      { id: 'cgs', type: 'C', n1: 'x', n2: 'g', value: capOn ? 1e-12 : 0 },
      { id: 'gm', type: 'vccs', n1: 'x', n2: '0', cp: 'x', cn: 'g', gm },
    ];
    const at = (mhz) => mna.solveCircuit({ elements }, { freqHz: mhz * 1e6 });
    const result = at(freq);
    const low = testVoltage / at(0).branches.test.mag;
    const magnitude = testVoltage / result.branches.test.mag;
    const phase = Math.atan2(result.branches.test.im, -result.branches.test.re) * 180 / Math.PI;
    const capCurrent = result.branches.cgs.mag;
    const gmCurrent = result.branches.gm.mag;
    const error = 100 * Math.abs(low - magnitude) / magnitude;
    const main = capCurrent > gmCurrent
      ? '커패시터를 지나 앞단 저항으로 가는 전류가 더 큽니다.'
      : '트랜지스터의 제어 전류가 커패시터 전류보다 크거나 같습니다.';
    const phaseLabel = Math.abs(phase) < 0.05 ? '0.0' : phase.toFixed(1);

    return {
      tiles: [
        { label: '출력 임피던스 크기', val: omegaText(magnitude) },
        { label: '커패시터 전류', val: currentText(capCurrent) },
        { label: '제어 전류', val: currentText(gmCurrent) },
      ],
      diagnosis: {
        kind: error >= 10 ? 'warn' : 'ok',
        title: capOn ? '선택 주파수의 시험 전류' : '커패시터 개방',
        text: capOn ? main : '시험 전류가 제어 전류와 같습니다. 모든 주파수에서 출력 임피던스는 $1/g_m$입니다.',
      },
      summary: `출력 임피던스 위상은 ${phaseLabel}°, 시험 전류의 크기는 ${currentText(result.branches.test.mag)}입니다. 저주파 값은 ${omegaText(low)}이고, ${capOn ? `모델의 고주파 극한은 ${omegaText(rs)}입니다.` : '이 설정에서는 주파수에 따라 변하지 않습니다.'}`,
      formula: String.raw`$$\begin{aligned}
      Z_{\mathrm{out}}&=\frac{v_x}{i_x}\\
      &=\frac{1+sR_SC_{GS}}{g_m+sC_{GS}}
      \end{aligned}$$
      $s=j2\pi f$. 소신호 모델에서 $r_o$, 몸체효과, 나머지 기생 용량을 생략합니다.`,
      nodes: {
        g: { badge: `${(result.nodes.g.mag * 1000).toFixed(2)} mV`, hot: state.causalStep === 3 },
        x: { badge: '10.00 mV', hot: state.causalStep === 1 },
      },
      branches: {
        cgs: { hot: capOn && capCurrent > gmCurrent },
        gm: { hot: gmCurrent >= capCurrent },
      },
      plotData: {
        title: '시험 주파수에 따른 출력 임피던스', xLabel: 'f (MHz)', yLabel: '|Z| (Ω)', xScale: 'log',
        xMin: 1, xMax: 30000, yMin: 0, yMax: Math.max(low, capOn ? rs : low) * 1.15,
        exact: frequencies.map((f) => [f, testVoltage / at(f).branches.test.mag]),
        approx: [[1, low], [30000, low]],
        exactLabel: '소신호 해석', approxLabel: '저주파 1/gₘ',
        marker: [freq, magnitude], approxMarker: [freq, low], errPct: error,
      },
    };
  },
};
