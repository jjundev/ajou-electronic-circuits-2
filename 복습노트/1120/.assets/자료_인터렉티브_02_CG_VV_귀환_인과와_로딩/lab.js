// Interactive Lab 02 (1120): Example I CG Stage V-V Feedback +Δv Causal Domino & Divider Loading Probe
// Archetype: probe — solves full closed-loop and duplicate-terminated open-loop CG circuits via MNA,
// displays live node voltages & branch currents in SVG badges, and drives a 4-beat +Δv causal domino.

const SVG_NS_ATTR = 'xmlns="http://www.w3.org/2000/svg"';

function sub(base, s) {
  return `${base}<tspan baseline-shift="sub" font-size="78%">${s}</tspan>`;
}

function gndSym(x, y) {
  return [
    '<g class="sym" data-symbol="gnd">',
    `  <line class="fig-ink" x1="${x}" y1="${y}" x2="${x}" y2="${y + 6}"/>`,
    `  <line class="fig-ink" x1="${x - 10}" y1="${y + 6}" x2="${x + 10}" y2="${y + 6}"/>`,
    `  <line class="fig-ink" x1="${x - 6}" y1="${y + 11}" x2="${x + 6}" y2="${y + 11}"/>`,
    `  <line class="fig-ink" x1="${x - 2.5}" y1="${y + 16}" x2="${x + 2.5}" y2="${y + 16}"/>`,
    '</g>',
  ].join('');
}

function vRes(x, yTop, yBot) {
  const mid = (yTop + yBot) / 2;
  const zTop = mid - 24;
  const d = `M${x} ${zTop}l6 4-12 8 12 8-12 8 12 8-12 8 6 4`;
  return [
    `<line class="fig-ink" x1="${x}" y1="${yTop}" x2="${x}" y2="${zTop}"/>`,
    `<g class="sym" data-symbol="resistor"><path class="fig-ink" d="${d}"/></g>`,
    `<line class="fig-ink" x1="${x}" y1="${zTop + 48}" x2="${x}" y2="${yBot}"/>`,
  ].join('');
}

function buildCgBaseParts() {
  return [
    // V_DD AC ground bar + R_D branch (i_RD)
    '<g class="sym" data-symbol="vdd"><path class="fig-ink" d="M168 46h24"/></g>',
    `<text class="fig-text fig-math" x="200" y="51" text-anchor="start" font-size="14">${sub('V', 'DD')} (AC 접지)</text>`,
    `<g data-branch="i_RD" data-causal-step="3,4">`,
    '  ' + vRes(180, 46, 122),
    '</g>',
    `<text class="fig-text fig-math" x="158" y="88" text-anchor="end" font-size="14">${sub('R', 'D')}</text>`,

    // Output horizontal rail + M1 drain wire (i_D1)
    '<g data-branch="i_D1" data-causal-step="3">',
    '  <line class="fig-ink" x1="180" y1="122" x2="180" y2="188"/>',
    '  <line class="fig-ink" x1="180" y1="220" x2="180" y2="264"/>',
    '</g>',

    // M1 CG NMOS symbol (gate center y=204, drain y=188, source y=220)
    '<g data-causal-step="2">',
    '  <g class="sym" data-symbol="nmos">',
    '    <path class="fig-ink" d="M180 188h14M194 220h-14"/>',
    '    <path class="fig-ink" d="M194 182v44M201 186v36M189 216l-6 4 6 4"/>',
    '  </g>',
    `  <text class="fig-text fig-math" x="158" y="172" text-anchor="end" font-size="14">${sub('M', '1')}</text>`,
    '</g>',

    // Input source vin + source wire (causal step 1)
    '<g data-causal-step="1">',
    '  <line class="fig-ink" x1="180" y1="264" x2="60" y2="264"/>',
    '  <line class="fig-ink" x1="60" y1="264" x2="60" y2="278"/>',
    '  <g class="sym" data-symbol="vsrc">',
    '    <circle class="fig-ink" cx="60" cy="294" r="16"/>',
    '    <path class="fig-ink" d="M55 288h10M60 283v10M55 302h10"/>',
    '  </g>',
    '  <line class="fig-ink" x1="60" y1="310" x2="60" y2="322"/>',
    '  ' + gndSym(60, 322),
    '  <circle class="fig-dot" cx="180" cy="264" r="4" data-node="in" data-node-color="blue"/>',
    `  <text class="fig-text fig-math" x="34" y="298" text-anchor="end" font-size="14" data-node="in" data-node-color="blue">${sub('v', 'in')}</text>`,
    '</g>',
  ];
}

