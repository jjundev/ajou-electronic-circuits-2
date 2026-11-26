const ground = (x, y) => `<g class="sym"><path class="fig-ink" d="M${x - 10} ${y}h20 m-16 5h12 m-9 5h6"/></g>`;
const resistor = (x, y) => `<g class="sym"><path class="fig-ink" d="M${x} ${y}v5l-6 4 12 7-12 7 12 7-6 4v5"/></g>`;

function circuit(mos) {
  const returnPath = mos ? `
    <path class="fig-ink" d="M286 76v28m0 39v42M188 76v28m0 39v42"/>
    ${resistor(188, 104)}
    <g class="sym"><path class="fig-ink" d="M286 104l19 19-19 20-19-20Z M286 113v19m-4-5 4 5 4-5"/></g>
    <text class="fig-text fig-math" x="207" y="150">r<tspan baseline-shift="sub" font-size="78%">o</tspan></text>
    <text class="fig-text fig-math" x="256" y="128" text-anchor="end">g<tspan baseline-shift="sub" font-size="78%">m</tspan>v<tspan baseline-shift="sub" font-size="78%">gs</tspan></text>
    <circle class="fig-dot" cx="188" cy="76" r="3"/>
    ${ground(188, 185)}${ground(286, 185)}
    <text class="fig-muted" x="237" y="224" text-anchor="middle">MOS 소신호 반송</text>
  ` : `
    <path class="fig-ink" d="M238 76v28m0 39v7m0 34v1"/>
    ${resistor(238, 104)}
    <text class="fig-text fig-math" x="260" y="129">R<tspan baseline-shift="sub" font-size="78%">F</tspan></text>
    <g class="sym"><circle class="fig-ink" cx="238" cy="167" r="17"/><path class="fig-ink" d="M232 160h12m-6-5v10m-6 10h12"/></g>
    ${ground(238, 185)}
    <text class="fig-muted" x="268" y="172">반송 전압원</text>
    <text class="fig-muted" x="237" y="224" text-anchor="middle">저항 반송</text>
  `;
  const tap = mos ? 286 : 238;
  return `<svg viewBox="0 0 400 248" role="img">
    <g data-causal-step="1">
      <path class="fig-ink" d="M56 76v38m0 34v37M56 76h75"/>
      <g class="sym"><circle class="fig-ink" cx="56" cy="131" r="17"/><path class="fig-ink" d="M50 124h12m-6-5v10m-6 10h12"/></g>
      ${ground(56, 185)}
      <text class="fig-muted" x="56" y="224" text-anchor="middle">시험 전압원</text>
      <circle class="fig-dot" data-node="n" data-node-color="blue" cx="131" cy="76" r="4"/>
      <text class="fig-text fig-math" data-node-color="blue" x="131" y="56" text-anchor="middle">v<tspan baseline-shift="sub" font-size="78%">n</tspan></text>
    </g>
    <g data-causal-step="2">
      <path class="fig-ink" d="M131 76h${tap - 131}" data-branch="return"/>
      <g class="sym"><path class="fig-ink" d="M145 107v19m-4-5 4 5 4-5"/></g>
      <text class="fig-text fig-math" x="134" y="121" text-anchor="end">i<tspan baseline-shift="sub" font-size="78%">F</tspan></text>
      ${returnPath}
    </g>
    <g data-causal-step="3">
      <path class="fig-ink" d="M${tap} 76h${356 - tap}v28m0 39v42" data-branch="input"/>
      <circle class="fig-dot" cx="${tap}" cy="76" r="3"/>
      ${resistor(356, 104)}${ground(356, 185)}
      <text class="fig-text fig-math" x="374" y="127">i<tspan baseline-shift="sub" font-size="78%">e</tspan></text>
      <text class="fig-muted" x="356" y="224" text-anchor="middle">증폭기 입력</text>
    </g>
    <g data-badges><g data-badge-for="n" transform="translate(131,24)"/></g>
  </svg>`;
}

const mistakes = [
  { title: '반송과 증폭기 입력은 직렬이다?', text: '같은 입력 노드에서 두 전류가 갈라져 $i_{test}=i_F+i_e$를 만족합니다.' },
  { title: '반송 신호가 고정되면 반송 전류도 고정된다?', text: '노드 전압이 바뀌면 유한한 반송 저항을 지나가는 전류도 달라집니다.' },
  { title: '반송 저항이 작을수록 전류원에 가깝다?', text: '같은 전압 변화에서 반송 전류의 변화는 저항에 반비례합니다.' },
];
const tex = String.raw;

