// Interactive Lab 03 (1120): Example II CG+CS TIA RF Loading & Feedback Sign K = -1/RF
// Archetype: approx — compares exact full-loading open-loop |R0| and exact MNA closed-loop
// against toggled RF loading approximations (rf-in, rf-out) across RF = 1..100 kΩ,
// and verifies K = IF / V1 = -1/RF < 0 in the sense-return test circuit.

const SVG_NS_ATTR = 'xmlns="http://www.w3.org/2000/svg"';

function sub(base, s) {
  return `${base}<tspan baseline-shift="sub" font-size="78%">${s}</tspan>`;
}

function gndSym(x, y, cls = 'fig-ink') {
  return [
    '<g class="sym" data-symbol="gnd">',
    `  <line class="${cls}" x1="${x}" y1="${y}" x2="${x}" y2="${y + 6}"/>`,
    `  <line class="${cls}" x1="${x - 10}" y1="${y + 6}" x2="${x + 10}" y2="${y + 6}"/>`,
    `  <line class="${cls}" x1="${x - 6}" y1="${y + 11}" x2="${x + 6}" y2="${y + 11}"/>`,
    `  <line class="${cls}" x1="${x - 2.5}" y1="${y + 16}" x2="${x + 2.5}" y2="${y + 16}"/>`,
    '</g>',
  ].join('');
}

function vRes(x, yTop, yBot, cls = 'fig-ink') {
  const mid = (yTop + yBot) / 2;
  const zTop = mid - 24;
  const d = `M${x} ${zTop}l6 4-12 8 12 8-12 8 12 8-12 8 6 4`;
  return [
    `<line class="${cls}" x1="${x}" y1="${yTop}" x2="${x}" y2="${zTop}"/>`,
    `<g class="sym" data-symbol="resistor"><path class="${cls}" d="${d}"/></g>`,
    `<line class="${cls}" x1="${x}" y1="${zTop + 48}" x2="${x}" y2="${yBot}"/>`,
  ].join('');
}

function hRes(xLeft, xRight, y, cls = 'fig-ink') {
  const mid = (xLeft + xRight) / 2;
  const zLeft = mid - 24;
  const d = `M${zLeft} ${y}l4-6 8 12 8-12 8 12 8-12 8 12 4-6`;
  return [
    `<line class="${cls}" x1="${xLeft}" y1="${y}" x2="${zLeft}" y2="${y}"/>`,
    `<g class="sym" data-symbol="resistor"><path class="${cls}" d="${d}"/></g>`,
    `<line class="${cls}" x1="${zLeft + 48}" y1="${y}" x2="${xRight}" y2="${y}"/>`,
  ].join('');
}

function buildLoadingSvg() {
  const parts = [
    `<svg viewBox="0 0 700 302" style="max-height:216px" ${SVG_NS_ATTR} role="img" aria-label="예제 II CG+CS 트랜스임피던스 증폭기와 입출력 RF 로딩 복제 회로도">`,
    // V_DD AC ground bars & RD1, RD2
    '<g class="sym" data-symbol="vdd"><path class="fig-ink" d="M154 38h24M410 38h24"/></g>',
    `<text class="fig-text fig-math" x="166" y="20" text-anchor="middle" font-size="13">${sub('V', 'DD')}</text>`,
    `<text class="fig-text fig-math" x="422" y="20" text-anchor="middle" font-size="13">${sub('V', 'DD')} (AC 접지)</text>`,
    vRes(166, 38, 94),
    `<text class="fig-text fig-math" x="142" y="70" text-anchor="end" font-size="14">${sub('R', 'D1')}</text>`,
    vRes(422, 38, 94),
    `<text class="fig-text fig-math" x="398" y="70" text-anchor="end" font-size="14">${sub('R', 'D2')}</text>`,

    // M1 drain/source vertical wires & node X -> M2 gate
    '<line class="fig-ink" x1="166" y1="94" x2="166" y2="138"/>',
    '<line class="fig-ink" x1="166" y1="170" x2="166" y2="218"/>',
    '<path class="fig-ink" d="M166 94h216v48h10"/>',
    '<circle class="fig-dot" cx="166" cy="94" r="4" data-node="x" data-node-color="red"/>',
    '<text class="fig-text fig-math" x="142" y="99" text-anchor="end" font-size="14" data-node="x" data-node-color="red">X</text>',

    // M1 CG NMOS (drain y=138, gate y=154, source y=170)
    '<g class="sym" data-symbol="nmos">',
    '  <path class="fig-ink" d="M166 138h14M180 170h-14"/>',
    '  <path class="fig-ink" d="M180 132v44M187 136v36M175 166l-6 4 6 4"/>',
    '</g>',
    `<text class="fig-text fig-math" x="142" y="158" text-anchor="end" font-size="14">${sub('M', '1')}</text>`,
    '<line class="fig-ink" x1="187" y1="154" x2="222" y2="154"/>',
    '<line class="fig-ink" x1="222" y1="154" x2="222" y2="160"/>',
    gndSym(222, 160),
    `<text class="fig-text fig-math" x="238" y="158" text-anchor="start" font-size="13">${sub('V', 'b')} (0 V)</text>`,

    // Input current source I_in -> s1
    '<line class="fig-ink" x1="166" y1="218" x2="72" y2="218"/>',
    '<line class="fig-ink" x1="72" y1="218" x2="72" y2="232"/>',
    '<g class="sym" data-symbol="isrc">',
    '  <circle class="fig-ink" cx="72" cy="246" r="14"/>',
    '  <path class="fig-ink" d="M72 254v-16M67 243l5-5 5 5"/>',
    '</g>',
    '<line class="fig-ink" x1="72" y1="260" x2="72" y2="272"/>',
    gndSym(72, 272),
    `<text class="fig-text fig-math" x="44" y="250" text-anchor="end" font-size="14">${sub('I', 'in')}</text>`,
    '<circle class="fig-dot" cx="166" cy="218" r="4" data-node="s1" data-node-color="blue"/>',
    `<text class="fig-text fig-math" x="118" y="200" text-anchor="middle" font-size="14" data-node="s1" data-node-color="blue">${sub('v', 's1')}</text>`,

    // M2 CS NMOS (gate y=142, drain y=126 -> 94, source y=158 -> 182 GND)
    '<g class="sym" data-symbol="nmos">',
    '  <path class="fig-ink" d="M392 142h7M399 122v40M406 120v44M406 126h16M406 158h16M416 154l6 4-6 4"/>',
    '</g>',
    '<line class="fig-ink" x1="422" y1="126" x2="422" y2="94"/>',
    '<line class="fig-ink" x1="422" y1="158" x2="422" y2="182"/>',
    gndSym(422, 182),
    `<text class="fig-text fig-math" x="444" y="146" text-anchor="start" font-size="14">${sub('M', '2')}</text>`,

    // Output rail
    '<line class="fig-ink" x1="422" y1="94" x2="616" y2="94"/>',
    '<circle class="fig-dot" cx="422" cy="94" r="4" data-node="out" data-node-color="red"/>',
    '<circle class="fig-dot" cx="536" cy="94" r="4" data-node="out" data-node-color="red"/>',
    '<circle class="fig-dot" cx="616" cy="94" r="4" data-node="out" data-node-color="red"/>',
    `<text class="fig-text fig-math" x="632" y="99" text-anchor="start" font-size="14" data-node="out" data-node-color="red">${sub('v', 'out')}</text>`,

    // Toggleable Element 1: rf-in (return duplicate RF on s1 -> GND)
    '<g data-elem="rf-in">',
    '  <ellipse cx="264" cy="222" rx="76" ry="34" fill="transparent" stroke="none"/>',
    '  <g data-branch="rin_branch">',
    '    <line class="fig-accent" x1="170" y1="218" x2="228" y2="218"/>',
    '    ' + hRes(228, 296, 218, 'fig-accent'),
    '    <path class="fig-accent" d="M296 218h22v18"/>',
    '    ' + gndSym(318, 236, 'fig-accent'),
    '  </g>',
    `  <text class="fig-text fig-math" x="262" y="198" text-anchor="middle" font-size="13">${sub('R', 'F')} (입력 복제)</text>`,
    '</g>',

    // Toggleable Element 2: rf-out (sense duplicate RF on out -> GND)
    '<g data-elem="rf-out">',
    '  <ellipse cx="556" cy="172" rx="78" ry="76" fill="transparent" stroke="none"/>',
    '  <g data-branch="rout_branch">',
    '    <line class="fig-accent" x1="536" y1="98" x2="536" y2="136"/>',
    '    ' + vRes(536, 136, 196, 'fig-accent'),
    '    <line class="fig-accent" x1="536" y1="196" x2="536" y2="226"/>',
    '    ' + gndSym(536, 226, 'fig-accent'),
    '  </g>',
    `  <text class="fig-text fig-math" x="560" y="170" text-anchor="start" font-size="13">${sub('R', 'F')} (출력 복제)</text>`,
    '</g>',

    // Static badge slots (well clear of all wires & symbols)
    '<g data-badges>',
    '  <g data-badge-for="x" transform="translate(274, 62)"></g>',
    '  <g data-badge-for="out" transform="translate(536, 62)"></g>',
    '  <g data-badge-for="s1" transform="translate(198, 276)"></g>',
    '  <g data-badge-for="rin_branch" transform="translate(362, 276)"></g>',
    '  <g data-badge-for="rout_branch" transform="translate(556, 276)"></g>',
    '</g>',
    '</svg>',
  ];
  return parts.join('\n');
}

