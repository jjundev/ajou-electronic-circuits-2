const math = String.raw;
const dividerResistance = 1000;
const sourceVoltage = 1;
const idealPorts = { sense: 'open', return: 'short' };
const finitePorts = { sense: 'rated', return: 'rated' };
const swappedPorts = { sense: 'short', return: 'open' };

const gnd = (x, y) => `<path class="fig-ink sym" d="M${x - 10} ${y}h20m-16 5h12m-8 5h4"/>`;
const verticalResistor = (x, y) => `<path class="fig-ink sym" d="M${x} ${y}l-7 5 14 5-14 5 14 5-14 5 14 5-7 10"/>`;
const horizontalResistor = (x, y) => `<path class="fig-ink sym" d="M${x} ${y}l5-7 5 14 5-14 5 14 5-14 5 14 10-7"/>`;
const oneVoltSource = (x, y) => `<g class="sym">
  <circle class="fig-ink" cx="${x}" cy="${y}" r="19"/>
  <path class="fig-ink" d="M${x - 5} ${y - 7}h10m-5-5v10m-5 10h10"/>
</g>`;

function termination(id, x, y, label) {
  return `<g data-port="${id}" aria-label="${label}">
    <path class="fig-ink" d="M${x} ${y}v22"/>
    <circle class="fig-ink sym" cx="${x}" cy="${y + 25}" r="3"/>
    <g data-port-view="open" display="none"/>
    <g data-port-view="short" display="none">
      <path class="fig-ink" d="M${x} ${y + 28}v71"/>
      ${gnd(x, y + 99)}
    </g>
    <g data-port-view="rated" display="none">
      <path class="fig-ink" d="M${x} ${y + 28}v15m0 40v16"/>
      ${verticalResistor(x, y + 43)}
      ${gnd(x, y + 99)}
    </g>
    <g class="port-chip">
      <rect class="port-chip-bg" x="${x - 39}" y="${y + 115}" width="78" height="68" rx="8"/>
      <text class="port-chip" style="font-size:15px" x="${x}" y="${y + 155}" text-anchor="middle"></text>
    </g>
  </g>`;
}

const circuit = `<svg viewBox="0 0 410 535" role="img" aria-label="분압기를 두 벌 복제해 감지 복제본의 자유 출력과 반송 복제본의 자유 입력을 각각 종단하는 회로예요.">
  <text class="fig-text" style="font-size:18px;font-weight:700" x="20" y="29">감지 복제본 · 순방향 출력에 연결</text>
  <path class="fig-ink" d="M45 112V78h64m40 0h46m0 0h24m40 0h17m0 0h85 M45 150v34 M276 78v36m0 40v30"/>
  ${oneVoltSource(45, 131)}
  ${horizontalResistor(109, 78)}
  ${horizontalResistor(219, 78)}
  ${verticalResistor(276, 114)}
  ${gnd(45, 184)}
  ${gnd(276, 184)}
  ${termination('sense', 361, 78, '감지 복제본의 자유 출력 종단')}
  <text class="fig-text fig-math" style="font-size:15px" x="128" y="60" text-anchor="middle">R<tspan baseline-shift="sub" font-size="78%">o</tspan></text>
  <text class="fig-text fig-math" style="font-size:15px" x="239" y="109" text-anchor="middle">R<tspan baseline-shift="sub" font-size="78%">1</tspan></text>
  <text class="fig-text fig-math" style="font-size:15px" x="253" y="139" text-anchor="end">R<tspan baseline-shift="sub" font-size="78%">2</tspan></text>
  <text class="fig-text" x="78" y="135">내부 1 V</text>
  <circle class="fig-dot" data-node="output" data-node-color="blue" cx="195" cy="78" r="4"/>
  <text class="fig-text fig-math" data-node-color="blue" x="194" y="109" text-anchor="middle">V<tspan baseline-shift="sub" font-size="78%">out</tspan></text>
  <circle class="fig-dot" cx="276" cy="78" r="4"/>
  <text class="fig-text" x="361" y="58" text-anchor="middle">자유 출력</text>

  <text class="fig-text" style="font-size:18px;font-weight:700" x="20" y="283">반송 복제본 · 순방향 입력에 연결</text>
  <path class="fig-ink" d="M49 335h64m40 0h68m0 0h144v34 M221 335v36m0 40v30 M365 407v34"/>
  ${horizontalResistor(113, 335)}
  ${verticalResistor(221, 371)}
  ${oneVoltSource(365, 388)}
  ${gnd(221, 441)}
  ${gnd(365, 441)}
  ${termination('return', 49, 335, '반송 복제본의 자유 입력 종단')}
  <text class="fig-text" x="49" y="316" text-anchor="middle">자유 입력</text>
  <text class="fig-text fig-math" style="font-size:15px" x="133" y="316" text-anchor="middle">R<tspan baseline-shift="sub" font-size="78%">1</tspan></text>
  <text class="fig-text fig-math" style="font-size:15px" x="245" y="396">R<tspan baseline-shift="sub" font-size="78%">2</tspan></text>
  <text class="fig-text" x="335" y="392" text-anchor="end">시험원 1 V</text>
  <circle class="fig-dot" cx="221" cy="335" r="4"/>
  <text class="fig-muted" x="205" y="525" text-anchor="middle">두 복제본 모두 R₁ = R₂ = 1 kΩ인 예시예요.</text>
  <g data-badges>
    <g data-badge-for="output" transform="translate(203 54)"/>
  </g>
</svg>`;