module.exports = {
  id: 'ec2-1113-current-return',
  title: '반송 저항이 전류에 미치는 영향',
  archetype: 'probe',
  modes: [
    { key: 'mos', label: 'MOS 반송', svg: circuit(true), ariaLabel: '시험 전압원과 MOS 소신호 모델 및 증폭기 입력을 병렬로 연결한 회로' },
    { key: 'resistor', label: '저항 반송', svg: circuit(false), ariaLabel: '시험 전압원과 저항 반송 가지 및 증폭기 입력을 병렬로 연결한 회로' },
  ],
  predict: {
    mode: 'mos',
    prompt: '게이트 신호를 고정하고 입력 노드를 0 mV에서 10 mV로 올리면, 반송 전류는 어떻게 될까요? (rₒ = 1 kΩ)',
    options: [{ id: 'same', label: '그대로다' }, { id: 'up', label: '10 µA 늘어난다' }, { id: 'down', label: '10 µA 줄어든다' }],
    answerId: 'up',
    explain: '게이트가 정한 9 µA에, 노드 전압이 rₒ에 만드는 10 µA가 더해집니다.',
    check: { before: { params: { vn: 0, resistance: 1 } }, after: { params: { vn: 10, resistance: 1 }, causalStep: 2 }, tiles: ['returned', 'deviation'] },
  },
  params: [
    { key: 'vn', label: '입력 노드 시험 전압', min: 0, max: 30, step: 1, def: 0, unit: 'mV' },
    { key: 'resistance', label: 'MOS 출력 저항 rₒ', mode: 'mos', min: 1, max: 1000, def: 100, scale: 'log', unit: 'kΩ' },
    { key: 'resistance', label: '반송 저항 RF', mode: 'resistor', min: 1, max: 1000, def: 100, scale: 'log', unit: 'kΩ' },
  ],
  presets: [
    { id: 'nominal', label: '기준점 · 0 mV', params: { vn: 0, resistance: 100 }, causalStep: 1 },
    { id: 'sensitive', label: '10 mV · 1 kΩ', params: { vn: 10, resistance: 1 }, causalStep: 2 },
    { id: 'stiff', label: '10 mV · 1 MΩ', params: { vn: 10, resistance: 1000 }, causalStep: 2 },
  ],
  steps: [
    { title: '시험 전압 걸기', text: '입력 전류원 자리에 전압원을 달아 입력 노드 전압을 직접 지정해요.', params: { vn: 10 }, causalStep: 1 },
    { title: '반송 전류 읽기', text: '반송 신호를 고정하고 입력 노드 전압에 의한 변화량을 읽어요.', causalStep: 2 },
    { title: '증폭기 입력과 합하기', text: '시험 전류는 반송 가지와 증폭기 입력으로 갈라져요.', causalStep: 3 },
  ],
  causalSteps: [
    { id: 1, label: '입력 노드 전압', detail: '시험 전압원이 노드 전압을 고정합니다.' },
    { id: 2, label: '반송 가지', detail: '노드 전압이 만드는 추가 전류가 반송 가지에 흐릅니다.' },
    { id: 3, label: '증폭기 입력과 합산', detail: '반송 전류와 증폭기 입력 전류를 합하면 시험 전압원이 공급한 전류입니다.' },
  ],
  toggles: [['labels', '노드 배지', true]],
  mistakes: { mos: mistakes, resistor: mistakes },
  evaluate(state, mna) {
    const mos = state.mode === 'mos';
    const resistance = state.params.resistance * 1000;
    const nominal = 9e-6;
    const elements = [
      { id: 'test', type: 'vsrc', n1: 'n', n2: '0', value: state.params.vn * 1e-3 },
      { id: 'input', type: 'R', n1: 'n', n2: '0', value: 1000 },
      { id: 'return', type: 'R', n1: 'n', n2: mos ? '0' : 'ref', value: resistance },
      ...(mos ? [
        { id: 'gate', type: 'vsrc', n1: 'gate', n2: '0', value: 9e-3 },
        { id: 'gm', type: 'vccs', n1: 'n', n2: '0', cp: 'gate', cn: '0', gm: 1e-3 },
      ] : [
        { id: 'ref', type: 'vsrc', n1: 'ref', n2: '0', value: -nominal * resistance },
      ]),
    ];
    const solved = mna.solveCircuit({ elements });
    if (!solved.ok) throw new Error(solved.reason);
    const returned = solved.branches.return.re + (mos ? solved.branches.gm.re : 0);
    const deviation = returned - nominal;
    const input = solved.branches.input.re;
    const test = -solved.branches.test.re;
    const micro = (i) => `${(Math.abs(i) < 5e-9 ? 0 : i * 1e6).toFixed(2)} µA`;
    const nodeMv = Math.round(solved.nodes.n.re * 1000);

    return {
      tiles: [
        { id: 'returned', label: '반송 전류', val: micro(returned) },
        { id: 'deviation', label: '반송 전류 변화', val: micro(deviation) },
        { id: 'input', label: '증폭기 입력 전류', val: micro(input) },
      ],
      nodes: { n: { v: nodeMv, unit: 'mV', hot: state.causalStep === 1 } },
      branches: { return: { hot: state.causalStep === 2 }, input: { hot: state.causalStep === 3 } },
      diagnosis: {
        kind: deviation > nominal * 0.1 ? 'warn' : 'ok',
        title: '기준 반송 전류 9 µA',
        text: mos
          ? tex`게이트 소신호 9 mV와 $g_m=1\,\mathrm{mS}$를 고정합니다. 증폭기 입력은 1 kΩ으로 모델링합니다.`
          : tex`$R_F$를 바꾸면 기준 반송 전류가 같도록 반송 전압원의 전압을 다시 설정합니다. 각 저항에서 노드 전압을 바꿀 때는 그 전압을 고정합니다. 증폭기 입력은 1 kΩ입니다.`,
      },
      formula: mos
        ? tex`$$i_F = g_m v_{gs} + v_n/r_o$$`
        : tex`$$i_F = (v_n-v_{\mathrm{ref}})/R_F$$`,
      summary: `시험 전압원이 공급하는 ${micro(test)}는 반송 가지의 ${micro(returned)}와 증폭기 입력의 ${micro(input)}로 나뉩니다. 반송 전류 변화는 입력 노드를 0 mV로 놓았을 때와 비교한 값입니다.`,
    };
  },
};
