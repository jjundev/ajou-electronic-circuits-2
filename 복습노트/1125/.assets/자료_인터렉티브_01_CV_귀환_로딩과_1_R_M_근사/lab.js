// Lab 01: C-V 귀환 로딩과 1/R_M 근사 비교 (archetype: 'approx')
// 1125 수업 예제 III (CG M1 + SF M2 + R_L + R_M)

const CV_OPEN_SVG = [
  '<svg viewBox="0 0 500 290" role="img" aria-label="C-V 귀환 개루프 로딩 소신호 회로도">',
  '  <g data-causal-step="1">',
  '    <line class="fig-ink" x1="60" y1="150" x2="60" y2="180"/>',
  '    <line class="fig-ink" x1="60" y1="212" x2="60" y2="246"/>',
  '    <g class="sym" data-symbol="vsrc">',
  '      <circle class="fig-ink" cx="60" cy="196" r="16"/>',
  '      <path class="fig-ink" d="M55 190h10M60 185v10M55 204h10"/>',
  '    </g>',
  '    <g class="sym" data-symbol="gnd">',
  '      <line class="fig-ink" x1="48" y1="246" x2="72" y2="246"/>',
  '      <line class="fig-ink" x1="52" y1="252" x2="68" y2="252"/>',
  '      <line class="fig-ink" x1="56" y1="258" x2="64" y2="258"/>',
  '    </g>',
  '    <line class="fig-ink" x1="60" y1="150" x2="145" y2="150"/>',
  '    <circle class="fig-dot" data-node="in" data-node-color="blue" cx="60" cy="150" r="3.5"/>',
  '    <text class="fig-text fig-math" data-node="in" data-node-color="blue" x="26" y="200" text-anchor="middle">v<tspan baseline-shift="sub" font-size="78%">in</tspan></text>',
  '    <line class="fig-ink" x1="145" y1="74" x2="145" y2="112"/>',
  '    <g class="sym" data-symbol="nmos">',
  '      <line class="fig-ink" x1="130" y1="112" x2="130" y2="148"/>',
  '      <line class="fig-ink" x1="135" y1="112" x2="135" y2="148"/>',
  '      <line class="fig-ink" x1="135" y1="116" x2="145" y2="116"/>',
  '      <line class="fig-ink" x1="135" y1="144" x2="145" y2="144"/>',
  '      <line class="fig-ink" x1="145" y1="144" x2="145" y2="150"/>',
  '      <line class="fig-ink" x1="114" y1="130" x2="130" y2="130"/>',
  '    </g>',
  '    <text class="fig-text fig-math" x="172" y="135" text-anchor="start">M<tspan baseline-shift="sub" font-size="78%">1</tspan></text>',
  '    <line class="fig-ink" x1="114" y1="130" x2="114" y2="180"/>',
  '    <g class="sym" data-symbol="resistor">',
  '      <path class="fig-ink" d="M114 180v6l-6 3 12 5-12 5 12 5-12 5 12 5-6 3v6"/>',
  '    </g>',
  '    <line class="fig-ink" x1="114" y1="223" x2="114" y2="246"/>',
  '    <g class="sym" data-symbol="gnd">',
  '      <line class="fig-ink" x1="102" y1="246" x2="126" y2="246"/>',
  '      <line class="fig-ink" x1="106" y1="252" x2="122" y2="252"/>',
  '      <line class="fig-ink" x1="110" y1="258" x2="118" y2="258"/>',
  '    </g>',
  '    <text class="fig-muted fig-math" x="92" y="205" text-anchor="end">R<tspan baseline-shift="sub" font-size="78%">M</tspan></text>',
  '    <line class="fig-ink" x1="145" y1="74" x2="195" y2="74"/>',
  '    <g class="sym" data-symbol="resistor">',
  '      <path class="fig-ink" d="M195 74h6l3-6 5 12 5-12 5 12 5-12 5 12 3-6h6"/>',
  '    </g>',
  '    <line class="fig-ink" x1="238" y1="74" x2="256" y2="74"/>',
  '    <g class="sym" data-symbol="gnd">',
  '      <line class="fig-ink" x1="256" y1="62" x2="256" y2="86"/>',
  '      <line class="fig-ink" x1="262" y1="66" x2="262" y2="82"/>',
  '      <line class="fig-ink" x1="268" y1="70" x2="268" y2="78"/>',
  '    </g>',
  '    <text class="fig-text fig-math" x="216" y="56" text-anchor="middle">R<tspan baseline-shift="sub" font-size="78%">D</tspan></text>',
  '    <line class="fig-ink" data-branch="vx_line" x1="145" y1="102" x2="310" y2="102"/>',
  '    <circle class="fig-dot" data-node="x" data-node-color="red" cx="145" cy="102" r="3.5"/>',
  '    <text class="fig-text fig-math" data-node="x" data-node-color="red" x="292" y="82" text-anchor="end">V<tspan baseline-shift="sub" font-size="78%">X</tspan></text>',
  '  </g>',
  '  <g data-causal-step="2">',
  '    <line class="fig-ink" x1="330" y1="64" x2="330" y2="84"/>',
  '    <g class="sym" data-symbol="gnd">',
  '      <line class="fig-ink" x1="318" y1="64" x2="342" y2="64"/>',
  '    </g>',
  '    <text class="fig-muted fig-math" x="358" y="68" text-anchor="start">V<tspan baseline-shift="sub" font-size="78%">DD</tspan></text>',
  '    <g class="sym" data-symbol="nmos">',
  '      <line class="fig-ink" x1="315" y1="84" x2="315" y2="120"/>',
  '      <line class="fig-ink" x1="320" y1="84" x2="320" y2="120"/>',
  '      <line class="fig-ink" x1="320" y1="88" x2="330" y2="88"/>',
  '      <line class="fig-ink" x1="320" y1="116" x2="330" y2="116"/>',
  '      <line class="fig-ink" x1="310" y1="102" x2="315" y2="102"/>',
  '    </g>',
  '    <text class="fig-text fig-math" x="356" y="106" text-anchor="start">M<tspan baseline-shift="sub" font-size="78%">2</tspan></text>',
  '    <line class="fig-ink" data-branch="i_out" x1="330" y1="116" x2="330" y2="146"/>',
  '    <circle class="fig-dot" data-node="s2" data-node-color="blue" cx="330" cy="134" r="3.5"/>',
  '    <text class="fig-text fig-math" data-node="s2" data-node-color="blue" x="304" y="138" text-anchor="end">V<tspan baseline-shift="sub" font-size="78%">S2</tspan></text>',
  '    <g class="sym" data-symbol="resistor">',
  '      <path class="fig-ink" d="M330 146v5l-6 3 12 5-12 5 12 5-12 5 12 5-6 3v5"/>',
  '    </g>',
  '    <text class="fig-text fig-math" x="362" y="168" text-anchor="start">R<tspan baseline-shift="sub" font-size="78%">L</tspan></text>',
  '  </g>',
  '  <g data-elem="rm_load" data-causal-step="3">',
  '    <line class="fig-ink" x1="330" y1="187" x2="330" y2="202"/>',
  '    <circle class="fig-dot" data-node="vf" data-node-color="red" cx="330" cy="196" r="3.5"/>',
  '    <text class="fig-text fig-math" data-node="vf" data-node-color="red" x="304" y="200" text-anchor="end">V<tspan baseline-shift="sub" font-size="78%">F</tspan></text>',
  '    <g class="sym" data-symbol="resistor">',
  '      <path class="fig-ink" d="M330 202v4l-6 3 12 5-12 5 12 5-12 5 12 5-6 3v4"/>',
  '    </g>',
  '    <text class="fig-text fig-math" x="362" y="226" text-anchor="start">R<tspan baseline-shift="sub" font-size="78%">M</tspan> 복제</text>',
  '    <line class="fig-ink" x1="330" y1="241" x2="330" y2="254"/>',
  '    <g class="sym" data-symbol="gnd">',
  '      <line class="fig-ink" x1="318" y1="254" x2="342" y2="254"/>',
  '      <line class="fig-ink" x1="322" y1="260" x2="338" y2="260"/>',
  '      <line class="fig-ink" x1="326" y1="266" x2="334" y2="266"/>',
  '    </g>',
  '  </g>',
  '  <g data-badges>',
  '    <g data-badge-for="in" transform="translate(70, 26)"></g>',
  '    <g data-badge-for="x" transform="translate(195, 26)"></g>',
  '    <g data-badge-for="s2" transform="translate(320, 26)"></g>',
  '    <g data-badge-for="vf" transform="translate(435, 26)"></g>',
  '  </g>',
  '</svg>',
].join('\n');