function buildSignSvg() {
  const parts = [
    `<svg viewBox="0 0 640 320" ${SVG_NS_ATTR} role="img" aria-label="V-C 귀환율 K 측정 회로: 왼쪽 감지 포트에 V1을 걸고 오른쪽 반송 포트를 단락한 채 K로 들어가는 기준 전류 IF를 잰다">`,
    '<style>',
    '  [data-branch="i_actual"] .rev-only { display: none; }',
    '  [data-branch="i_actual"][data-dir="rev"] .fwd-only { display: none; }',
    '  [data-branch="i_actual"][data-dir="rev"] .rev-only { display: inline; }',
    '  [data-branch="i_actual"].is-dim .fwd-only, [data-branch="i_actual"].is-dim .rev-only { display: none; }',
    '</style>',

    // Step 1: Left sense port voltage source V1
    '<g data-causal-step="1">',
    '  <line class="fig-ink" x1="110" y1="110" x2="110" y2="160"/>',
    '  <g class="sym" data-symbol="vsrc">',
    '    <circle class="fig-ink" cx="110" cy="178" r="18"/>',
    '    <path class="fig-ink" d="M105 171h10M110 166v10M105 186h10"/>',
    '  </g>',
    '  <line class="fig-ink" x1="110" y1="196" x2="110" y2="248"/>',
    '  ' + gndSym(110, 248),
    '  <circle class="fig-dot" cx="110" cy="110" r="4" data-node="sense" data-node-color="blue"/>',
    `  <text class="fig-text fig-math" x="76" y="182" text-anchor="end" font-size="14" data-node="sense" data-node-color="blue">${sub('V', '1')}</text>`,
    '  <text class="fig-text fig-math" x="144" y="164" font-size="14" data-node="sense" data-node-color="blue">+</text>',
    '  <text class="fig-text fig-math" x="144" y="198" font-size="14" data-node="sense" data-node-color="blue">−</text>',
    '  <text class="fig-muted" x="110" y="294" text-anchor="middle">감지 포트 (원래 Vout)</text>',
    '</g>',

    // Top feedback resistor RF & right-side shorted return port
    hRes(110, 420, 110),
    `<text class="fig-text fig-math" x="265" y="82" text-anchor="middle" font-size="14">${sub('R', 'F')}</text>`,
    '<path class="fig-ink" d="M420 110h80v138"/>',
    gndSym(500, 248),
    '<circle class="fig-dot" cx="500" cy="110" r="4" data-node="ret" data-node-color="red"/>',
    '<text class="fig-muted" x="500" y="294" text-anchor="middle">반송 포트 (단락선)</text>',

    // Step 2: Physical current arrow (parallel below RF)
    '<g data-branch="i_actual" data-causal-step="2">',
    '  <line class="fig-ink" x1="200" y1="160" x2="330" y2="160"/>',
    '  <path class="fig-ink fwd-only" d="M320 154l12 6-12 6"/>',
    '  <path class="fig-ink rev-only" d="M210 154l-12 6 12 6"/>',
    '  <text class="fig-text" x="265" y="188" text-anchor="middle" font-size="13">실제 전류</text>',
    '</g>',

    // Step 3: Defined feedback return current IF arrow (entering RF from right short)
    '<g data-branch="i_f_ref" data-causal-step="3">',
    '  <path class="fig-accent" d="M476 110H392M404 103l-12 7 12 7"/>',
    `  <text class="fig-text fig-math" x="434" y="82" text-anchor="middle" font-size="13">기준 ${sub('I', 'F')} (K로 진입)</text>`,
    '</g>',

    // Static badge slots
    '<g data-badges>',
    '  <g data-badge-for="sense" transform="translate(110, 44)"></g>',
    '  <g data-badge-for="i_f_ref" transform="translate(434, 44)"></g>',
    '  <g data-badge-for="i_actual" transform="translate(265, 224)"></g>',
    '  <g data-badge-for="ret" transform="translate(560, 178)"></g>',
    '</g>',
    '</svg>',
  ];
  return parts.join('\n');
}

