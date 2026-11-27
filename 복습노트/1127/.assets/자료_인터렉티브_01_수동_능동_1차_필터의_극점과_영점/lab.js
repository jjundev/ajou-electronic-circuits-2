// 1127 수동 RC 분압기 vs 반전 증폭기 1차 필터: 극점·영점을 정하는 소자 프로브
const SUB = (s) => `<tspan baseline-shift="sub" font-size="78%">${s}</tspan>`;

const GND = (x, y) => `<g class="sym" data-symbol="gnd"><path class="fig-ink" d="M${x - 12} ${y}h24M${x - 8} ${y + 6}h16M${x - 4} ${y + 12}h8"/></g>`;
const SRC = (x, cy) => `<g class="sym" data-symbol="vsrc"><circle class="fig-ink" cx="${x}" cy="${cy}" r="16"/><path class="fig-ink" d="M${x - 5} ${cy - 7}h10M${x} ${cy - 12}v10M${x - 5} ${cy + 8}h10"/></g>`;
const RES_H = (x, y) => `<g class="sym" data-symbol="resistor"><path class="fig-ink" d="M${x} ${y}h6l4-7 6 14 6-14 6 14 6-14 6 14 4-7h6"/></g>`; // 50 px wide
const RES_V = (x, y) => `<g class="sym" data-symbol="resistor"><path class="fig-ink" d="M${x} ${y}v6l-7 4 14 6-14 6 14 6-14 6 14 6-7 4v6"/></g>`; // 50 px tall
const CAP_H = (x, y) => `<g class="sym" data-symbol="cap"><path class="fig-ink" d="M${x} ${y - 13}v26M${x + 9} ${y - 13}v26"/></g>`; // plates at x, x+9
const CAP_V = (x, y) => `<g class="sym" data-symbol="cap"><path class="fig-ink" d="M${x - 14} ${y}h28M${x - 14} ${y + 9}h28"/></g>`; // plates at y, y+9

const PASSIVE_SVG = `<svg viewBox="0 0 560 280" role="img" aria-label="수동 1차 필터: 입력 v_in에서 R1과 C1을 병렬로 묶은 직렬 가지를 지나 출력 노드에 닿고, 출력 노드에서 R2와 C2가 각각 접지로 내려가요">
  <g data-causal-step="1">
    <path class="fig-ink" d="M50 154V100H96"/>
    ${SRC(50, 170)}
    <path class="fig-ink" d="M50 186v30"/>
    ${GND(50, 216)}
    <circle class="fig-dot" data-node="in" data-node-color="blue" cx="50" cy="100" r="4"/>
    <text class="fig-text fig-math" data-node="in" data-node-color="blue" x="14" y="175" text-anchor="middle">v${SUB('in')}</text>
  </g>
  <g data-branch="z1" data-causal-step="2">
    <path class="fig-ink" d="M96 100h24M120 64v72M120 64h30M200 64h40M120 136h56M185 136h55M240 64v72M240 100h60"/>
    ${RES_H(150, 64)}
    ${CAP_H(176, 136)}
  </g>
  <text class="fig-text fig-math" x="175" y="46" text-anchor="middle">R${SUB('1')}</text>
  <text class="fig-text fig-math" x="180" y="172" text-anchor="middle">C${SUB('1')}</text>
  <text class="fig-muted" x="180" y="196" text-anchor="middle">입력 가지 Z${SUB('1')}</text>
  <g data-branch="z2" data-causal-step="2">
    <path class="fig-ink" d="M300 100v34M300 184v32M300 100h80M380 100v54M380 163v53"/>
    ${RES_V(300, 134)}
    ${CAP_V(380, 154)}
    ${GND(300, 216)}
    ${GND(380, 216)}
  </g>
  <text class="fig-text fig-math" x="282" y="164" text-anchor="end">R${SUB('2')}</text>
  <text class="fig-text fig-math" x="404" y="164" text-anchor="start">C${SUB('2')}</text>
  <text class="fig-muted" x="340" y="258" text-anchor="middle">접지 가지 Z${SUB('2')}</text>
  <g data-causal-step="3">
    <path class="fig-ink" d="M380 100h86"/>
    <circle class="fig-ink" cx="470" cy="100" r="4"/>
    <circle class="fig-dot" data-node="out" data-node-color="red" cx="300" cy="100" r="4"/>
    <circle class="fig-dot" cx="380" cy="100" r="3"/>
    <circle class="fig-dot" cx="120" cy="100" r="3"/>
    <circle class="fig-dot" cx="240" cy="100" r="3"/>
    <text class="fig-text fig-math" data-node="out" data-node-color="red" x="502" y="105" text-anchor="middle">v${SUB('out')}</text>
  </g>
  <g data-badges>
    <g data-badge-for="in" transform="translate(56 30)"></g>
    <g data-badge-for="out" transform="translate(340 30)"></g>
  </g>
</svg>`;