function buildClosedSvg() {
  const parts = [
    `<svg viewBox="0 0 650 370" ${SVG_NS_ATTR} role="img" aria-label="예제 I V-V 귀환 공통 게이트(CG) 폐루프 소신호 회로도">`,
    ...buildCgBaseParts(),

    // Output bus & output terminal (causal step 4)
    '<g data-causal-step="4">',
    '  <line class="fig-ink" x1="180" y1="122" x2="560" y2="122"/>',
    '  <circle class="fig-dot" cx="180" cy="122" r="4" data-node="out" data-node-color="red"/>',
    '  <circle class="fig-dot" cx="440" cy="122" r="4" data-node="out" data-node-color="red"/>',
    '  <circle class="fig-dot" cx="560" cy="122" r="4" data-node="out" data-node-color="red"/>',
    `  <text class="fig-text fig-math" x="576" y="127" text-anchor="start" font-size="14" data-node="out" data-node-color="red">${sub('v', 'out')}</text>`,
    '</g>',

    // Feedback divider R1-R2 + direct return to M1 gate
    '<g data-branch="i_div" data-causal-step="3,4">',
    '  ' + vRes(440, 122, 204),
    '  ' + vRes(440, 204, 276),
    '  ' + gndSym(440, 276),
    '</g>',
    '<g data-causal-step="4">',
    '  <line class="fig-ink" x1="440" y1="204" x2="201" y2="204"/>',
    '  <circle class="fig-dot" cx="440" cy="204" r="4" data-node="g" data-node-color="blue"/>',
    `  <text class="fig-text fig-math" x="342" y="186" text-anchor="end" font-size="14" data-node="g" data-node-color="blue">${sub('v', 'G')}</text>`,
    '</g>',
    `<rect class="fig-ink" x="400" y="132" width="96" height="164" rx="6" style="stroke-width:1;stroke-dasharray:4 3"/>`,
    `<text class="fig-text fig-math" x="466" y="168" text-anchor="start" font-size="14">${sub('R', '1')}</text>`,
    `<text class="fig-text fig-math" x="466" y="246" text-anchor="start" font-size="14">${sub('R', '2')}</text>`,
    '<text class="fig-muted" x="448" y="324" text-anchor="middle">귀환 분배기 K</text>',

    // Static badge slots (comfortably clear of all wires)
    '<g data-badges>',
    '  <g data-badge-for="i_RD" transform="translate(310, 76)"></g>',
    '  <g data-badge-for="out" transform="translate(545, 76)"></g>',
    '  <g data-badge-for="i_D1" transform="translate(76, 224)"></g>',
    '  <g data-badge-for="in" transform="translate(176, 338)"></g>',
    '  <g data-badge-for="g" transform="translate(300, 244)"></g>',
    '  <g data-badge-for="i_div" transform="translate(568, 204)"></g>',
    '</g>',
    '</svg>',
  ];
  return parts.join('\n');
}

function buildOpenSvg() {
  const parts = [
    `<svg viewBox="0 0 650 370" ${SVG_NS_ATTR} role="img" aria-label="예제 I V-V 귀환 복제 달린 개루프 소신호 회로도">`,
    ...buildCgBaseParts(),

    // Output bus & output terminal (causal step 4)
    '<g data-causal-step="4">',
    '  <line class="fig-ink" x1="180" y1="122" x2="560" y2="122"/>',
    '  <circle class="fig-dot" cx="180" cy="122" r="4" data-node="out" data-node-color="red"/>',
    '  <circle class="fig-dot" cx="440" cy="122" r="4" data-node="out" data-node-color="red"/>',
    '  <circle class="fig-dot" cx="560" cy="122" r="4" data-node="out" data-node-color="red"/>',
    `  <text class="fig-text fig-math" x="576" y="127" text-anchor="start" font-size="14" data-node="out" data-node-color="red">${sub('v', 'out')}</text>`,
    '</g>',

    // Return duplicate on M1 gate (R1 top shorted to AC GND, R2 bottom to GND)
    '<g data-causal-step="2">',
    '  <line class="fig-ink" x1="201" y1="204" x2="280" y2="204"/>',
    '  <circle class="fig-dot" cx="280" cy="204" r="4" data-node="g" data-node-color="blue"/>',
    `  <text class="fig-text fig-math" x="220" y="180" text-anchor="middle" font-size="14" data-node="g" data-node-color="blue">${sub('v', 'G')}</text>`,
    '</g>',
    vRes(280, 148, 204),
    '<line class="fig-ink" x1="280" y1="148" x2="318" y2="148"/>',
    '<line class="fig-ink" x1="318" y1="148" x2="318" y2="156"/>',
    gndSym(318, 156),
    vRes(280, 204, 260),
    gndSym(280, 260),
    `<rect class="fig-ink" x="244" y="136" width="96" height="144" rx="6" style="stroke-width:1;stroke-dasharray:4 3"/>`,
    `<text class="fig-text fig-math" x="266" y="178" text-anchor="end" font-size="13">${sub('R', '1')}</text>`,
    `<text class="fig-text fig-math" x="298" y="236" text-anchor="start" font-size="13">${sub('R', '2')}</text>`,
    '<text class="fig-muted" x="292" y="308" text-anchor="middle">반송 복제 (접지)</text>',

    // Sense duplicate on output (R1-R2 series to GND, midpoint open)
    '<g data-branch="i_div" data-causal-step="3,4">',
    '  ' + vRes(440, 122, 204),
    '  ' + vRes(440, 204, 276),
    '  ' + gndSym(440, 276),
    '</g>',
    '<g data-causal-step="4">',
    '  <circle class="fig-dot" cx="440" cy="204" r="4" data-node="sense_mid" data-node-color="blue"/>',
    '  <line class="fig-ink" x1="440" y1="204" x2="412" y2="204"/>',
    '  <circle class="fig-ink" cx="407" cy="204" r="5"/>',
    '</g>',
    `<rect class="fig-ink" x="392" y="132" width="102" height="164" rx="6" style="stroke-width:1;stroke-dasharray:4 3"/>`,
    `<text class="fig-text fig-math" x="464" y="168" text-anchor="start" font-size="14">${sub('R', '1')}</text>`,
    `<text class="fig-text fig-math" x="464" y="246" text-anchor="start" font-size="14">${sub('R', '2')}</text>`,
    '<text class="fig-muted" x="443" y="324" text-anchor="middle">감지 복제 (개방)</text>',

    // Static badge slots
    '<g data-badges>',
    '  <g data-badge-for="i_RD" transform="translate(310, 76)"></g>',
    '  <g data-badge-for="out" transform="translate(545, 76)"></g>',
    '  <g data-badge-for="i_D1" transform="translate(76, 224)"></g>',
    '  <g data-badge-for="in" transform="translate(176, 338)"></g>',
    '  <g data-badge-for="g" transform="translate(292, 340)"></g>',
    '  <g data-badge-for="sense_mid" transform="translate(443, 350)"></g>',
    '  <g data-badge-for="i_div" transform="translate(568, 204)"></g>',
    '</g>',
    '</svg>',
  ];
  return parts.join('\n');
}

