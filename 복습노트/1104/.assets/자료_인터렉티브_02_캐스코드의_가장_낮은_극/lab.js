const circuit = `<svg viewBox="0 0 520 294" role="img" aria-label="유한 출력저항을 생략한 MOS 캐스코드의 소신호 등가 회로">
  <g data-causal-step="1">
    <path class="fig-ink" d="M37 118h26m54 0h37M37 118v80m0 32v20M154 118v54m0 12v66"/>
    <g class="sym">
      <path class="fig-ink" d="M63 118h8l4-7 6 14 6-14 6 14 6-14 6 14 4-7h8M142 172h24m-24 12h24M142 250h24m-20 5h16m-12 5h8"/>
      <circle class="fig-ink" cx="37" cy="214" r="16"/>
      <path class="fig-ink" d="M32 209h10m-5-5v10m-5 8h10M25 250h24m-20 5h16m-12 5h8"/>
    </g>
    <text class="fig-text fig-math" x="90" y="99" text-anchor="middle">R<tspan baseline-shift="sub" font-size="78%">S</tspan></text>
    <text class="fig-text fig-math" x="37" y="282" text-anchor="middle">v<tspan baseline-shift="sub" font-size="78%">sig</tspan></text>
    <text class="fig-text fig-math" x="131" y="207" text-anchor="end">C<tspan baseline-shift="sub" font-size="78%">GS1</tspan></text>
  </g>
  <g data-elem="cgd" data-branch="feedbackCap" data-causal-step="2">
    <path class="fig-ink" d="M154 118V65h54m12 0h54v53"/>
    <g class="sym"><path class="fig-ink" d="M208 51v28m12-28v28"/></g>
    <text class="fig-text fig-math" x="213" y="42" text-anchor="middle">C<tspan baseline-shift="sub" font-size="78%">GD1</tspan></text>
  </g>
  <g data-causal-step="2">
    <path class="fig-ink" d="M228 148v-30h46v54m0 12v66M228 192v58"/>
    <g class="sym">
      <path class="fig-ink" d="M228 148l22 22-22 22-22-22zM228 158v23m-5-6 5 6 5-6M216 250h24m-20 5h16m-12 5h8M262 172h24m-24 12h24M262 250h24m-20 5h16m-12 5h8"/>
    </g>
    <text class="fig-text fig-math" x="228" y="282" text-anchor="middle">g<tspan baseline-shift="sub" font-size="78%">m1</tspan>v<tspan baseline-shift="sub" font-size="78%">X</tspan></text>
    <text class="fig-text fig-math" x="299" y="182">C<tspan baseline-shift="sub" font-size="78%">Y0</tspan></text>
  </g>
  <g data-branch="upper" data-causal-step="3">
    <path class="fig-ink" d="M274 118h47m44 0h120"/>
    <g class="sym"><path class="fig-ink" d="M321 118l22-22 22 22-22 22zM332 118h22m-16-5-6 5 6 5"/></g>
    <text class="fig-text fig-math" x="343" y="158" text-anchor="middle">−g<tspan baseline-shift="sub" font-size="78%">m2</tspan>v<tspan baseline-shift="sub" font-size="78%">Y</tspan></text>
  </g>
  <g data-causal-step="3">
    <path class="fig-ink" d="M420 118v44m0 46v42M485 118v54m0 12v66"/>
    <g class="sym">
      <path class="fig-ink" d="M420 162v6l-7 4 14 6-14 6 14 6-14 6 7 6v6M408 250h24m-20 5h16m-12 5h8M473 172h24m-24 12h24M473 250h24m-20 5h16m-12 5h8"/>
    </g>
    <text class="fig-text fig-math" x="397" y="189" text-anchor="end">R<tspan baseline-shift="sub" font-size="78%">L</tspan></text>
    <text class="fig-text fig-math" x="465" y="223" text-anchor="end">C<tspan baseline-shift="sub" font-size="78%">out</tspan></text>
  </g>
  <circle class="fig-dot" data-node="x" data-node-color="blue" cx="154" cy="118" r="4"/>
  <text class="fig-text fig-math" data-node="x" data-node-color="blue" x="132" y="142" text-anchor="end">v<tspan baseline-shift="sub" font-size="78%">X</tspan></text>
  <circle class="fig-dot" data-node="y" data-node-color="blue" cx="274" cy="118" r="4"/>
  <text class="fig-text fig-math" data-node="y" data-node-color="blue" x="292" y="97">v<tspan baseline-shift="sub" font-size="78%">Y</tspan></text>
  <circle class="fig-dot" data-node="out" data-node-color="red" cx="420" cy="118" r="4"/>
  <text class="fig-text fig-math" data-node="out" data-node-color="red" x="420" y="95" text-anchor="middle">v<tspan baseline-shift="sub" font-size="78%">out</tspan></text>
  <g data-badges>
    <g data-badge-for="x" transform="translate(108,23)"/>
    <g data-badge-for="y" transform="translate(314,23)"/>
    <g data-badge-for="out" transform="translate(420,23)"/>
  </g>
</svg>`;

