const gm = 1 / 150;
const cx = 350e-15;
const cgd = 80e-15;
const cdb = 100e-15;
const hzToMHz = 1e-6;
const minFreq = 10;
const maxFreq = 20000;

const circuit = [
  '<svg id="cg-schematic" viewBox="0 0 640 250" role="img" aria-label="공통 게이트 소신호 회로. 신호원이 직렬 저항을 거쳐 소스 X를 구동하고, 종속 전류원이 드레인 Y에서 X 방향으로 연결되어 있다.">',
  '  <style>',
  '    @media (max-width: 639px) {',
  '      #cg-schematic .fig-math { font-size: 19px; }',
  '      #cg-schematic .fig-muted, #cg-schematic .lab-badge-text { font-size: 17px; }',
  '    }',
  '  </style>',
  '  <path class="fig-ink" data-causal-step="1" d="M48 125V100H88M152 100H312"/>',
  '  <g class="sym" data-causal-step="1">',
  '    <circle class="fig-ink" cx="48" cy="146" r="21"/>',
  '    <path class="fig-ink" d="M35 146q6-13 13 0t13 0"/>',
  '    <text class="fig-text fig-math" x="75" y="149">v<tspan baseline-shift="sub" font-size="78%">sig</tspan></text>',
  '  </g>',
  '  <g class="sym"><path class="fig-ink" d="M48 167v37m-12 0h24m-20 6h16m-12 6h8"/></g>',
  '  <g class="sym" data-causal-step="1">',
  '    <path class="fig-ink" d="M88 100h6l4-9 7 18 7-18 7 18 7-18 7 18 7-18 6 9h6"/>',
  '    <text class="fig-text fig-math" x="120" y="78" text-anchor="middle">R<tspan baseline-shift="sub" font-size="78%">S</tspan></text>',
  '  </g>',
  '  <g data-branch="ix" data-causal-step="1">',
  '    <path class="fig-ink" d="M213 100v43m0 11v50"/>',
  '    <g class="sym"><path class="fig-ink" d="M201 143h24m-24 11h24m-24 50h24m-20 6h16m-12 6h8"/></g>',
  '    <text class="fig-text fig-math" x="235" y="153">C<tspan baseline-shift="sub" font-size="78%">X</tspan></text>',
  '  </g>',
  '  <g class="sym" data-branch="gm" data-causal-step="2">',
  '    <path class="fig-ink" d="M312 100l27-26 27 26-27 26zM352 100h-26m0 0 7-5m-7 5 7 5"/>',
  '    <text class="fig-text fig-math" x="339" y="150" text-anchor="middle">g<tspan baseline-shift="sub" font-size="78%">m</tspan>v<tspan baseline-shift="sub" font-size="78%">gs</tspan></text>',
  '  </g>',
  '  <path class="fig-ink" data-causal-step="3" d="M366 100H577"/>',
  '  <g data-causal-step="3">',
  '    <path class="fig-ink" d="M420 100v23m0 51v30"/>',
  '    <g class="sym"><path class="fig-ink" d="M420 123v4l-8 5 16 7-16 7 16 7-16 7 16 7-8 4v3m-12 30h24m-20 6h16m-12 6h8"/></g>',
  '    <text class="fig-text fig-math" x="442" y="153">R<tspan baseline-shift="sub" font-size="78%">D</tspan></text>',
  '  </g>',
  '  <g data-branch="iy" data-causal-step="3">',
  '    <path class="fig-ink" d="M500 100v43m0 11v50"/>',
  '    <g class="sym"><path class="fig-ink" d="M488 143h24m-24 11h24m-24 50h24m-20 6h16m-12 6h8"/></g>',
  '    <text class="fig-text fig-math" x="520" y="153">C<tspan baseline-shift="sub" font-size="78%">GD</tspan></text>',
  '  </g>',
  '  <g data-elem="cdb" data-causal-step="3" aria-label="드레인 바디 용량 전환">',
  '    <path class="fig-ink" d="M577 100v43m0 11v50"/>',
  '    <g class="sym"><path class="fig-ink" d="M565 143h24m-24 11h24m-24 50h24m-20 6h16m-12 6h8"/></g>',
  '    <text class="fig-text fig-math" x="597" y="153">C<tspan baseline-shift="sub" font-size="78%">DB</tspan></text>',
  '  </g>',
  '  <circle class="fig-dot" data-node="x" data-node-color="blue" cx="213" cy="100" r="4"/>',
  '  <text class="fig-text fig-math" data-node-color="blue" x="213" y="75" text-anchor="middle">X · 소스</text>',
  '  <circle class="fig-dot" data-node="y" data-node-color="red" cx="420" cy="100" r="4"/>',
  '  <text class="fig-text fig-math" data-node-color="red" x="420" y="75" text-anchor="middle">Y · 드레인</text>',
  '  <circle class="fig-dot" cx="500" cy="100" r="3"/>',
  '  <circle class="fig-dot" cx="577" cy="100" r="3"/>',
  '  <text class="fig-muted" x="320" y="236" text-anchor="middle">게이트와 바디는 AC 접지 · v<tspan baseline-shift="sub" font-size="78%">gs</tspan> = −v<tspan baseline-shift="sub" font-size="78%">x</tspan></text>',
  '  <g data-badges><g data-badge-for="x" transform="translate(213 32)"/><g data-badge-for="y" transform="translate(420 32)"/></g>',
  '</svg>',
].join('\n');