function fmtSignedMv(mv) {
  if (Math.abs(mv) < 1e-4) return '0.00 mV';
  const sign = mv > 0 ? '+' : '−';
  const abs = Math.abs(mv);
  if (abs >= 1000) return `${sign}${(abs / 1000).toFixed(2)} V`;
  return `${sign}${abs.toFixed(2)} mV`;
}

function fmtSignedMvShort(mv) {
  if (Math.abs(mv) < 1e-4) return '0.00 mV';
  const sign = mv > 0 ? '+' : '−';
  const abs = Math.abs(mv);
  if (abs >= 1000) return `${sign}${(abs / 1000).toFixed(2)} V`;
  if (abs >= 100) return `${sign}${abs.toFixed(1)} mV`;
  return `${sign}${abs.toFixed(2)} mV`;
}

function fmtSignedUa(ua) {
  if (Math.abs(ua) < 1e-4) return '0.0 μA';
  const sign = ua > 0 ? '+' : '−';
  const abs = Math.abs(ua);
  if (abs >= 1000) return `${sign}${(abs / 1000).toFixed(2)} mA`;
  return `${sign}${abs.toFixed(1)} μA`;
}

function fmtMvTex(mv) {
  if (Math.abs(mv) < 1e-4) return '0.00\\ \\text{mV}';
  const sign = mv > 0 ? '+' : '-';
  const abs = Math.abs(mv);
  if (abs >= 1000) return `${sign}${(abs / 1000).toFixed(2)}\\ \\text{V}`;
  return `${sign}${abs.toFixed(2)}\\ \\text{mV}`;
}

function fmtUaTex(ua) {
  if (Math.abs(ua) < 1e-4) return '0.0\\ \\mu\\text{A}';
  const sign = ua > 0 ? '+' : '-';
  const abs = Math.abs(ua);
  if (abs >= 1000) return `${sign}${(abs / 1000).toFixed(2)}\\ \\text{mA}`;
  return `${sign}${abs.toFixed(1)}\\ \\mu\\text{A}`;
}

function fmtOhms(ohms) {
  if (ohms >= 1000) return `${(ohms / 1000).toFixed(2)} kΩ`;
  return `${ohms.toFixed(0)} Ω`;
}

function fmtOhmsTex(ohms) {
  if (ohms >= 1000) return `${(ohms / 1000).toFixed(2)}\\ \\text{k}\\Omega`;
  return `${ohms.toFixed(0)}\\ \\Omega`;
}

function dirFromVal(val) {
  if (val > 1e-6) return 'up';
  if (val < -1e-6) return 'down';
  return undefined;
}

