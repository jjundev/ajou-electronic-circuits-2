const SVG = `<svg viewBox="0 0 426 259" role="img" aria-label="게이트와 드레인 사이에 CGD가 연결된 CS 소신호 회로">
  <g data-causal-step="1">
    <path class="fig-ink" d="M39 165v-33h28m41 0h23 M39 201v25"/>
    <g class="sym" data-symbol="vsrc">
      <circle class="fig-ink" cx="39" cy="183" r="18"/>
      <path class="fig-ink" d="M31 183h7v-7h9"/>
    </g>
    <g class="sym" data-symbol="resistor">
      <path class="fig-ink" d="M67 132h5l3-6 5 12 5-12 5 12 5-12 5 12 3-6h5"/>
    </g>
    <text class="fig-text fig-math" x="88" y="113" text-anchor="middle">R<tspan baseline-shift="sub" font-size="78%">S</tspan></text>
    <text class="fig-text fig-math" x="62" y="190">+1 mV</text>
    <path class="fig-ink" d="M131 132v47m0 12v35"/>
    <g class="sym" data-symbol="capacitor"><path class="fig-ink" d="M120 179h22m-22 12h22"/></g>
    <text class="fig-text fig-math" x="152" y="190">C<tspan baseline-shift="sub" font-size="78%">GS</tspan></text>
    <circle class="fig-dot" data-node="gate" data-node-color="blue" cx="131" cy="132" r="3.5"/>
    <text class="fig-text fig-math" data-node-color="blue" x="106" y="157" text-anchor="middle">v<tspan baseline-shift="sub" font-size="78%">G</tspan></text>
  </g>
  <g data-elem="cgd" data-branch="cgd" data-causal-step="2" aria-label="게이트–드레인 커패시턴스 CGD">
    <path class="fig-ink" d="M131 132V82h74m12 0h70v50"/>
    <g class="sym" data-symbol="capacitor"><rect x="182" y="39" width="58" height="58" opacity="0" pointer-events="all"/><path class="fig-ink" d="M205 71v22m12-22v22"/></g>
    <text class="fig-text fig-math" x="211" y="56" text-anchor="middle">C<tspan baseline-shift="sub" font-size="78%">GD</tspan></text>
  </g>
  <g data-causal-step="3">
    <path class="fig-ink" d="M230 166v-34h149v47m0 12v35 M230 204v22 M318 132v35m0 40v19"/>
    <g class="sym" data-symbol="vccs" data-branch="gm">
      <path class="fig-ink" d="m230 166 19 19-19 19-19-19Z M230 175v19m-5-5 5 5 5-5"/>
    </g>
    <text class="fig-text fig-math" x="219" y="216" text-anchor="end">g<tspan baseline-shift="sub" font-size="78%">m</tspan>v<tspan baseline-shift="sub" font-size="78%">G</tspan></text>
    <g class="sym" data-symbol="resistor">
      <path class="fig-ink" d="M318 167v6l-6 4 12 5-12 5 12 5-12 5 6 4v6"/>
    </g>
    <text class="fig-text fig-math" x="340" y="190">R<tspan baseline-shift="sub" font-size="78%">L</tspan></text>
    <g class="sym" data-symbol="capacitor"><path class="fig-ink" d="M368 179h22m-22 12h22"/></g>
    <text class="fig-text fig-math" x="394" y="190">C<tspan baseline-shift="sub" font-size="78%">DB</tspan></text>
    <circle class="fig-dot" data-node-color="red" cx="318" cy="132" r="3"/>
    <circle class="fig-dot" data-node="out" data-node-color="red" cx="287" cy="132" r="3.5"/>
    <text class="fig-text fig-math" data-node-color="red" x="277" y="157" text-anchor="middle">v<tspan baseline-shift="sub" font-size="78%">out</tspan></text>
  </g>
  <g class="sym" data-symbol="gnd">
    <path class="fig-ink" d="M27 226h24m-20 6h16m-12 6h8 M119 226h24m-20 6h16m-12 6h8 M218 226h24m-20 6h16m-12 6h8 M306 226h24m-20 6h16m-12 6h8 M367 226h24m-20 6h16m-12 6h8"/>
  </g>
  <g data-badges>
    <g data-badge-for="gate" transform="translate(131,27)"></g>
    <g data-badge-for="out" transform="translate(287,27)"></g>
  </g>
</svg>`;