const CV_CLOSED_SVG = [
  '<svg viewBox="0 0 500 290" role="img" aria-label="C-V 귀환 폐루프 소신호 회로도">',
  '  <g data-causal-step="1">',
  '    <line class="fig-ink" x1="60" y1="150" x2="60" y2="180"/>',
  '    <line class="fig-ink" x1="60" y1="212" x2="60" y2="246"/>',
  '    <g class="sym" data-symbol="vsrc">',
  '      <circle class="fig-ink" cx="60" cy="196" r="16"/>',
  '      <path class="fig-ink" d="M55 190h10M60 185v10M55 204h10"/>',
  '    </g>',
  '    <g class="sym" data-symbol="gnd">',
  '      <line class="fig-ink" x1="48" y1="246" x2="72" y2="246"/>',
  '      <line class="fig-ink" x1="52" y1="252" x2="68" y2="252"/>',
  '      <line class="fig-ink" x1="56" y1="258" x2="64" y2="258"/>',
  '    </g>',
  '    <line class="fig-ink" x1="60" y1="150" x2="145" y2="150"/>',
  '    <circle class="fig-dot" data-node="in" data-node-color="blue" cx="60" cy="150" r="3.5"/>',
  '    <text class="fig-text fig-math" data-node="in" data-node-color="blue" x="26" y="200" text-anchor="middle">v<tspan baseline-shift="sub" font-size="78%">in</tspan></text>',
  '    <line class="fig-ink" x1="145" y1="74" x2="145" y2="112"/>',
  '    <g class="sym" data-symbol="nmos">',
  '      <line class="fig-ink" x1="130" y1="112" x2="130" y2="148"/>',
  '      <line class="fig-ink" x1="135" y1="112" x2="135" y2="148"/>',
  '      <line class="fig-ink" x1="135" y1="116" x2="145" y2="116"/>',
  '      <line class="fig-ink" x1="135" y1="144" x2="145" y2="144"/>',
  '      <line class="fig-ink" x1="145" y1="144" x2="145" y2="150"/>',
  '      <line class="fig-ink" x1="114" y1="130" x2="130" y2="130"/>',
  '    </g>',
  '    <text class="fig-text fig-math" x="172" y="135" text-anchor="start">M<tspan baseline-shift="sub" font-size="78%">1</tspan></text>',
  '    <line class="fig-ink" x1="145" y1="74" x2="195" y2="74"/>',
  '    <g class="sym" data-symbol="resistor">',
  '      <path class="fig-ink" d="M195 74h6l3-6 5 12 5-12 5 12 5-12 5 12 3-6h6"/>',
  '    </g>',
  '    <line class="fig-ink" x1="238" y1="74" x2="256" y2="74"/>',
  '    <g class="sym" data-symbol="gnd">',
  '      <line class="fig-ink" x1="256" y1="62" x2="256" y2="86"/>',
  '      <line class="fig-ink" x1="262" y1="66" x2="262" y2="82"/>',
  '      <line class="fig-ink" x1="268" y1="70" x2="268" y2="78"/>',
  '    </g>',
  '    <text class="fig-text fig-math" x="216" y="56" text-anchor="middle">R<tspan baseline-shift="sub" font-size="78%">D</tspan></text>',
  '    <line class="fig-ink" data-branch="vx_line" x1="145" y1="102" x2="310" y2="102"/>',
  '    <circle class="fig-dot" data-node="x" data-node-color="red" cx="145" cy="102" r="3.5"/>',
  '    <text class="fig-text fig-math" data-node="x" data-node-color="red" x="292" y="82" text-anchor="end">V<tspan baseline-shift="sub" font-size="78%">X</tspan></text>',
  '  </g>',
  '  <g data-causal-step="2">',
  '    <line class="fig-ink" x1="330" y1="64" x2="330" y2="84"/>',
  '    <g class="sym" data-symbol="gnd">',
  '      <line class="fig-ink" x1="318" y1="64" x2="342" y2="64"/>',
  '    </g>',
  '    <text class="fig-muted fig-math" x="358" y="68" text-anchor="start">V<tspan baseline-shift="sub" font-size="78%">DD</tspan></text>',
  '    <g class="sym" data-symbol="nmos">',
  '      <line class="fig-ink" x1="315" y1="84" x2="315" y2="120"/>',
  '      <line class="fig-ink" x1="320" y1="84" x2="320" y2="120"/>',
  '      <line class="fig-ink" x1="320" y1="88" x2="330" y2="88"/>',
  '      <line class="fig-ink" x1="320" y1="116" x2="330" y2="116"/>',
  '      <line class="fig-ink" x1="310" y1="102" x2="315" y2="102"/>',
  '    </g>',
  '    <text class="fig-text fig-math" x="356" y="106" text-anchor="start">M<tspan baseline-shift="sub" font-size="78%">2</tspan></text>',
  '    <line class="fig-ink" data-branch="i_out" x1="330" y1="116" x2="330" y2="146"/>',
  '    <circle class="fig-dot" data-node="s2" data-node-color="blue" cx="330" cy="134" r="3.5"/>',
  '    <text class="fig-text fig-math" data-node="s2" data-node-color="blue" x="304" y="138" text-anchor="end">V<tspan baseline-shift="sub" font-size="78%">S2</tspan></text>',
  '    <g class="sym" data-symbol="resistor">',
  '      <path class="fig-ink" d="M330 146v5l-6 3 12 5-12 5 12 5-12 5 12 5-6 3v5"/>',
  '    </g>',
  '    <text class="fig-text fig-math" x="362" y="168" text-anchor="start">R<tspan baseline-shift="sub" font-size="78%">L</tspan></text>',
  '    <line class="fig-ink" x1="330" y1="187" x2="330" y2="202"/>',
  '    <circle class="fig-dot" data-node="vf" data-node-color="red" cx="330" cy="196" r="3.5"/>',
  '    <text class="fig-text fig-math" data-node="vf" data-node-color="red" x="362" y="200" text-anchor="start">V<tspan baseline-shift="sub" font-size="78%">F</tspan></text>',
  '    <g class="sym" data-symbol="resistor">',
  '      <path class="fig-ink" d="M330 202v4l-6 3 12 5-12 5 12 5-12 5 12 5-6 3v4"/>',
  '    </g>',
  '    <text class="fig-text fig-math" x="362" y="228" text-anchor="start">R<tspan baseline-shift="sub" font-size="78%">M</tspan></text>',
  '    <line class="fig-ink" x1="330" y1="241" x2="330" y2="254"/>',
  '    <g class="sym" data-symbol="gnd">',
  '      <line class="fig-ink" x1="318" y1="254" x2="342" y2="254"/>',
  '      <line class="fig-ink" x1="322" y1="260" x2="338" y2="260"/>',
  '      <line class="fig-ink" x1="326" y1="266" x2="334" y2="266"/>',
  '    </g>',
  '  </g>',
  '  <g data-elem="fb_loop" data-causal-step="3">',
  '    <path class="fig-accent" data-branch="fb_wire" d="M330 196H114V130"/>',
  '    <text class="fig-text" x="222" y="218" text-anchor="middle">전압 반송 경로 (V<tspan baseline-shift="sub" font-size="78%">F</tspan> → M<tspan baseline-shift="sub" font-size="78%">1</tspan> 게이트)</text>',
  '  </g>',
  '  <g data-badges>',
  '    <g data-badge-for="in" transform="translate(70, 26)"></g>',
  '    <g data-badge-for="x" transform="translate(195, 26)"></g>',
  '    <g data-badge-for="s2" transform="translate(320, 26)"></g>',
  '    <g data-badge-for="vf" transform="translate(435, 26)"></g>',
  '  </g>',
  '</svg>',
].join('\n');