const ACTIVE_SVG = `<svg viewBox="0 0 580 300" role="img" aria-label="반전 증폭기 1차 필터: 입력 v_in에서 R1과 C1을 병렬로 묶은 입력 가지를 지나 OP-amp 반전 단자에 닿고, 반전 단자에서 R2와 C2를 병렬로 묶은 귀환 가지가 출력으로 돌아가요. 비반전 단자는 접지예요">
  <g data-causal-step="1">
    <path class="fig-ink" d="M50 184V150H86"/>
    ${SRC(50, 200)}
    <path class="fig-ink" d="M50 216v30"/>
    ${GND(50, 246)}
    <circle class="fig-dot" data-node="in" data-node-color="blue" cx="50" cy="150" r="4"/>
    <text class="fig-text fig-math" data-node="in" data-node-color="blue" x="14" y="205" text-anchor="middle">v${SUB('in')}</text>
  </g>
  <g data-branch="z1" data-causal-step="2">
    <path class="fig-ink" d="M86 150h24M110 120v60M110 120h30M190 120h40M110 180h56M175 180h55M230 120v60M230 150h60"/>
    ${RES_H(140, 120)}
    ${CAP_H(166, 180)}
  </g>
  <text class="fig-text fig-math" x="165" y="104" text-anchor="middle">R${SUB('1')}</text>
  <text class="fig-text fig-math" x="170" y="216" text-anchor="middle">C${SUB('1')}</text>
  <text class="fig-muted" x="170" y="240" text-anchor="middle">입력 가지 Z${SUB('1')}</text>
  <g data-causal-step="3">
    <path class="fig-ink" d="M290 150h40"/>
    <circle class="fig-dot" data-node="m" data-node-color="red" cx="290" cy="150" r="4"/>
    <circle class="fig-dot" cx="110" cy="150" r="3"/>
    <circle class="fig-dot" cx="230" cy="150" r="3"/>
    <circle class="fig-dot" cx="290" cy="90" r="3"/>
    <circle class="fig-dot" cx="480" cy="90" r="3"/>
    <text class="fig-muted" x="262" y="174" text-anchor="middle">가상 접지</text>
  </g>
  <g class="sym" data-symbol="opamp">
    <path class="fig-ink" d="M330 125v100l90-50z"/>
    <path class="fig-ink" d="M337 150h10M337 200h10M342 195v10"/>
  </g>
  <path class="fig-ink" d="M330 200h-30v30"/>
  ${GND(300, 230)}
  <g data-branch="z2" data-causal-step="3">
    <path class="fig-ink" d="M290 150V40M290 40h65M405 40h75M290 90h91M390 90h90M480 40v135"/>
    ${RES_H(355, 40)}
    ${CAP_H(381, 90)}
  </g>
  <text class="fig-text fig-math" x="380" y="24" text-anchor="middle">R${SUB('2')}</text>
  <text class="fig-text fig-math" x="385" y="122" text-anchor="middle">C${SUB('2')}</text>
  <text class="fig-muted" x="440" y="70" text-anchor="middle">귀환 가지 Z${SUB('2')}</text>
  <g data-causal-step="4">
    <path class="fig-ink" d="M420 175h96"/>
    <circle class="fig-ink" cx="520" cy="175" r="4"/>
    <circle class="fig-dot" data-node="out" data-node-color="blue" cx="480" cy="175" r="4"/>
    <text class="fig-text fig-math" data-node="out" data-node-color="blue" x="545" y="180" text-anchor="middle">v${SUB('out')}</text>
  </g>
  <g data-badges>
    <g data-badge-for="in" transform="translate(56 90)"></g>
    <g data-badge-for="m" transform="translate(260 200)"></g>
    <g data-badge-for="out" transform="translate(500 222)"></g>
  </g>
</svg>`;

