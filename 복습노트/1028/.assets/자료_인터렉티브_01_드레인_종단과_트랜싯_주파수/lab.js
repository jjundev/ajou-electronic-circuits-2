const SVG = `<svg viewBox="0 0 396 254" role="img" aria-label="드레인 종단을 바꿀 수 있는 MOS 단락 전류 측정 회로">
  <g data-causal-step="1">
    <path class="fig-ink" d="M48 137V98H116 M48 173v40"/>
    <g class="sym" data-symbol="isrc">
      <circle class="fig-ink" cx="48" cy="155" r="18"/>
      <path class="fig-ink" d="M48 167v-23m-5 5 5-5 5 5"/>
    </g>
    <text class="fig-text fig-math" x="20" y="130">i<tspan baseline-shift="sub" font-size="78%">in</tspan></text>
  </g>
  <g data-causal-step="2" data-branch="cgs">
    <path class="fig-ink" d="M116 98v48m0 12v55"/>
    <g class="sym" data-symbol="capacitor"><path class="fig-ink" d="M104 146h24m-24 12h24"/></g>
    <text class="fig-text fig-math" x="141" y="156">C<tspan baseline-shift="sub" font-size="78%">GS</tspan></text>
    <circle class="fig-dot" data-node="gate" data-node-color="blue" cx="116" cy="98" r="3.5"/>
    <text class="fig-text fig-math" data-node-color="blue" x="116" y="77" text-anchor="middle">v<tspan baseline-shift="sub" font-size="78%">G</tspan></text>
  </g>
  <g data-causal-step="3">
    <path class="fig-ink" d="M206 137V98H340 M206 173v40"/>
    <g class="sym" data-symbol="vccs" data-branch="gm">
      <path class="fig-ink" d="m206 137 18 18-18 18-18-18Z M206 146v18m-5-5 5 5 5-5"/>
    </g>
    <text class="fig-text fig-math" x="178" y="188" text-anchor="end">g<tspan baseline-shift="sub" font-size="78%">m</tspan>v<tspan baseline-shift="sub" font-size="78%">G</tspan></text>
    <circle class="fig-dot" data-node="drain" data-node-color="red" cx="267" cy="98" r="3.5"/>
    <text class="fig-text fig-math" data-node-color="red" x="267" y="77" text-anchor="middle">v<tspan baseline-shift="sub" font-size="78%">D</tspan></text>
  </g>
  <g data-elem="cdb" data-branch="cdb" aria-label="드레인 커패시턴스 CDB">
    <path class="fig-ink" d="M267 98v48m0 12v55"/>
    <g class="sym" data-symbol="capacitor"><rect x="228" y="123" width="60" height="60" opacity="0" pointer-events="all"/><path class="fig-ink" d="M255 146h24m-24 12h24"/></g>
    <text class="fig-text fig-math" x="288" y="156">C<tspan baseline-shift="sub" font-size="78%">DB</tspan></text>
  </g>
  <g data-port="drain" data-causal-step="3" aria-label="드레인 측정 종단">
    <g data-port-view="short" class="sym" data-symbol="short">
      <path class="fig-ink" d="M340 98v115 M368 162v-24m-5 5 5-5 5 5"/>
      <text class="fig-text fig-math" x="368" y="184" text-anchor="middle">i<tspan baseline-shift="sub" font-size="78%">t</tspan></text>
    </g>
    <g data-port-view="load" class="sym" data-symbol="resistor">
      <path class="fig-ink" d="M340 98v38l-7 4 14 6-14 6 14 6-14 6 7 4v45 M368 162v-24m-5 5 5-5 5 5"/>
      <text class="fig-text fig-math" x="368" y="184" text-anchor="middle">i<tspan baseline-shift="sub" font-size="78%">t</tspan></text>
    </g>
    <g data-port-view="open" class="sym" data-symbol="open">
      <path class="fig-ink" d="M340 98v44m0 28v43 M340 170l14-22"/>
      <circle class="fig-dot" cx="340" cy="142" r="3"/>
      <circle class="fig-dot" cx="340" cy="170" r="3"/>
    </g>
    <g class="port-chip">
      <rect class="port-chip-bg" x="309" y="18" width="62" height="54" rx="7"/>
      <text class="port-chip" x="340" y="45" text-anchor="middle">AC 단락</text>
    </g>
  </g>
  <g class="sym" data-symbol="gnd">
    <path class="fig-ink" d="M36 213h24m-20 6h16m-12 6h8 M104 213h24m-20 6h16m-12 6h8 M194 213h24m-20 6h16m-12 6h8 M255 213h24m-20 6h16m-12 6h8 M328 213h24m-20 6h16m-12 6h8"/>
  </g>
  <g data-badges>
    <g data-badge-for="gate" transform="translate(116,45)"></g>
    <g data-badge-for="drain" transform="translate(255,45)"></g>
  </g>
</svg>`;

const GM = 1 / 150;
const DRIVE = 10e-9;
const LOAD = 2000;
const CDB = 100e-15;
const F_MIN = 0.1;
const F_MAX = 40;
const unityGHz = (cgs) => GM / (2 * Math.PI * cgs) / 1e9;