function solveCgFeedback(modeKey, params, mna) {
  const vinMv = Number(params.vin);
  const vinV = vinMv * 1e-3;
  const rdivK = Number(params.rdiv);
  const r1Ohm = 0.75 * rdivK * 1000;
  const r2Ohm = 0.25 * rdivK * 1000;
  const gm1S = Number(params.gm1) * 1e-3;
  const rdOhm = Number(params.rd) * 1000;

  const makeClosedEls = (vInVal) => [
    { id: 'vin', type: 'vsrc', n1: 'in', n2: '0', value: vInVal },
    { id: 'gm1', type: 'vccs', n1: 'out', n2: 'in', cp: 'g', cn: 'in', gm: gm1S },
    { id: 'rd', type: 'R', n1: '0', n2: 'out', value: rdOhm },
    { id: 'r1', type: 'R', n1: 'out', n2: 'g', value: r1Ohm },
    { id: 'r2', type: 'R', n1: 'g', n2: '0', value: r2Ohm },
  ];

  const makeOpenEls = (vInVal) => [
    { id: 'vin', type: 'vsrc', n1: 'in', n2: '0', value: vInVal },
    { id: 'gm1', type: 'vccs', n1: 'out', n2: 'in', cp: 'g', cn: 'in', gm: gm1S },
    { id: 'rd', type: 'R', n1: '0', n2: 'out', value: rdOhm },
    { id: 'r1_ret', type: 'R', n1: '0', n2: 'g', value: r1Ohm },
    { id: 'r2_ret', type: 'R', n1: 'g', n2: '0', value: r2Ohm },
    { id: 'r1_sense', type: 'R', n1: 'out', n2: 'sense_mid', value: r1Ohm },
    { id: 'r2_sense', type: 'R', n1: 'sense_mid', n2: '0', value: r2Ohm },
    { id: 'sense_port', type: 'open', n1: 'sense_mid', n2: '0' },
  ];

  // Solve actual operating point (handles vin = 0 cleanly) + unit 1 V gain + open-loop Rout test
  const closedOp = mna.solveCircuit({ elements: makeClosedEls(vinV) });
  const closedUnit = mna.solveCircuit({ elements: makeClosedEls(1.0) });
  const openOp = mna.solveCircuit({ elements: makeOpenEls(vinV) });
  const openUnit = mna.solveCircuit({ elements: makeOpenEls(1.0) });
  const openRoutTest = mna.solveCircuit({
    elements: [
      { id: 'vin', type: 'vsrc', n1: 'in', n2: '0', value: 0 },
      { id: 'gm1', type: 'vccs', n1: 'out', n2: 'in', cp: 'g', cn: 'in', gm: gm1S },
      { id: 'rd', type: 'R', n1: '0', n2: 'out', value: rdOhm },
      { id: 'r1_ret', type: 'R', n1: '0', n2: 'g', value: r1Ohm },
      { id: 'r2_ret', type: 'R', n1: 'g', n2: '0', value: r2Ohm },
      { id: 'r1_sense', type: 'R', n1: 'out', n2: 'sense_mid', value: r1Ohm },
      { id: 'r2_sense', type: 'R', n1: 'sense_mid', n2: '0', value: r2Ohm },
      { id: 'it', type: 'isrc', n1: '0', n2: 'out', value: 1e-3 },
    ],
  });
  // Ideal open-loop without divider loading (to demonstrate the no-loading error)
  const noLoadOpenUnit = mna.solveCircuit({
    elements: [
      { id: 'vin', type: 'vsrc', n1: 'in', n2: '0', value: 1.0 },
      { id: 'gm1', type: 'vccs', n1: 'out', n2: 'in', cp: 'g', cn: 'in', gm: gm1S },
      { id: 'rd', type: 'R', n1: '0', n2: 'out', value: rdOhm },
      { id: 'g_gnd', type: 'short', n1: 'g', n2: '0' },
    ],
  });
  const kTest = mna.solveCircuit({
    elements: [
      { id: 'v1', type: 'vsrc', n1: 'out', n2: '0', value: 1.0 },
      { id: 'r1', type: 'R', n1: 'out', n2: 'g', value: r1Ohm },
      { id: 'r2', type: 'R', n1: 'g', n2: '0', value: r2Ohm },
    ],
  });

  if (!closedOp.ok || !closedUnit.ok || !openOp.ok || !openUnit.ok || !openRoutTest.ok || !noLoadOpenUnit.ok || !kTest.ok) {
    return { ok: false, reason: '회로 해석 중 특이 행렬이 발생했어요.' };
  }

  const kFactor = kTest.nodes.g.re;
  const avOpen = openUnit.nodes.out.re;
  const avClosed = closedUnit.nodes.out.re;
  const rOutOpenOhm = openRoutTest.nodes.out.re / 1e-3;
  const avNoLoadOpen = noLoadOpenUnit.nodes.out.re;
  const avNoLoadClosed = avNoLoadOpen / (1 + kFactor * avNoLoadOpen);
  const noLoadErrPct = ((avNoLoadClosed - avClosed) / avClosed) * 100;

  const op = modeKey === 'open' ? openOp : closedOp;
  const vInMv = op.nodes.in.re * 1000;
  const vGMv = op.nodes.g.re * 1000;
  const vOutMv = op.nodes.out.re * 1000;
  const vGsMv = vGMv - vInMv;
  const vSenseMidMv = modeKey === 'open' ? openOp.nodes.sense_mid.re * 1000 : vGMv;

  const iD1Ua = op.branches.gm1.re * 1e6;
  const iRdUa = op.branches.rd.re * 1e6;
  const iDivUa = (modeKey === 'open' ? op.branches.r1_sense.re : op.branches.r1.re) * 1e6;

  return {
    ok: true,
    r1K: 0.75 * rdivK,
    r2K: 0.25 * rdivK,
    rdivK,
    gm1Ms: Number(params.gm1),
    rdK: Number(params.rd),
    kFactor,
    rOutOpenOhm,
    avOpen,
    loopGain: kFactor * avOpen,
    avClosed,
    avNoLoadOpen,
    avNoLoadClosed,
    noLoadErrPct,
    vInMv,
    vGMv,
    vOutMv,
    vGsMv,
    vSenseMidMv,
    iD1Ua,
    iRdUa,
    iDivUa,
  };
}