const W_MIN = 1e4;
const W_MAX = 1e8;
const TWO_PI = 2 * Math.PI;
const sup = (e) => String(e).split('').map((c) => '⁰¹²³⁴⁵⁶⁷⁸⁹'['0123456789'.indexOf(c)] || (c === '-' ? '⁻' : c)).join('');
const fmtWText = (w) => {
  const e = Math.floor(Math.log10(w));
  let m = w / 10 ** e;
  let mm = m.toFixed(2);
  if (Number(mm) >= 10) { mm = (m / 10).toFixed(2); return `${mm}×10${sup(e + 1)}`; }
  return `${mm}×10${sup(e)}`;
};
const fmtWTex = (w) => {
  let e = Math.floor(Math.log10(w));
  let m = Number((w / 10 ** e).toFixed(2));
  if (m >= 10) { m /= 10; e += 1; }
  return `${m.toFixed(2)}\\times10^{${e}}`;
};
const g3 = (v) => {
  const a = Math.abs(v);
  if (a >= 100) return v.toFixed(0);
  if (a >= 10) return v.toFixed(1);
  if (a >= 1) return v.toFixed(2);
  return v.toPrecision(3);
};

function netlist(mode, p) {
  const R1 = p.r1 * 1e3;
  const C1 = p.c1 * 1e-9;
  const R2 = p.r2 * 1e3;
  const C2 = p.c2 * 1e-9;
  if (mode === 'passive') {
    return [
      { id: 'vs', type: 'vsrc', n1: 'in', n2: '0', value: 1 },
      { id: 'r1', type: 'R', n1: 'in', n2: 'out', value: R1 },
      { id: 'c1', type: 'C', n1: 'in', n2: 'out', value: C1 },
      { id: 'r2', type: 'R', n1: 'out', n2: '0', value: R2 },
      { id: 'c2', type: 'C', n1: 'out', n2: '0', value: C2 },
    ];
  }
  // 이상적 OP-amp 근사: 출력 = -A·v(m), A = gm·Ro = 10^6, Ro = 1 Ω
  return [
    { id: 'vs', type: 'vsrc', n1: 'in', n2: '0', value: 1 },
    { id: 'r1', type: 'R', n1: 'in', n2: 'm', value: R1 },
    { id: 'c1', type: 'C', n1: 'in', n2: 'm', value: C1 },
    { id: 'r2', type: 'R', n1: 'm', n2: 'out', value: R2 },
    { id: 'c2', type: 'C', n1: 'm', n2: 'out', value: C2 },
    { id: 'amp', type: 'vccs', n1: '0', n2: 'out', cp: '0', cn: 'm', gm: 1e6 },
    { id: 'ro', type: 'R', n1: 'out', n2: '0', value: 1 },
  ];
}