function termination(id) {
  if (id === 'short') return { id: 'term', type: 'short', n1: '0', n2: 'drain' };
  if (id === 'load') return { id: 'term', type: 'R', n1: '0', n2: 'drain', value: LOAD };
  return { id: 'term', type: 'open', n1: '0', n2: 'drain' };
}

const spec = {
  id: 'mos-transit-termination-1028',
  title: '드레인 종단과 트랜싯 주파수',
  archetype: 'bench',
  modes: [{ key: 'measure', label: '단락 전류 측정', svg: SVG, ariaLabel: 'MOS 단락 전류 측정 회로' }],
  predict: {
    prompt: '드레인을 AC 단락하면 $C_{DB}$로 전류가 흐를까요?',
    options: [{ id: 'none', label: '흐르지 않아요' }, { id: 'flows', label: '흐를 수 있어요' }],
    answerId: 'none',
    explain: '단락에서는 $C_{DB}$ 양단의 AC 전압이 0이라 전류도 0이에요.',
  },
  ports: [{
    id: 'drain', label: '드레인 측정 종단', def: 'short', answer: 'short', badOption: 'load',
    options: [
      { id: 'short', label: 'AC 단락', shortLabel: 'AC 단락' },
      { id: 'load', label: '2 kΩ 저항 종단', shortLabel: '2 kΩ' },
      { id: 'open', label: '포트 개방', shortLabel: '개방' },
    ],
  }],
  elems: [{ id: 'cdb', label: '드레인 커패시턴스 CDB (100 fF)' }],
  params: [
    { key: 'freq', label: '주파수', min: F_MIN, max: F_MAX, def: 1, scale: 'log', unit: 'GHz' },
    { key: 'cgs', label: '게이트 커패시턴스 CGS', min: 150, max: 500, step: 5, def: 250, unit: 'fF' },
  ],
  causalSteps: [
    { id: 1, label: '시험 전류 넣기', detail: '10 nA의 교류 시험 전류를 게이트에 넣어요.' },
    { id: 2, label: '게이트 전압 만들기', detail: 'CGS의 임피던스가 낮아질수록 같은 전류가 만드는 게이트 전압이 작아져요.' },
    { id: 3, label: '종단 전류 측정하기', detail: '단락선은 종속원 전류를 모두 공급해요. 저항으로 바꾸면 CDB에도 전류가 흘러요.' },
  ],
  presets: [
    { id: 'unity', label: '단락 0 dB 교차', ports: { drain: 'short' }, params: { freq: unityGHz(250e-15), cgs: 250 }, disabledElems: [] },
    { id: 'loaded', label: '2 kΩ에서 측정', ports: { drain: 'load' }, params: { freq: 1, cgs: 250 }, disabledElems: [] },
    { id: 'open', label: '종단만 개방', ports: { drain: 'open' }, params: { freq: 1, cgs: 250 }, disabledElems: [] },
    { id: 'floating', label: '드레인 부유', ports: { drain: 'open' }, params: { freq: 1, cgs: 250 }, disabledElems: ['cdb'] },
  ],
  steps: [
    { title: '단락으로 전류 재기', text: '드레인 전압이 0이어도 단락선에 전류가 흘러요.', ports: { drain: 'short' }, params: { freq: 1, cgs: 250 }, disabledElems: [], causalStep: 3 },
    { title: '같은 입력에 저항 연결하기', text: '기생 커패시터 전류와 종단 전류를 비교해 보세요.', ports: { drain: 'load' }, params: { freq: 1, cgs: 250 }, disabledElems: [], causalStep: 3 },
  ],
  toggles: [['labels', '노드 배지', true]],
  mistakes: {
    measure: [
      { title: '전압 이득 1과 혼동하기', text: '$f_T$는 단락 전류 이득의 크기가 1이 되는 주파수예요. 측정 중 드레인 전압은 0이에요.' },
      { title: '단락인데 CDB에 전류가 흐른다고 보기', text: '주파수가 높아도 단락은 $v_D=0$을 유지해요. 그래서 $j\\omega C_{DB}v_D=0$이에요.' },
      { title: '저항 종단의 교차점도 fT라고 부르기', text: '저항을 연결해 잰 값에는 부하와 $C_{DB}$의 영향이 들어가요. $f_T$는 단락 조건에서 읽어요.' },
    ],
  },
  evaluate(state, mna) {
    const port = state.ports.drain;
    const frequency = state.params.freq;
    const cgs = state.params.cgs * 1e-15;
    const cdbOn = !state.disabledElems.includes('cdb');
    const elements = [
      { id: 'iin', type: 'isrc', n1: '0', n2: 'gate', value: DRIVE },
      { id: 'cgs', type: 'C', n1: 'gate', n2: '0', value: cgs },
      { id: 'gm', type: 'vccs', n1: 'drain', n2: '0', cp: 'gate', cn: '0', gm: GM },
      { id: 'cdb', type: cdbOn ? 'C' : 'open', n1: 'drain', n2: '0', value: CDB },
    ];
    const measure = (ghz, id) => mna.solveCircuit(
      { elements: [...elements, termination(id)] },
      { freqHz: ghz * 1e9 },
    );
    const solved = measure(frequency, port);
    const pulse = state.causalStep;
    if (!solved.ok) {
      return {
        tiles: [{ label: '측정 상태', val: '부유 드레인' }],
        diagnosis: { kind: 'bad', singular: true, title: '드레인 전류의 반환 경로가 없어요', text: '포트를 열고 $C_{DB}$를 떼면 드레인 전압을 정할 수 없어요. 단락이나 저항을 연결해 보세요.' },
        ports: { drain: { bad: true } },
      };
    }

    const fT = unityGHz(cgs);
    const gain = solved.branches.term.mag / DRIVE;
    const cdCurrent = solved.branches.cdb.mag * 1e9;
    const termCurrent = solved.branches.term.mag * 1e9;
    const conducting = port !== 'open';
    const loaded = port === 'load';
    const loadFactor = 2 * Math.PI * fT * 1e9 * LOAD * (cdbOn ? CDB : 0);
    const loadedUnity = fT * Math.sqrt(2 / (1 + Math.sqrt(1 + 4 * loadFactor ** 2)));
    const toDb = (solution) => 20 * Math.log10(solution.branches.term.mag / DRIVE);
    let plotData;
    if (conducting) {
      const frequencies = Array.from({ length: 65 }, (_, i) => F_MIN * (F_MAX / F_MIN) ** (i / 64));
      const yDb = toDb(solved);
      plotData = {
        title: '주파수에 따른 전류 이득',
        xLabel: '주파수 (GHz)', yLabel: '전류 이득 (dB)', xScale: 'log',
        xMin: F_MIN, xMax: F_MAX, yMin: -64, yMax: 64,
        exact: frequencies.map((f) => [f, toDb(measure(f, port))]),
        exactLabel: loaded ? '2 kΩ 종단' : 'AC 단락',
        approx: loaded
          ? frequencies.map((f) => [f, toDb(measure(f, 'short'))])
          : [[F_MIN, 0], [F_MAX, 0]],
        approxLabel: loaded ? 'AC 단락 기준' : '전류 이득 1 (0 dB)',
        marker: [frequency, yDb],
      };
    }

    const formula = !conducting ? undefined : loaded
      ? String.raw`$$\frac{I_t}{I_{\rm in}}=\frac{I_T/I_{\rm in}}{1+j\omega R_L C_D}$$`
      : String.raw`$$\left|\frac{I_T}{I_{\rm in}}\right|=\frac{g_m}{2\pi f C_{GS}}$$`;
    const diagnosis = !conducting
      ? { kind: 'warn', title: '종단에서 잴 전류가 없어요', text: '$C_{DB}$가 교류 전류 경로를 제공해요. 외부 측정선으로는 전류가 흐르지 않아요.' }
      : loaded
        ? { kind: 'warn', title: '부하를 단 상태의 전류 이득이에요', text: cdbOn
          ? '(교과서 보충) 드레인에 AC 전압이 생겨 저항과 $C_{DB}$가 전류를 나눠 공급해요.'
          : '$C_{DB}$를 뗀 이상 모델에서는 저항이 모든 전류를 공급해 단락과 같은 전류 이득이 나와요.' }
        : { kind: 'ok', title: '단락 전류를 측정하고 있어요', text: '드레인 전압과 $C_{DB}$ 전류가 0이에요. 실선이 0 dB를 지나는 곳에서 $f_T$를 읽어요.' };

    return {
      tiles: [
        { label: '종단 전류', val: `${termCurrent.toFixed(3)} nA` },
        { label: '전류 이득 크기', val: conducting ? gain.toFixed(3) : '측정선 개방' },
        { label: '단락 fT', val: `${fT.toFixed(3)} GHz` },
      ],
      diagnosis,
      formula,
      summary: `10 nA 시험 전류에서 CDB 가지 전류의 크기는 ${cdCurrent.toFixed(3)} nA예요. 소신호 모델에서 $r_o$와 $C_{GD}$를 생략했어요.${loaded ? ` 저항 종단의 0 dB 교차는 ${loadedUnity.toFixed(3)} GHz예요. 식의 $C_D$는 CDB를 끄면 0이에요.` : ''}`,
      nodes: {
        gate: { badge: `${(solved.nodes.gate.mag * 1e6).toFixed(3)} µV`, hot: pulse === 2 },
        drain: { badge: `${(solved.nodes.drain.mag * 1e6).toFixed(3)} µV`, hot: pulse === 3 },
      },
      branches: { cgs: { hot: pulse === 2 }, gm: { hot: pulse === 3 }, cdb: { hot: pulse === 3 && cdbOn && port !== 'short' } },
      ports: { drain: { hot: pulse === 3, bad: port !== 'short' } },
      plotData,
    };
  },
};

module.exports = spec;
