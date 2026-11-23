// Minimal reference lab.js for ec2-interactive v2.
// Demonstrates the 'probe' archetype, MNA solver usage, native SVG <tspan> subscripts,
// and all 5 interactive data-* hooks (node, branch, elem, port, causal-step).
const DIVIDER_SVG = [
  '<svg viewBox="0 0 380 220" role="img" aria-label="전압 분배기 소신호 회로도">',
  '  <g data-causal-step="1">',
  '    <line class="fig-ink" x1="60" y1="80" x2="60" y2="114"/>',
  '    <line class="fig-ink" x1="60" y1="146" x2="60" y2="180"/>',
  '    <g class="sym" data-symbol="vsrc">',
  '      <circle class="fig-ink" cx="60" cy="130" r="16"/>',
  '      <path class="fig-ink" d="M55 124h10M60 119v10M55 138h10"/>',
  '    </g>',
  '    <g class="sym" data-symbol="gnd">',
  '      <line class="fig-ink" x1="48" y1="180" x2="72" y2="180"/>',
  '      <line class="fig-ink" x1="52" y1="186" x2="68" y2="186"/>',
  '      <line class="fig-ink" x1="56" y1="192" x2="64" y2="192"/>',
  '    </g>',
  '    <line class="fig-ink" x1="60" y1="80" x2="78" y2="80"/>',
  '    <circle class="fig-dot" data-node="in" data-node-color="blue" cx="60" cy="80" r="3.5"/>',
  '    <text class="fig-text fig-math" data-node="in" data-node-color="blue" x="24" y="134" text-anchor="middle">v<tspan baseline-shift="sub" font-size="78%">in</tspan></text>',
  '  </g>',
  '  <g class="sym" data-symbol="resistor">',
  '    <path class="fig-ink" d="M78 80h6l4-7 6 14 6-14 6 14 6-14 6 14 4-7h6"/>',
  '  </g>',
  '  <text class="fig-text fig-math" x="103" y="114" text-anchor="middle">R<tspan baseline-shift="sub" font-size="78%">1</tspan></text>',
  '  <line class="fig-ink" data-branch="i_div" data-causal-step="2" x1="128" y1="80" x2="220" y2="80"/>',
  '  <g data-elem="r2" data-causal-step="2">',
  '    <line class="fig-ink" x1="220" y1="80" x2="220" y2="102"/>',
  '    <g class="sym" data-symbol="resistor">',
  '      <path class="fig-ink" d="M220 102v6l-7 4 14 6-14 6 14 6-14 6 14 6-7 4v6"/>',
  '    </g>',
  '    <line class="fig-ink" x1="220" y1="152" x2="220" y2="180"/>',
  '    <g class="sym" data-symbol="gnd">',
  '      <line class="fig-ink" x1="208" y1="180" x2="232" y2="180"/>',
  '      <line class="fig-ink" x1="212" y1="186" x2="228" y2="186"/>',
  '      <line class="fig-ink" x1="216" y1="192" x2="224" y2="192"/>',
  '    </g>',
  '    <text class="fig-text fig-math" x="188" y="132" text-anchor="end">R<tspan baseline-shift="sub" font-size="78%">2</tspan></text>',
  '  </g>',
  '  <g data-causal-step="3">',
  '    <line class="fig-ink" x1="220" y1="80" x2="318" y2="80"/>',
  '    <circle class="fig-dot" data-node="out" data-node-color="red" cx="220" cy="80" r="3.5"/>',
  '    <text class="fig-text fig-math" data-node="out" data-node-color="red" x="348" y="84" text-anchor="middle">v<tspan baseline-shift="sub" font-size="78%">out</tspan></text>',
  '  </g>',
  '  <line class="fig-ink" x1="290" y1="80" x2="290" y2="104"/>',
  '  <g data-port="load">',
  '    <g class="port-chip">',
  '      <rect class="port-chip-bg" x="252" y="116" width="76" height="24" rx="6"/>',
  '      <text class="port-chip" x="290" y="132" text-anchor="middle">개방</text>',
  '    </g>',
  '    <g data-port-view="open"></g>',
  '    <g data-port-view="rl">',
  '      <text class="fig-muted fig-math" x="346" y="132" text-anchor="start">R<tspan baseline-shift="sub" font-size="78%">L</tspan></text>',
  '    </g>',
  '  </g>',
  '  <line class="fig-ink" x1="290" y1="156" x2="290" y2="180"/>',
  '  <g class="sym" data-symbol="gnd">',
  '    <line class="fig-ink" x1="278" y1="180" x2="302" y2="180"/>',
  '    <line class="fig-ink" x1="282" y1="186" x2="298" y2="186"/>',
  '    <line class="fig-ink" x1="286" y1="192" x2="294" y2="192"/>',
  '  </g>',
  '  <g data-badges>',
  '    <g data-badge-for="in" transform="translate(60, 32)"></g>',
  '    <g data-badge-for="out" transform="translate(220, 32)"></g>',
  '  </g>',
  '</svg>',
].join('\n');

