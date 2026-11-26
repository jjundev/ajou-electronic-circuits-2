const R = 1000;
const F0 = 1000;
const C = 1 / (2 * Math.PI * R * F0);

const svg = `<svg viewBox="0 0 460 272" role="img" aria-label="차동 입력 종속 전류원과 출력 RC, 전압 귀환 K의 단일 극점 회로">
  <text class="fig-text fig-math" x="52" y="50" text-anchor="middle" data-node="in" data-node-color="blue">v<tspan baseline-shift="sub" font-size="78%">in</tspan></text>
  <circle class="fig-dot" cx="52" cy="72" r="4" data-node="in" data-node-color="blue"/>
  <text class="fig-text fig-math" x="52" y="117" text-anchor="middle" data-node="fb" data-node-color="blue">v<tspan baseline-shift="sub" font-size="78%">F</tspan></text>
  <circle class="fig-dot" cx="52" cy="135" r="4" data-node="fb" data-node-color="blue"/>
  <path class="fig-ink" d="M52 72h47M52 135h47"/>
  <rect class="fig-ink" x="99" y="54" width="68" height="94" rx="7"/>
  <text class="fig-text fig-math" x="116" y="77">+</text>
  <text class="fig-text fig-math" x="116" y="140">−</text>
  <text class="fig-text fig-math" x="134" y="104" text-anchor="middle">g<tspan baseline-shift="sub" font-size="78%">m</tspan></text>
  <path class="fig-muted" d="M167 101h32" fill="none" stroke="currentColor" stroke-dasharray="3 4"/>
  <path class="fig-ink" d="M218 81V62H414M218 126v50M301 62v38M301 141v35"/>
  <g class="sym">
    <path class="fig-ink" d="M218 81l20 23-20 22-20-22zM218 115V93m-5 6 5-6 5 6"/>
    <path class="fig-ink" d="M301 100l-7 5 14 6-14 6 14 6-14 6 7 6v6"/>
    <path class="fig-ink" d="M208 176h20m-16 5h12m-9 5h6M291 176h20m-16 5h12m-9 5h6"/>
  </g>
  <text class="fig-text fig-math" x="276" y="125" text-anchor="end">1 kΩ</text>
  <g data-elem="c" aria-label="출력 커패시터">
    <path class="fig-ink" d="M366 62v48m0 14v52"/>
    <g class="sym">
      <path class="fig-ink" d="M352 110h28m-28 14h28M356 176h20m-16 5h12m-9 5h6"/>
    </g>
    <text class="fig-text fig-math" x="395" y="121">C</text>
  </g>
  <path class="fig-accent" d="M414 62v166H257m-52 0H52v-93"/>
  <rect class="fig-ink" x="205" y="208" width="52" height="40" rx="7"/>
  <text class="fig-text fig-math" x="231" y="233" text-anchor="middle">K</text>
  <circle class="fig-dot" cx="301" cy="62" r="3"/>
  <circle class="fig-dot" cx="366" cy="62" r="3"/>
  <circle class="fig-dot" cx="414" cy="62" r="4" data-node="out" data-node-color="red"/>
  <text class="fig-text fig-math" x="414" y="42" text-anchor="middle" data-node="out" data-node-color="red">v<tspan baseline-shift="sub" font-size="78%">out</tspan></text>
  <g data-badges>
    <g data-badge-for="in" transform="translate(52 20)"></g>
    <g data-badge-for="fb" transform="translate(52 92)"></g>
    <g data-badge-for="out" transform="translate(408 14)"></g>
  </g>
</svg>`;