const rs = 4000;
const gm1 = 0.005;
const cgs = 0.6e-12;
const cy0 = 0.3e-12;
const cout = 1e-12;
const defaults = { rl: 2, gm2: 5, freq: 40 };
const frequencies = Array.from({ length: 101 }, (_, index) => 1000 ** (index / 100));
const db = (gain) => 20 * Math.log10(gain);
const mhz = (value) => `${value.toFixed(1)} MHz`;

module.exports = {
  id: 'ec2-1104-cascode-pole',
  title: '캐스코드의 가장 낮은 극',
  archetype: 'approx',
  modes: [{ key: 'cascode', label: 'MOS 캐스코드', svg: circuit, ariaLabel: 'MOS 캐스코드 소신호 등가 회로' }],
  predict: {
    prompt: '출력 부하 저항을 키워 입력과 출력의 추정 극 주파수가 가까워졌어요. 전체 −3 dB 대역폭은 그 주파수와 어떻게 비교될까요?',
    options: [{ id: 'lower', label: '더 낮다' }, { id: 'equal', label: '거의 같다' }, { id: 'higher', label: '더 높다' }],
    answerId: 'lower',
    explain: '입력과 출력에서 감쇠가 겹쳐 전체 응답이 더 낮은 주파수에서 −3 dB에 도달합니다.',
    check: {
      after: { params: { ...defaults, rl: 4 }, disabledElems: [], causalStep: 3 },
      tiles: ['한 극으로 추정', '전체 −3 dB'],
    },
  },
  params: [
    { key: 'rl', label: '부하 저항 Rₗ', min: 1, max: 20, step: 0.05, unit: 'kΩ', def: defaults.rl },
    { key: 'gm2', label: '위 소자의 gₘ₂', min: 2, max: 12, step: 0.5, unit: 'mS', def: defaults.gm2 },
    { key: 'freq', label: '관찰 주파수', min: 1, max: 1000, scale: 'log', unit: 'MHz', def: defaults.freq },
  ],
  elems: [{ id: 'cgd', label: 'X–Y 연결 C (0.2 pF)' }],
  causalSteps: [
    { id: 1, label: 'X의 입력 충전', detail: '앞단 저항을 통해 게이트 용량을 충전합니다. X–Y 연결 C가 켜져 있으면 이 가지에도 전류가 흐릅니다.' },
    { id: 2, label: 'Y의 국소 반전', detail: '아래 소자가 만드는 전류와 위 소자의 낮은 소스 쪽 저항이 Y의 전압을 정합니다.' },
    { id: 3, label: '출력의 부하와 충전', detail: '위 소자의 드레인 전류가 부하에 전압을 만들고 출력 용량을 충전합니다. 부하 저항이 커지면 출력 쪽 감쇠가 더 일찍 시작합니다.' },
  ],
  presets: [
    { id: 'input', label: '입력 극이 낮음', params: { ...defaults }, disabledElems: [] },
    { id: 'meet', label: '두 극이 만나는 곳', params: { ...defaults, rl: 4 }, disabledElems: [] },
    { id: 'output', label: '출력 극이 낮음', params: { ...defaults, rl: 10, freq: 16 }, disabledElems: [] },
  ],
  steps: [
    { title: 'X 쪽 밀러 용량 줄이기', text: '위 소자의 gₘ₂를 바꿔 보세요. 커지면 Y가 덜 움직여 X 쪽 밀러 배율이 작아집니다.', params: { ...defaults, gm2: 12 }, disabledElems: [], causalStep: 2 },
    { title: '−3 dB 대역폭 비교', text: '두 극이 가까울 때 가장 낮은 극 하나로 읽은 대역폭과 전체 회로의 대역폭을 비교하세요.', params: { ...defaults, rl: 4 }, disabledElems: [], causalStep: 3 },
  ],
  mistakes: {
    cascode: [
      { title: '전체 이득으로 X 쪽 밀러 배율을 계산한다', text: '$C_{GD1}$의 두 끝은 X와 Y입니다. 밀러 배율을 정하는 것은 $v_Y/v_X$입니다.' },
      { title: '용량이 큰 노드가 가장 낮은 극을 만든다', text: '극의 순서는 $RC$ 곱으로 추정합니다. Y에 용량이 모여도 $1/g_{m2}$가 작아 시정수가 짧을 수 있습니다.' },
      { title: '가장 낮은 극이 항상 −3 dB 주파수다', text: '극이 가까우면 여러 노드의 감쇠가 겹칩니다. 전체 응답이 저주파보다 3.01 dB 낮아지는 주파수를 따로 읽어야 합니다.' },
    ],
  },
  evaluate(state, mna) {
    const { rl: rlKiloOhms, gm2: gmMilliSiemens, freq } = state.params;
    const rl = rlKiloOhms * 1000;
    const gm2 = gmMilliSiemens * 1e-3;
    const capOn = !state.disabledElems.includes('cgd');
    const cgd = capOn ? 0.2e-12 : 0;
    const elements = [
      { id: 'sig', type: 'vsrc', n1: 'sig', n2: '0', value: 1 },
      { id: 'rs', type: 'R', n1: 'sig', n2: 'x', value: rs },
      { id: 'cgs', type: 'C', n1: 'x', n2: '0', value: cgs },
      { id: 'cgd', type: 'C', n1: 'x', n2: 'y', value: cgd },
      { id: 'cy0', type: 'C', n1: 'y', n2: '0', value: cy0 },
      { id: 'gm1', type: 'vccs', n1: 'y', n2: '0', cp: 'x', cn: '0', gm: gm1 },
      { id: 'gm2', type: 'vccs', n1: 'out', n2: 'y', cp: '0', cn: 'y', gm: gm2 },
      { id: 'rl', type: 'R', n1: 'out', n2: '0', value: rl },
      { id: 'cout', type: 'C', n1: 'out', n2: '0', value: cout },
    ];
    const at = (mhz) => mna.solveCircuit({ elements }, { freqHz: mhz * 1e6 });
    const dc = at(0);
    const local = dc.nodes.y.re / dc.nodes.x.re;
    const tauX = rs * (cgs + (1 - local) * cgd);
    const tauY = (cy0 + (1 - 1 / local) * cgd) / gm2;
    const tauOut = rl * cout;
    const times = [tauX, tauY, tauOut];
    const [longest, second] = [...times].sort((a, b) => b - a);
    const names = ['X', 'Y', '출력'].filter((_, i) => Math.abs(times[i] - longest) < 1e-14).join(' · ');
    const pole = 1 / (2 * Math.PI * longest * 1e6);
    const dcGain = dc.nodes.out.mag;
    const response = (f) => at(f).nodes.out.mag / dcGain;
    const onePole = (f) => 1 / Math.hypot(1, f / pole);
    let lower = 0;
    let upper = 1000;
    for (let i = 0; i < 24; i++) {
      const mid = (lower + upper) / 2;
      if (response(mid) > Math.SQRT1_2) lower = mid;
      else upper = mid;
    }
    const bandwidth = (lower + upper) / 2;
    const point = at(freq);
    const gain = point.nodes.out.mag / dcGain;
    const error = 100 * Math.abs(onePole(freq) - gain) / gain;
    const badge = (node) => `${node.mag.toFixed(2)} V/V`;
    const time = (tau) => `${(tau * 1e9).toFixed(2)} ns`;
    const spread = longest / second;

    return {
      tiles: [
        { label: '가장 낮은 추정 극', val: names },
        { label: '한 극으로 추정', val: mhz(pole) },
        { label: '전체 −3 dB', val: mhz(bandwidth) },
      ],
      diagnosis: {
        kind: error >= 10 ? 'warn' : 'ok',
        title: spread < 2 ? '두 추정 극이 가까워요' : '시정수의 크기를 비교해요',
        text: `X ${time(tauX)}, Y ${time(tauY)}, 출력 ${time(tauOut)}. 그래프의 오차는 선택한 주파수에서 두 응답의 전압비 크기를 비교한 값입니다.`,
      },
      summary: `저주파 X→Y 이득은 ${local.toFixed(2)} V/V, 전체 저주파 이득은 ${dc.nodes.out.re.toFixed(1)} V/V입니다. 배지는 선택 주파수에서 신호원 대비 각 노드의 전압비 크기입니다.`,
      formula: String.raw`$$\begin{aligned}
      C_X&\approx C_{GS1}+(1-A_{XY})C_{GD1}\\
      f_{p,k}&\approx\frac{1}{2\pi R_k C_k}
      \end{aligned}$$
      $A_{XY}$에는 저주파 국소 이득을 씁니다. $C_{Y0}=C_{DB1}+C_{GS2}+C_{SB2}$입니다. 아래 소자의 $g_{m1}=5\,\mathrm{mS}$, $R_S=4\,\mathrm{k\Omega}$, $C_{GS1}=0.6\,\mathrm{pF}$, $C_{Y0}=0.3\,\mathrm{pF}$, $C_{out}=1\,\mathrm{pF}$입니다. 소신호 모델에서 $r_o$와 몸체효과를 생략했습니다.`,
      nodes: {
        x: { badge: badge(point.nodes.x), hot: state.causalStep === 1 },
        y: { badge: badge(point.nodes.y), hot: state.causalStep === 2 },
        out: { badge: badge(point.nodes.out), hot: state.causalStep === 3 },
      },
      branches: {
        feedbackCap: { hot: capOn && state.causalStep === 2 },
        upper: { hot: state.causalStep === 3 },
      },
      plotData: {
        title: '캐스코드의 저주파 대비 이득', xScale: 'log', xMin: 1, xMax: 1000,
        xLabel: 'f (MHz)', yLabel: '저주파 대비 (dB)',
        exactLabel: '소신호 해석', approxLabel: '가장 낮은 극만',
        exact: frequencies.map((f) => [f, db(response(f))]),
        approx: frequencies.map((f) => [f, db(onePole(f))]),
        marker: [freq, db(gain)], approxMarker: [freq, db(onePole(freq))], errPct: error,
      },
    };
  },
};