const GM2_MS = 4; // 4 mS -> 1/gm2 = 0.25 kOhm
const VIN_MV = 10; // 10 mV small-signal input

function solveCVOpen(mna, gm1Ms, rdK, rlK, rmK, rmActive) {
  const gm1 = gm1Ms * 1e-3;
  const gm2 = GM2_MS * 1e-3;
  const rd = rdK * 1e3;
  const rl = rlK * 1e3;
  const rm = rmK * 1e3;
  const vin = VIN_MV * 1e-3;

  const elements = [
    { id: 'vs', type: 'vsrc', n1: 'in', n2: '0', value: vin },
    // Input replica R_M at M1 gate (open at sense port -> g1 to gnd)
    { id: 'rm_in', type: 'R', n1: 'g1', n2: '0', value: Math.max(rm, 1) },
    { id: 'm1', type: 'vccs', n1: 'x', n2: 'in', cp: 'g1', cn: 'in', gm: gm1 },
    { id: 'rd', type: 'R', n1: 'x', n2: '0', value: rd },
    { id: 'm2', type: 'vccs', n1: '0', n2: 's2', cp: 'x', cn: 's2', gm: gm2 },
    { id: 'rl', type: 'R', n1: 's2', n2: 'vf', value: rl },
    rmActive
      ? { id: 'rm_out', type: 'R', n1: 'vf', n2: '0', value: rm }
      : { id: 'rm_out', type: 'short', n1: 'vf', n2: '0' },
  ];
  return mna.solveCircuit({ elements });
}