function fmtKOhmParam(v) {
  const num = Number(v);
  if (num >= 10) return `${num.toFixed(1).replace(/\.0$/, '')} kΩ`;
  return `${num.toFixed(2).replace(/\.?0+$/, '')} kΩ`;
}

function fmtKOhmTex(v) {
  const num = Number(v);
  const s = num >= 10 ? num.toFixed(1).replace(/\.0$/, '') : num.toFixed(2).replace(/\.?0+$/, '');
  return `${s}\\ \\text{k}\\Omega`;
}

function fmtSignedUaParam(v) {
  const num = Number(v);
  if (Math.abs(num) < 1e-6) return '0 μA';
  const sign = num > 0 ? '+' : '−';
  return `${sign}${Math.abs(num).toFixed(1).replace(/\.0$/, '')} μA`;
}

function fmtSignedVParam(v) {
  const num = Number(v);
  if (Math.abs(num) < 1e-6) return '0.0 V';
  const sign = num > 0 ? '+' : '−';
  return `${sign}${Math.abs(num).toFixed(1)} V`;
}

function fmtSignedVoltageFromMv(mv) {
  if (Math.abs(mv) < 1e-5) return '0.00 mV';
  const sign = mv > 0 ? '+' : '−';
  const abs = Math.abs(mv);
  if (abs >= 1000) return `${sign}${(abs / 1000).toFixed(2)} V`;
  if (abs < 1) return `${sign}${(abs * 1000).toFixed(1)} μV`;
  return `${sign}${abs.toFixed(2)} mV`;
}

function fmtOhmsUnsigned(ohm) {
  const abs = Math.abs(ohm);
  if (abs >= 1000) return `${(abs / 1000).toFixed(2)} kΩ`;
  if (abs >= 200) return `${abs.toFixed(1)} Ω`;
  return `${abs.toFixed(2)} Ω`;
}

function fmtOhmsSigned(ohm) {
  if (Math.abs(ohm) < 1e-6) return '0.00 Ω';
  const sign = ohm > 0 ? '+' : '−';
  return `${sign}${fmtOhmsUnsigned(ohm)}`;
}

function fmtOhmsSignedTex(ohm) {
  if (Math.abs(ohm) < 1e-6) return '0.00\\ \\Omega';
  const sign = ohm > 0 ? '+' : '-';
  const abs = Math.abs(ohm);
  if (abs >= 1000) return `${sign}${(abs / 1000).toFixed(2)}\\ \\text{k}\\Omega`;
  if (abs >= 200) return `${sign}${abs.toFixed(1)}\\ \\Omega`;
  return `${sign}${abs.toFixed(2)}\\ \\Omega`;
}

function fmtOhmsUnsignedTex(ohm) {
  const abs = Math.abs(ohm);
  if (abs >= 1000) return `${(abs / 1000).toFixed(2)}\\ \\text{k}\\Omega`;
  if (abs >= 200) return `${abs.toFixed(1)}\\ \\Omega`;
  return `${abs.toFixed(2)}\\ \\Omega`;
}

function fmtSignedMs(ms) {
  if (Math.abs(ms) < 1e-6) return '0.000 mS';
  const sign = ms > 0 ? '+' : '−';
  return `${sign}${Math.abs(ms).toFixed(3)} mS`;
}

function fmtSignedMa(ma) {
  if (Math.abs(ma) < 1e-6) return '0.000 mA';
  const sign = ma > 0 ? '+' : '−';
  const abs = Math.abs(ma);
  if (abs < 0.01) return `${sign}${(abs * 1000).toFixed(1)} μA`;
  return `${sign}${abs.toFixed(3)} mA`;
}

function fmtSignedMaTex(ma) {
  if (Math.abs(ma) < 1e-6) return '0.000\\ \\text{mA}';
  const sign = ma > 0 ? '+' : '-';
  const abs = Math.abs(ma);
  if (abs < 0.01) return `${sign}${(abs * 1000).toFixed(1)}\\ \\mu\\text{A}`;
  return `${sign}${abs.toFixed(3)}\\ \\text{mA}`;
}

function fmtAbsMa(ma) {
  const abs = Math.abs(ma);
  if (abs < 1e-6) return '0.000 mA';
  if (abs < 0.01) return `${(abs * 1000).toFixed(1)} μA`;
  return `${abs.toFixed(3)} mA`;
}

function dirFromVal(val) {
  if (val > 1e-6) return 'up';
  if (val < -1e-6) return 'down';
  return undefined;
}

function buildOpenElements(gm1S, gm2S, rd1Ohm, rd2Ohm, rfOhm, rfInOn, rfOutOn, iInA) {
  return [
    { id: 'iin', type: 'isrc', n1: '0', n2: 's1', value: iInA },
    { id: 'm1', type: 'vccs', n1: 'x', n2: 's1', cp: '0', cn: 's1', gm: gm1S },
    { id: 'rd1', type: 'R', n1: 'x', n2: '0', value: rd1Ohm },
    { id: 'm2', type: 'vccs', n1: 'out', n2: '0', cp: 'x', cn: '0', gm: gm2S },
    { id: 'rd2', type: 'R', n1: 'out', n2: '0', value: rd2Ohm },
    rfInOn
      ? { id: 'rf_in', type: 'R', n1: 's1', n2: '0', value: rfOhm }
      : { id: 'rf_in', type: 'open', n1: 's1', n2: '0' },
    rfOutOn
      ? { id: 'rf_out', type: 'R', n1: 'out', n2: '0', value: rfOhm }
      : { id: 'rf_out', type: 'open', n1: 'out', n2: '0' },
  ];
}

function solveKNetwork(rfOhm, v1V, mna) {
  return mna.solveCircuit({
    elements: [
      { id: 'v1', type: 'vsrc', n1: 'sense', n2: '0', value: v1V },
      { id: 'rf', type: 'R', n1: 'sense', n2: 'ret', value: rfOhm },
      { id: 'short_ret', type: 'short', n1: 'ret', n2: '0' },
    ],
  });
}