const start = { rs: 200, rd: 2000, f: 442 };
const cross = { rs: 1000, rd: 235, f: 2330 };
const inputFirst = { rs: 1000, rd: 70, f: 5200 };
const fLabel = (value) => value.toFixed(1) + ' MHz';
const db = (gain) => 20 * Math.log10(gain);

module.exports = {
  id: 'ec2-1030-cg-pole-bottleneck',
  title: '공통 게이트의 대역폭은 어디서 막힐까?',
  archetype: 'approx',
  modes: [{ key: 'cg', label: '공통 게이트', ariaLabel: '공통 게이트 소신호 회로', svg: circuit }],
  predict: {
    prompt: '출력 극점이 더 낮을 때, $R_D$를 충분히 줄이면 어떤 일이 생길까요?',
    options: [
      { id: 'shift', label: '입력 쪽이 대역폭을 제한할 수 있다' },
      { id: 'same', label: '출력 쪽이 계속 대역폭을 제한한다' },
    ],
    answerId: 'shift',
    explain: '$R_D$를 줄이면 출력 극점이 올라갑니다. 이 실험에서는 입력 극점이 더 낮아져 입력 쪽이 대역폭을 주로 제한합니다.',
    check: {
      before: { params: { rs: 1000, rd: start.rd }, disabledElems: [] },
      after: { params: { rd: inputFirst.rd, f: inputFirst.f }, causalStep: 3 },
      tiles: ['입력 극점', '출력 극점', '−3 dB 대역폭'],
    },
  },
  params: [
    { key: 'rs', label: '신호원 저항 Rₛ', min: 25, max: 2000, def: start.rs, unit: 'Ω', scale: 'log' },
    { key: 'rd', label: '드레인 저항 Rᴅ', min: 50, max: 3000, def: start.rd, unit: 'Ω', scale: 'log' },
    { key: 'f', label: '측정 주파수', min: minFreq, max: maxFreq, def: start.f, unit: 'MHz', scale: 'log' },
  ],
  elems: [{ id: 'cdb', label: '드레인–바디 용량 (100 fF)' }],
  causalSteps: [
    { id: 1, label: '소스 X를 구동', detail: '신호원 저항을 통과한 변화가 X에 나타납니다.' },
    { id: 2, label: '드레인 전류 변화', detail: '게이트가 AC 접지여서 X가 오르면 드레인에서 소스로 흐르는 전류가 줄어듭니다.' },
    { id: 3, label: '드레인 Y의 응답', detail: '드레인 저항과 접지 용량이 출력의 크기와 위상을 정합니다.' },
  ],
  presets: [
    { id: 'output', label: '출력 극점이 먼저', params: start, disabledElems: [] },
    { id: 'near', label: '두 극점이 만나는 곳', params: cross, disabledElems: [] },
    { id: 'input', label: '입력 극점이 먼저', params: inputFirst, disabledElems: [] },
  ],
  steps: [
    { title: '출력부터 확인', text: '측정점을 낮은 출력 극점 부근에 놓고 두 곡선을 비교하세요.', params: start, disabledElems: [], causalStep: 1 },
    { title: '두 극점이 겹칠 때', text: '측정점은 각각의 극점보다 낮습니다. 그래도 두 감쇠가 곱해져 벌써 약 3 dB 내려갑니다.', params: cross, disabledElems: [], causalStep: 3 },
    { title: '출력 용량을 줄이기', text: '드레인–바디 용량을 빼면 출력 극점이 올라갑니다. 입력 극점은 그대로입니다.', params: cross, disabledElems: ['cdb'], causalStep: 3 },
  ],
  toggles: [['labels', '노드 전압 크기 (신호원 10 mV)', true]],
  mistakes: {
    cg: [
      { title: '첫 극점을 곧바로 대역폭으로 쓰기', text: '극점 간격이 좁으면 두 감쇠가 곱해집니다. 같은 위치의 두 극점에서는 그 주파수에서 이미 약 6 dB가 줄어요.' },
      { title: '저항을 줄이면 언제나 이득도 좋아진다고 보기', text: '$R_D$를 낮추면 출력 극점은 올라가고, 신호원 기준 저주파 이득은 작아져요.' },
      { title: '게이트 접지에서 드레인 쪽 용량을 빼기', text: '$C_{GD}$는 드레인과 AC 접지 사이에 남아 출력 극점을 정하는 데 기여해요.' },
    ],
  },
  evaluate(state, mna) {
    const { rs, rd, f } = state.params;
    const hasCdb = !state.disabledElems.includes('cdb');
    const cy = cgd + (hasCdb ? cdb : 0);
    const elements = [
      { id: 'sig', type: 'vsrc', n1: 'sig', n2: '0', value: 0.01 },
      { id: 'rs', type: 'R', n1: 'sig', n2: 'x', value: rs },
      { id: 'cx', type: 'C', n1: 'x', n2: '0', value: cx },
      { id: 'gm', type: 'vccs', n1: 'y', n2: 'x', cp: '0', cn: 'x', gm },
      { id: 'rd', type: 'R', n1: 'y', n2: '0', value: rd },
      { id: 'cgd', type: 'C', n1: 'y', n2: '0', value: cgd },
      { id: 'cdb', type: 'C', n1: 'y', n2: '0', value: hasCdb ? cdb : 0 },
    ];
    const solve = (mhz) => mna.solveCircuit({ elements }, { freqHz: mhz * 1e6 });
    const dc = solve(0);
    const current = solve(f);
    const gain0 = dc.nodes.y.mag / dc.nodes.sig.mag;
    const normalized = (result) => result.nodes.y.mag / dc.nodes.y.mag;

    const fpX = hzToMHz * (1 / rs + gm) / (2 * Math.PI * cx);
    const fpY = hzToMHz / (2 * Math.PI * rd * cy);
    const firstPole = Math.min(fpX, fpY);
    const ratio = firstPole / Math.max(fpX, fpY);
    // Solve |H/H(0)|² = 1/2 in terms of (f / firstPole)².
    const bandwidth = firstPole * Math.sqrt(2 / (1 + ratio ** 2 + Math.hypot(1 + ratio ** 2, 2 * ratio)));
    const approx = (mhz) => 1 / Math.hypot(1, mhz / firstPole);
    const exactAtF = normalized(current);
    const approxAtF = approx(f);
    const errPct = 100 * Math.abs(approxAtF / exactAtF - 1);

    const frequencies = Array.from({ length: 65 }, (_, i) => minFreq * (maxFreq / minFreq) ** (i / 64));
    const near = ratio > 0.8;
    const first = fpX < fpY ? '입력 X' : '출력 Y';
    const phase = state.causalStep;
    const equation = '$$\\begin{aligned}f_X&=\\frac{1/R_S+g_m}{2\\pi C_X}\\\\ f_Y&=\\frac{1}{2\\pi R_DC_Y}\\end{aligned}$$';

    return {
      tiles: [
        { label: '입력 극점', val: fLabel(fpX) },
        { label: '출력 극점', val: fLabel(fpY) },
        { label: '−3 dB 대역폭', val: fLabel(bandwidth) },
      ],
      diagnosis: {
        kind: errPct >= 10 ? 'warn' : 'ok',
        title: near ? '두 극점이 비슷해요' : first + ' 극점이 먼저예요',
        text: '측정점에서 저주파 대비 ' + db(exactAtF).toFixed(2) + ' dB예요. 오차는 두 곡선의 선형 전압비 차이를 실선 기준 백분율로 표시해요.',
      },
      equations: [equation, '$$\\frac{H(s)}{H(0)}=\\frac{1}{(1+s/\\omega_X)(1+s/\\omega_Y)}$$'],
      summary: '저주파 이득은 ' + gain0.toFixed(3) + ' V/V예요. 이 모델에서 $R_D$를 낮추면 출력 극점이 올라가고 저주파 이득은 줄어요. $g_m=1/(150\\,\\Omega)$, $C_X=350\\,\\mathrm{fF}$인 소신호 회로예요. $C_X$에는 실험에서 가정한 $C_{SB}=100\\,\\mathrm{fF}$를 포함했어요. $r_o$와 바디 효과는 생략했어요.',
      nodes: {
        x: { badge: (current.nodes.x.mag * 1e3).toFixed(2) + ' mV', hot: phase === 1 },
        y: { badge: (current.nodes.y.mag * 1e3).toFixed(2) + ' mV', hot: phase === 3 },
      },
      branches: { ix: { hot: phase === 1 }, gm: { hot: phase === 2 }, iy: { hot: phase === 3 } },
      elems: { cdb: { hot: hasCdb && phase === 3 } },
      plotData: {
        title: '저주파 대비 이득과 한 극점 근사',
        xLabel: '주파수 (MHz)', yLabel: '상대 이득 (dB)', xScale: 'log',
        xMin: minFreq, xMax: maxFreq, yMin: -60, yMax: 0,
        exact: frequencies.map((mhz) => [mhz, db(normalized(solve(mhz)))]),
        approx: frequencies.map((mhz) => [mhz, db(approx(mhz))]),
        exactLabel: '두 극점', approxLabel: '낮은 극점만',
        marker: [f, db(exactAtF)], approxMarker: [f, db(approxAtF)], errPct,
      },
    };
  },
};
