const svg = `<svg viewBox="0 0 440 254" role="img" aria-label="1 V 출력 등가원, 1 kΩ 출력 저항과 부하, 위치를 바꿀 수 있는 감지 저항">
  <path class="fig-ink" d="M38 131V84h58m52 0h37M38 165v50h347v-40m0-44V84h-82"/>
  <g class="sym">
    <circle class="fig-ink" cx="38" cy="148" r="17"/>
    <path class="fig-ink" d="M33 141h10m-5-5v10m-5 10h10M96 84h5l5-7 7 14 7-14 7 14 7-14 7 14 4-7h3M385 131v5l-7 5 14 6-14 6 14 6-14 6 7 5v5"/>
    <path class="fig-ink" d="M208 215v13m-10 0h20m-16 5h12m-9 5h6"/>
  </g>
  <text class="fig-text fig-math" x="67" y="153">1 V</text>
  <text class="fig-text fig-math" x="122" y="62" text-anchor="middle">1 kΩ</text>
  <text class="fig-text fig-math" x="362" y="154" text-anchor="end">부하 1 kΩ</text>
  <circle class="fig-dot" data-node="load" data-node-color="red" cx="385" cy="84" r="4"/>
  <text class="fig-text fig-math" data-node="load" data-node-color="red" x="385" y="61" text-anchor="middle">v<tspan baseline-shift="sub" font-size="78%">L</tspan></text>
  <g data-port="sense">
    <g class="port-chip">
      <rect class="port-chip-bg" x="179" y="12" width="130" height="34" rx="8"/>
      <text class="port-chip" x="244" y="34" text-anchor="middle">기준 결선</text>
    </g>
    <g data-port-view="ref">
      <path class="fig-ink" d="M185 84h118"/>
    </g>
    <g data-port-view="parallel">
      <path class="fig-ink" d="M185 84h118"/>
      <path class="fig-accent" d="M242 84v47m0 46v38"/>
      <g class="sym">
        <path class="fig-accent" d="M242 131v5l-7 5 14 6-14 6 14 6-14 6 7 6v6"/>
      </g>
      <circle class="fig-dot" cx="242" cy="84" r="3.5"/>
      <circle class="fig-dot" cx="242" cy="215" r="3.5"/>
      <text class="fig-text fig-math" x="222" y="157" text-anchor="end">R<tspan baseline-shift="sub" font-size="78%">S</tspan></text>
    </g>
    <g data-port-view="series">
      <path class="fig-accent" d="M185 84h31m56 0h31"/>
      <g class="sym">
        <path class="fig-accent" d="M216 84h5l5-7 7 14 7-14 7 14 7-14 7 14 5-7h6"/>
      </g>
      <text class="fig-text fig-math" x="244" y="116" text-anchor="middle">R<tspan baseline-shift="sub" font-size="78%">S</tspan></text>
    </g>
    <g data-port-view="open">
      <path class="fig-danger" d="M185 84h36m46 0h36"/>
      <circle class="fig-dot" cx="221" cy="84" r="3.5"/>
      <circle class="fig-dot" cx="267" cy="84" r="3.5"/>
    </g>
  </g>
  <g data-badges>
    <g data-badge-for="load" transform="translate(385 30)"></g>
  </g>
</svg>`;

const options = [
  { id: 'ref', label: '기준 결선 · 감지기 없음', shortLabel: '기준 결선' },
  { id: 'parallel', label: '부하와 병렬로 연결', shortLabel: '병렬 연결' },
  { id: 'series', label: '부하와 직렬로 연결', shortLabel: '직렬 연결' },
  { id: 'open', label: '출력 경로 열기', shortLabel: '경로 개방' },
];

