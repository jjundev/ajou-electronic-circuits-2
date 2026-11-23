const math = String.raw;
const forwardResistance = 1000;
const inputResistance = 1000;
const outputResistance = 1000;

const ground = (x, y) => `<path class="fig-ink sym" d="M${x - 11} ${y}h22m-18 5h14m-10 5h6"/>`;

const circuit = `<svg viewBox="0 0 410 425" role="img" aria-label="전압–전류 귀환 소신호 시험 회로. 위는 전류가 분기하는 입력, 아래는 전압을 만드는 출력이에요.">
  <text class="fig-text" style="font-size:18px;font-weight:700" x="20" y="25">입력 포트 · 전류를 재요</text>
  <g data-causal-step="1,4" data-branch="test">
    <path class="fig-ink" d="M50 126V88h125 M50 168v48"/>
    <path class="fig-ink sym" d="M95 88h24m-7-5 7 5-7 5"/>
    <g class="sym">
      <circle class="fig-ink" cx="50" cy="147" r="21"/>
      <path class="fig-ink" d="M44 137h12m-6-6v12m-6 14h12"/>
    </g>
    ${ground(50, 216)}
    <text class="fig-text fig-math" style="font-size:16px" x="84" y="152">V<tspan baseline-shift="sub" font-size="78%">X</tspan></text>
    <text class="fig-text fig-math" x="99" y="68">I<tspan baseline-shift="sub" font-size="78%">X</tspan></text>
  </g>
  <g data-causal-step="2" data-branch="forward">
    <path class="fig-ink" d="M175 88v39m0 40v49"/>
    <path class="fig-ink sym" d="M175 127l-7 5 14 5-14 5 14 5-14 5 14 5-7 10"/>
    ${ground(175, 216)}
    <text class="fig-text fig-math" style="font-size:16px" x="194" y="150">R<tspan baseline-shift="sub" font-size="78%">in</tspan></text>
    <text class="fig-text fig-math" data-node="forward" x="149" y="196" text-anchor="end">I<tspan baseline-shift="sub" font-size="78%">A</tspan> ↓</text>
  </g>
  <g data-elem="feedback" aria-label="귀환 전류원 켜기 또는 끄기">
    <g data-causal-step="3" data-branch="feedback">
      <path class="fig-ink" d="M175 88h126 M301 88v37m0 44v47"/>
      <path class="fig-ink sym" d="M301 125l20 22-20 22-20-22z M301 136v22m-5-6 5 6 5-6"/>
      ${ground(301, 216)}
      <text class="fig-text fig-math" style="font-size:16px" x="334" y="150">KV<tspan baseline-shift="sub" font-size="78%">out</tspan></text>
      <text class="fig-text fig-math" data-node="feedback" x="275" y="196" text-anchor="end">I<tspan baseline-shift="sub" font-size="78%">F</tspan> ↓</text>
    </g>
  </g>
  <circle class="fig-dot" data-node="input" data-node-color="blue" cx="175" cy="88" r="4"/>
  <text class="fig-text fig-math" data-node-color="blue" x="159" y="68">V<tspan baseline-shift="sub" font-size="78%">X</tspan></text>
  <text class="fig-text" style="font-size:18px;font-weight:700" x="20" y="263">출력 포트 · 전압을 감지해요</text>
  <g data-causal-step="2" data-branch="output">
    <path class="fig-ink" d="M75 337v-28h226v28 M75 381v19m226-19v19"/>
    <path class="fig-ink sym" d="M75 337l20 22-20 22-20-22z M75 370v-22m-5 6 5-6 5 6 M301 337l-7 5 14 5-14 5 14 5-14 5 14 5-7 14"/>
    ${ground(75, 400)}
    ${ground(301, 400)}
    <text class="fig-text fig-math" style="font-size:16px" x="109" y="364">I<tspan baseline-shift="sub" font-size="78%">A</tspan></text>
    <text class="fig-text fig-math" style="font-size:16px" x="324" y="364">R<tspan baseline-shift="sub" font-size="78%">o</tspan></text>
  </g>
  <circle class="fig-dot" data-node="output" data-node-color="red" cx="301" cy="309" r="4"/>
  <text class="fig-text fig-math" data-node-color="red" x="316" y="311">V<tspan baseline-shift="sub" font-size="78%">out</tspan></text>
  <g data-badges>
    <g data-badge-for="input" transform="translate(50 61)"/>
    <g data-badge-for="forward" transform="translate(222 58)"/>
    <g data-badge-for="feedback" transform="translate(321 58)"/>
    <g data-badge-for="output" transform="translate(182 285)"/>
  </g>
</svg>`;