function solveLoadingModel(params, rfInOn, rfOutOn, mna) {
  const rfK = Number(params.rf);
  const rfOhm = rfK * 1000;
  const gm1Ms = Number(params.gm1);
  const gm2Ms = Number(params.gm2);
  const gm1S = gm1Ms * 1e-3;
  const gm2S = gm2Ms * 1e-3;
  const rd1Ohm = Number(params.rd1) * 1000;
  const rd2Ohm = Number(params.rd2) * 1000;
  const iinUa = Number(params.iin);
  const iinA = iinUa * 1e-6;

  // 1. Toggled open-loop circuit (actual signal + 1 A unit gain)
  const openOp = mna.solveCircuit({
    elements: buildOpenElements(gm1S, gm2S, rd1Ohm, rd2Ohm, rfOhm, rfInOn, rfOutOn, iinA),
  });
  const openUnit = mna.solveCircuit({
    elements: buildOpenElements(gm1S, gm2S, rd1Ohm, rd2Ohm, rfOhm, rfInOn, rfOutOn, 1.0),
  });
  // 2. Reference full-loading open-loop & ideal no-loading open-loop (1 A unit gain)
  const fullOpenUnit = mna.solveCircuit({
    elements: buildOpenElements(gm1S, gm2S, rd1Ohm, rd2Ohm, rfOhm, true, true, 1.0),
  });
  const idealOpenUnit = mna.solveCircuit({
    elements: buildOpenElements(gm1S, gm2S, rd1Ohm, rd2Ohm, rfOhm, false, false, 1.0),
  });

  // 3. Open-loop input and output impedances
  const rinOpenTest = mna.solveCircuit({
    elements: buildOpenElements(gm1S, gm2S, rd1Ohm, rd2Ohm, rfOhm, rfInOn, rfOutOn, 1.0),
  });
  const routOpenTest = mna.solveCircuit({
    elements: [
      ...buildOpenElements(gm1S, gm2S, rd1Ohm, rd2Ohm, rfOhm, rfInOn, rfOutOn, 0),
      { id: 'it_out', type: 'isrc', n1: '0', n2: 'out', value: 1.0 },
    ],
  });

  // 4. Exact full closed-loop MNA (single RF resistor connecting out <-> s1)
  const makeClosedEls = (iVal) => [
    { id: 'iin', type: 'isrc', n1: '0', n2: 's1', value: iVal },
    { id: 'm1', type: 'vccs', n1: 'x', n2: 's1', cp: '0', cn: 's1', gm: gm1S },
    { id: 'rd1', type: 'R', n1: 'x', n2: '0', value: rd1Ohm },
    { id: 'm2', type: 'vccs', n1: 'out', n2: '0', cp: 'x', cn: '0', gm: gm2S },
    { id: 'rd2', type: 'R', n1: 'out', n2: '0', value: rd2Ohm },
    { id: 'rf', type: 'R', n1: 'out', n2: 's1', value: rfOhm },
  ];
  const exactClosedUnit = mna.solveCircuit({ elements: makeClosedEls(1.0) });
  const exactClosedRoutTest = mna.solveCircuit({
    elements: [
      ...makeClosedEls(0),
      { id: 'it_out', type: 'isrc', n1: '0', n2: 'out', value: 1.0 },
    ],
  });

  // 5. Feedback factor K = I_F / V1 = -1 / RF
  const kUnit = solveKNetwork(rfOhm, 1.0, mna);

  const allSolved = [openOp, openUnit, fullOpenUnit, idealOpenUnit, rinOpenTest, routOpenTest, exactClosedUnit, exactClosedRoutTest, kUnit];
  if (allSolved.some((s) => !s.ok)) {
    return { ok: false, reason: '회로 해석 중 특이 행렬이 발생했어요.' };
  }

  const r0ToggledOhm = openUnit.nodes.out.re;
  const r0FullOhm = fullOpenUnit.nodes.out.re;
  const r0IdealOhm = idealOpenUnit.nodes.out.re;
  const rInOpenOhm = rinOpenTest.nodes.s1.re;
  const rOutOpenOhm = routOpenTest.nodes.out.re;
  const rClosedExactOhm = exactClosedUnit.nodes.out.re;
  const rInClosedExactOhm = exactClosedUnit.nodes.s1.re;
  const rOutClosedExactOhm = exactClosedRoutTest.nodes.out.re;

  const kFactorS = -kUnit.branches.rf.re;
  const loopGain = kFactorS * r0ToggledOhm;
  const denom = 1 + loopGain;
  const rClosed2PortOhm = r0ToggledOhm / denom;
  const rInClosed2PortOhm = rInOpenOhm / denom;
  const rOutClosed2PortOhm = rOutOpenOhm / denom;

  const openLoopErrPct = (Math.abs(Math.abs(r0ToggledOhm) - Math.abs(r0FullOhm)) / Math.max(Math.abs(r0FullOhm), 1e-12)) * 100;
  const noLoadOpenErrPct = (Math.abs(Math.abs(r0IdealOhm) - Math.abs(r0FullOhm)) / Math.max(Math.abs(r0FullOhm), 1e-12)) * 100;
  const feedthroughErrPct = (Math.abs(rClosed2PortOhm - rClosedExactOhm) / Math.max(Math.abs(rClosedExactOhm), 1e-12)) * 100;

  // Sweep RF = 1..100 kΩ (41 log-spaced points) for synced plot
  const exactCurve = [];
  const approxCurve = [];
  for (let i = 0; i <= 40; i++) {
    const sweepRfK = Math.pow(100, i / 40);
    const sweepRfOhm = sweepRfK * 1000;
    const fRes = mna.solveCircuit({ elements: buildOpenElements(gm1S, gm2S, rd1Ohm, rd2Ohm, sweepRfOhm, true, true, 1.0) });
    const aRes = mna.solveCircuit({ elements: buildOpenElements(gm1S, gm2S, rd1Ohm, rd2Ohm, sweepRfOhm, rfInOn, rfOutOn, 1.0) });
    if (!fRes.ok || !aRes.ok) return { ok: false, reason: '그래프 스윕 계산 중 특이 행렬이 발생했어요.' };
    exactCurve.push([sweepRfK, Math.abs(fRes.nodes.out.re) / 1000]);
    approxCurve.push([sweepRfK, Math.abs(aRes.nodes.out.re) / 1000]);
  }

  return {
    ok: true,
    rfK,
    rfOhm,
    gm1Ms,
    gm2Ms,
    rd1K: Number(params.rd1),
    rd2K: Number(params.rd2),
    iinUa,
    vS1Mv: openOp.nodes.s1.re * 1000,
    vXMv: openOp.nodes.x.re * 1000,
    vOutMv: openOp.nodes.out.re * 1000,
    r0ToggledOhm,
    r0FullOhm,
    r0IdealOhm,
    rInOpenOhm,
    rOutOpenOhm,
    kFactorS,
    loopGain,
    denom,
    rClosed2PortOhm,
    rInClosed2PortOhm,
    rOutClosed2PortOhm,
    rClosedExactOhm,
    rInClosedExactOhm,
    rOutClosedExactOhm,
    openLoopErrPct,
    noLoadOpenErrPct,
    feedthroughErrPct,
    exactCurve,
    approxCurve,
  };
}