module.exports = {
  id: 'ec2-1111-feedback-gain',
  title: '음귀환 이득과 1/K 근사',
  archetype: 'approx',
  modes: [{ key: 'feedback', label: '단일 극점 음귀환', ariaLabel: '단일 극점 음귀환 회로', svg }],
  params: [
    { key: 'a0', label: '개루프 저주파 이득 A₀', min: 5, max: 1000, scale: 'log', def: 120 },
    { key: 'k', label: '귀환율 K', min: 0.02, max: 0.5, step: 0.01, def: 0.1 },
    { key: 'f', label: '측정 주파수', min: 100, max: 1000000, scale: 'log', unit: 'Hz', def: 100 },
  ],
  elems: [{ id: 'c', label: '출력 커패시터 C' }],
  presets: [
    { id: 'strong', label: '강한 저주파 귀환', params: { a0: 1000, k: 0.1, f: 100 }, disabledElems: [] },
    { id: 'weak', label: '작은 개루프 이득', params: { a0: 5, k: 0.1, f: 100 }, disabledElems: [] },
    { id: 'cutoff', label: '폐루프 극점에서 측정', params: { a0: 100, k: 0.1, f: 11000 }, disabledElems: [] },
  ],
  predict: {
    prompt: '낮은 주파수에서 $K=0.1$을 유지하며 $A_0$를 1000에서 5로 줄이면, 실제 이득과 $1/K$의 차이는 어떻게 될까요?',
    options: [{ id: 'same', label: '차이가 거의 그대로예요' }, { id: 'larger', label: '차이가 커져요' }],
    answerId: 'larger',
    explain: '루프 이득 $KA_0$가 100에서 0.5로 줄면 폐루프 이득이 저항비로 정해지는 영역에서 벗어나요.',
    check: {
      before: { params: { a0: 1000, k: 0.1, f: 100 }, disabledElems: [] },
      after: { params: { a0: 5 } },
      tiles: ['gain', 'ideal'],
    },
  },
  toggles: [['labels', '노드 배지', true]],
  mistakes: {
    feedback: [
      { title: 'K만 알면 이득이 정확히 1/K예요', text: '저주파에서도 $KA_0$가 작으면 분모의 1을 버릴 수 없어요.' },
      { title: '저주파 이득이 정확하면 고주파도 같아요', text: '출력 커패시터 때문에 주파수가 올라갈수록 개루프 이득의 크기가 줄고 $1/K$와 차이가 커져요.' },
      { title: '폐루프 극점은 저주파 이득이 절반인 곳이에요', text: '단일 극점에서 전압 이득의 크기는 저주파의 $1/\\sqrt{2}$배예요. 약 −3 dB에 해당해요.' },
    ],
  },
  evaluate(state, mna) {
    const { a0, k, f } = state.params;
    const withCap = !state.disabledElems.includes('c');
    const elements = [
      { id: 'drive', type: 'vsrc', n1: 'in', n2: '0', value: 0.001 },
      { id: 'gain', type: 'vccs', n1: '0', n2: 'out', cp: 'in', cn: 'fb', gm: a0 / R },
      { id: 'resistance', type: 'R', n1: 'out', n2: '0', value: R },
      { id: 'feedback', type: 'vccs', n1: '0', n2: 'fb', cp: 'out', cn: '0', gm: k / R },
      { id: 'feedbackScale', type: 'R', n1: 'fb', n2: '0', value: R },
    ];
    if (withCap) elements.push({ id: 'cap', type: 'C', n1: 'out', n2: '0', value: C });

    function solve(freqHz) {
      const result = mna.solveCircuit({ elements }, { freqHz });
      if (!result.ok) throw new Error(result.reason);
      return result.nodes;
    }
    const atFrequency = solve(f);
    const gain = atFrequency.out.mag / atFrequency.in.mag;
    const dcGain = solve(0).out.mag / atFrequency.in.mag;
    const ideal = 1 / k;
    const error = 100 * (ideal - gain) / gain;
    const db = value => 20 * Math.log10(value);
    const display = value => value < 0.1 ? value.toPrecision(3) : value.toFixed(2);
    const feedbackMv = atFrequency.fb.mag * 1000;
    const exact = Array.from({ length: 65 }, (_, i) => {
      const hz = 100 * 10 ** (i / 16);
      return [hz, db(solve(hz).out.mag / atFrequency.in.mag)];
    });
    const near = error <= 10;
    return {
      tiles: [
        { id: 'gain', label: '측정 주파수 이득', val: `${display(gain)} V/V` },
        { id: 'ideal', label: '이상 이득 1/K', val: `${ideal.toFixed(2)} V/V` },
        { id: 'dc', label: '저주파 이득', val: `${dcGain.toFixed(2)} V/V` },
        { id: 'bw', label: '−3 dB 대역폭', val: withCap ? `${(a0 / dcGain).toFixed(2)} kHz` : '모델 내 극점 없음' },
      ],
      diagnosis: {
        kind: near ? 'ok' : 'warn',
        title: near ? '크기 오차 10% 이내' : '크기 오차 10% 초과',
        text: `정확 이득 크기를 기준으로 ${error.toFixed(1)}% 차이예요. 저주파 루프 이득 $KA_0$는 ${(k * a0).toFixed(2)}예요.`,
      },
      formula: withCap
        ? '$$H(f)=\\frac{A_0}{1+KA_0+jf/f_0}$$'
        : '$$H=\\frac{A_0}{1+KA_0}$$',
      summary: withCap
        ? '입력은 1 mV예요. 배지는 각 노드 전압의 크기를 표시해요. 이상적 귀환 블록 K는 출력을 무한 입력 임피던스로 감지해요. 출력 RC의 개루프 극점은 $f_0=1$ kHz예요.'
        : '출력 커패시터를 빼면 이 이상적 선형 모델의 이득은 주파수에 따라 바뀌지 않아요. 유한한 개루프 이득 때문에 생기는 오차만 남아요.',
      nodes: {
        in: { v: 1, unit: 'mV' },
        fb: { v: feedbackMv, text: `${display(feedbackMv)} mV` },
        out: { v: gain, text: `${display(gain)} mV` },
      },
      plotData: {
        title: '정확 이득과 1/K 비교',
        xScale: 'log', yMin: -50, yMax: 40, xLabel: '주파수 (Hz)', yLabel: '|H| (dB)',
        exact, approx: exact.map(([hz]) => [hz, db(ideal)]),
        exactLabel: '회로 계산', approxLabel: '1/K 근사',
        marker: [f, db(gain)], approxMarker: [f, db(ideal)], errPct: error,
      },
    };
  },
};