module.exports = {
  id: 'ec2-1111-output-sensing',
  title: '출력 전압과 전류 감지',
  archetype: 'bench',
  modes: [
    {
      key: 'voltage', label: '전압 감지', ariaLabel: '출력 등가 회로의 전압 감지기 연결', svg,
      ports: [{ id: 'sense', label: '전압 감지기 연결', options, def: 'ref', answer: 'parallel', badOption: 'series' }],
      presets: [{ id: 'voltmeter', label: '높은 저항의 전압계', params: { r: 100 }, ports: { sense: 'parallel' } }],
    },
    {
      key: 'current', label: '전류 감지', ariaLabel: '출력 등가 회로의 전류 감지기 연결', svg,
      ports: [{ id: 'sense', label: '전류 감지기 연결', options, def: 'ref', answer: 'series', badOption: 'parallel' }],
      presets: [{ id: 'ammeter', label: '낮은 저항의 전류계', params: { r: 0.01 }, ports: { sense: 'series' } }],
    },
  ],
  params: [{ key: 'r', label: '감지기 저항', min: 0.01, max: 100, scale: 'log', def: 1, unit: 'kΩ' }],
  predict: {
    mode: 'voltage',
    prompt: '전압 감지기를 부하에 병렬로 달아요. 감지기 저항을 1 kΩ에서 100 kΩ으로 올리면, 부하 전압은 연결 전의 0.500 V에 더 가까워질까요?',
    options: [{ id: 'closer', label: '가까워져요' }, { id: 'farther', label: '멀어져요' }],
    answerId: 'closer',
    explain: '감지기 저항이 커지면 병렬 갈래로 빠지는 전류가 줄어요. 그래서 감지기를 달기 전의 부하 전압에 가까워져요.',
    check: {
      before: { params: { r: 1 }, ports: { sense: 'parallel' } },
      after: { params: { r: 100 } },
      tiles: ['voltage', 'loss'],
    },
  },
  toggles: [['labels', '노드 배지', true]],
  mistakes: {
    voltage: [
      { title: '전압계를 직렬로 넣으면 부하 전압을 읽어요', text: '직렬로 넣으면 전압계 자체의 전압 강하를 읽고 부하 양단의 전압과 달라질 수 있어요.' },
      { title: '병렬이면 원래 전압이 그대로예요', text: '유한한 감지기 저항으로 전류가 흘러 출력 저항에 걸리는 전압이 더 커져요.' },
      { title: '전압계 저항이 작을수록 좋아요', text: '병렬 감지기는 저항이 클수록 전류를 덜 가져가요.' },
    ],
    current: [
      { title: '전류계를 병렬로 대면 부하 전류를 읽어요', text: '병렬로 댄 전류계에는 감지기 갈래의 전류가 흘러요.' },
      { title: '직렬이면 원래 전류가 그대로예요', text: '직렬 감지기의 저항이 더해져 부하 전류가 줄어요.' },
      { title: '전류계 저항이 클수록 좋아요', text: '직렬 감지기는 저항이 작을수록 전압 강하가 작아요.' },
    ],
  },
  evaluate(state, mna) {
    const { mode, params, ports } = state;
    const connection = ports.sense;
    const resistance = params.r * 1000;
    const isVoltage = mode === 'voltage';
    const parallel = connection === 'parallel';
    const series = connection === 'series';
    const open = connection === 'open';
    const attached = parallel || series;
    const correct = isVoltage ? parallel : series;
    const elements = [
      { id: 'source', type: 'vsrc', n1: 'source', n2: '0', value: 1 },
      { id: 'outputResistance', type: 'R', n1: 'source', n2: 'terminal', value: 1000 },
      { id: 'loadResistance', type: 'R', n1: 'load', n2: '0', value: 1000 },
    ];
    if (series) {
      elements.push({ id: 'meter', type: 'R', n1: 'terminal', n2: 'load', value: resistance });
    } else if (!open) {
      elements.push({ id: 'jumper', type: 'short', n1: 'terminal', n2: 'load' });
      if (parallel) elements.push({ id: 'meter', type: 'R', n1: 'load', n2: '0', value: resistance });
    }
    const reference = mna.solveCircuit({ elements: [
      ...elements.slice(0, 3),
      { id: 'jumper', type: 'short', n1: 'terminal', n2: 'load' },
    ] });
    const solved = mna.solveCircuit({ elements });
    if (!solved.ok || !reference.ok) throw new Error(solved.reason || reference.reason);
    const voltage = solved.nodes.load.re;
    const current = solved.branches.loadResistance.re * 1000;
    const loss = 100 * (1 - voltage / reference.nodes.load.re);
    const meterCurrent = attached ? solved.branches.meter.re * 1000 : 0;
    const meterVoltage = parallel ? voltage : solved.nodes.terminal.re - voltage;
    const reading = isVoltage ? `${meterVoltage.toFixed(3)} V` : `${meterCurrent.toFixed(3)} mA`;
    const diagnosis = {
      ref: { title: '감지기를 달기 전', text: '기준 전압은 0.500 V, 기준 전류는 0.500 mA예요. 회로의 결선을 눌러 감지기를 연결해 보세요.' },
      open: { title: '부하 경로가 끊겼어요', text: '부하 쪽은 부하 저항을 통해 접지되어 있어요. 닫힌 전류 경로가 없어 부하 전압과 전류가 모두 0이에요.' },
      parallel: {
        title: isVoltage ? '부하와 같은 전압을 읽어요' : '감지기 갈래의 전류를 읽어요',
        text: '갈래가 하나 더 생겨요. 저항을 키우면 이 갈래로 흐르는 전류가 줄어 부하 전압이 덜 내려가요.',
      },
      series: {
        title: isVoltage ? '감지기 양단의 전압을 읽어요' : '부하와 같은 전류를 읽어요',
        text: '감지기 저항이 부하와 직렬로 더해져요. 이 저항을 낮추면 감지기를 달기 전의 부하 전류에 가까워져요.',
      },
    }[connection];
    return {
      tiles: [
        { id: 'voltage', label: '부하 전압', val: `${voltage.toFixed(3)} V` },
        { id: 'current', label: '부하 전류', val: `${current.toFixed(3)} mA` },
        { id: 'reading', label: isVoltage ? '감지기 전압' : '감지기 전류', val: attached ? reading : '연결 안 됨' },
        { id: 'loss', label: '기준 대비 감소', val: `${loss.toFixed(1)}%` },
      ],
      diagnosis: {
        ...diagnosis,
        kind: open || (attached && !correct) ? 'bad' : correct ? (loss > 5 ? 'warn' : 'ok') : 'info',
      },
      formula: parallel ? '$$R_{\\rm eq}=R_{\\rm L}\\parallel R_{\\rm S}$$'
        : series ? '$$R_{\\rm tot}=R_{\\rm out}+R_{\\rm S}+R_{\\rm L}$$' : '$$v_{\\rm L}=i_{\\rm L}R_{\\rm L}$$',
      summary: '1 V 전압원과 1 kΩ 출력 저항으로 증폭기 출력을 나타내요. 감지 저항의 로딩만 보는 모델이에요. 감지 신호를 입력으로 돌려보내는 경로는 생략했어요.',
      nodes: { load: { v: voltage, text: `${voltage.toFixed(3)} V` } },
      ports: { sense: { ok: correct, bad: open || (attached && !correct) } },
    };
  },
};
