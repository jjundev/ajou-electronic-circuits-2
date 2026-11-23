const gm = 1 / 150;
const cgs = 250e-15;
const cgd = 80e-15;
const csb = 100e-15;
const cl = 400e-15;
const minFreq = 10;
const maxFreq = 30000;
const ff = 1e15;

const circuit = [
  '<svg id="follower-schematic" viewBox="0 0 620 250" role="img" aria-label="소스 팔로워 소신호 회로. C GS는 게이트 G와 출력 S 사이에, C GD는 게이트와 AC 접지 사이에 연결되어 있다.">',
  '  <style>',
  '    @media (max-width: 639px) {',
  '      #follower-schematic .fig-math { font-size: 19px; }',
  '      #follower-schematic .fig-muted, #follower-schematic .lab-badge-text { font-size: 17px; }',
  '    }',
  '  </style>',
  '  <path class="fig-ink" data-causal-step="1" d="M48 125V100H237"/>',
  '  <g class="sym" data-causal-step="1">',
  '    <circle class="fig-ink" cx="48" cy="146" r="21"/>',
  '    <path class="fig-ink" d="M35 146q6-13 13 0t13 0"/>',
  '    <text class="fig-text fig-math" x="75" y="149">v<tspan baseline-shift="sub" font-size="78%">g</tspan></text>',
  '  </g>',
  '  <g class="sym"><path class="fig-ink" d="M48 167v37m-12 0h24m-20 6h16m-12 6h8"/></g>',
  '  <path class="fig-ink" d="M148 100v43m0 11v50"/>',
  '  <g class="sym"><path class="fig-ink" d="M136 143h24m-24 11h24m-24 50h24m-20 6h16m-12 6h8"/></g>',
  '  <text class="fig-text fig-math" x="170" y="153">C<tspan baseline-shift="sub" font-size="78%">GD</tspan></text>',
  '  <g data-branch="cgs" data-causal-step="3">',
  '    <path class="fig-ink" d="M249 100h30"/>',
  '    <g class="sym"><path class="fig-ink" d="M237 86v28m12-28v28"/></g>',
  '    <text class="fig-text fig-math" x="243" y="74" text-anchor="middle">C<tspan baseline-shift="sub" font-size="78%">GS</tspan></text>',
  '  </g>',
  '  <path class="fig-ink" data-causal-step="2" d="M279 100H555"/>',
  '  <g data-branch="gm" data-causal-step="2">',
  '    <path class="fig-ink" d="M320 100v25m0 52v27"/>',
  '    <g class="sym"><path class="fig-ink" d="M320 125l20 26-20 26-20-26zM320 163v-24m0 0-5 7m5-7 5 7m-17 58h24m-20 6h16m-12 6h8"/></g>',
  '    <text class="fig-text fig-math" x="290" y="154" text-anchor="end">g<tspan baseline-shift="sub" font-size="78%">m</tspan>v<tspan baseline-shift="sub" font-size="78%">gs</tspan></text>',
  '  </g>',
  '  <g data-causal-step="2">',
  '    <path class="fig-ink" d="M402 100v23m0 51v30"/>',
  '    <g class="sym"><path class="fig-ink" d="M402 123v4l-8 5 16 7-16 7 16 7-16 7 16 7-8 4v3m-12 30h24m-20 6h16m-12 6h8"/></g>',
  '    <text class="fig-text fig-math" x="423" y="153">R<tspan baseline-shift="sub" font-size="78%">L</tspan></text>',
  '  </g>',
  '  <path class="fig-ink" d="M478 100v43m0 11v50"/>',
  '  <g class="sym"><path class="fig-ink" d="M466 143h24m-24 11h24m-24 50h24m-20 6h16m-12 6h8"/></g>',
  '  <text class="fig-text fig-math" x="498" y="153">C<tspan baseline-shift="sub" font-size="78%">SB</tspan></text>',
  '  <g data-elem="cl" data-causal-step="2" aria-label="출력 부하 용량 전환">',
  '    <path class="fig-ink" d="M555 100v43m0 11v50"/>',
  '    <g class="sym"><path class="fig-ink" d="M543 143h24m-24 11h24m-24 50h24m-20 6h16m-12 6h8"/></g>',
  '    <text class="fig-text fig-math" x="575" y="153">C<tspan baseline-shift="sub" font-size="78%">L</tspan></text>',
  '  </g>',
  '  <circle class="fig-dot" data-node="g" data-node-color="blue" cx="148" cy="100" r="4"/>',
  '  <text class="fig-text fig-math" data-node-color="blue" x="148" y="75" text-anchor="middle">G · 게이트</text>',
  '  <circle class="fig-dot" data-node="s" data-node-color="red" cx="320" cy="100" r="4"/>',
  '  <text class="fig-text fig-math" data-node-color="red" x="320" y="75" text-anchor="middle">S · 소스</text>',
  '  <circle class="fig-dot" cx="402" cy="100" r="3"/>',
  '  <circle class="fig-dot" cx="478" cy="100" r="3"/>',
  '  <circle class="fig-dot" cx="555" cy="100" r="3"/>',
  '  <text class="fig-muted" x="310" y="236" text-anchor="middle">드레인과 바디는 AC 접지 · 이상적인 게이트 구동</text>',
  '  <g data-badges><g data-badge-for="g" transform="translate(148 32)"/><g data-badge-for="s" transform="translate(320 32)"/></g>',
  '</svg>',
].join('\n');

