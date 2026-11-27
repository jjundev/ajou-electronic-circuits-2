// 1127 RC 두 단 저역 통과: 로딩이 겹친 두 극점을 가르는 정도를 1차 단 곱 근사와 비교
const SUB = (s) => `<tspan baseline-shift="sub" font-size="78%">${s}</tspan>`;
const GND = (x, y) => `<g class="sym" data-symbol="gnd"><path class="fig-ink" d="M${x - 12} ${y}h24M${x - 8} ${y + 6}h16M${x - 4} ${y + 12}h8"/></g>`;
const SRC = (x, cy) => `<g class="sym" data-symbol="vsrc"><circle class="fig-ink" cx="${x}" cy="${cy}" r="16"/><path class="fig-ink" d="M${x - 5} ${cy - 7}h10M${x} ${cy - 12}v10M${x - 5} ${cy + 8}h10"/></g>`;
const RES_H = (x, y) => `<g class="sym" data-symbol="resistor"><path class="fig-ink" d="M${x} ${y}h6l4-7 6 14 6-14 6 14 6-14 6 14 4-7h6"/></g>`;
const CAP_V = (x, y) => `<g class="sym" data-symbol="cap"><path class="fig-ink" d="M${x - 14} ${y}h28M${x - 14} ${y + 9}h28"/></g>`;

const SVG = `<svg viewBox="0 0 600 270" role="img" aria-label="RC 두 단 저역 통과 필터: 입력에서 R1을 지나 노드 X, X에서 C1이 접지로 가요. X에서 버퍼 또는 직결 경로를 거쳐 R2를 지나 출력, 출력에서 C2가 접지로 가요">
  ${SRC(50, 170)}
  <path class="fig-ink" d="M50 154V90h50M150 90h50M50 186v30"/>
  ${GND(50, 216)}
  ${RES_H(100, 90)}
  <text class="fig-text fig-math" x="125" y="70" text-anchor="middle">R${SUB('1')}</text>
  <circle class="fig-dot" data-node="in" data-node-color="blue" cx="50" cy="90" r="4"/>
  <text class="fig-text fig-math" data-node="in" data-node-color="blue" x="14" y="175" text-anchor="middle">v${SUB('in')}</text>
  <path class="fig-ink" d="M200 90v54M200 153v63"/>
  ${CAP_V(200, 144)}
  ${GND(200, 216)}
  <text class="fig-text fig-math" x="176" y="154" text-anchor="end">C${SUB('1')}</text>
  <circle class="fig-dot" data-node="x" data-node-color="red" cx="200" cy="90" r="4"/>
  <text class="fig-text fig-math" data-node="x" data-node-color="red" x="214" y="78" text-anchor="start">X</text>
  <path class="fig-ink" d="M200 90h50M290 90h40"/>
  <g data-elem="buf" aria-label="이상적 버퍼(이득 1)">
    <rect x="242" y="34" width="56" height="84" style="fill:none;stroke:none" pointer-events="all"/>
    <g class="sym" data-symbol="buffer"><path class="fig-ink" pointer-events="all" d="M250 68v44l40-22z"/></g>
    <text class="fig-muted" x="270" y="50" text-anchor="middle">버퍼 ×1</text>
  </g>
  <g data-branch="bypass">
    <path class="fig-ink" d="M232 90v44h76V90"/>
    <circle class="fig-dot" cx="232" cy="90" r="3"/>
    <circle class="fig-dot" cx="308" cy="90" r="3"/>
    <text class="fig-muted" x="270" y="158" text-anchor="middle">직결 (버퍼를 뺐을 때)</text>
  </g>
  ${RES_H(330, 90)}
  <text class="fig-text fig-math" x="355" y="70" text-anchor="middle">R${SUB('2')}</text>
  <path class="fig-ink" d="M380 90h60M440 90v54M440 153v63M440 90h76"/>
  ${CAP_V(440, 144)}
  ${GND(440, 216)}
  <text class="fig-text fig-math" x="464" y="154" text-anchor="start">C${SUB('2')}</text>
  <circle class="fig-dot" data-node="out" data-node-color="blue" cx="440" cy="90" r="4"/>
  <circle class="fig-ink" cx="520" cy="90" r="4"/>
  <text class="fig-text fig-math" data-node="out" data-node-color="blue" x="552" y="95" text-anchor="middle">v${SUB('out')}</text>
  <g data-badges>
    <g data-badge-for="in" transform="translate(56 34)"></g>
    <g data-badge-for="x" transform="translate(180 34)"></g>
    <g data-badge-for="out" transform="translate(450 34)"></g>
  </g>
</svg>`;