function solveCVClosed(mna, gm1Ms, rdK, rlK, rmK, fbActive) {
  const gm1 = gm1Ms * 1e-3;
  const gm2 = GM2_MS * 1e-3;
  const rd = rdK * 1e3;
  const rl = rlK * 1e3;
  const rm = rmK * 1e3;
  const vin = VIN_MV * 1e-3;

  const elements = [
    { id: 'vs', type: 'vsrc', n1: 'in', n2: '0', value: vin },
    fbActive
      ? { id: 'fb_wire', type: 'short', n1: 'g1', n2: 'vf' }
      : { id: 'fb_wire', type: 'short', n1: 'g1', n2: '0' },
    { id: 'm1', type: 'vccs', n1: 'x', n2: 'in', cp: 'g1', cn: 'in', gm: gm1 },
    { id: 'rd', type: 'R', n1: 'x', n2: '0', value: rd },
    { id: 'm2', type: 'vccs', n1: '0', n2: 's2', cp: 'x', cn: 's2', gm: gm2 },
    { id: 'rl', type: 'R', n1: 's2', n2: 'vf', value: rl },
    { id: 'rm_out', type: 'R', n1: 'vf', n2: '0', value: rm },
  ];
  return mna.solveCircuit({ elements });
}

const spec = {
  id: 'cv-feedback-loading-approx',
  title: 'C-V 귀환 로딩과 1/R_M 근사 비교',
  archetype: 'approx',
  modes: [
    {
      key: 'open',
      label: '개루프 로딩',
      svg: CV_OPEN_SVG,
      ariaLabel: 'C-V 귀환 개루프 로딩 소신호 회로도',
      viewBox: '0 0 500 290',
      elems: [{ id: 'rm_load', label: '출력 쪽 R_M 복제 포함' }],
      causalSteps: [
        { id: 1, label: 'CG 단 V_X 형성', detail: '입력 전압이 공통 게이트 M1을 거쳐 V_X = g_m1 R_D v_in으로 커집니다.' },
        { id: 2, label: 'M2 소스 전압 상승', detail: '부하 R_L 아래에 직렬로 붙은 R_M 복제가 M2 소스 전압을 끌어올립니다.' },
        { id: 3, label: 'V_GS2 감소와 이득 하락', detail: 'V_GS2가 줄어들면서 레이저 전류 I_out이 이상 개루프보다 작아집니다.' },
      ],
      presets: [
        { id: 'class_ex', label: '수업 예시 (R_M = 1 kΩ)', params: { gm1: 2, rd: 5, rm: 1, rl: 0.5 }, disabledElems: [] },
        { id: 'ideal_near', label: '근사 성립 (R_M = 0.05 kΩ)', params: { gm1: 2, rd: 5, rm: 0.05, rl: 0.5 }, disabledElems: [] },
        { id: 'heavy_load', label: '큰 로딩 (R_M = 3 kΩ)', params: { gm1: 2, rd: 5, rm: 3, rl: 0.5 }, disabledElems: [] },
      ],
    },
    {
      key: 'closed',
      label: '폐루프 근사',
      svg: CV_CLOSED_SVG,
      ariaLabel: 'C-V 귀환 폐루프 소신호 회로도',
      viewBox: '0 0 500 290',
      elems: [{ id: 'fb_loop', label: '전압 반송 귀환 경로 연결' }],
      causalSteps: [
        { id: 1, label: '입력·반송 차동 증폭', detail: 'M1이 v_in과 반송 전압 V_F의 차이를 증폭해 V_X를 만듭니다.' },
        { id: 2, label: '감지 저항 V_F 생성', detail: '레이저 전류 I_out이 R_M을 지나며 V_F = I_out R_M을 만듭니다.' },
        { id: 3, label: '루프 안정화 (1/R_M 근접)', detail: '루프 이득 KA_0가 클수록 폐루프 이득이 1/R_M에 가까워집니다.' },
      ],
      presets: [
        { id: 'closed_ex', label: '수업 예시 (KA_0 = 5.71)', params: { gm1: 2, rd: 5, rm: 1, rl: 0.5 }, disabledElems: [] },
        { id: 'high_lg', label: '큰 루프 이득 (근사 성립)', params: { gm1: 5, rd: 10, rm: 1, rl: 0.5 }, disabledElems: [] },
        { id: 'low_lg', label: '작은 루프 이득 (근사 붕괴)', params: { gm1: 0.5, rd: 2, rm: 0.2, rl: 1.5 }, disabledElems: [] },
      ],
    },
  ],
  predict: {
    mode: 'open',
    prompt: '개루프 회로에서 출력 쪽 복제 $R_M = 1\\text{ k}\\Omega$을 켜면 개루프 이득 $I_{\\text{out}}/V_{\\text{in}}$은 어떻게 바뀔까요?',
    options: [
      { id: 'drop', label: '줄어든다' },
      { id: 'same', label: '변하지 않는다' },
      { id: 'rise', label: '커진다' },
    ],
    answerId: 'drop',
    explain: '출력 쪽 $R_M$ 복제가 $R_L$ 아래에 직렬로 더해지면 $M_2$ 소스 전압이 올라가 $V_{GS2}$가 줄어드므로 개루프 이득이 $13.33\\text{ mS}$에서 $5.71\\text{ mS}$로 크게 줄어듭니다.',
    check: {
      before: { params: { gm1: 2, rd: 5, rm: 1, rl: 0.5 }, disabledElems: ['rm_load'] },
      after: { disabledElems: [], causalStep: 3 },
      tiles: ['개루프 이득', '출력 임피던스'],
    },
  },
  params: [
    { key: 'rm', label: '감지 저항 R_M', min: 0.05, max: 4, step: 0.05, unit: 'kΩ', def: 1 },
    { key: 'gm1', label: 'M1 트랜스컨덕턴스 g_m1', min: 0.5, max: 5, step: 0.1, unit: 'mS', def: 2 },
    { key: 'rd', label: '드레인 저항 R_D', min: 1, max: 10, step: 0.5, unit: 'kΩ', def: 5 },
    { key: 'rl', label: '부하 저항 R_L (레이저)', min: 0.1, max: 2, step: 0.1, unit: 'kΩ', def: 0.5 },
  ],
  toggles: [['labels', '노드 배지', true]],
  mistakes: {
    open: [
      {
        title: 'R_M을 지운 이상 개루프 이득을 그대로 사용',
        text: '$R_M$이 $1/g_{m2} + R_L$에 비해 작지 않으면 직렬 로딩으로 개루프 이득이 크게 줄어듭니다. 반드시 분모에 $R_M$을 더해야 합니다.',
      },
      {
        title: '출력 임피던스에서 1/g_m2와 R_M을 병렬로 계산',
        text: '부하 $R_L$ 양단에서 위쪽 $1/g_{m2}$와 아래쪽 $R_M$은 같은 AC 접지로 한 고리를 이루므로 직렬 합 $1/g_{m2} + R_M$입니다.',
      },
      {
        title: '입력 쪽 R_M 복제가 첫 단 이득을 바꾼다고 오해',
        text: '입력 쪽 $R_M$ 복제는 $M_1$ 게이트에 붙어 있고 게이트 전류가 $0$이므로 $V_{G1}=0$이 유지되어 $V_X/V_{\\text{in}} = g_{m1}R_D$는 변하지 않습니다.',
      },
    ],
    closed: [
      {
        title: '루프 이득이 작아도 무조건 1/R_M이라고 근사',
        text: '$G_{m,\\text{closed}} = \\frac{1}{R_M}\\cdot\\frac{KA_0}{1+KA_0}$이므로 $KA_0$가 작으면 $1/R_M$ 근사 오차가 급격히 커집니다.',
      },
      {
        title: 'R_M 하나로 정한 이득이 공정 변동에 완벽하다고 오해',
        text: '이 회로는 저항 비가 아니라 $R_M$ 하나의 절댓값으로 $K$를 정하므로 저항 절댓값 변동의 영향을 받습니다.',
      },
      {
        title: 'C-V 귀환에서 출력 임피던스가 줄어든다고 혼동',
        text: '출력 전류를 직렬 감지해 조절하므로 폐루프 출력 임피던스는 $(1+KA_0)$배 커져 더 좋은 전류원이 됩니다.',
      },
    ],
  },
  evaluate(state, mna) {
    const gm1 = Number(state.params.gm1);
    const rd = Number(state.params.rd);
    const rm = Number(state.params.rm);
    const rl = Number(state.params.rl);
    const invGm2 = 1 / GM2_MS; // 0.25 kOhm

    if (state.mode === 'open') {
      const rmActive = !state.disabledElems.includes('rm_load');
      const solved = solveCVOpen(mna, gm1, rd, rl, rm, rmActive);
      if (!solved.ok) {
        return {
          tiles: [{ label: '상태', val: '오류' }],
          diagnosis: { kind: 'bad', title: '회로 해석 실패', text: solved.reason },
        };
      }

      const vInMv = solved.nodes.in.re * 1e3;
      const vXMv = solved.nodes.x.re * 1e3;
      const vS2Mv = solved.nodes.s2.re * 1e3;
      const vFMv = solved.nodes.vf.re * 1e3;
      const iOutUa = solved.branches.rl.re * 1e6;
      const gainMs = (solved.branches.rl.re / solved.nodes.in.re) * 1e3;
      const idealGainMs = (gm1 * rd) / (invGm2 + rl);
      const exactAtRmMs = (gm1 * rd) / (invGm2 + rl + rm);
      const rOutOpenK = invGm2 + (rmActive ? rm : 0);
      const errPct = ((idealGainMs - exactAtRmMs) / exactAtRmMs) * 100;

      // Sweep R_M from 0.05 to 4.0 kOhm
      const exactCurve = [];
      const approxCurve = [];
      for (let i = 0; i <= 40; i++) {
        const xRm = 0.05 + (3.95 * i) / 40;
        const gEx = (gm1 * rd) / (invGm2 + rl + xRm);
        exactCurve.push([Number(xRm.toFixed(3)), Number(gEx.toFixed(4))]);
        approxCurve.push([Number(xRm.toFixed(3)), Number(idealGainMs.toFixed(4))]);
      }

      const diag = !rmActive
        ? {
            kind: 'info',
            title: '출력 쪽 R_M 복제 OFF (이상 개루프)',
            text: `감지 저항을 $0\\ \\Omega$으로 무시해 개루프 이득이 $${gainMs.toFixed(2)}\\text{ mS}$로 크게 계산됩니다. 실제 $R_M = ${rm.toFixed(2)}\\text{ k}\\Omega$을 켜면 직렬 로딩을 확인할 수 있습니다.`,
          }
        : errPct > 10
          ? {
              kind: 'warn',
              title: '로딩 효과 큼 (이상 근사 붕괴)',
              text: `$R_M = ${rm.toFixed(2)}\\text{ k}\\Omega$이 $1/g_{m2}+R_L = ${(invGm2 + rl).toFixed(2)}\\text{ k}\\Omega$에 비해 무시할 수 없어, $R_M$을 지운 근사가 실제보다 $${errPct.toFixed(1)}\\%$ 크게 벗어납니다.`,
            }
          : {
              kind: 'ok',
              title: '로딩 효과 작음 (이상 근사 성립)',
              text: `$R_M = ${rm.toFixed(2)}\\text{ k}\\Omega$이 충분히 작아 이상 개루프 근사 오차가 $${errPct.toFixed(1)}\\%$ 이내입니다.`,
            };

      return {
        tiles: [
          { label: '개루프 이득', val: `${gainMs.toFixed(2)} mS` },
          { label: '이상 근사 (R_M=0)', val: `${idealGainMs.toFixed(2)} mS` },
          { label: '출력 임피던스', val: `${rOutOpenK.toFixed(2)} kΩ` },
        ],
        diagnosis: diag,
        formula: '$$\\begin{aligned}A_0 &= \\frac{g_{m1}R_D}{1/g_{m2}+R_L+R_M} \\\\ R_{\\text{out,open}} &= \\frac{1}{g_{m2}} + R_M\\end{aligned}$$',
        summary: `소신호 선형 모델($r_O\\to\\infty$, $g_{m2}=4\\text{ mS}$, $v_{\\text{in}}=10\\text{ mV}$)에서 레이저 전류는 $${iOutUa.toFixed(1)}\\ \\mu\\text{A}$이고, ${rmActive ? '$R_M$ 복제가 직렬로 더해져 개루프 이득이 줄었습니다.' : '$R_M$ 복제를 꺼 두어 이상 개루프 값만 보이고 있습니다.'}`,
        nodes: {
          in: { v: Number(vInMv.toFixed(1)), unit: 'mV', dir: 'up', hot: state.causalStep === 1 },
          x: { v: Number(vXMv.toFixed(1)), unit: 'mV', dir: 'up', hot: state.causalStep === 1 },
          s2: { v: Number(vS2Mv.toFixed(1)), unit: 'mV', dir: 'up', hot: state.causalStep === 2 },
          vf: { v: Number(vFMv.toFixed(1)), unit: 'mV', dir: vFMv > 0.05 ? 'up' : undefined, hot: state.causalStep === 3 },
        },
        branches: {
          vx_line: { hot: state.causalStep === 1, dir: 'fwd' },
          i_out: { hot: state.causalStep >= 2, dir: 'fwd' },
        },
        elems: {
          rm_load: { hot: rmActive && state.causalStep === 3 },
        },
        plotData: {
          title: 'R_M에 따른 개루프 이득: 로딩 포함 정확식 vs R_M=0 근사',
          ariaLabel: '감지 저항 R_M에 따른 개루프 트랜스컨덕턴스 정확 곡선과 이상 근사 곡선 비교',
          xLabel: 'R_M (kΩ)',
          yLabel: 'A_0 (mS)',
          xMin: 0.05,
          xMax: 4,
          yMin: 0,
          exact: exactCurve,
          approx: approxCurve,
          exactLabel: '로딩 포함 정확식',
          approxLabel: 'R_M=0 이상 근사',
          marker: [rm, Number(gainMs.toFixed(4))],
          approxMarker: [rm, Number(idealGainMs.toFixed(4))],
          errPct: Number(errPct.toFixed(1)),
          thresholdPct: 10,
        },
      };
    }

    // Closed-loop mode
    const fbActive = !state.disabledElems.includes('fb_loop');
    const solved = solveCVClosed(mna, gm1, rd, rl, rm, fbActive);
    if (!solved.ok) {
      return {
        tiles: [{ label: '상태', val: '오류' }],
        diagnosis: { kind: 'bad', title: '회로 해석 실패', text: solved.reason },
      };
    }

    const vInMv = solved.nodes.in.re * 1e3;
    const vXMv = solved.nodes.x.re * 1e3;
    const vS2Mv = solved.nodes.s2.re * 1e3;
    const vFMv = solved.nodes.vf.re * 1e3;
    const gmClosedMs = (solved.branches.rl.re / solved.nodes.in.re) * 1e3;
    const a0Ms = (gm1 * rd) / (invGm2 + rl + rm);
    const loopGain = rm * a0Ms; // kOhm * mS = dimensionless
    const approxInvRmMs = 1 / rm; // 1 / kOhm = mS
    const exactClosedMs = a0Ms / (1 + loopGain);
    const errPct = ((approxInvRmMs - exactClosedMs) / exactClosedMs) * 100;
    const rOutClosedK = (invGm2 + rm) * (fbActive ? (1 + loopGain) : 1);

    // Sweep gm1 from 0.5 to 5.0 mS
    const exactCurve = [];
    const approxCurve = [];
    for (let i = 0; i <= 40; i++) {
      const g = 0.5 + (4.5 * i) / 40;
      const a0 = (g * rd) / (invGm2 + rl + rm);
      const cl = a0 / (1 + rm * a0);
      exactCurve.push([Number(g.toFixed(3)), Number(cl.toFixed(4))]);
      approxCurve.push([Number(g.toFixed(3)), Number(approxInvRmMs.toFixed(4))]);
    }

    const diag = !fbActive
      ? {
          kind: 'info',
          title: '귀환 경로 OFF (개루프 동작)',
          text: `반송 경로를 끊어 $M_1$ 게이트가 접지되었습니다. 이득이 $${gmClosedMs.toFixed(2)}\\text{ mS}$로 커졌지만 $g_{m1}$ 변동에 그대로 흔들립니다.`,
        }
      : errPct > 10
        ? {
            kind: 'warn',
            title: '루프 이득 부족 (1/R_M 근사 붕괴)',
            text: `루프 이득 $KA_0 = ${loopGain.toFixed(2)}$이 충분히 크지 않아 $1/R_M = ${approxInvRmMs.toFixed(2)}\\text{ mS}$ 근사가 실제 폐루프 이득보다 $${errPct.toFixed(1)}\\%$ 큽니다.`,
          }
        : {
            kind: 'ok',
            title: '큰 루프 이득 (1/R_M 근사 성립)',
            text: `루프 이득 $KA_0 = ${loopGain.toFixed(2)}$이 커서 폐루프 이득이 $1/R_M = ${approxInvRmMs.toFixed(2)}\\text{ mS}$에 오차 $${errPct.toFixed(1)}\\%$ 이내로 수렴합니다.`,
          };

    return {
      tiles: [
        { label: '폐루프 이득', val: `${gmClosedMs.toFixed(2)} mS` },
        { label: '루프 이득 KA_0', val: `${loopGain.toFixed(2)}` },
        { label: '출력 임피던스', val: `${rOutClosedK.toFixed(2)} kΩ` },
      ],
      diagnosis: diag,
      formula: '$$\\begin{aligned}G_{m,\\text{cl}} &= \\frac{A_0}{1 + R_M A_0} \\approx \\frac{1}{R_M} \\\\ R_{\\text{out,cl}} &= (1/g_{m2}+R_M)(1+KA_0)\\end{aligned}$$',
      summary: `현재 $K = R_M = ${rm.toFixed(2)}\\text{ k}\\Omega$, $1/R_M = ${approxInvRmMs.toFixed(2)}\\text{ mS}$입니다. ${fbActive ? `$V_F = ${vFMv.toFixed(2)}\\text{ mV}$가 $M_1$ 게이트로 반송되어 출력 임피던스가 $(1+KA_0) = ${(1 + loopGain).toFixed(2)}$배 커졌습니다.` : '귀환 경로가 꺼져 있어 개루프 상태입니다.'}`,
      nodes: {
        in: { v: Number(vInMv.toFixed(1)), unit: 'mV', dir: 'up', hot: state.causalStep === 1 },
        x: { v: Number(vXMv.toFixed(1)), unit: 'mV', dir: 'up', hot: state.causalStep === 1 },
        s2: { v: Number(vS2Mv.toFixed(1)), unit: 'mV', dir: 'up', hot: state.causalStep === 2 },
        vf: { v: Number(vFMv.toFixed(2)), unit: 'mV', dir: 'up', hot: state.causalStep === 3 },
      },
      branches: {
        vx_line: { hot: state.causalStep === 1, dir: 'fwd' },
        i_out: { hot: state.causalStep === 2, dir: 'fwd' },
        fb_wire: { hot: fbActive && state.causalStep === 3, dim: !fbActive, dir: 'rev' },
      },
      elems: {
        fb_loop: { hot: fbActive && state.causalStep === 3 },
      },
      plotData: {
        title: 'g_m1 변화에 따른 폐루프 이득 vs 1/R_M 이상 근사',
        ariaLabel: 'g_m1 변화에 따른 C-V 폐루프 이득 정확 곡선과 1/R_M 근사선 비교',
        xLabel: 'g_m1 (mS)',
        yLabel: 'G_m,closed (mS)',
        xMin: 0.5,
        xMax: 5,
        yMin: 0,
        exact: exactCurve,
        approx: approxCurve,
        exactLabel: '폐루프 정확식',
        approxLabel: '1/R_M 이상 근사',
        marker: [gm1, Number(exactClosedMs.toFixed(4))],
        approxMarker: [gm1, Number(approxInvRmMs.toFixed(4))],
        errPct: Number(errPct.toFixed(1)),
        thresholdPct: 10,
      },
    };
  },
};

module.exports = spec;