const GM = 1 / 150;
const RL = 2000;
const CGS = 250e-15;
const CDB = 100e-15;
const INPUT_STEP = 0.001;
const EARLY_PS = 40;
const FULL_PS = 20000;
const EXACT_LABEL = '정확한 소신호 모델';
const MILLER_LABEL = '저주파 밀러 근사';

function exactPoles(a, b) {
  const root = Math.sqrt(Math.max(0, b * b - 4 * a));
  return [2 / (b + root), (b + root) / (2 * a)];
}

// Response with two real poles at -p and -q, prescribed DC value and
// initial slope. The limiting response also covers coincident poles.
function response(t, [p, q], final, slope) {
  const gap = q - p;
  const fast = Math.exp(-q * t);
  const slow = Math.exp(-p * t);
  const impulse = slow * (gap === 0 ? t : -Math.expm1(-gap * t) / gap);
  return {
    v: final * (-Math.expm1(-p * t) - p * impulse) + slope * impulse,
    dv: final * p * q * impulse + slope * (fast - p * impulse),
  };
}

function dcSolution(mna, rs, cgd, miller) {
  const gain = GM * RL;
  const elements = [
    { id: 'step', type: 'vsrc', n1: 'in', n2: '0', value: INPUT_STEP },
    { id: 'rs', type: 'R', n1: 'in', n2: 'gate', value: rs },
    { id: 'gm', type: 'vccs', n1: 'out', n2: '0', cp: 'gate', cn: '0', gm: GM },
    { id: 'rl', type: 'R', n1: 'out', n2: '0', value: RL },
    { id: 'cgs', type: 'C', n1: 'gate', n2: '0', value: CGS + (miller ? (1 + gain) * cgd : 0) },
    { id: 'cdb', type: 'C', n1: 'out', n2: '0', value: CDB + (miller ? (1 + 1 / gain) * cgd : 0) },
  ];
  if (!miller) elements.push({ id: 'cgd', type: 'C', n1: 'gate', n2: 'out', value: cgd });
  const solved = mna.solveCircuit({ elements }, { freqHz: 0 });
  if (!solved.ok) throw new Error(solved.reason);
  return { gate: solved.nodes.gate.re, out: solved.nodes.out.re };
}

function buildModels(mna, rs, cgd) {
  const exact = dcSolution(mna, rs, cgd, false);
  const miller = dcSolution(mna, rs, cgd, true);
  const a = rs * RL * (CGS * CDB + cgd * (CGS + CDB));
  const b = rs * (CGS + (1 + GM * RL) * cgd) + RL * (CDB + cgd);
  const poles = exactPoles(a, b);
  const outSlope = RL * cgd * INPUT_STEP / a;
  const gateSlope = RL * (CDB + cgd) * INPUT_STEP / a;
  const millerPoles = [
    1 / (rs * (CGS + (1 + GM * RL) * cgd)),
    1 / (RL * (CDB + (1 + 1 / (GM * RL)) * cgd)),
  ].sort((left, right) => left - right);
  return {
    gate: (t) => response(t, poles, exact.gate, gateSlope),
    exact: (t) => response(t, poles, exact.out, outSlope),
    miller: (t) => response(t, millerPoles, miller.out, 0),
    finalOut: exact.out,
  };
}

const mistakes = [
  { title: '반전 단이면 처음부터 아래로 간다고 보기', text: '입력 계단 직후에는 $C_{GD}$가 드레인에 전류를 넣어요. 게이트 전압이 자라면 $g_mv_G$가 커져 출력이 결국 아래로 가요.' },
  { title: '영점에서 사인파 출력이 사라진다고 보기', text: '영점 $s_z=g_m/C_{GD}$는 양의 실수예요. 사인파 응답은 허수축 $s=j\\omega$에서 읽어요.' },
  { title: '밀러 근사가 두 노드의 직접 경로를 보존한다고 보기', text: '저주파 이득을 고정해 $C_{GD}$를 두 접지 커패시터로 나누면 게이트→드레인 직접 경로가 사라져요.' },
];