const spec = {
  id: 'cg-vv-feedback-causal-loading',
  title: 'CG 단 V-V 귀환 +Δv 인과와 분배기 로딩',
  archetype: 'probe',
  modes: [
    {
      key: 'closed',
      label: '폐루프 귀환',
      svg: buildClosedSvg(),
      ariaLabel: '예제 I V-V 귀환 공통 게이트 폐루프 소신호 회로도',
    },
    {
      key: 'open',
      label: '복제 개루프',
      svg: buildOpenSvg(),
      ariaLabel: '예제 I V-V 귀환 반송·감지 복제 달린 개루프 소신호 회로도',
    },
  ],
  predict: {
    prompt: 'V-V 귀환 CG 단에서 분배기 로딩($R_1+R_2$)을 빼고 개루프를 $g_{m1}R_D$로 계산하면, 폐루프 이득은 실제보다 어떻게 나올까요?',
    options: [
      { id: 'larger', label: '실제보다 크게 나온다 (과대평가)' },
      { id: 'smaller', label: '실제보다 작게 나온다 (과소평가)' },
      { id: 'same', label: '로딩과 무관하게 같다' },
    ],
    answerId: 'larger',
    explain: '분배기 $R_1+R_2$가 $R_D$와 병렬로 걸려 실제 개루프 이득이 $g_{m1}[R_D\\parallel(R_1+R_2)]$로 줄어들므로, 이를 빼먹으면 폐루프 이득도 실제보다 크게(기본값 $2.67$ 대신 $3.20$, $+20\\%$) 나와요.',
  },
  params: [
    {
      key: 'vin',
      label: '입력 신호 vin',
      min: -20,
      max: 20,
      step: 1,
      unit: 'mV',
      def: 10,
      format: (v) => `${Number(v) > 0 ? '+' : ''}${Math.round(Number(v))} mV`,
    },
    { key: 'rdiv', label: '분배기 합 R1+R2 (3:1)', min: 1, max: 40, step: 1, unit: 'kΩ', def: 4 },
    { key: 'gm1', label: '트랜스컨덕턴스 gm1', min: 2, max: 10, step: 0.5, unit: 'mS', def: 4 },
    { key: 'rd', label: '부하 저항 RD', min: 1, max: 8, step: 0.5, unit: 'kΩ', def: 4 },
  ],
  causalSteps: [
    {
      id: 1,
      label: '소스에 입력 vin 인가',
      detail: '입력 전압원 vin이 M1 소스 노드를 직접 움직여요.',
    },
    {
      id: 2,
      label: 'vgs = vG − vin 반대 변화',
      detail: '소스가 오르면 게이트−소스 전압 vgs가 먼저 줄어들고(↓), 음의 입력이면 커져요(↑).',
    },
    {
      id: 3,
      label: '드레인 전류 iD1 변화',
      detail: 'iD1 = gm1·vgs가 줄어들면(↓) M1이 출력 노드에서 전류를 덜 끌어내려 RD와 R1+R2로 전류가 밀려 나가요.',
    },
    {
      id: 4,
      label: 'vout 및 분배기 vG 응답',
      detail: '출력 vout이 오르고(↑), 폐루프에서는 분배기 vG = K·vout도 함께 올라(↑) vgs 변동을 억제해요.',
    },
  ],
  presets: [
    { id: 'lecture-def', label: '수업 기본 (4 kΩ)', params: { vin: 10, rdiv: 4, gm1: 4, rd: 4 } },
    { id: 'heavy-load', label: '무거운 로딩 (1 kΩ)', params: { vin: 10, rdiv: 1, gm1: 4, rd: 4 } },
    { id: 'light-load', label: '가벼운 로딩 (40 kΩ)', params: { vin: 10, rdiv: 40, gm1: 4, rd: 4 } },
    { id: 'neg-vin', label: '음의 입력 (−10 mV)', params: { vin: -10, rdiv: 4, gm1: 4, rd: 4 } },
  ],
  steps: [
    {
      mode: 'closed',
      title: '1박자: 소스에 +10 mV 인가',
      who: 'vin = +10 mV ↑',
      text: '입력 신호 vin = +10.00 mV가 M1 소스에 바로 인가돼요. 게이트가 아니라 소스가 입력 단자라는 점이 CG 단의 출발점이에요.',
      params: { vin: 10, rdiv: 4, gm1: 4, rd: 4 },
      causalStep: 1,
    },
    {
      mode: 'closed',
      title: '2박자: vgs = vG − vin 감소',
      who: 'vG = +6.67 mV → vgs = −3.33 mV ↓',
      text: '소스가 +10.00 mV 오를 때 분배기가 게이트를 +6.67 mV만 올려 주므로 vgs = vG − vin = −3.33 mV로 작아져요. 개루프(−10.00 mV)의 1/3로 억제됐어요.',
      params: { vin: 10, rdiv: 4, gm1: 4, rd: 4 },
      causalStep: 2,
    },
    {
      mode: 'closed',
      title: '3박자: 드레인 전류 iD1 감소',
      who: 'iD1 = −13.3 μA ↓ → 출력으로 전류 공급',
      text: 'vgs가 음수(−3.33 mV)라 드레인 전류 iD1 = −13.3 μA가 되어 출력 쪽으로 전류가 올라와요. 이 전류가 RD(위쪽 접지로 6.7 μA)와 R1+R2(아래로 6.7 μA)로 나뉘어요.',
      params: { vin: 10, rdiv: 4, gm1: 4, rd: 4 },
      causalStep: 3,
    },
    {
      mode: 'closed',
      title: '4박자: vout 상승 및 귀환 억제',
      who: 'vout = +26.67 mV ↑ · Av = 2.67 (오답 3.20)',
      text: '출력 vout = +26.67 mV가 올라가면 K = 0.25를 거쳐 vG = +6.67 mV로 돌아와 vgs 감소를 되돌려요. 로딩 무시 오답 3.20보다 20% 낮은 실제 이득 2.67을 얻어요.',
      params: { vin: 10, rdiv: 4, gm1: 4, rd: 4 },
      causalStep: 4,
    },
    {
      mode: 'closed',
      title: '로딩 심화: R1+R2 = 1 kΩ',
      who: 'Av,closed = 1.78 vs 오답 3.20 (+80%)',
      text: 'R1+R2 = 1 kΩ이 되면 RD = 4 kΩ과 병렬인 Rout,open = 0.80 kΩ으로 급감해 폐루프 이득이 1.78까지 떨어져요. 로딩을 빼먹은 오답 3.20과는 +80.0% 차이가 나요.',
      params: { vin: 10, rdiv: 1, gm1: 4, rd: 4 },
      causalStep: 0,
    },
    {
      mode: 'closed',
      title: '가벼운 로딩: R1+R2 = 40 kΩ',
      who: 'Av,closed = 3.14 (오답 3.20과 +2% 차이)',
      text: 'R1+R2 = 40 kΩ이 RD = 4 kΩ의 10배이면 분배기가 끄는 전류가 작아져 Av,closed = 3.14가 되고, 로딩 무시 근사값 3.20과의 오차도 +2.0%로 줄어들어요.',
      params: { vin: 10, rdiv: 40, gm1: 4, rd: 4 },
      causalStep: 0,
    },
    {
      mode: 'open',
      title: '1. 복제 종단과 게이트 0 V 확인',
      who: '반송 접지 · 감지 개방 → vG = 0.00 mV',
      text: '반송 복제는 R1 위 끝을 접지해 게이트에 R1 ∥ R2가 보이지만, 게이트 전류가 0이므로 vG = 0.00 mV로 고정돼요. 출력 쪽 감지 복제는 가운데 단자가 개방돼 R1+R2가 직렬로 달려요.',
      params: { vin: 10, rdiv: 4, gm1: 4, rd: 4 },
      causalStep: 4,
    },
    {
      mode: 'open',
      title: '2. 로딩 포함 개루프 값 확인',
      who: 'Rout,open = 2.00 kΩ · Av,open = 8.00',
      text: '출력 저항은 RD ∥ (R1+R2) = 4 ∥ 4 = 2.00 kΩ, 개루프 이득은 4 mS × 2.00 kΩ = 8.00이에요. 루프 이득 K·Av,open = 2.00이므로 폐루프는 이 8.00을 1+2 = 3으로 나눈 2.67이 돼요.',
      params: { vin: 10, rdiv: 4, gm1: 4, rd: 4 },
      causalStep: 0,
    },
    {
      mode: 'open',
      title: '3. 음의 입력 (−10 mV) 인과 확인',
      who: 'vin = −10 mV ↓ → iD1 = +40 μA ↑ → vout = −80 mV ↓',
      text: '소스가 −10.00 mV 내려가면 vgs = +10.00 mV로 커져 드레인 전류 iD1 = +40.0 μA가 아래로 더 흐르고, 출력 전압은 −80.00 mV로 함께 내려가요(비반전).',
      params: { vin: -10, rdiv: 4, gm1: 4, rd: 4 },
      causalStep: 3,
    },
  ],
  toggles: [['labels', '노드·전류 배지', true]],
  mistakes: {
    closed: [
      {
        title: '분배기 R1+R2 로딩을 빼고 계산',
        text: '개루프 이득을 $g_{m1}R_D$로만 계산하면 $R_1+R_2$로 흐르는 전류를 놓쳐요. 수업 기본값에서 실제 폐루프 이득은 $8/3\\approx 2.67$인데, 로딩을 무시하면 $16/5=3.20$으로 $+20\\%$ 과대평가해요.',
      },
      {
        title: '게이트를 입력 단자로 착각',
        text: 'CG 단에서 입력 $v_{\\text{in}}$은 소스로 들어가고, 게이트 $v_G$에는 분배기 귀환 전압만 들어와요. $v_{gs}=v_G-v_{\\text{in}}$이므로 소스가 오르면 $v_{gs}$가 줄어 비반전 이득이 돼요.',
      },
      {
        title: '폐루프 이득을 바로 1/K = 4로 근사',
        text: '$A_{v,\\text{closed}}\\approx 1/K=4$는 루프 이득 $KA_{v,\\text{open}}\\gg 1$일 때의 근사예요. 기본값에서는 $KA_{v,\\text{open}}=2$라서 $8/3\\approx 2.67$로 $4$와 큰 차이가 나요.',
      },
    ],
    open: [
      {
        title: '반송 복제가 입력저항을 바꾼다고 오해',
        text: '저주파에서 MOSFET 게이트 전류는 $0$이므로 반송 복제($R_1\\parallel R_2$)에 신호 전류가 흐르지 않아요. 그래서 $v_G=0$이고 $R_{\\text{in,open}}=1/g_{m1}$은 그대로 유지돼요.',
      },
      {
        title: '감지 복제의 남은 단자를 접지로 단락',
        text: '출력 쪽 감지 복제의 가운데 단자는 원래 전압 입력(게이트, 이상적 임피던스 $\\infty$)에 붙어 있었으므로 개방해야 $R_1+R_2$ 직렬 로딩이 남아요. 단락하면 $R_2$가 빠져 과대 로딩이 돼요.',
      },
      {
        title: '개루프에서도 vG가 따라 올라간다고 혼동',
        text: '루프를 끊은 개루프에서는 $v_G=0$으로 고정되므로 $v_{gs}=-v_{\\text{in}}$이 억제되지 않아요. 그래서 $i_{D1}$과 $v_{\\text{out,open}}$이 폐루프보다 $(1+KA_{v,\\text{open}})$배 크게 변해요.',
      },
    ],
  },
  evaluate(state, mna) {
    const modeKey = state.mode === 'open' ? 'open' : 'closed';
    const d = solveCgFeedback(modeKey, state.params, mna);
    if (!d.ok) {
      return {
        tiles: [{ label: '상태', val: '오류' }],
        diagnosis: { kind: 'bad', title: '회로 해석 오류', text: d.reason },
      };
    }

    const cStep = Number(state.causalStep) || 0;
    const isZero = Math.abs(d.vInMv) < 1e-6;
    const ratio = d.rdivK / d.rdK;
    const lightLoading = ratio >= 5;

    let tiles;
    let diagnosis;
    let equations;
    let summary;

    if (modeKey === 'closed') {
      tiles = [
        { label: '폐루프 이득 Av,closed', val: `${d.avClosed.toFixed(2)} V/V` },
        { label: '출력 전압 vout', val: fmtSignedMvShort(d.vOutMv) },
        { label: `로딩 무시 (+${d.noLoadErrPct.toFixed(1)}%)`, val: `${d.avNoLoadClosed.toFixed(2)} V/V` },
      ];

      if (isZero) {
        diagnosis = {
          kind: 'info',
          title: '소신호 영점 ($v_{\\text{in}} = 0\\ \\text{mV}$)',
          text: `입력 변동이 $0\\ \\text{mV}$라서 모든 노드 전압과 가지 전류가 $0$이에요. 이 동작점에서 소신호 폐루프 이득은 $A_{v,\\text{closed}}=${d.avClosed.toFixed(2)}$(로딩 무시 오답 $${d.avNoLoadClosed.toFixed(2)}$, $+${d.noLoadErrPct.toFixed(1)}\\%$)예요. ($\\lambda=0$ 선형 모델)`,
        };
      } else if (lightLoading) {
        diagnosis = {
          kind: 'ok',
          title: `가벼운 분배기 로딩 ($R_1+R_2 = ${ratio.toFixed(1)}\\,R_D$)`,
          text: `$R_1+R_2=${d.rdivK.toFixed(0)}\\ \\text{k}\\Omega$가 $R_D=${d.rdK.toFixed(1)}\\ \\text{k}\\Omega$보다 충분히 커서 로딩 무시 근사($${d.avNoLoadClosed.toFixed(2)}$)와의 오차가 $+${d.noLoadErrPct.toFixed(1)}\\%$로 작아요. ($\\lambda=0$ 선형 모델)`,
        };
      } else {
        diagnosis = {
          kind: 'warn',
          title: `분배기 로딩 영향 뚜렷 ($R_1+R_2 = ${ratio.toFixed(2)}\\,R_D$)`,
          text: `$R_1+R_2=${d.rdivK.toFixed(0)}\\ \\text{k}\\Omega$가 $R_D=${d.rdK.toFixed(1)}\\ \\text{k}\\Omega$와 비슷하거나 작아 $R_{\\text{out,open}}=${fmtOhmsTex(d.rOutOpenOhm)}$로 줄었어요. 로딩을 빼고 $g_{m1}R_D$로 계산하면 폐루프 이득을 $+${d.noLoadErrPct.toFixed(1)}\\%$ 과대평가해요. ($\\lambda=0$ 선형 모델)`,
        };
      }

      equations = [
        {
          name: '로딩 포함 폐루프 이득 (R1:R2 = 3:1, K = 0.25)',
          tex: `$$\\begin{aligned}R_{\\text{out,open}}&=R_D\\parallel(R_1+R_2)\\\\&=${(d.rOutOpenOhm / 1000).toFixed(2)}\\ \\text{k}\\Omega\\\\A_{v,\\text{open}}&=g_{m1}R_{\\text{out,open}}=${d.avOpen.toFixed(2)}\\\\A_{v,\\text{closed}}&=\\frac{A_{v,\\text{open}}}{1+KA_{v,\\text{open}}}\\\\&=\\frac{${d.avOpen.toFixed(2)}}{1+${d.loopGain.toFixed(2)}}=${d.avClosed.toFixed(2)}\\end{aligned}$$`,
        },
        {
          name: '로딩 무시 오답과 상대 오차',
          tex: `$$\\begin{aligned}A_{v,\\text{no-load}}&=\\frac{g_{m1}R_D}{1+Kg_{m1}R_D}\\\\&=${d.avNoLoadClosed.toFixed(2)}\\quad(+${d.noLoadErrPct.toFixed(1)}\\%)\\end{aligned}$$`,
        },
      ];

      if (isZero) {
        summary = '입력이 $0\\ \\text{mV}$일 때는 $v_{gs}=0$, $i_{D1}=0$, $v_{\\text{out}}=0$이에요. 슬라이더를 움직이거나 $+\\Delta v$ 인과 도미노 1–4박자를 눌러 보세요.';
      } else {
        const upDownIn = d.vInMv > 0 ? '올라가고' : '내려가고';
        const vgsDir = d.vGsMv < 0 ? '감소해' : '증가해';
        const outDir = d.vOutMv > 0 ? '상승하고' : '하강하고';
        const vgDir = d.vGMv > 0 ? '올라' : '내려가';
        summary = `$v_{\\text{in}}=${fmtMvTex(d.vInMv)}$만큼 소스가 ${upDownIn}, $v_{gs}=v_G-v_{\\text{in}}=${fmtMvTex(d.vGsMv)}$로 ${vgsDir} $i_{D1}=${fmtUaTex(d.iD1Ua)}$가 흘러요. 출력은 $v_{\\text{out}}=${fmtMvTex(d.vOutMv)}$로 ${outDir}, 분배기가 게이트를 $v_G=${fmtMvTex(d.vGMv)}$로 ${vgDir} $v_{gs}$ 변동을 $(1+KA_{v,\\text{open}})=${(1 + d.loopGain).toFixed(2)}$배 억제해요.`;
      }
    } else {
      tiles = [
        { label: '개루프 출력저항 Rout,open', val: fmtOhms(d.rOutOpenOhm) },
        { label: '개루프 이득 Av,open', val: `${d.avOpen.toFixed(2)} V/V` },
        { label: '개루프 출력 vout,open', val: fmtSignedMvShort(d.vOutMv) },
      ];

      if (isZero) {
        diagnosis = {
          kind: 'info',
          title: '개루프 소신호 영점 ($v_{\\text{in}} = 0\\ \\text{mV}$)',
          text: `반송 복제는 접지되어 있고 감지 복제는 가운데가 개방돼 $R_{\\text{out,open}}=${fmtOhmsTex(d.rOutOpenOhm)}$, $A_{v,\\text{open}}=${d.avOpen.toFixed(2)}$예요. ($\\lambda=0$ 선형 모델)`,
        };
      } else {
        diagnosis = {
          kind: lightLoading ? 'ok' : 'warn',
          title: lightLoading ? '복제 달린 개루프 (로딩 작음)' : '감지 복제 $R_1+R_2$ 병렬 로딩 반영됨',
          text: `게이트 전류가 $0$이라 반송 복제에서는 $v_G=0\\ \\text{mV}$가 유지되고, 출력 쪽 감지 복제 $R_1+R_2=${d.rdivK.toFixed(0)}\\ \\text{k}\\Omega$만 $R_D$와 병렬로 걸려 $R_{\\text{out,open}}=${fmtOhmsTex(d.rOutOpenOhm)}$·$A_{v,\\text{open}}=${d.avOpen.toFixed(2)}$가 돼요. ($\\lambda=0$ 선형 모델)`,
        };
      }

      equations = [
        {
          name: '복제 종단 후 개루프 이득·저항 (게이트 전류 0)',
          tex: `$$\\begin{aligned}R_{\\text{out,open}}&=R_D\\parallel(R_1+R_2)\\\\&=${(d.rOutOpenOhm / 1000).toFixed(2)}\\ \\text{k}\\Omega\\\\A_{v,\\text{open}}&=g_{m1}R_{\\text{out,open}}=${d.avOpen.toFixed(2)}\\\\R_{\\text{in,open}}&=\\frac{1}{g_{m1}}=${(1000 / d.gm1Ms).toFixed(0)}\\ \\Omega\\end{aligned}$$`,
        },
        {
          name: '폐루프 연결 시 예상 값 (K = 0.25)',
          tex: `$$\\begin{aligned}1+KA_{v,\\text{open}}&=${(1 + d.loopGain).toFixed(2)}\\\\A_{v,\\text{closed}}&=${d.avClosed.toFixed(2)}\\end{aligned}$$`,
        },
      ];

      if (isZero) {
        summary = '개루프에서도 입력이 $0\\ \\text{mV}$이면 모든 소신호 전류·전압이 $0$이에요. $v_{\\text{in}}$을 바꾸면 반송 복제($v_G=0$)와 감지 복제 분배 전류가 바로 드러나요.';
      } else {
        summary = `게이트가 $v_G=0.00\\ \\text{mV}$로 묶여 $v_{gs}=-v_{\\text{in}}=${fmtMvTex(d.vGsMv)}$가 그대로 걸리고 $i_{D1}=${fmtUaTex(d.iD1Ua)}$가 흘러요. 이 전류가 $R_D$($i_{R_D}=${fmtUaTex(d.iRdUa)}$)와 감지 복제($i_{\\text{div}}=${fmtUaTex(d.iDivUa)}$)로 나뉘어 $v_{\\text{out,open}}=${fmtMvTex(d.vOutMv)}$(개방 중간 단자 $${fmtMvTex(d.vSenseMidMv)}$)가 돼요.`;
      }
    }

    const nodes = {
      in: {
        badge: `vin ${fmtSignedMv(d.vInMv)}`,
        dir: dirFromVal(d.vInMv),
        hot: cStep === 1,
      },
      g: {
        badge: `vG ${fmtSignedMv(d.vGMv)}`,
        dir: modeKey === 'closed' ? dirFromVal(d.vGMv) : undefined,
        hot: modeKey === 'closed' ? (cStep === 2 || cStep === 4) : (cStep === 2),
        dim: modeKey === 'open' && cStep === 4,
      },
      out: {
        badge: `vout ${fmtSignedMv(d.vOutMv)}`,
        dir: dirFromVal(d.vOutMv),
        hot: cStep === 4,
      },
    };
    if (modeKey === 'open') {
      nodes.sense_mid = {
        badge: `개방 ${fmtSignedMv(d.vSenseMidMv)}`,
        dir: dirFromVal(d.vSenseMidMv),
        hot: cStep === 4,
      };
    }

    const branches = {
      i_D1: {
        badge: `iD1 ${fmtSignedUa(d.iD1Ua)}`,
        dir: d.iD1Ua >= 0 ? 'fwd' : 'rev',
        hot: cStep === 3,
      },
      i_RD: {
        badge: `iRD ${fmtSignedUa(d.iRdUa)}`,
        dir: d.iRdUa >= 0 ? 'fwd' : 'rev',
        hot: cStep === 3 || cStep === 4,
      },
      i_div: {
        badge: `idiv ${fmtSignedUa(d.iDivUa)}`,
        dir: d.iDivUa >= 0 ? 'fwd' : 'rev',
        hot: cStep === 3 || cStep === 4,
      },
    };

    return {
      tiles,
      diagnosis,
      equations,
      summary,
      nodes,
      branches,
    };
  },
};

module.exports = spec;