const spec = {
  id: '1118-vc-input-current',
  title: '전압–전류 귀환과 입력저항',
  archetype: 'probe',
  modes: [{ key: 'input', label: '입력저항 측정', svg: circuit, ariaLabel: '전압–전류 귀환의 입력 전류 분기와 출력 포트' }],
  predict: {
    prompt: math`시험 전압이 같은데 귀환 가지가 전류를 더 가져가면, 시험원이 보는 입력저항은 어떻게 될까요?`,
    options: [
      { id: 'lower', label: '작아져요' },
      { id: 'higher', label: '커져요' },
    ],
    answerId: 'lower',
    explain: math`분자 $V_X$가 일정하고 분모 $I_X$가 커지므로 $V_X/I_X$는 작아져요.`,
  },
  params: [
    { key: 'voltage', label: '시험 전압', min: 0.1, max: 1, step: 0.1, def: 1, unit: 'V' },
    { key: 'feedback', label: '귀환율 K', min: 0, max: 9, step: 0.25, def: 1, unit: 'mS' },
  ],
  elems: [{ id: 'feedback', label: '귀환 전류원' }],
  causalSteps: [
    { id: 1, label: '시험 전압 +Δv', detail: '시험원이 입력 노드의 전압을 정해요.' },
    { id: 2, label: '순방향 전류 → 출력 전압', detail: '순방향 가지 전류가 늘면 출력 전압이 함께 높아져요.' },
    { id: 3, label: '출력 → 귀환 전류', detail: '귀환 전류원이 출력 전압을 읽고 입력 노드에서 전류를 빼요.' },
    { id: 4, label: '시험원 전체 전류', detail: '시험원이 두 가지 전류를 모두 공급해요.' },
  ],
  presets: [
    { id: 'off', label: '귀환 전류원 끄기', params: { voltage: 1, feedback: 1 }, disabledElems: ['feedback'] },
    { id: 'double', label: '시험 전류 두 배', params: { voltage: 1, feedback: 1 }, disabledElems: [] },
    { id: 'ten', label: '부귀환 T = 9', params: { voltage: 1, feedback: 9 }, disabledElems: [] },
  ],
  steps: [
    { title: '귀환을 끈 상태', text: '1 V를 걸어요. 시험원은 순방향 가지에만 전류를 공급해요.', params: { voltage: 1, feedback: 1 }, disabledElems: ['feedback'] },
    { title: '가지 전류 두 개를 더하기', text: '같은 1 V에서 귀환을 켜고, 두 가지와 시험원 전류를 비교해요.', params: { voltage: 1, feedback: 1 }, disabledElems: [], causalStep: 4 },
    { title: '시험 전압을 바꾸기', text: '전압과 전류가 함께 줄어드는 동안 V/I가 어떻게 되는지 확인해요.', params: { voltage: 0.5, feedback: 1 }, disabledElems: [] },
  ],
  toggles: [['labels', '전압·전류 배지', true]],
  mistakes: {
    input: [
      { title: '순방향 전류만으로 나누기', text: math`시험원이 보낸 전류는 $I_A + I_F$예요. 입력저항을 구할 때는 이 합으로 나눠요.` },
      { title: '시험 중 출력이 떨어진다고 생각하기', text: math`이 시험에서는 이상적인 시험원이 $V_X$를 유지해요. 같은 $V_X$에서 귀환율을 키우면 시험 전류가 늘어요.` },
      { title: '시험 전압이 커지면 저항도 커진다고 생각하기', text: math`선형 모델에서 두 가지 전류와 $V_X$가 같은 비율로 변해요. $V_X/I_X$는 그대로예요.` },
    ],
  },
  evaluate(state, mna) {
    const enabled = !state.disabledElems.includes('feedback');
    const k = enabled ? state.params.feedback / 1000 : 0;
    const solved = mna.solveCircuit({
      elements: [
        { id: 'test', type: 'vsrc', n1: 'input', n2: '0', value: state.params.voltage },
        { id: 'input', type: 'R', n1: 'input', n2: '0', value: inputResistance },
        { id: 'forward', type: 'vccs', n1: '0', n2: 'output', cp: 'input', cn: '0', gm: forwardResistance / (inputResistance * outputResistance) },
        { id: 'output', type: 'R', n1: 'output', n2: '0', value: outputResistance },
        { id: 'feedback', type: 'vccs', n1: 'input', n2: '0', cp: 'output', cn: '0', gm: k },
      ],
    });
    if (!solved.ok) throw new Error(solved.reason);

    const v = solved.nodes.input.re;
    const out = solved.nodes.output.re;
    const testMa = -solved.branches.test.re * 1000;
    const forwardMa = solved.branches.input.re * 1000;
    const feedbackMa = solved.branches.feedback.re * 1000;
    const resistance = v / (testMa / 1000);
    const loop = k * forwardResistance;
    const stage = state.causalStep;
    const ma = value => `${value.toFixed(2)} mA`;
    const voltage = value => `${value.toFixed(2)} V`;
    const summaries = [
      `시험 전류 ${ma(testMa)}는 순방향 ${ma(forwardMa)}와 귀환 ${ma(feedbackMa)}의 합이에요.`,
      '시험원이 입력 전압을 0.10 V 높였다고 가정해요. 파란 강조는 변화가 전달되는 순서를 보여줘요.',
      '순방향 가지 전류는 0.10 mA 늘고, 출력 전압은 0.10 V 높아져요.',
      `출력 변화로 귀환 전류가 ${ma(loop * 0.1)} 늘어요.`,
      `시험원은 증가분 ${ma(0.1)}와 ${ma(loop * 0.1)}를 합쳐 ${ma((1 + loop) * 0.1)}를 더 공급해요.`,
    ];

    return {
      tiles: [
        { label: '시험 전류', val: ma(testMa) },
        { label: '귀환 전류', val: ma(feedbackMa) },
        { label: '입력저항', val: `${Number(resistance.toFixed(1))} Ω` },
      ],
      diagnosis: loop > 0
        ? { kind: 'ok', title: `루프 이득 T = ${loop.toFixed(2)}`, text: '같은 시험 전압에서 귀환 가지가 전류를 더 가져가요.' }
        : { kind: 'info', title: '귀환 전류 없음', text: '시험원의 전류가 모두 순방향 입력저항을 흘러요.' },
      equations: [
        { name: '입력 노드', tex: math`$$I_X=I_A+I_F,\quad I_A=\frac{V_X}{R_{\mathrm{in}}}$$` },
        { name: '시험원에서 본 저항', tex: math`$$R_{\mathrm{in,cl}}=\frac{V_X}{I_X}=\frac{R_{\mathrm{in}}}{1+KR_0}$$` },
        { name: '소신호 예시 모델 (교과서 보충)', tex: math`$$V_{\mathrm{out}}=R_0 I_A,\quad I_F=KV_{\mathrm{out}}$$` },
      ],
      summary: summaries[stage] || summaries[0],
      nodes: {
        input: { v, badge: voltage(v) },
        forward: { badge: ma(forwardMa) },
        feedback: { badge: ma(feedbackMa) },
        output: { v: out, badge: voltage(out) },
      },
      branches: {
        test: { hot: stage === 1 || stage === 4 },
        forward: { hot: stage === 2 },
        output: { hot: stage === 2 },
        feedback: { hot: stage === 3 && loop > 0, dim: loop === 0 },
      },
    };
  },
};

module.exports = spec;