const spec = {
  id: 'cs-rhp-zero-step-1028',
  title: '우반면 영점과 첫 출력 방향',
  archetype: 'approx',
  modes: [
    { key: 'early', label: '처음 40 ps', svg: SVG, ariaLabel: 'CS 단의 초기 계단 응답 회로' },
    { key: 'full', label: '전체 응답', svg: SVG, ariaLabel: 'CS 단의 전체 계단 응답 회로' },
  ],
  predict: {
    prompt: 'CS 단에 +1 mV를 갑자기 넣으면 $C_{GD}$가 있는 출력은 처음 어느 쪽으로 움직일까요?',
    options: [{ id: 'up', label: '위로 움직여요' }, { id: 'down', label: '아래로 움직여요' }],
    answerId: 'up',
    explain: '먼저 $C_{GD}$가 드레인에 전류를 넣어 출력이 조금 올라가요. 이후 트랜지스터가 전류를 끌어가 출력은 음전압으로 향해요.',
    mode: 'early',
    check: {
      before: { params: { earlyTime: 0 }, disabledElems: [] },
      after: { params: { earlyTime: 10 }, causalStep: 2 },
      tiles: ['정확 출력'],
    },
  },
  params: [
    { key: 'rs', label: '신호원 저항 RS', min: 100, max: 1000, step: 25, def: 200, unit: 'Ω' },
    { key: 'cgd', label: '게이트–드레인 CGD', min: 20, max: 160, step: 5, def: 80, unit: 'fF' },
    { key: 'earlyTime', label: '관찰 시각', min: 0, max: EARLY_PS, step: 1, def: 10, unit: 'ps', mode: 'early' },
    { key: 'fullTime', label: '관찰 시각', min: 0, max: FULL_PS, step: 100, def: 2000, unit: 'ps', mode: 'full' },
  ],
  elems: [{ id: 'cgd', label: '게이트–드레인 커패시턴스 CGD' }],
  causalSteps: [
    { id: 1, label: '게이트에 계단 넣기', detail: '신호원 저항에 전류가 생기고 게이트 쪽 커패시턴스가 충전되기 시작해요.' },
    { id: 2, label: 'CGD로 드레인 밀어 올리기', detail: 'CGD가 연결돼 있으면 게이트의 변화가 곧바로 드레인에 전류를 공급해요.' },
    { id: 3, label: '트랜지스터가 전류 끌어가기', detail: '종속원 전류가 커지면 출력이 아래로 향해요. 이 강조는 회로 경로를 보여 줘요. 시각은 슬라이더로 옮겨 보세요.' },
  ],
  presets: [
    { id: 'slide-early', mode: 'early', label: '수업 회로 · 10 ps', params: { rs: 200, cgd: 80, earlyTime: 10 }, disabledElems: [] },
    { id: 'remove-bridge', mode: 'early', label: 'CGD 제거 · 10 ps', params: { rs: 200, cgd: 80, earlyTime: 10 }, disabledElems: ['cgd'] },
    { id: 'larger-bridge', mode: 'early', label: 'CGD 160 fF · 18 ps', params: { rs: 200, cgd: 160, earlyTime: 18 }, disabledElems: [] },
    { id: 'settled', mode: 'full', label: '수업 회로 · 5 ns', params: { rs: 200, cgd: 80, fullTime: 5000 }, disabledElems: [] },
  ],
  steps: [
    { mode: 'early', title: '계단을 넣은 직후', text: '2 ps에서 CGD와 트랜지스터의 전류를 비교해 보세요.', params: { rs: 200, cgd: 80, earlyTime: 2 }, disabledElems: [], causalStep: 1 },
    { mode: 'early', title: '직접 경로 끊기', text: '같은 2 ps에서 출력 전압의 부호를 비교해 보세요.', params: { rs: 200, cgd: 80, earlyTime: 2 }, disabledElems: ['cgd'], causalStep: 2 },
    { mode: 'full', title: '최종 반전 확인하기', text: '5 ns에서는 두 모델 모두 음전압에 가까워요.', params: { rs: 200, cgd: 80, fullTime: 5000 }, disabledElems: [], causalStep: 3 },
  ],
  toggles: [['labels', '노드 배지', true]],
  mistakes: { early: mistakes, full: mistakes },
  evaluate(state, mna) {
    const early = state.mode === 'early';
    const timePs = early ? state.params.earlyTime : state.params.fullTime;
    const t = timePs * 1e-12;
    const cgdOn = !state.disabledElems.includes('cgd');
    const cgd = cgdOn ? state.params.cgd * 1e-15 : 0;
    const model = buildModels(mna, state.params.rs, cgd);
    const gate = model.gate(t);
    const out = model.exact(t);
    const approx = model.miller(t);
    const iCgd = 1e9 * cgd * (gate.dv - out.dv);
    const iGm = 1e9 * GM * gate.v;
    const scale = early ? 1e6 : 1e3;
    const unit = early ? 'µV' : 'mV';
    const format = (v) => `${(v * scale).toFixed(early ? 2 : 3)} ${unit}`;
    const errorScale = Math.max(Math.abs(out.v), Math.abs(approx.v));
    const errPct = errorScale > 0 ? 100 * Math.abs(out.v - approx.v) / errorScale : 0;

    const xMax = early ? EARLY_PS : FULL_PS / 1000;
    const points = Array.from({ length: 161 }, (_, i) => xMax * i / 160);
    const toSeconds = early ? 1e-12 : 1e-9;
    const exact = points.map((x) => [x, model.exact(x * toSeconds).v * scale]);
    const approximate = points.map((x) => [x, model.miller(x * toSeconds).v * scale]);
    const earlyExtent = early ? Math.max(1, ...[...exact, ...approximate].map(([, y]) => Math.abs(y))) : 0;
    const pulse = state.causalStep;

    const diagnosis = !cgdOn
      ? { kind: 'ok', title: '두 모델의 경로가 같아졌어요', text: '$C_{GD}$를 떼면 드레인으로 바로 전달되는 경로가 사라져요. 출력은 처음부터 음의 방향으로 움직여요.' }
      : out.v > 0
        ? { kind: 'warn', title: '정확 모델의 출력이 먼저 올라가요', text: '(교과서 보충) 두 모델의 최종 값은 같아요. 처음에는 정확 모델만 직접 전달 전류를 받아요.' }
        : { kind: 'info', title: timePs === 0 ? '계단이 막 시작됐어요' : '출력이 반전돼요', text: '정확 모델의 초기 상승은 「처음 40 ps」에서 보여요. 시간이 지나면 출력은 $-g_m R_L$의 저주파 이득으로 정해져요.' };

    return {
      tiles: [
        { label: '정확 출력', val: format(out.v) },
        { label: '밀러 출력', val: format(approx.v) },
        { label: '최종 출력', val: `${(model.finalOut * 1e3).toFixed(2)} mV` },
      ],
      diagnosis,
      equations: [
        { name: '드레인 KCL', tex: String.raw`$$C_{DB}\dot v_{\rm out} = i_{GD}-g_mv_G-\frac{v_{\rm out}}{R_L}$$` },
        { name: '직접 경로', tex: String.raw`$$i_{GD}=C_{GD}(\dot v_G-\dot v_{\rm out})$$` },
      ],
      summary: `(교과서 보충) +1 mV 계단에 대한 선형 소신호 응답이에요. 선택 시각에서 게이트→드레인 기준 전류는 ${iCgd.toFixed(2)} nA, 드레인→접지의 종속원 전류는 ${iGm.toFixed(2)} nA예요. 그래프의 오차율은 두 출력 차이의 크기를 둘 중 큰 크기로 나눈 값이에요.`,
      nodes: {
        gate: { badge: format(gate.v), hot: pulse === 1 },
        out: { badge: format(out.v), hot: pulse === 2 || pulse === 3 },
      },
      branches: {
        cgd: { hot: cgdOn && pulse === 2, dir: iCgd >= 0 ? 'fwd' : 'rev' },
        gm: { hot: pulse === 3 },
      },
      elems: { cgd: { hot: cgdOn && pulse === 2 } },
      plotData: {
        title: early ? '입력 계단 직후의 출력 방향' : '최종 반전까지의 출력 전압',
        xLabel: early ? '시각 (ps)' : '시각 (ns)', yLabel: `출력 (${unit})`,
        xScale: 'linear', xMin: 0, xMax,
        yMin: early ? -earlyExtent : model.finalOut * scale * 1.06,
        yMax: early ? earlyExtent : 0.4,
        exact, approx: approximate,
        exactLabel: EXACT_LABEL, approxLabel: MILLER_LABEL,
        marker: [early ? timePs : timePs / 1000, out.v * scale],
        approxMarker: [early ? timePs : timePs / 1000, approx.v * scale],
        errPct,
      },
    };
  },
};

module.exports = spec;