const spec = {
  id: 'example-voltage-divider',
  title: '전압 분배기 동작 프로브',
  archetype: 'probe',
  modes: [
    {
      key: 'divider',
      label: '분배기',
      svg: DIVIDER_SVG,
      ariaLabel: '전압 분배기 소신호 회로도',
      viewBox: '0 0 380 220',
    },
  ],
  predict: {
    prompt: '무부하 상태에서 $v_{\\text{in}}$을 2배로 키우면 분압비 $v_{\\text{out}} / v_{\\text{in}}$은 어떻게 될까요?',
    options: [
      { id: 'same', label: '그대로 유지된다' },
      { id: 'double', label: '2배가 된다' },
    ],
    answerId: 'same',
    explain: '선형 저항 분배기의 분압비 $R_2 / (R_1 + R_2)$는 저항비로만 결정되므로 입력 크기가 커져도 분압비는 일정합니다.',
    check: {
      before: { params: { vin: 4 }, ports: { load: 'open' }, disabledElems: [] },
      after: { params: { vin: 8 }, causalStep: 3 },
      tiles: ['출력 전압', '분압비'],
    },
  },
  params: [
    { key: 'vin', label: '입력 전압', min: -10, max: 10, step: 0.5, unit: 'V', def: 4 },
    { key: 'r1', label: '상단 저항 R1', min: 1, max: 10, step: 0.5, unit: 'kΩ', def: 3 },
  ],
  elems: [
    { id: 'r2', label: '하단 저항 R2 (1 kΩ)' },
  ],
  ports: [
    {
      id: 'load',
      label: '출력 부하 종단',
      options: [
        { id: 'open', label: '개방 (무부하)', shortLabel: '개방' },
        { id: 'rl', label: '4 kΩ 부하', shortLabel: '4 kΩ' },
      ],
      def: 'open',
      answer: 'open',
    },
  ],
  causalSteps: [
    { id: 1, label: '입력 전압 인가', detail: '입력 노드 전압이 기준 전위에서 변화합니다.' },
    { id: 2, label: '직렬 저항 전류 형성', detail: '상단 저항과 하단 경로를 따라 분배 전류가 흐릅니다.' },
    { id: 3, label: '출력 전압 결정', detail: '병렬 합성 저항에 전류가 곱해져 출력 전압이 정해집니다.' },
  ],
  presets: [
    { id: 'quarter', label: '기본 1:3 분배', params: { vin: 4, r1: 3 }, ports: { load: 'open' }, disabledElems: [] },
    { id: 'loaded', label: '부하 로딩 확인', params: { vin: 4, r1: 3 }, ports: { load: 'rl' }, disabledElems: [] },
  ],
  toggles: [['labels', '노드 배지', true]],
  mistakes: {
    divider: [
      {
        title: '부하 저항을 무시한 무부하 공식 고집',
        text: '출력에 $R_L$이 연결되면 하단 저항은 $R_2$가 아니라 $R_2 \\parallel R_L$로 줄어들어 분압비가 낮아집니다.',
      },
      {
        title: '선형 분압비와 출력 크기의 혼동',
        text: '입력 $v_{\\text{in}}$을 키우면 출력 $v_{\\text{out}}$은 비례해 커지지만 비 $v_{\\text{out}}/v_{\\text{in}}$은 변하지 않습니다.',
      },
      {
        title: '하단 경로 개방 시 0 V로 착각',
        text: '$R_2$와 부하가 모두 개방이면 전류가 흐르지 않아 저항 $R_1$의 전압 강하가 $0\\text{ V}$가 되고 $v_{\\text{out}} = v_{\\text{in}}$이 됩니다.',
      },
    ],
  },
  evaluate(state, mna) {
    const vin = Number(state.params.vin);
    const r1Ohm = Number(state.params.r1) * 1000;
    const r2Active = !state.disabledElems.includes('r2');
    const loadOn = state.ports.load === 'rl';

    const solved = mna.solveCircuit({
      elements: [
        { id: 'vs', type: 'vsrc', n1: 'in', n2: '0', value: vin },
        { id: 'r1', type: 'R', n1: 'in', n2: 'out', value: r1Ohm },
        r2Active
          ? { id: 'r2', type: 'R', n1: 'out', n2: '0', value: 1000 }
          : { id: 'r2', type: 'open', n1: 'out', n2: '0' },
        loadOn
          ? { id: 'rl', type: 'R', n1: 'out', n2: '0', value: 4000 }
          : { id: 'rl', type: 'open', n1: 'out', n2: '0' },
      ],
    });

    if (!solved.ok) {
      return {
        tiles: [{ label: '상태', val: '오류' }],
        diagnosis: { kind: 'bad', singular: true, title: '회로 해석 실패', text: solved.reason },
      };
    }

    const vIn = solved.nodes.in.re;
    const vOut = solved.nodes.out.re;
    const iDivMa = solved.branches.r1.re * 1000;
    const gain = Math.abs(vIn) > 1e-12
      ? vOut / vIn
      : (r2Active ? (loadOn ? 800 / (r1Ohm + 800) : 1000 / (r1Ohm + 1000)) : (loadOn ? 4000 / (r1Ohm + 4000) : 1));
    const dirIn = vIn > 1e-6 ? 'up' : (vIn < -1e-6 ? 'down' : undefined);
    const dirOut = vOut > 1e-6 ? 'up' : (vOut < -1e-6 ? 'down' : undefined);

    return {
      tiles: [
        { label: '입력 전압', val: `${vIn.toFixed(2)} V` },
        { label: '출력 전압', val: `${vOut.toFixed(2)} V` },
        { label: '분압비', val: `${gain.toFixed(3)} V/V` },
      ],
      diagnosis: loadOn
        ? { kind: 'warn', title: '출력 부하 로딩', text: '$R_L = 4\\text{ k}\\Omega$이 $R_2$와 병렬로 걸려 출력 전압이 내려갔습니다.' }
        : (!r2Active
          ? { kind: 'info', title: '하단 저항 개방', text: '전류가 흐르지 않아 $v_{\\text{out}} = v_{\\text{in}}$ 그대로 전달됩니다.' }
          : { kind: 'ok', title: '무부하 분배', text: '이상적인 무부하 전압 분배 조건에서 동작하고 있습니다.' }),
      formula: '$$v_{\\text{out}} = \\frac{R_{\\text{eq}}}{R_1 + R_{\\text{eq}}} v_{\\text{in}}$$',
      summary: `현재 $v_{\\text{in}} = ${vIn.toFixed(2)}\\text{ V}$일 때 $i_{\\text{div}} = ${iDivMa.toFixed(2)}\\text{ mA}$가 흘러 $v_{\\text{out}} = ${vOut.toFixed(2)}\\text{ V}$가 됩니다.`,
      nodes: {
        in: { v: Number(vIn.toFixed(2)), unit: 'V', dir: dirIn, hot: state.causalStep === 1 },
        out: { v: Number(vOut.toFixed(2)), unit: 'V', dir: dirOut, hot: state.causalStep === 3 },
      },
      branches: {
        i_div: { hot: state.causalStep === 2, dir: iDivMa >= 0 ? 'fwd' : 'rev' },
      },
      elems: {
        r2: { hot: r2Active && state.causalStep === 2 },
      },
      ports: {
        load: { hot: loadOn },
      },
    };
  },
};

module.exports = spec;