const spec = {
  id: 'cg-cs-rf-loading-and-sign',
  title: 'CG+CS 귀환 RF 로딩과 반송 부호',
  archetype: 'approx',
  modes: [
    {
      key: 'loading',
      label: '로딩·근사',
      svg: buildLoadingSvg(),
      ariaLabel: '예제 II CG+CS 트랜스임피던스 증폭기와 입출력 RF 로딩 복제 회로도',
      elems: [
        { id: 'rf-in', label: '입력 반송 복제 RF (1/gm1 ∥ RF)' },
        { id: 'rf-out', label: '출력 감지 복제 RF (RD2 ∥ RF)' },
      ],
      presets: [
        { id: 'default-load', label: '수업 기본 (양쪽 ON)', params: { rf: 10, gm1: 10, gm2: 10, rd1: 5, rd2: 2, iin: 1 }, disabledElems: [] },
        { id: 'no-rf-out', label: '출력 복제 OFF', params: { rf: 10, gm1: 10, gm2: 10, rd1: 5, rd2: 2, iin: 1 }, disabledElems: ['rf-out'] },
        { id: 'ideal-noload', label: '이상적 무로딩 (둘 다 OFF)', params: { rf: 10, gm1: 10, gm2: 10, rd1: 5, rd2: 2, iin: 1 }, disabledElems: ['rf-in', 'rf-out'] },
        { id: 'heavy-collapse', label: '강한 로딩 붕괴 (RF 1 kΩ)', params: { rf: 1, gm1: 10, gm2: 10, rd1: 5, rd2: 2, iin: 1 }, disabledElems: ['rf-in', 'rf-out'] },
        { id: 'light-valid', label: '큰 RF 허용 (RF 100 kΩ)', params: { rf: 100, gm1: 10, gm2: 10, rd1: 5, rd2: 2, iin: 1 }, disabledElems: ['rf-in', 'rf-out'] },
        { id: 'weak-feedthrough', label: '피드스루 한계 (2포트 vs MNA)', params: { rf: 1, gm1: 2, gm2: 2, rd1: 1, rd2: 0.5, iin: 1 }, disabledElems: [] },
      ],
    },
    {
      key: 'sign',
      label: '반송 부호 K',
      svg: buildSignSvg(),
      ariaLabel: 'V-C 귀환율 K = -1/RF 부호 측정 회로도',
      causalSteps: [
        { id: 1, label: '감지 포트에 +ΔV1 인가', detail: '출력 전압 자리(감지 포트)에 시험 전압원 V1을 걸어요.' },
        { id: 2, label: '실제 전류 V1 → RF → 단락선', detail: 'V1 > 0이면 실제 전류 V1/RF가 RF를 지나 오른쪽 단락선으로 흘러가요.' },
        { id: 3, label: '기준 IF 반대 → K = −1/RF', detail: '단락선에서 RF로 들어가는 방향이 양이라 IF = −V1/RF, K = −1/RF < 0이 돼요.' },
      ],
      presets: [
        { id: 'sign-pos', label: '기본 시험 (+1 V, 10 kΩ)', params: { v1: 1, rf: 10 }, causalStep: 3 },
        { id: 'sign-neg', label: '음의 시험 (−1 V, 10 kΩ)', params: { v1: -1, rf: 10 }, causalStep: 3 },
        { id: 'sign-small-rf', label: '작은 RF (+1 V, 1 kΩ)', params: { v1: 1, rf: 1 }, causalStep: 3 },
        { id: 'sign-zero', label: '영 입력 (V1 = 0 V)', params: { v1: 0, rf: 10 }, causalStep: 0 },
      ],
    },
  ],
  predict: {
    prompt: '예제 II(기본값: $R_{D2}=2\\ \\text{k}\\Omega$, $1/g_{m1}=100\\ \\Omega$, $R_F=10\\ \\text{k}\\Omega$)에서 $R_F$ 로딩은 어느 쪽에서 더 크게 나타날까요?',
    options: [
      { id: 'out', label: '출력 쪽 감지 복제 (RD2 ∥ RF)' },
      { id: 'in', label: '입력 쪽 반송 복제 (1/gm1 ∥ RF)' },
      { id: 'same', label: '양쪽 복제의 비율 감소가 같다' },
    ],
    answerId: 'out',
    explain: '$R_F=10\\ \\text{k}\\Omega$은 입력 $1/g_{m1}=100\\ \\Omega$의 $100$배($1\\%$ 감소)이지만, 출력 $R_{D2}=2\\ \\text{k}\\Omega$의 $5$배뿐이라 출력 부하가 $16.7\\%$($2\\ \\text{k}\\Omega \\to 1.67\\ \\text{k}\\Omega$) 줄어들어요.',
  },
  params: [
    { key: 'rf', label: '귀환 저항 RF', min: 1, max: 100, scale: 'log', unit: 'kΩ', def: 10, format: fmtKOhmParam },
    { key: 'gm1', label: 'CG gm1', min: 2, max: 20, step: 0.5, unit: 'mS', def: 10, mode: 'loading' },
    { key: 'gm2', label: 'CS gm2', min: 2, max: 20, step: 0.5, unit: 'mS', def: 10, mode: 'loading' },
    { key: 'rd1', label: '첫 단 RD1', min: 1, max: 10, step: 0.5, unit: 'kΩ', def: 5, mode: 'loading' },
    { key: 'rd2', label: '둘째 단 RD2', min: 0.5, max: 5, step: 0.5, unit: 'kΩ', def: 2, mode: 'loading' },
    { key: 'iin', label: '입력 전류 Iin', min: -5, max: 5, step: 0.5, unit: 'μA', def: 1, mode: 'loading', format: fmtSignedUaParam },
    { key: 'v1', label: '시험 전압 V1', min: -2, max: 2, step: 0.2, unit: 'V', def: 1, mode: 'sign', format: fmtSignedVParam },
  ],
  toggles: [['labels', '노드 배지', true]],
  steps: [
    {
      mode: 'loading',
      title: '수업 기본: 양쪽 RF 로딩 반영',
      who: 'R0 = −82.51 kΩ · 폐루프 −8.92 kΩ',
      params: { rf: 10, gm1: 10, gm2: 10, rd1: 5, rd2: 2, iin: 1 },
      disabledElems: [],
      text: 'RF = 10 kΩ일 때 입력(100 Ω ∥ 10 kΩ = 99.01 Ω)과 출력(2 kΩ ∥ 10 kΩ = 1.67 kΩ) 로딩을 모두 넣으면 R0 = −82.51 kΩ, 1+KR0 = 9.25로 2포트 폐루프(−8.92 kΩ)가 정확 MNA(−8.92 kΩ)와 일치해요.',
    },
    {
      mode: 'loading',
      title: '출력 복제만 끄면 (rf-out OFF)',
      who: 'RD2 ∥ RF 생략 → 개루프 오차 +20.0%',
      params: { rf: 10, gm1: 10, gm2: 10, rd1: 5, rd2: 2, iin: 1 },
      disabledElems: ['rf-out'],
      text: '회로도의 출력 복제 RF를 클릭해 끄면 출력 부하가 1.67 kΩ 대신 2.00 kΩ으로 남아 |R0|가 99.01 kΩ로 커져요. 실제 로딩 개루프(82.51 kΩ) 대비 +20.0% 오차로 10% 기준을 넘겨 근사가 붕괴해요.',
    },
    {
      mode: 'loading',
      title: '이상적 무로딩 근사 (둘 다 OFF)',
      who: 'R0,ideal = −100.00 kΩ · 오차 +21.2%',
      params: { rf: 10, gm1: 10, gm2: 10, rd1: 5, rd2: 2, iin: 1 },
      disabledElems: ['rf-in', 'rf-out'],
      text: '양쪽 복제를 모두 끄면 이상적 개루프 −100.00 kΩ이 되어 실제 로딩 개루프(−82.51 kΩ) 대비 +21.2% 과대평가해요. 입력(1%)보다 출력(16.7%) 감소가 훨씬 커서 RF ≫ RD2 확인이 핵심이에요.',
    },
    {
      mode: 'loading',
      title: '강한 로딩 붕괴 (RF = 1 kΩ)',
      who: 'R0 = −30.30 kΩ · 무로딩 오차 +230.0%',
      params: { rf: 1, gm1: 10, gm2: 10, rd1: 5, rd2: 2, iin: 1 },
      disabledElems: ['rf-in', 'rf-out'],
      text: 'RF = 1 kΩ은 RD2(2 kΩ)의 절반이라 실제 |R0|가 30.30 kΩ까지 줄어요. 이때 무로딩 근사(100.00 kΩ)를 그대로 쓰면 실제 대비 +230.0% 오차로 크게 빗나가요.',
    },
    {
      mode: 'loading',
      title: '큰 RF에서 무로딩 성립 (RF = 100 kΩ)',
      who: 'R0 = −97.94 kΩ · 오차 +2.1%',
      params: { rf: 100, gm1: 10, gm2: 10, rd1: 5, rd2: 2, iin: 1 },
      disabledElems: ['rf-in', 'rf-out'],
      text: 'RF = 100 kΩ이면 1/gm1(100 Ω)의 1000배, RD2(2 kΩ)의 50배라서 실제 |R0|(97.94 kΩ)와 무로딩 근사(100.00 kΩ) 차이가 +2.1%로 10% 이내예요.',
    },
    {
      mode: 'loading',
      title: '약한 전방단: 2포트 대 정확 MNA 한계',
      who: '직접 피드스루 1/RF 때문에 +23.1% 차이',
      params: { rf: 1, gm1: 2, gm2: 2, rd1: 1, rd2: 0.5, iin: 1 },
      disabledElems: [],
      text: 'gm1 = gm2 = 2 mS, RD1 = 1 kΩ, RD2 = 0.5 kΩ, RF = 1 kΩ처럼 gm1·gm2·RD1(4 mS)이 1/RF(1 mS)보다 압도적으로 크지 않으면, 양쪽 로딩을 다 넣어도 2포트 공식(−307.7 Ω)과 정확 MNA(−250.0 Ω)가 +23.1% 달라져요.',
    },
    {
      mode: 'sign',
      title: '반송 전류 부호: V1 = +1.0 V 인가',
      who: '실제 +0.100 mA → · IF = −0.100 mA ←',
      params: { v1: 1, rf: 10 },
      causalStep: 3,
      text: '감지 포트에 V1 = +1.0 V를 걸고 반송 포트를 접지로 단락하면 실제 전류 +0.100 mA는 오른쪽 단락선으로 나가요. IF는 단락선에서 RF로 들어가는 왼쪽 방향이 양이므로 IF = −0.100 mA, K = −0.100 mS가 돼요.',
    },
    {
      mode: 'sign',
      title: '음의 V1 = −1.0 V일 때도 K는 −0.100 mS',
      who: 'IF = +0.100 mA ← · K = IF/V1 = −0.100 mS',
      params: { v1: -1, rf: 10 },
      causalStep: 3,
      text: 'V1 = −1.0 V로 바꾸면 실제 전류도 왼쪽으로 흘러 IF = +0.100 mA가 되지만, V1도 음수이므로 비 K = IF/V1 = −0.100 mS는 변하지 않아요. R0 < 0과 곱해 KR0 > 0 음귀환을 확인해요.',
    },
  ],
  mistakes: {
    loading: [
      {
        title: 'RF가 크다는 조건 없이 무로딩 R0 사용',
        text: '문제에 "$R_F$가 크다"는 가정이 없으면 입력과 출력에 $R_F$ 사본을 모두 접지해 $R_0$, $R_{\\text{in,open}}$, $R_{\\text{out,open}}$을 다시 구해야 해요.',
      },
      {
        title: '입력·출력 로딩 비중을 똑같이 취급',
        text: '입력 쪽은 $1/g_{m1}=100\\ \\Omega$이라 $R_F=10\\ \\text{k}\\Omega$에서 $1\\%$만 새지만, 출력 쪽은 $R_{D2}=2\\ \\text{k}\\Omega$이라 $16.7\\%$나 줄어 $R_F \\gg R_{D2}$ 조건이 훨씬 민감해요.',
      },
      {
        title: 'V-C 폐루프 입력저항 증감 방향 혼동',
        text: 'V-C 귀환은 입력에 전류를 병렬 반송하고 출력 전압을 병렬 감지하므로 $R_{\\text{in,closed}}$와 $R_{\\text{out,closed}}$ 모두 $(1+KR_0)$로 나뉘어 작아져요.',
      },
    ],
    sign: [
      {
        title: '슬라이드 iRF 화살표 그대로 K > 0으로 오해',
        text: '반송 전류 $I_F$의 양의 기준은 입력 노드에서 빠져 $K$로 들어가는 방향이에요. $V_1>0$이면 실제 전류가 반대로 나가므로 $I_F=-V_1/R_F$, $K=-1/R_F<0$이에요.',
      },
      {
        title: 'K < 0만 보고 양귀환으로 오인',
        text: '음귀환 판정은 $K$ 단독이 아니라 루프 이득 $KR_0$의 부호로 해요. $R_0<0$과 $K<0$을 곱하면 $KR_0>0$이라 분모 $1+KR_0>1$인 음귀환이에요.',
      },
      {
        title: '반송 포트를 개방해 전류가 0이 되는 실수',
        text: 'V-C 귀환의 반송량은 전류이므로 $K$를 잴 때 반송 포트를 개방하면 $I_F=0$이 돼요. 반드시 단락하고 단락선 전류를 재야 해요.',
      },
    ],
  },
  evaluate(state, mna) {
    if (state.mode === 'sign') {
      const v1V = Number(state.params.v1);
      const rfK = Number(state.params.rf);
      const rfOhm = rfK * 1000;
      const op = solveKNetwork(rfOhm, v1V, mna);
      const unit = solveKNetwork(rfOhm, 1.0, mna);
      const refOpen = solveLoadingModel(state.params, true, true, mna);
      if (!op.ok || !unit.ok || !refOpen.ok) {
        return {
          tiles: [{ label: '상태', val: '오류' }],
          diagnosis: { kind: 'bad', title: '해석 오류', text: '회로 해석 중 특이 행렬이 발생했어요.' },
        };
      }

      const iActualMa = op.branches.rf.re * 1000;
      const iFMa = -iActualMa;
      const kMs = -unit.branches.rf.re * 1000;
      const r0RefOhm = refOpen.r0FullOhm;
      const kr0 = (kMs * 1e-3) * r0RefOhm;
      const onePlusKr0 = 1 + kr0;

      const actualArrowDir = v1V >= 0 ? 'fwd' : 'rev';
      const isZeroV1 = Math.abs(v1V) < 1e-6;
      const dirTxt = isZeroV1
        ? '전류 0 (V1 = 0)'
        : (v1V > 0 ? '실제 전류(→)와 기준 IF(←) 반대' : '실제 전류(←)가 기준 IF(←)와 같지만 V1 < 0');

      return {
        tiles: [
          { label: '귀환율 K', val: fmtSignedMs(kMs) },
          { label: '반송 전류 IF', val: fmtSignedMa(iFMa) },
          { label: '1 + KR0 (음귀환)', val: onePlusKr0.toFixed(2) },
        ],
        diagnosis: {
          kind: 'ok',
          title: '음귀환 부호 확인 (K < 0, R0 < 0 ⇒ KR0 > 0)',
          text: `$K = I_F / V_1 = -1/R_F = ${kMs.toFixed(3)}\\ \\text{mS}$이고 기준 개루프 $R_0 = ${fmtOhmsSignedTex(r0RefOhm)}$이므로 $KR_0 = ${kr0.toFixed(2)} > 0$, $1+KR_0 = ${onePlusKr0.toFixed(2)} > 1$인 음귀환이에요.`,
        },
        equations: [
          {
            name: '반송 전류와 귀환율 K',
            tex: `$$\\begin{aligned}I_F &= -\\frac{V_1}{R_F} = ${fmtSignedMaTex(iFMa)}\\\\ K &= \\frac{I_F}{V_1} = -\\frac{1}{R_F}\\\\ &= ${kMs.toFixed(3)}\\ \\text{mS}\\end{aligned}$$`,
          },
          {
            name: '루프 이득 부호 확인',
            tex: `$$\\begin{aligned}KR_0 &= (${kMs.toFixed(3)}\\ \\text{mS})(${fmtOhmsSignedTex(r0RefOhm)})\\\\ &= +${kr0.toFixed(2)} > 0\\end{aligned}$$`,
          },
        ],
        summary: `${dirTxt}라서 $K = ${kMs.toFixed(3)}\\ \\text{mS}$로 항상 음수예요. 개루프 $R_0 < 0$과 곱하면 $1 + KR_0 = ${onePlusKr0.toFixed(2)}$가 되어 음귀환이 성립해요.`,
        nodes: {
          sense: { text: `V1 ${fmtSignedVParam(v1V)}`, hot: state.causalStep === 1, dir: dirFromVal(v1V) },
          ret: { text: '단락 0.00 V', hot: state.causalStep === 3 },
        },
        branches: {
          i_actual: { text: `실제 ${fmtAbsMa(iActualMa)}`, hot: state.causalStep === 2, dim: isZeroV1, dir: actualArrowDir },
          i_f_ref: { text: `IF ${fmtSignedMa(iFMa)}`, hot: state.causalStep === 3, dir: 'fwd' },
        },
      };
    }

    // Mode: 'loading' (approx)
    const rfInOn = !state.disabledElems.includes('rf-in');
    const rfOutOn = !state.disabledElems.includes('rf-out');
    const res = solveLoadingModel(state.params, rfInOn, rfOutOn, mna);
    if (!res.ok) {
      return {
        tiles: [{ label: '상태', val: '오류' }],
        diagnosis: { kind: 'bad', title: '해석 오류', text: res.reason },
      };
    }

    const r0IdealK = Math.abs(res.r0IdealOhm) / 1000;
    const yMax = r0IdealK <= 5
      ? Math.max(2, Math.ceil(r0IdealK * 1.2))
      : Math.ceil((r0IdealK * 1.12) / 10) * 10;

    let diag;
    if (res.openLoopErrPct >= 10) {
      diag = {
        kind: 'bad',
        title: `로딩 생략 근사 붕괴 (개루프 오차 ${res.openLoopErrPct.toFixed(1)}%)`,
        text: `선택한 모델의 $|R_0| = ${fmtOhmsUnsignedTex(res.r0ToggledOhm)}$가 전체 로딩 $|R_0| = ${fmtOhmsUnsignedTex(res.r0FullOhm)}$보다 ${res.openLoopErrPct.toFixed(1)}% 크게 어긋나요. 꺼진 $R_F$ 복제를 다시 켜서 비교해 보세요.`,
      };
    } else if (res.feedthroughErrPct >= 10) {
      diag = {
        kind: 'warn',
        title: `2포트 일방성 근사 한계 (피드스루 차이 ${res.feedthroughErrPct.toFixed(1)}%)`,
        text: `개루프 로딩은 모두 반영했지만, 전방 전달량 $g_{m1}g_{m2}R_{D1}$에 비해 $1/R_F$ 직접 피드스루가 무시할 수 없어 2포트 폐루프($${fmtOhmsSignedTex(res.rClosed2PortOhm)}$)와 정확 MNA($${fmtOhmsSignedTex(res.rClosedExactOhm)}$)가 달라졌어요.`,
      };
    } else if (!rfInOn && !rfOutOn) {
      diag = {
        kind: 'info',
        title: `무로딩 근사 허용 구간 (개루프 오차 ${res.openLoopErrPct.toFixed(1)}% · 10% 이내)`,
        text: `$R_F = ${fmtKOhmTex(res.rfK)}$가 $1/g_{m1} = ${(1000 / res.gm1Ms).toFixed(0)}\\ \\Omega$과 $R_{D2} = ${fmtKOhmTex(res.rd2K)}$보다 충분히 커서, 양쪽 로딩을 생략해도 개루프 오차가 ${res.openLoopErrPct.toFixed(1)}%로 $10\\%$ 이내예요.`,
      };
    } else if (res.openLoopErrPct > 0.05) {
      diag = {
        kind: 'warn',
        title: `일부 로딩 생략 (개루프 오차 ${res.openLoopErrPct.toFixed(1)}% · 10% 이내)`,
        text: !rfOutOn
          ? `출력 쪽 $R_{D2} = ${fmtKOhmTex(res.rd2K)}$에 비해 $R_F = ${fmtKOhmTex(res.rfK)}$가 커서 출력 복제를 꺼도 개루프 오차가 ${res.openLoopErrPct.toFixed(1)}%예요.`
          : `입력 쪽 $(1/g_{m1}=${(1000 / res.gm1Ms).toFixed(0)}\\ \\Omega)$은 $R_F=${fmtKOhmTex(res.rfK)}$에 비해 작아 오차가 ${res.openLoopErrPct.toFixed(1)}%예요. 출력 쪽 $R_{D2}$ 로딩과 비교해 보세요.`,
      };
    } else if (res.noLoadOpenErrPct >= 10) {
      diag = {
        kind: 'ok',
        title: '양쪽 RF 로딩 반영 완료 (무로딩 시 붕괴 구간)',
        text: `양쪽 복제를 켜서 정확 로딩 $|R_0| = ${fmtOhmsUnsignedTex(res.r0FullOhm)}$와 폐루프 $${fmtOhmsSignedTex(res.rClosed2PortOhm)}$를 얻었어요. 복제를 모두 끄면 무로딩 근사($${fmtOhmsUnsignedTex(res.r0IdealOhm)}$)가 ${res.noLoadOpenErrPct.toFixed(1)}% 빗나가는 구간이에요.`,
      };
    } else {
      diag = {
        kind: 'ok',
        title: `큰 RF 구간 (무로딩 근사도 ${res.noLoadOpenErrPct.toFixed(1)}% 이내)`,
        text: `$R_F = ${fmtKOhmTex(res.rfK)}$가 $1/g_{m1}$과 $R_{D2}$보다 충분히 커서 양쪽 로딩을 빼도 개루프 오차가 ${res.noLoadOpenErrPct.toFixed(1)}%로 $10\\%$ 이내예요.`,
      };
    }

    const rInSingleOhm = 1000 / res.gm1Ms;
    const r0Tex = `\\begin{aligned}R_0 &= -\\frac{${rfInOn ? 'R_F R_{D1}' : 'R_{D1}'}}{${rfInOn ? 'R_F + 1/g_{m1}' : '1'}}\\\\ &\\quad \\times g_{m2}${rfOutOn ? '(R_{D2} \\parallel R_F)' : 'R_{D2}'}\\\\ &= ${fmtOhmsSignedTex(res.r0ToggledOhm)}\\end{aligned}`;
    const closedTex = `\\begin{aligned}\\text{2포트}\\ \\frac{R_0}{1+KR_0} &= ${fmtOhmsSignedTex(res.rClosed2PortOhm)}\\\\ \\text{정확 MNA} &= ${fmtOhmsSignedTex(res.rClosedExactOhm)}\\end{aligned}`;

    const modeLabel = rfInOn && rfOutOn
      ? '양쪽 복제 ON (2포트 로딩 일치)'
      : (!rfInOn && !rfOutOn ? '이상적 무로딩 근사' : (!rfOutOn ? '출력 복제 생략 (rf-out OFF)' : '입력 복제 생략 (rf-in OFF)'));

    return {
      tiles: [
        { label: '개루프 R0', val: fmtOhmsSigned(res.r0ToggledOhm) },
        { label: '2포트 폐루프', val: fmtOhmsSigned(res.rClosed2PortOhm) },
        { label: '정확 MNA 폐루프', val: fmtOhmsSigned(res.rClosedExactOhm) },
      ],
      diagnosis: diag,
      equations: [
        { name: '선택 모델 개루프 이득', tex: `$$${r0Tex}$$` },
        { name: '폐루프 비교 (1 + KR0 = ' + res.denom.toFixed(2) + ')', tex: `$$${closedTex}$$` },
      ],
      summary: `${modeLabel} 상태에서 $R_{\\text{in,open}} = ${fmtOhmsUnsignedTex(res.rInOpenOhm)}$, $R_{\\text{out,open}} = ${fmtOhmsUnsignedTex(res.rOutOpenOhm)}$, $1 + KR_0 = ${res.denom.toFixed(2)}$예요. 폐루프 저항은 $R_{\\text{in,closed}} = ${fmtOhmsUnsignedTex(res.rInClosedExactOhm)}$, $R_{\\text{out,closed}} = ${fmtOhmsUnsignedTex(res.rOutClosedExactOhm)}$(이상적 무로딩 개루프는 $|R_0| = ${fmtOhmsUnsignedTex(res.r0IdealOhm)}$, $1/g_{m1} = ${fmtOhmsUnsignedTex(rInSingleOhm)}$)예요.`,
      nodes: {
        s1: { text: `vs1 ${fmtSignedVoltageFromMv(res.vS1Mv)}`, hot: rfInOn, dir: dirFromVal(res.vS1Mv) },
        x: { text: `VX ${fmtSignedVoltageFromMv(res.vXMv)}`, dir: dirFromVal(res.vXMv) },
        out: {
          text: `Vout ${fmtSignedVoltageFromMv(res.vOutMv)}`,
          bad: res.openLoopErrPct >= 10,
          hot: rfOutOn && res.openLoopErrPct < 10,
          dir: dirFromVal(res.vOutMv),
        },
      },
      branches: {
        rin_branch: { text: `Rin ${fmtOhmsUnsigned(res.rInOpenOhm)}`, hot: rfInOn, dim: !rfInOn },
        rout_branch: {
          text: `Rout ${fmtOhmsUnsigned(res.rOutOpenOhm)}`,
          hot: rfOutOn,
          bad: !rfOutOn && res.openLoopErrPct >= 10,
          dim: !rfOutOn,
        },
      },
      elems: {
        'rf-in': { hot: rfInOn },
        'rf-out': { hot: rfOutOn, bad: !rfOutOn && res.openLoopErrPct >= 10 },
      },
      plotData: {
        title: 'RF 크기에 따른 개루프 이득 |R0| 로딩 비교',
        ariaLabel: '귀환 저항 RF(1~100 kΩ)에 따른 정확 로딩 개루프 |R0| 대 선택 근사 곡선',
        xLabel: '귀환 저항 RF (kΩ, 로그 눈금)',
        yLabel: '개루프 |R0| (kΩ)',
        xScale: 'log',
        xMin: 1,
        xMax: 100,
        yMin: 0,
        yMax,
        exact: res.exactCurve,
        approx: res.approxCurve,
        exactLabel: '전체 로딩 개루프 |R0| (실선)',
        approxLabel: rfInOn && rfOutOn
          ? '현재 모델 |R0| (양쪽 ON 일치)'
          : (!rfInOn && !rfOutOn ? '무로딩 근사 |R0| (점선)' : '일부 로딩 생략 |R0| (점선)'),
        marker: [res.rfK, Math.abs(res.r0FullOhm) / 1000],
        approxMarker: [res.rfK, Math.abs(res.r0ToggledOhm) / 1000],
        errPct: res.openLoopErrPct,
        thresholdPct: 10,
      },
    };
  },
};

module.exports = spec;