const spec = {
  id: 'ec2-1127-first-order-pole-zero',
  title: '수동·능동 1차 필터의 극점과 영점',
  archetype: 'probe',
  modes: [
    {
      key: 'passive',
      label: '수동 RC 분압기',
      svg: PASSIVE_SVG,
      ariaLabel: '수동 RC 분압기 1차 필터 회로',
      causalSteps: [
        { id: 1, label: '입력 전압을 걸어요', detail: '입력 전압이 직렬 가지 Z₁과 접지 가지 Z₂를 합친 양 끝에 걸려요.' },
        { id: 2, label: '두 가지에 같은 전류', detail: '출력에 다른 부하가 없어 Z₁을 지난 전류가 모두 Z₂로 흘러요. 전류는 입력 전압 ÷ (Z₁+Z₂)라서 네 소자가 함께 정해요.' },
        { id: 3, label: '출력은 분압비', detail: '출력 = 입력 × Z₂/(Z₁+Z₂)라서 크기는 늘 1보다 작아요.' },
      ],
      presets: [
        { id: 'p-lec', label: '정리노트 예시 (R₁=R₂, C₂=3C₁)', params: { r1: 1, c1: 1, r2: 1, c2: 3, w: 1e5 } },
        { id: 'p-same', label: '능동 예시와 같은 값', params: { r1: 1, c1: 1, r2: 2, c2: 2, w: 1e5 } },
      ],
    },
    {
      key: 'active',
      label: '반전 증폭기',
      svg: ACTIVE_SVG,
      ariaLabel: '반전 증폭기 1차 능동 필터 회로',
      causalSteps: [
        { id: 1, label: '입력 전압을 걸어요', detail: '입력 전압이 입력 가지 Z₁의 왼쪽 끝에 걸려요.' },
        { id: 2, label: '입력 가지 전류', detail: '반전 단자가 가상 접지(0 V)라서 Z₁ 양 끝 전압은 입력 전압 그대로예요. 전류 i = 입력 전압 ÷ Z₁이고, Z₂는 이 전류를 바꾸지 않아요.' },
        { id: 3, label: '같은 전류가 귀환 가지로', detail: 'OP-amp 입력으로는 전류가 들어가지 않아 같은 i가 Z₂를 지나 출력 쪽으로 흘러요.' },
        { id: 4, label: '출력 전압', detail: '출력 = 0 − i·Z₂ = −입력 × Z₂/Z₁이에요. 극점은 Z₂, 영점은 Z₁에서만 나와요.' },
      ],
      presets: [
        { id: 'a-lpf', label: '정리노트 예시 LPF (R₂C₂ > R₁C₁)', params: { r1: 1, c1: 1, r2: 2, c2: 2, w: 1e5 } },
        { id: 'a-hpf', label: 'HPF (R₂C₂ < R₁C₁)', params: { r1: 1, c1: 4, r2: 2, c2: 0.5, w: 1e5 } },
        { id: 'a-flat', label: '평탄 (R₂C₂ = R₁C₁)', params: { r1: 1, c1: 4, r2: 2, c2: 2, w: 1e5 } },
      ],
    },
  ],
  predict: {
    mode: 'passive',
    prompt: '수동 RC 분압기에서 입력 가지의 $C_1$만 1 nF에서 2 nF로 키우면 극점 크기 $|p|$는 어떻게 될까요?',
    options: [
      { id: 'same', label: '그대로예요 (극점은 접지 가지가 정해요)' },
      { id: 'down', label: '작아져요 (더 낮은 주파수로 가요)' },
      { id: 'up', label: '커져요 (더 높은 주파수로 가요)' },
    ],
    answerId: 'down',
    explain: '수동 분압기의 극점 $|p|=\\dfrac{R_1+R_2}{R_1R_2(C_1+C_2)}$에는 $C_1$도 들어 있어 $0.5\\times10^6$에서 $0.375\\times10^6$ rad/s로 내려가요. 영점 $1/(R_1C_1)$도 함께 움직여요. 반전 증폭기 모드에서 같은 조작을 하면 극점은 $1/(R_2C_2)$ 그대로예요.',
    check: {
      before: { params: { r1: 1, c1: 1, r2: 2, c2: 2, w: 1e5 } },
      after: { params: { c1: 2 } },
      tiles: ['pole', 'zero'],
    },
  },
  params: [
    { key: 'r1', label: 'R₁ (입력 가지)', min: 0.5, max: 8, step: 0.5, unit: 'kΩ', def: 1 },
    { key: 'c1', label: 'C₁ (입력 가지)', min: 0.5, max: 8, step: 0.5, unit: 'nF', def: 1 },
    { key: 'r2', label: 'R₂ (접지·귀환 가지)', min: 0.5, max: 8, step: 0.5, unit: 'kΩ', def: 2 },
    { key: 'c2', label: 'C₂ (접지·귀환 가지)', min: 0.5, max: 8, step: 0.5, unit: 'nF', def: 2 },
    { key: 'w', label: '측정 각주파수 ω', min: W_MIN, max: W_MAX, scale: 'log', unit: 'rad/s', def: 1e5, format: (v) => `${fmtWText(v)} rad/s` },
  ],
  steps: [
    { mode: 'passive', title: '수동: 두 끝의 이득', text: 'R₁ = R₂, C₂ = 3C₁이면 저주파 이득은 1/2, 고주파 이득은 1/4이에요. 둘 다 1보다 작아요.', params: { r1: 1, c1: 1, r2: 1, c2: 3, w: 1e5 } },
    { mode: 'passive', title: '수동: C₁이 극점을 움직여요', text: '기본값(1 kΩ, 1 nF, 2 kΩ, 2 nF)에서 C₁만 2 nF로 키운 상태예요. 영점만이 아니라 극점도 5.00×10⁵에서 3.75×10⁵ rad/s로 내려가요. 수동 분압기의 극점에는 네 소자가 모두 들어 있어요.', params: { r1: 1, c1: 2, r2: 2, c2: 2, w: 1e5 } },
    { mode: 'active', title: '능동: C₁은 영점만 바꿔요', text: '반전 증폭기에서도 C₁ = 2 nF예요. C₁을 1 nF로 되돌려 보세요. 영점만 움직이고 극점 1/(R₂C₂)는 그대로예요.', params: { r1: 1, c1: 2, r2: 2, c2: 2, w: 1e5 } },
    { mode: 'active', title: '능동: 이득이 1보다 커요', text: 'R₂ = 2R₁이면 저주파 이득의 크기가 2예요. 수동 분압기로는 만들 수 없는 값이에요.', params: { r1: 1, c1: 1, r2: 2, c2: 2, w: 1e4 } },
  ],
  toggles: [['labels', '노드 배지', true]],
  mistakes: {
    passive: [
      { title: '극점은 접지 가지 $R_2C_2$만 정한다', text: '수동 분압기의 극점은 $|p|=\\frac{R_1+R_2}{R_1R_2(C_1+C_2)}$라서 네 소자가 모두 들어가요. $1/(R_2C_2)$는 반전 증폭기의 극점이에요.' },
      { title: '저항비를 키우면 이득을 1보다 크게 만들 수 있다', text: '저주파 이득 $\\frac{R_2}{R_1+R_2}$와 고주파 이득 $\\frac{C_1}{C_1+C_2}$는 어떤 값을 넣어도 1보다 작아요.' },
      { title: '직렬 가지는 $R_1+1/(sC_1)$이다', text: '그림의 $R_1$과 $C_1$은 병렬이라 $Z_1=R_1\\parallel\\frac{1}{sC_1}$이에요. 그래서 영점 $-1/(R_1C_1)$이 생겨요.' },
    ],
    active: [
      { title: '반전 단자는 실제로 접지에 이어져 있다', text: '반전 단자는 접지와 연결되지 않았어요. 음의 귀환 때문에 전압만 0 V에 가까운 가상 접지예요. 배지에서 아주 작은 전압이 남아 있는 것을 확인할 수 있어요.' },
      { title: '입력 가지를 바꾸면 극점도 움직인다', text: '$-Z_2/Z_1$에서 극점은 $Z_2$의 분모 $1+sR_2C_2$에서만 나와요. $R_1$·$C_1$은 영점과 이득만 바꿔요.' },
      { title: '고주파 이득은 $C_2/C_1$이다', text: '$s\\to\\infty$에서 $-Z_2/Z_1\\to-\\frac{1/(sC_2)}{1/(sC_1)}=-\\frac{C_1}{C_2}$예요. 수업에서도 $C_1/C_2$로 정정했어요.' },
    ],
  },
  evaluate(state, mna) {
    const mode = state.mode === 'active' ? 'active' : 'passive';
    const p = state.params;
    const R1 = p.r1 * 1e3;
    const C1 = p.c1 * 1e-9;
    const R2 = p.r2 * 1e3;
    const C2 = p.c2 * 1e-9;
    const els = netlist(mode, p);
    const solve = (w) => {
      const r = mna.solveCircuit({ elements: els }, { freqHz: w / TWO_PI });
      if (!r.ok) throw new Error(r.reason);
      return r;
    };
    const ratio = (r) => r.nodes.out.mag / r.nodes.in.mag;

    const pole = mode === 'active' ? 1 / (R2 * C2) : (R1 + R2) / (R1 * R2 * (C1 + C2));
    const zero = 1 / (R1 * C1);
    const dc = solve(0);
    const hi = solve(Math.max(pole, zero) * 1e3);
    const atW = solve(p.w);
    const gLow = ratio(dc);
    const gHigh = ratio(hi);
    const gW = ratio(atW);
    const sign = mode === 'active' ? '−' : '';
    const kind = Math.abs(pole - zero) / zero < 1e-9 ? 'flat' : (pole < zero ? 'lpf' : 'hpf');
    const kindText = kind === 'flat' ? '평탄 (극점과 영점이 겹쳐요)' : (kind === 'lpf' ? 'LPF (극점에서 먼저 꺾여 내려가요)' : 'HPF (영점에서 먼저 꺾여 올라가요)');
    const db = (x) => 20 * Math.log10(x);
    const pts = Array.from({ length: 81 }, (_, i) => {
      const w = W_MIN * 10 ** (i / 20);
      return [w, db(ratio(solve(w)))];
    });
    const cs = state.causalStep;
    const vm = mode === 'active' ? atW.nodes.m.mag : 0;
    const phOut = atW.nodes.out.phaseDeg;

    const nodes = {
      in: { text: '1 V', hot: cs === 1 },
      out: { text: `|v|=${g3(gW)} V`, hot: mode === 'active' ? cs === 4 : cs === 3 },
    };
    if (mode === 'active') nodes.m = { text: `${(vm * 1e6).toPrecision(2)} µV`, hot: cs === 3 || cs === 2 };

    const branches = mode === 'active'
      ? { z1: { hot: cs === 2, dir: 'fwd' }, z2: { hot: cs === 3, dir: 'fwd' } }
      : { z1: { hot: cs === 2, dir: 'fwd' }, z2: { hot: cs === 2, dir: 'fwd' } };

    const equations = mode === 'active'
      ? ['$$\\frac{v_{out}}{v_{in}}=-\\frac{Z_2}{Z_1}$$',
        '$$=-\\frac{R_2}{R_1}\\cdot\\frac{1+sR_1C_1}{1+sR_2C_2}$$',
        '$$|p|=\\frac{1}{R_2C_2}$$',
        '$$|z|=\\frac{1}{R_1C_1}$$']
      : ['$$\\frac{v_{out}}{v_{in}}=\\frac{Z_2}{Z_1+Z_2}$$',
        '$$|p|=\\frac{R_1+R_2}{R_1R_2(C_1+C_2)}$$',
        '$$|z|=\\frac{1}{R_1C_1}$$'];

    const gainNote = mode === 'active'
      ? `저주파 이득 $-R_2/R_1=${sign}${g3(gLow)}$, 고주파 이득 $-C_1/C_2=${sign}${g3(gHigh)}$.`
      : `저주파 이득 $R_2/(R_1+R_2)=${g3(gLow)}$, 고주파 이득 $C_1/(C_1+C_2)=${g3(gHigh)}$.`;
    const summary = mode === 'active'
      ? `반전 단자는 ${(vm * 1e6).toPrecision(2)} µV로 거의 0 V예요(이상적 OP-amp를 이득 $10^6$으로 근사했고, OP-amp 자체의 극점(대역폭 한계)은 넣지 않았어요). ${gainNote} 측정 각주파수 $\\omega=${fmtWTex(p.w)}$ rad/s에서 잰 크기는 $|v_{out}/v_{in}|=${g3(gW)}$이고, 위상은 반전 −180°를 포함해 ${(phOut > 0 ? phOut - 360 : phOut).toFixed(0)}°(= ${(phOut > 0 ? phOut : phOut + 360).toFixed(0)}°)예요.`
      : `출력에 부하가 없어 $Z_1$과 $Z_2$에 같은 전류가 흘러요. ${gainNote} 측정 각주파수 $\\omega=${fmtWTex(p.w)}$ rad/s에서 잰 크기: $|v_{out}/v_{in}|=${g3(gW)}$.`;

    const diagnosis = mode === 'active'
      ? { kind: gLow > 1 + 1e-9 || gHigh > 1 + 1e-9 ? 'ok' : 'info', title: kindText, text: `$R_2C_2=${(R2 * C2 * 1e6).toPrecision(3)}\\ \\mu s$, $R_1C_1=${(R1 * C1 * 1e6).toPrecision(3)}\\ \\mu s$예요. 극점은 귀환 가지, 영점은 입력 가지만으로 정해져요.` }
      : { kind: 'info', title: kindText, text: `$R_2C_2=${(R2 * C2 * 1e6).toPrecision(3)}\\ \\mu s$, $R_1C_1=${(R1 * C1 * 1e6).toPrecision(3)}\\ \\mu s$예요. 극점에는 네 소자가 모두 들어 있고, 이득은 양 끝 모두 1보다 작아요.` };

    return {
      tiles: [
        { id: 'pole', label: '극점 |p|', val: `${fmtWText(pole)} rad/s` },
        { id: 'zero', label: '영점 |z|', val: `${fmtWText(zero)} rad/s` },
        { id: 'low', label: '저주파 이득', val: `${sign}${g3(gLow)}` },
        { id: 'high', label: '고주파 이득', val: `${sign}${g3(gHigh)}` },
      ],
      diagnosis,
      equations,
      summary,
      nodes,
      branches,
      plotData: {
        title: '크기 응답 |v_out/v_in|',
        ariaLabel: '각주파수에 따른 전달함수 크기(dB)',
        xLabel: 'ω (rad/s)',
        yLabel: '|H| (dB)',
        xScale: 'log',
        xMin: W_MIN,
        xMax: W_MAX,
        yMin: -30,
        yMax: 30,
        exact: pts,
        exactLabel: mode === 'active' ? '반전 증폭기 (회로 계산)' : '수동 분압기 (회로 계산)',
        marker: [p.w, db(gW)],
      },
    };
  },
};

module.exports = spec;