const spec = {
  id: '1118-vv-termination',
  title: 'V–V 귀환망 종단 조립',
  archetype: 'bench',
  modes: [{ key: 'termination', label: '종단 조립', svg: circuit, ariaLabel: 'V–V 귀환망의 감지와 반송 복제본' }],
  predict: {
    prompt: '감지 복제본의 자유 출력이 원래 이상적인 전압 입력을 봤다면, 어떤 종단을 달까요?',
    options: [
      { id: 'open', label: '개방해요' },
      { id: 'short', label: '접지해요' },
    ],
    answerId: 'open',
    explain: '이상적인 전압 입력은 전류를 받지 않아요. 그 포트가 보던 무한대 저항을 개방으로 나타내요.',
  },
  params: [
    { key: 'rin', label: '원래 전압 입력 저항', min: 1, max: 100, step: 1, def: 100, unit: 'kΩ' },
    { key: 'rout', label: '원래 전압 출력 저항', min: 10, max: 1000, step: 10, def: 100, unit: 'Ω' },
  ],
  ports: [
    {
      id: 'sense', label: '감지 복제본의 자유 출력', def: 'open', answer: 'open', badOption: 'short',
      options: [
        { id: 'open', label: '개방', shortLabel: '개방' },
        { id: 'short', label: '접지', shortLabel: '접지' },
        { id: 'rated', label: '원래 입력저항', shortLabel: '입력저항' },
      ],
    },
    {
      id: 'return', label: '반송 복제본의 자유 입력', def: 'short', answer: 'short', badOption: 'open',
      options: [
        { id: 'open', label: '개방', shortLabel: '개방' },
        { id: 'short', label: '접지', shortLabel: '접지' },
        { id: 'rated', label: '원래 출력저항', shortLabel: '출력저항' },
      ],
    },
  ],
  presets: [
    { id: 'ideal', label: '이상 종단 조립', ports: idealPorts, params: { rin: 100, rout: 100 } },
    { id: 'finite', label: '원래 저항으로 종단', ports: finitePorts, params: { rin: 100, rout: 100 } },
    { id: 'swapped', label: '개방·접지 뒤바꾸기', ports: swappedPorts, params: { rin: 100, rout: 100 } },
  ],
  steps: [
    { title: '감지 복제본의 자유 출력', text: '개방에서 접지로 바꿔 분압기의 아래쪽 저항이 우회되는 모습을 확인해요.', ports: idealPorts },
    { title: '반송 복제본의 자유 입력', text: '접지에서 개방으로 바꿔 시험원 전류가 어느 저항으로만 흐르는지 확인해요.', ports: idealPorts },
    { title: '유한 저항이 종단에 들어갈 때', text: '원래 입력저항을 1 kΩ까지 낮추고 감지 부하가 얼마나 달라지는지 보세요.', ports: finitePorts, params: { rin: 100, rout: 100 } },
  ],
  toggles: [['labels', '출력 전압 배지', true]],
  mistakes: {
    termination: [
      { title: '두 포트를 같은 방식으로 열기', text: '자유 포트가 원래 보던 임피던스가 달라요. 감지 출력은 전압 입력을 보고, 반송 입력은 전압 출력을 봐요.' },
      { title: '감지 출력을 열면 감지 부하도 사라진다고 생각하기', text: math`자유 출력이 열려 있어도 순방향 출력은 분압기의 $R_1+R_2$ 경로에 전류를 공급해요.` },
      { title: '항상 이상 종단과 같은 값이 나온다고 생각하기', text: '원래 포트 저항이 분압기 저항과 비슷하면 개방·접지 근사의 차이가 커져요.' },
    ],
  },
  evaluate(state, mna) {
    const rin = state.params.rin * 1000;
    const rout = state.params.rout;
    const sense = state.ports.sense;
    const returned = state.ports.return;
    function load(id, setting, n1, value) {
      if (setting === 'rated') return { id, type: 'R', n1, n2: '0', value };
      return { id, type: setting, n1, n2: '0' };
    }

    const solved = mna.solveCircuit({
      elements: [
        { id: 'drive', type: 'vsrc', n1: 'drive', n2: '0', value: sourceVoltage },
        { id: 'ro', type: 'R', n1: 'drive', n2: 'output', value: rout },
        { id: 'senseR1', type: 'R', n1: 'output', n2: 'senseFree', value: dividerResistance },
        { id: 'senseR2', type: 'R', n1: 'senseFree', n2: '0', value: dividerResistance },
        load('senseTerm', sense, 'senseFree', rin),
        { id: 'test', type: 'vsrc', n1: 'returnOutput', n2: '0', value: sourceVoltage },
        { id: 'returnR1', type: 'R', n1: 'returnFree', n2: 'returnOutput', value: dividerResistance },
        { id: 'returnR2', type: 'R', n1: 'returnOutput', n2: '0', value: dividerResistance },
        load('returnTerm', returned, 'returnFree', rout),
      ],
    });
    if (!solved.ok) throw new Error(solved.reason);

    const output = solved.nodes.output.re;
    const senseLoad = output / solved.branches.senseR1.re;
    const returnLoad = sourceVoltage / -solved.branches.test.re;
    const incorrectSense = sense === 'short';
    const incorrectReturn = returned === 'open';
    const incorrect = incorrectSense || incorrectReturn;
    const senseSummary = {
      open: '감지 쪽 출력 부하는 R₁과 R₂의 직렬 합이에요.',
      short: '감지 쪽 R₂의 양단이 접지되어 R₁만 출력 부하로 남아요.',
      rated: '감지 쪽 원래 입력저항이 R₂와 병렬로 걸려요.',
    };
    const returnSummary = {
      open: '반송 쪽 시험 전류는 R₂만 흘러요.',
      short: '반송 쪽 시험 전류는 R₁과 R₂에 나뉘어 흘러요.',
      rated: '반송 쪽 원래 출력저항이 R₁에 직렬로 더해져요.',
    };
    const kohm = ohm => `${(ohm / 1000).toFixed(3)} kΩ`;
    const vout = `${output.toFixed(3)} V`;

    return {
      tiles: [
        { label: '감지 쪽 출력 부하', val: kohm(senseLoad) },
        { label: '반송 쪽 입력 부하', val: kohm(returnLoad) },
        { label: '부하를 단 출력', val: vout },
      ],
      diagnosis: incorrect
        ? { kind: 'bad', title: 'V–V의 표준 종단과 달라요', text: [
          incorrectSense && '감지 복제본의 자유 출력은 원래 전압 입력을 봐요.',
          incorrectReturn && '반송 복제본의 자유 입력은 원래 전압 출력을 봐요.',
        ].filter(Boolean).join(' ') }
        : { kind: 'ok', title: sense === 'open' && returned === 'short' ? '이상 종단 조립' : '유한 저항을 포함한 종단', text: '두 분압기가 각각 입력 쪽과 출력 쪽에 부하를 남겨요.' },
      equations: [
        { name: '감지 복제본의 부하', tex: math`$$R_{\mathrm{S}}=R_1+(R_2\parallel R_{\mathrm{T,S}})$$` },
        { name: '반송 복제본의 부하', tex: math`$$R_{\mathrm{R}}=R_2\parallel(R_1+R_{\mathrm{T,R}})$$` },
        { name: '분압기 예시의 출력 로딩 (교과서 보충)', tex: math`$$V_{\mathrm{out}}=1\,\mathrm{V}\cdot\frac{R_{\mathrm S}}{R_o+R_{\mathrm S}}$$` },
      ],
      summary: `${senseSummary[sense]} ${returnSummary[returned]}`,
      nodes: { output: { v: output, badge: vout } },
      ports: {
        sense: { bad: incorrectSense, ok: !incorrectSense },
        return: { bad: incorrectReturn, ok: !incorrectReturn },
      },
    };
  },
};

module.exports = spec;