const start = { rl: 1500, f: 30 };
const high = { rl: 1500, f: 10000 };
const heavy = { rl: 25, f: 18000 };
const balanced = { rl: 75, f: 10000 };
const capLabel = (value) => value.toFixed(1) + ' fF';

module.exports = {
  id: 'ec2-1030-follower-input-cap',
  title: '따라가는 출력과 소스 팔로워의 입력 용량',
  archetype: 'approx',
  modes: [{ key: 'sf', label: '소스 팔로워', ariaLabel: '소스 팔로워 소신호 회로', svg: circuit }],
  predict: {
    prompt: '같은 낮은 주파수에서 $R_L$을 줄이면, 입력에서 보이는 $C_{GS}$의 기여는 어떻게 될까요?',
    options: [{ id: 'up', label: '커진다' }, { id: 'down', label: '작아진다' }],
    answerId: 'up',
    explain: '무거운 저항 부하는 소스 전압이 게이트를 따라가는 정도를 줄여요. 그러면 $C_{GS}$의 양단 전압 차가 커져요.',
    check: {
      before: { params: start, disabledElems: [] },
      after: { params: { rl: heavy.rl }, causalStep: 3 },
      tiles: ['현재 입력 용량', '게이트–소스 전압 차'],
    },
  },
  params: [
    { key: 'rl', label: '부하 저항 Rʟ', min: 25, max: 10000, def: start.rl, unit: 'Ω', scale: 'log' },
    { key: 'f', label: '측정 주파수', min: minFreq, max: maxFreq, def: start.f, unit: 'MHz', scale: 'log' },
  ],
  elems: [{ id: 'cl', label: '출력 부하 용량 (400 fF)' }],
  causalSteps: [
    { id: 1, label: '게이트 전압 인가', detail: '게이트 전압을 입력의 크기와 위상 기준으로 삼습니다.' },
    { id: 2, label: '게이트를 따라가는 소스', detail: '저항과 접지 용량이 소스 전압의 크기와 위상을 바꿉니다.' },
    { id: 3, label: '게이트 전류 측정', detail: '게이트–소스 전압 차가 두 노드 사이의 커패시터 전류를 정합니다.' },
  ],
  presets: [
    { id: 'lf', label: '가벼운 부하 · 저주파', params: start, disabledElems: [] },
    { id: 'hf', label: '가벼운 부하 · 고주파', params: high, disabledElems: [] },
    { id: 'heavy', label: '무거운 부하 · 고주파', params: heavy, disabledElems: [] },
  ],
  steps: [
    { title: '출력이 따라오는 저주파', text: '게이트와 소스의 크기가 비슷해요. 입력 용량이 게이트–드레인 용량에 가까운 값을 확인하세요.', params: start, disabledElems: [], causalStep: 1 },
    { title: '고주파에서 벌어지는 차이', text: '주파수를 올린 뒤 출력 용량을 껐다 켜며 입력 용량을 비교하세요.', params: high, disabledElems: [], causalStep: 2 },
    { title: '저항을 줄여 기울기 뒤집기', text: '가벼운 부하와 무거운 부하에서 입력 용량이 주파수에 따라 어느 쪽으로 변하는지 비교하세요.', params: heavy, disabledElems: [], causalStep: 3 },
    { title: '두 경향이 만나는 부하', text: '이 소자값에서 75 Ω을 연결하면 저주파 이득과 고주파 용량 분압비가 같아요.', params: balanced, disabledElems: [], causalStep: 3 },
  ],
  toggles: [['labels', '노드 전압 크기 (게이트 10 mV)', true]],
  mistakes: {
    sf: [
      { title: '출력이 따라오면 입력 용량이 0이라고 보기', text: '$C_{GS}$의 기여가 줄어도 드레인이 AC 접지인 $C_{GD}$는 그대로 입력에서 보입니다.' },
      { title: '저주파 이득을 모든 주파수에 쓰기', text: '고주파에서는 $C_{GS}$와 출력 접지 용량의 분압이 중요해요. 부하에 따라 주파수에 대한 입력 용량의 변화 방향도 달라집니다.' },
      { title: '입력 어드미턴스를 전부 용량으로 해석하기', text: '그래프는 $\\operatorname{Im}(Y_{in})/\\omega$만 보여요. 위상차가 생기면 입력 어드미턴스에 실수부도 생길 수 있어요.' },
    ],
  },
  evaluate(state, mna) {
    const { rl, f } = state.params;
    const hasCl = !state.disabledElems.includes('cl');
    const elements = [
      { id: 'sig', type: 'vsrc', n1: 'g', n2: '0', value: 0.01 },
      { id: 'cgd', type: 'C', n1: 'g', n2: '0', value: cgd },
      { id: 'cgs', type: 'C', n1: 'g', n2: 's', value: cgs },
      { id: 'gm', type: 'vccs', n1: '0', n2: 's', cp: 'g', cn: 's', gm },
      { id: 'rl', type: 'R', n1: 's', n2: '0', value: rl },
      { id: 'csb', type: 'C', n1: 's', n2: '0', value: csb },
      { id: 'cl', type: 'C', n1: 's', n2: '0', value: hasCl ? cl : 0 },
    ];
    const solve = (mhz) => mna.solveCircuit({ elements }, { freqHz: mhz * 1e6 });
    const dc = solve(0);
    const current = solve(f);
    const gate = current.nodes.g.mag;
    const a0 = dc.nodes.s.mag / dc.nodes.g.mag;
    const approx = (cgd + cgs * (1 - a0)) * ff;
    // MNA reports current into the voltage source, so negate it for input current.
    const effectiveCap = (mhz, result) => -result.branches.sig.im * ff / (gate * 2 * Math.PI * mhz * 1e6);
    const actual = effectiveCap(f, current);
    const errPct = 100 * Math.abs(approx / actual - 1);
    const aInf = cgs / (cgs + csb + (hasCl ? cl : 0));
    const conductance = -current.branches.sig.re / gate * 1e6;
    const differential = Math.hypot(gate - current.nodes.s.re, current.nodes.s.im);
    const bridgeCurrent = current.branches.cgs.mag * 1e6;
    const frequencies = Array.from({ length: 65 }, (_, i) => minFreq * (maxFreq / minFreq) ** (i / 64));
    const direction = aInf > a0 ? '낮아져요' : '높아져요';
    const trend = Math.abs(a0 - aInf) < 1e-10 ? '거의 일정해요' : direction;
    const phase = state.causalStep;

    return {
      tiles: [
        { label: '현재 입력 용량', val: capLabel(actual) },
        { label: '저주파 근사', val: capLabel(approx) },
        { label: '게이트–소스 전압 차', val: (differential * 1e3).toFixed(2) + ' mV' },
      ],
      diagnosis: {
        kind: errPct >= 10 ? 'warn' : 'ok',
        title: '주파수를 올리면 입력 용량이 ' + trend,
        text: '저주파 이득 ' + a0.toFixed(3) + '와 고주파 용량 분압비 ' + aInf.toFixed(3) + '의 차이가 변화 방향을 정해요.',
      },
      equations: [
        { name: '주파수별 입력 용량 (교과서 보충)', tex: '$$\\begin{aligned}C_{\\mathrm{eff}}&=\\frac{\\operatorname{Im}(Y_{in})}{\\omega}\\\\&=C_{GD}+C_{GS}(1-\\Re A_v)\\end{aligned}$$' },
        '$$A_v=\\frac{v_s}{v_g}$$',
        '$$C_{\\mathrm{LF}}=C_{GD}+\\frac{C_{GS}}{1+g_mR_L}$$',
      ],
      summary: '현재 $C_{GS}$ 전류의 크기는 ' + bridgeCurrent.toFixed(1) + ' μA예요. 소스 위상은 게이트 기준 ' + current.nodes.s.phaseDeg.toFixed(1) + '°, 입력 어드미턴스의 실수부는 ' + conductance.toFixed(1) + ' μS예요. $g_m=1/(150\\,\\Omega)$, $C_{GS}=250\\,\\mathrm{fF}$, $C_{GD}=80\\,\\mathrm{fF}$, $C_{SB}=100\\,\\mathrm{fF}$인 소신호 모델로 $r_o$와 바디 효과는 생략했어요.',
      nodes: {
        g: { badge: (gate * 1e3).toFixed(2) + ' mV', hot: phase === 1 },
        s: { badge: (current.nodes.s.mag * 1e3).toFixed(2) + ' mV', hot: phase === 2 },
      },
      branches: { gm: { hot: phase === 2 }, cgs: { hot: phase === 3 } },
      elems: { cl: { hot: hasCl && phase === 2 } },
      plotData: {
        title: '주파수에 따른 입력 용량과 저주파 근사',
        xLabel: '주파수 (MHz)', yLabel: '입력 용량 (fF)', xScale: 'log',
        xMin: minFreq, xMax: maxFreq, yMin: 60, yMax: 320,
        exact: frequencies.map((mhz) => [mhz, effectiveCap(mhz, solve(mhz))]),
        approx: [[minFreq, approx], [maxFreq, approx]],
        exactLabel: '현재 회로', approxLabel: '저주파 근사',
        marker: [f, actual], approxMarker: [f, approx], errPct,
      },
    };
  },
};