// 기준 소자: R1 = 1 kΩ, C1 = 1 nF → ω0 = 1/(R1C1) = 10^6 rad/s. 2단은 R2 = k·R1, C2 = C1/k (R2C2 = R1C1 유지)
const R1 = 1e3;
const C1 = 1e-9;
const W0 = 1 / (R1 * C1);
const X_MIN = 0.01;
const X_MAX = 100;
const TWO_PI = 2 * Math.PI;
const g3 = (v) => {
  const a = Math.abs(v);
  if (a >= 100) return v.toFixed(0);
  if (a >= 10) return v.toFixed(1);
  if (a >= 1) return v.toFixed(2);
  return v.toPrecision(3);
};
const fmtK = (k) => (k >= 10 ? k.toFixed(0) : (k >= 1 ? k.toFixed(1) : k.toFixed(2)));

const spec = {
  id: 'ec2-1127-rc-two-stage-loading',
  title: 'RC 두 단 로딩과 극점 분리',
  archetype: 'approx',
  modes: [{ key: 'cascade', label: 'RC 두 단', svg: SVG, ariaLabel: 'RC 두 단 저역 통과 필터 회로' }],
  params: [
    { key: 'k', label: '2단 배율 k', min: 0.1, max: 100, scale: 'log', def: 1, format: (v) => `×${fmtK(v)}` },
    { key: 'x', label: '측정 주파수 ωR₁C₁', min: X_MIN, max: X_MAX, scale: 'log', def: 1, format: (v) => (v >= 10 ? v.toFixed(0) : (v >= 1 ? v.toFixed(2) : v.toPrecision(2))) },
  ],
  elems: [{ id: 'buf', label: '버퍼 ×1 (이상적, 교과서 보충)' }],
  initialDisabledElems: ['buf'],
  presets: [
    { id: 'lec', label: '수업 가정: R₁=R₂, C₁=C₂', params: { k: 1, x: 1 }, disabledElems: ['buf'] },
    { id: 'buffered', label: '버퍼로 두 단 분리', params: { k: 1, x: 1 }, disabledElems: [] },
    { id: 'light', label: '가벼운 2단 (k = 10)', params: { k: 10, x: 1 }, disabledElems: ['buf'] },
    { id: 'heavy', label: '무거운 2단 (k = 0.1)', params: { k: 0.1, x: 1 }, disabledElems: ['buf'] },
  ],
  steps: [
    { title: '수업의 가정', text: 'R₁ = R₂, C₁ = C₂이면 각 단만 따로 보면 극점이 둘 다 1/(RC)예요. 그래서 수업에서는 같은 자리에 극점 두 개가 있다고 봤어요.', params: { k: 1, x: 1 }, disabledElems: ['buf'] },
    { title: '실제로는 갈라져요', text: 'R₂와 C₂가 노드 X에서 전류를 빼 가요(로딩). 극점은 0.38/(RC)와 2.62/(RC)로 갈라지고, ω = 1/(RC)에서 크기는 1/2이 아니라 1/3이에요.', params: { k: 1, x: 1 }, disabledElems: ['buf'] },
    { title: '2단을 가볍게', text: 'R₂를 10배로 키우고 C₂를 1/10로 줄이면 2단이 X에서 빼 가는 전류가 작아져 근사 오차가 50%에서 약 5%로 줄어요.', params: { k: 10, x: 1 }, disabledElems: ['buf'] },
    { title: '버퍼로 끊기', text: '이상적 버퍼는 X의 전압을 그대로 옮기고 전류는 빼 가지 않아요. 그러면 두 1차 단의 곱이 정확한 답이 돼요. (교과서 보충)', params: { k: 1, x: 1 }, disabledElems: [] },
    { title: '멀리서 보면 같아요', text: '두 극점을 모두 지난 ωR₁C₁ = 100에서는 로딩이 있어도 기울기가 −40 dB/dec이고 크기도 거의 같아요. 로딩은 극점 근처의 모양을 바꿔요.', params: { k: 1, x: 100 }, disabledElems: ['buf'] },
  ],
  predict: {
    prompt: '버퍼 없이 $R_1=R_2$, $C_1=C_2$일 때, $\\omega=1/(R_1C_1)$에서 실제 $|v_{out}/v_{in}|$은 두 1차 단을 곱한 근사값 $1/2$와 비교해 어떨까요?',
    options: [
      { id: 'same', label: '1/2 그대로예요' },
      { id: 'less', label: '1/2보다 작아요' },
      { id: 'more', label: '1/2보다 커요' },
    ],
    answerId: 'less',
    explain: '분모가 $N(s)=1+3sRC+s^2R^2C^2$이라 $\\omega=1/(RC)$에서 $|N|=3$, 크기는 $1/3$이에요. 로딩 항 $sR_1C_2$만큼 분모가 커져 두 1차 단의 곱보다 작아요.',
    check: {
      after: { params: { k: 1, x: 1 }, disabledElems: ['buf'] },
      tiles: ['exact', 'approx'],
    },
  },
  toggles: [['labels', '노드 배지', true]],
  mistakes: {
    cascade: [
      { title: '같은 RC 두 단이면 극점이 정확히 겹친다', text: '2단이 노드 X를 로딩해 분모에 $sR_1C_2$가 더해져요. $R_1=R_2$, $C_1=C_2$에서 두 극점은 $0.38/(RC)$와 $2.62/(RC)$로 갈라져요.' },
      { title: '로딩 때문에 2차 필터가 아니게 된다', text: '분모는 여전히 $s$의 2차식이라 극점이 두 개예요. 두 극점을 모두 지난 뒤의 기울기도 $-40$ dB/dec예요.' },
      { title: 'RC만으로 복소 극점을 만들 수 있다', text: '판별식이 늘 양수라서 RC 두 단의 극점은 서로 다른 실수 극점이에요. 복소 극점과 높은 Q는 2차 필터 회로가 따로 필요해요.' },
    ],
  },
  evaluate(state, mna) {
    const k = Number(state.params.k);
    const x = Number(state.params.x);
    const bufOn = !state.disabledElems.includes('buf');
    const R2 = k * R1;
    const C2 = C1 / k;
    const elements = [
      { id: 'vs', type: 'vsrc', n1: 'in', n2: '0', value: 1 },
      { id: 'r1', type: 'R', n1: 'in', n2: 'x', value: R1 },
      { id: 'c1', type: 'C', n1: 'x', n2: '0', value: C1 },
      { id: 'r2', type: 'R', n1: 'xb', n2: 'out', value: R2 },
      { id: 'c2', type: 'C', n1: 'out', n2: '0', value: C2 },
    ];
    if (bufOn) {
      // 이상적 버퍼 근사: xb = gm·Rb·v(x), gm·Rb = 1, Rb = 1 µΩ
      elements.push({ id: 'buf', type: 'vccs', n1: '0', n2: 'xb', cp: 'x', cn: '0', gm: 1e6 });
      elements.push({ id: 'rb', type: 'R', n1: 'xb', n2: '0', value: 1e-6 });
    } else {
      elements.push({ id: 'link', type: 'short', n1: 'x', n2: 'xb' });
    }
    const solve = (xn) => {
      const r = mna.solveCircuit({ elements }, { freqHz: (xn * W0) / TWO_PI });
      if (!r.ok) throw new Error(r.reason);
      return r.nodes;
    };
    const approxMag = (xn) => 1 / (1 + xn * xn); // |1/(1+jx)^2|, R2C2 = R1C1
    const db = (v) => 20 * Math.log10(v);
    const at = solve(x);
    const exact = at.out.mag / at.in.mag;
    const approx = approxMag(x);
    const errPct = (100 * (approx - exact)) / exact;

    // 정규화 분모: N = 1 + b·(sτ) + (sτ)^2, b = 2 + 1/k (버퍼 없음) 또는 2 (버퍼)
    const b = bufOn ? 2 : 2 + 1 / k;
    const disc = Math.max(b * b - 4, 0);
    const p1 = (b - Math.sqrt(disc)) / 2;
    const p2 = (b + Math.sqrt(disc)) / 2;

    const exactPts = [];
    const approxPts = [];
    for (let i = 0; i <= 80; i += 1) {
      const xn = X_MIN * 10 ** (i / 20);
      const n = solve(xn);
      exactPts.push([xn, db(n.out.mag / n.in.mag)]);
      approxPts.push([xn, db(approxMag(xn))]);
    }
    const near = Math.abs(errPct) <= 10;
    const loadTerm = bufOn ? '0' : `${(1 / k).toPrecision(3)}`;

    return {
      tiles: [
        { id: 'p1', label: '극점 |p₁|·R₁C₁', val: p1.toFixed(3) },
        { id: 'p2', label: '극점 |p₂|·R₁C₁', val: p2.toFixed(3) },
        { id: 'exact', label: '실제 |H| (회로)', val: g3(exact) },
        { id: 'approx', label: '두 단 곱 근사 |H|', val: g3(approx) },
      ],
      diagnosis: bufOn
        ? { kind: 'ok', title: '버퍼로 두 단을 분리했어요', text: '버퍼가 X에서 전류를 빼 가지 않아 두 1차 단의 곱이 그대로 맞아요. 두 극점이 $1/(R_1C_1)$에 겹쳐요. (교과서 보충)' }
        : {
          kind: near ? 'ok' : 'warn',
          title: near ? '측정점에서 근사 오차 10% 이내' : '측정점에서 근사 오차 10% 초과',
          text: `실제 크기를 기준으로 근사가 ${errPct.toFixed(1)}% 차이 나요. 로딩 항 $sR_1C_2$의 계수는 $R_1C_2/(R_1C_1)=1/k=${loadTerm}$이에요.`,
        },
      equations: bufOn
        ? ['$$\\frac{v_{out}}{v_{in}}=\\frac{1}{N(s)}$$', '$$N(s)=(1+sR_1C_1)(1+sR_2C_2)$$']
        : ['$$\\frac{v_{out}}{v_{in}}=\\frac{1}{N(s)}$$', '$$\\begin{aligned}N(s)&=(1+sR_1C_1)(1+sR_2C_2)\\\\&\\quad+sR_1C_2\\end{aligned}$$'],
      summary: bufOn
        ? `버퍼가 노드 X와 2단을 끊었어요. 2단 임피던스 배율은 ×${fmtK(k)}이지만 $R_2C_2=R_1C_1$이라 두 극점이 $1/(R_1C_1)=10^6$ rad/s에 겹쳐요. 측정점 $\\omega R_1C_1=${g3(x)}$에서 잰 크기: ${g3(exact)}. (교과서 보충)`
        : `$R_2=${g3(R2 / 1e3)}$ kΩ, $C_2=${g3(C2 * 1e9)}$ nF가 노드 X에서 전류를 빼 가요. 두 극점은 $${p1.toFixed(3)}/(R_1C_1)$과 $${p2.toFixed(3)}/(R_1C_1)$로 갈라져요. 측정점 $\\omega R_1C_1=${g3(x)}$에서 실제 크기: ${g3(exact)}, 근사: ${g3(approx)}.`,
      nodes: {
        in: { text: '1 V' },
        x: { text: `|v|=${g3(at.x.mag)} V`, hot: !bufOn },
        out: { text: `|v|=${g3(at.out.mag)} V` },
      },
      branches: {
        bypass: bufOn ? { dim: true } : { hot: true },
      },
      elems: { buf: { hot: bufOn } },
      plotData: {
        title: '실제 크기와 두 1차 단 곱 근사',
        ariaLabel: '정규화 주파수에 따른 실제 크기와 근사 크기(dB) 비교',
        xLabel: 'ωR₁C₁',
        yLabel: '|H| (dB)',
        xScale: 'log',
        xMin: X_MIN,
        xMax: X_MAX,
        yMin: -90,
        yMax: 10,
        exact: exactPts,
        approx: approxPts,
        exactLabel: bufOn ? '회로 계산 (버퍼 있음)' : '회로 계산 (로딩 포함)',
        approxLabel: '두 1차 단의 곱',
        marker: [x, db(exact)],
        approxMarker: [x, db(approx)],
        errPct: Math.abs(errPct),
        thresholdPct: 10,
      },
    };
  },
};

module.exports = spec;
