const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 326" role="img">
  <title>E12.27 감지 복제 회로</title>
  <g class="fig-ink">
    <path d="M116 70 H296 M116 70 V157 M116 193 V275 H296 M296 275 V281 M278 281 H314 M283 287 H309 M289 293 H303"/>
    <circle cx="116" cy="175" r="18"/>
    <path d="M111 168 H121 M116 163 V173 M111 182 H121"/>
  </g>
  <g data-branch="r1">
    <path class="fig-ink" d="M296 70 V86 M296 134 V170"/>
    <rect class="fig-ink sym" x="287" y="86" width="18" height="48"/>
  </g>
  <g data-branch="r2">
    <path class="fig-ink" d="M296 170 V199 M296 248 V275"/>
    <rect class="fig-ink sym" x="287" y="199" width="18" height="49"/>
  </g>
  <path class="fig-ink" d="M296 170 H409"/>
  <g data-port="sense" aria-label="감지 복제 종단 선택">
    <rect x="382" y="124" width="72" height="70" rx="6" fill="transparent" opacity="0" pointer-events="all"/>
    <text class="fig-text" x="418" y="147" text-anchor="middle">종단 선택</text>
    <path class="fig-ink" d="M409 170 H413"/>
    <g data-port-view="open">
      <circle class="fig-ink" cx="418" cy="170" r="5"/>
    </g>
    <g data-port-view="short" data-branch="strap">
      <path class="fig-ink" d="M413 170 H418 V217 M403 217 H433 M407 223 H429 M412 229 H424"/>
    </g>
  </g>
  <circle class="fig-dot" cx="296" cy="70" r="4.5" data-node-color="blue"/>
  <circle class="fig-dot" cx="296" cy="170" r="4.5" data-node-color="red"/>
  <text class="fig-text" x="296" y="50" text-anchor="middle" data-node-color="blue">v<tspan baseline-shift="sub" font-size="78%">o</tspan></text>
  <text class="fig-text" x="76" y="178" text-anchor="middle">1 V</text>
  <text class="fig-text" x="270" y="112" text-anchor="end">R<tspan baseline-shift="sub" font-size="78%">1</tspan>  12 kΩ</text>
  <text class="fig-text" x="270" y="227" text-anchor="end">R<tspan baseline-shift="sub" font-size="78%">2</tspan>  8 kΩ</text>
</svg>`;

module.exports = {
  id: 'e12-27-sense-termination',
  title: 'E12.27 감지 복제 결선',
  archetype: 'bench',
  modes: [{
    key: 'sense',
    label: '감지 복제',
    svg,
    ariaLabel: '출력에서 R1과 R2를 거쳐 접지로 가는 감지 복제와 선택할 수 있는 게이트 포트.',
  }],
  ports: [{
    id: 'sense',
    label: '원래 M₂ 게이트에 붙던 포트',
    options: [{ id: 'open', label: '개방' }, { id: 'short', label: '단락·접지' }],
    def: 'short',
    answer: 'open',
    badOption: 'short',
  }],
  predict: {
    prompt: '귀환을 끊은 뒤에도 출력에서 R₂를 지나는 전류가 흐를까요?',
    options: [
      { id: 'flows', label: '감지 포트를 개방하면 흐른다' },
      { id: 'stops', label: '감지 포트를 개방하면 멈춘다' },
    ],
    answerId: 'flows',
    explain: '감지 포트의 가지는 열려도, 출력에서 두 저항을 거쳐 접지에 이르는 가지는 이어져 있어요.',
  },
  params: [],
  steps: [
    { title: '포트 단락', text: '중간점이 접지되면 아래 저항의 양쪽 전압은 어떻게 될까요?',
      ports: { sense: 'short' } },
    { title: '포트 개방', text: '중간점의 옆 가지를 열면 두 저항의 전류는 어떻게 될까요?',
      ports: { sense: 'open' } },
  ],
  presets: [],
  mistakes: {
    sense: [
      { title: '감지 포트를 증폭기 출력과 혼동', text: '종단을 고르는 자리에는 원래 M₂ 게이트가 붙어요. 이 전압 입력을 개방으로 나타내요.' },
      { title: '포트를 열면 두 저항도 끊어진다고 생각', text: '중간점 오른쪽의 가지가 열려도 두 저항을 거쳐 접지까지 갈 수 있어요.' },
      { title: '감지 복제의 저항만으로 출력저항 계산', text: '이 실험에서 측정한 부하는 증폭기 자체의 출력저항과 병렬로 들어가요.' },
    ],
  },
  evaluate(state, mna) {
    const open = state.ports.sense === 'open';
    const result = mna.solveCircuit({ elements: [
      { id: 'test', type: 'vsrc', n1: 'out', n2: '0', value: 1 },
      { id: 'r1', type: 'R', n1: 'out', n2: 'mid', value: 12000 },
      { id: 'r2', type: 'R', n1: 'mid', n2: '0', value: 8000 },
      { id: 'strap', type: open ? 'open' : 'short', n1: 'mid', n2: '0' },
    ] });
    if (!result.ok) {
      return { diagnosis: { kind: 'bad', singular: true, text: result.reason } };
    }

    const currentR1 = result.branches.r1.re;
    const currentR2 = result.branches.r2.re;
    return {
      tiles: [
        { label: '출력에 걸리는 부하', val: `${(1 / currentR1 / 1000).toFixed(0)} kΩ` },
        { label: '위 저항 전류', val: `${Number((currentR1 * 1e6).toFixed(2))} µA` },
        { label: '아래 저항 전류', val: `${Number((currentR2 * 1e6).toFixed(2))} µA` },
      ],
      ports: { sense: { ok: open, bad: !open } },
      branches: { r1: { hot: true }, r2: { hot: open, dim: !open },
        strap: { hot: !open } },
      diagnosis: open
        ? { kind: 'ok', title: '두 저항이 직렬', text: '같은 전류가 두 저항을 지나므로 출력에 R₁ + R₂가 걸려요.' }
        : { kind: 'warn', title: '아래 저항이 우회됨', text: '중간점이 접지돼 R₂ 양단이 0 V예요. 출력에는 R₁만 걸려요.' },
      summary: '감지 복제만 떼어 낸 회로예요. 표시된 저항과 1 V는 실험용 예시값이에요.',
      formula: open
        ? { name: '해설로 돌아가기', tex: '$$R_{\\mathrm{out,open}} \\approx r_{\\mathrm{ON}}\\parallel r_{\\mathrm{OP}}\\parallel(R_1+R_2)$$' }
        : { name: '단락에서 보이는 부하', tex: '$$R_{\\mathrm{load}}=R_1$$' },
    };
  },
};
