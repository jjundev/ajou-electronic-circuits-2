// Interactive Lab 01 (1120): Four Feedback Duplicate Terminations Assembly Bench
// Archetype: bench — lets students plug [단락/접지] or [개방] onto sense-rem and return-rem
// across V-V, V-C, C-V, and C-C feedback topologies and verifies loading impedance via MNA.

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

function arrowHead(x, y, dir) {
  let pts;
  if (dir === 'r') pts = `${x} ${y} ${x - 8} ${y - 4.5} ${x - 8} ${y + 4.5}`;
  else if (dir === 'l') pts = `${x} ${y} ${x + 8} ${y - 4.5} ${x + 8} ${y + 4.5}`;
  else if (dir === 'u') pts = `${x} ${y} ${x - 4.5} ${y + 8} ${x + 4.5} ${y + 8}`;
  else pts = `${x} ${y} ${x - 4.5} ${y - 8} ${x + 4.5} ${y - 8}`;
  return `<polygon class="sym" points="${pts}" fill="currentColor"/>`;
}

function hRes(xL, xR, y) {
  const span = xR - xL;
  const zigStart = xL + (span - 48) / 2;
  const z = zigStart;
  const d = `M${z} ${y}l4-6 8 12 8-12 8 12 8-12 8 12 4-6`;
  return [
    `<line class="fig-ink" x1="${xL}" y1="${y}" x2="${z}" y2="${y}"/>`,
    `<g class="sym" data-symbol="resistor"><path class="fig-ink" d="${d}"/></g>`,
    `<line class="fig-ink" x1="${z + 48}" y1="${y}" x2="${xR}" y2="${y}"/>`,
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

function testSourceSym(x, cy, isVoltage) {
  if (isVoltage) {
    return [
      `<line class="fig-ink" x1="${x}" y1="320" x2="${x}" y2="${cy - 16}"/>`,
      '<g class="sym" data-symbol="vsrc">',
      `  <circle class="fig-ink" cx="${x}" cy="${cy}" r="16"/>`,
      `  <path class="fig-ink" d="M${x - 5} ${cy - 6}h10M${x} ${cy - 11}v10M${x - 5} ${cy + 8}h10"/>`,
      '</g>',
      `<line class="fig-ink" x1="${x}" y1="${cy + 16}" x2="${x}" y2="392"/>`,
      gndSym(x, 392),
    ].join('');
  }
  return [
    `<line class="fig-ink" x1="${x}" y1="320" x2="${x}" y2="${cy - 16}"/>`,
    '<g class="sym" data-symbol="isrc">',
    `  <circle class="fig-ink" cx="${x}" cy="${cy}" r="16"/>`,
    `  <line class="fig-ink" x1="${x}" y1="${cy + 10}" x2="${x}" y2="${cy - 8}"/>`,
    arrowHead(x, cy - 11, 'u'),
    '</g>',
    `<line class="fig-ink" x1="${x}" y1="${cy + 16}" x2="${x}" y2="392"/>`,
    gndSym(x, 392),
  ].join('');
}

function buildBenchNetwork(key, isLeft) {
  const xSrc = isLeft ? 74 : 394;
  const xEnd = isLeft ? 240 : 560;
  const parts = [];

  if (key === 'vv') {
    if (isLeft) {
      parts.push(`<line class="fig-ink" x1="${xSrc}" y1="320" x2="136" y2="320"/>`);
      parts.push(vRes(136, 320, 392));
      parts.push(gndSym(136, 392));
      parts.push(`<text class="fig-text fig-math" x="116" y="360" text-anchor="end">${sub('R', '2')}</text>`);
      parts.push(hRes(136, 210, 320));
      parts.push(`<text class="fig-text fig-math" x="173" y="346" text-anchor="middle">${sub('R', '1')}</text>`);
      parts.push(`<line class="fig-ink" x1="210" y1="320" x2="${xEnd}" y2="320"/>`);
    } else {
      parts.push(hRes(xSrc, 488, 320));
      parts.push(`<text class="fig-text fig-math" x="441" y="346" text-anchor="middle">${sub('R', '1')}</text>`);
      parts.push(`<line class="fig-ink" x1="488" y1="320" x2="516" y2="320"/>`);
      parts.push(vRes(516, 320, 392));
      parts.push(gndSym(516, 392));
      parts.push(`<text class="fig-text fig-math" x="496" y="360" text-anchor="end">${sub('R', '2')}</text>`);
      parts.push(`<line class="fig-ink" x1="516" y1="320" x2="${xEnd}" y2="320"/>`);
    }
  } else if (key === 'vc') {
    const rx1 = isLeft ? 124 : 444;
    const rx2 = isLeft ? 196 : 516;
    parts.push(`<line class="fig-ink" x1="${xSrc}" y1="320" x2="${rx1}" y2="320"/>`);
    parts.push(hRes(rx1, rx2, 320));
    parts.push(`<text class="fig-text fig-math" x="${(rx1 + rx2) / 2}" y="346" text-anchor="middle">${sub('R', 'F')}</text>`);
    parts.push(`<line class="fig-ink" x1="${rx2}" y1="320" x2="${xEnd}" y2="320"/>`);
  } else if (key === 'cv') {
    const xShunt = isLeft ? 156 : 476;
    parts.push(`<line class="fig-ink" x1="${xSrc}" y1="320" x2="${xEnd}" y2="320"/>`);
    parts.push(vRes(xShunt, 320, 392));
    parts.push(gndSym(xShunt, 392));
    parts.push(`<text class="fig-text fig-math" x="${xShunt - 20}" y="360" text-anchor="end">${sub('R', 'M')}</text>`);
  } else {
    if (isLeft) {
      parts.push(hRes(xSrc, 166, 320));
      parts.push(`<text class="fig-text fig-math" x="120" y="346" text-anchor="middle">${sub('R', 'F')}</text>`);
      parts.push(`<line class="fig-ink" x1="166" y1="320" x2="196" y2="320"/>`);
      parts.push(vRes(196, 320, 392));
      parts.push(gndSym(196, 392));
      parts.push(`<text class="fig-text fig-math" x="176" y="360" text-anchor="end">${sub('R', 'M')}</text>`);
      parts.push(`<line class="fig-ink" x1="196" y1="320" x2="${xEnd}" y2="320"/>`);
    } else {
      parts.push(`<line class="fig-ink" x1="${xSrc}" y1="320" x2="450" y2="320"/>`);
      parts.push(vRes(450, 320, 392));
      parts.push(gndSym(450, 392));
      parts.push(`<text class="fig-text fig-math" x="430" y="360" text-anchor="end">${sub('R', 'M')}</text>`);
      parts.push(hRes(450, 536, 320));
      parts.push(`<text class="fig-text fig-math" x="493" y="346" text-anchor="middle">${sub('R', 'F')}</text>`);
      parts.push(`<line class="fig-ink" x1="536" y1="320" x2="${xEnd}" y2="320"/>`);
    }
  }
  return parts.join('');
}

function buildModeSvg(cfg) {
  const { key, label, ampBase, ampSub, inV, outV, ariaLabel } = cfg;
  const inZ = inV ? '∞' : '0';
  const outZ = outV ? '0' : '∞';
  const parts = [
    `<svg viewBox="0 0 660 420" ${SVG_NS_ATTR} role="img" aria-label="${ariaLabel}">`,
    `  <text class="fig-muted" x="330" y="22" text-anchor="middle">전방 증폭기 기준: ${sub('Z', 'in,ideal')}=${inZ} (${inV ? '전압' : '전류'} 입력) · ${sub('Z', 'out,ideal')}=${outZ} (${outV ? '전압' : '전류'} 출력)</text>`,
  ];

  // Top tier: Input side
  if (inV) {
    parts.push('  <circle class="fig-dot" cx="36" cy="66" r="4" data-node-color="blue"/>');
    parts.push(`  <text class="fig-text fig-math" x="36" y="40" text-anchor="middle" data-node-color="blue">${sub('V', 'in')}</text>`);
    parts.push('  <line class="fig-ink" x1="36" y1="66" x2="96" y2="66"/>');
    parts.push('  ' + arrowHead(98, 66, 'r'));
    parts.push('  <g class="sym" data-symbol="sum">');
    parts.push('    <circle class="fig-ink" cx="116" cy="66" r="16"/>');
    parts.push('    <line class="fig-ink" x1="108" y1="66" x2="124" y2="66"/>');
    parts.push('    <line class="fig-ink" x1="116" y1="58" x2="116" y2="74"/>');
    parts.push('    <text class="fig-text" x="88" y="50" text-anchor="middle">+</text>');
    parts.push('    <text class="fig-text" x="96" y="96" text-anchor="middle">−</text>');
    parts.push('  </g>');
    parts.push('  <line class="fig-ink" x1="132" y1="66" x2="262" y2="66"/>');
    parts.push('  ' + arrowHead(264, 66, 'r'));
    parts.push('  <line class="fig-ink" x1="176" y1="162" x2="116" y2="162"/>');
    parts.push('  <line class="fig-ink" x1="116" y1="162" x2="116" y2="85"/>');
    parts.push('  ' + arrowHead(116, 83, 'u'));
  } else {
    parts.push('  <g class="sym" data-symbol="isrc">');
    parts.push('    <circle class="fig-ink" cx="50" cy="114" r="15"/>');
    parts.push('    <line class="fig-ink" x1="50" y1="123" x2="50" y2="105"/>');
    parts.push('    ' + arrowHead(50, 102, 'u'));
    parts.push('  </g>');
    parts.push(`  <text class="fig-text fig-math" x="26" y="119" text-anchor="end">${sub('I', 'in')}</text>`);
    parts.push('  <line class="fig-ink" x1="50" y1="129" x2="50" y2="138"/>');
    parts.push('  ' + gndSym(50, 138));
    parts.push('  <line class="fig-ink" x1="50" y1="99" x2="50" y2="66"/>');
    parts.push('  <line class="fig-ink" x1="50" y1="66" x2="262" y2="66"/>');
    parts.push('  ' + arrowHead(264, 66, 'r'));
    parts.push('  <circle class="fig-dot" cx="116" cy="66" r="4" data-node-color="blue"/>');
    parts.push('  <line class="fig-ink" x1="116" y1="66" x2="116" y2="162"/>');
    parts.push('  <line class="fig-ink" x1="116" y1="162" x2="176" y2="162"/>');
    parts.push('  ' + arrowHead(116, 120, 'd'));
    parts.push(`  <text class="fig-text fig-math" x="134" y="118">${sub('I', 'F')}</text>`);
  }

  // Forward amplifier box
  parts.push('  <rect class="fig-ink" x="266" y="44" width="128" height="44" rx="4"/>');
  parts.push(`  <text class="fig-text fig-math" x="330" y="71" text-anchor="middle">${sub(ampBase, ampSub)} (${label})</text>`);

  // Top tier: Output side
  if (outV) {
    parts.push('  <line class="fig-ink" x1="394" y1="66" x2="616" y2="66"/>');
    parts.push('  <circle class="fig-dot" cx="544" cy="66" r="4" data-node-color="red"/>');
    parts.push('  <circle class="fig-dot" cx="616" cy="66" r="4" data-node-color="red"/>');
    parts.push(`  <text class="fig-text fig-math" x="616" y="40" text-anchor="middle" data-node-color="red">${sub('V', 'out')}</text>`);
    parts.push('  <line class="fig-ink" x1="544" y1="66" x2="544" y2="162"/>');
    parts.push('  <line class="fig-ink" x1="544" y1="162" x2="484" y2="162"/>');
  } else {
    parts.push('  <line class="fig-ink" x1="394" y1="66" x2="544" y2="66"/>');
    parts.push('  <line class="fig-ink" x1="544" y1="66" x2="544" y2="162"/>');
    parts.push('  ' + arrowHead(544, 120, 'd'));
    parts.push('  <line class="fig-ink" x1="544" y1="162" x2="484" y2="162"/>');
    parts.push(`  <text class="fig-text fig-math" x="564" y="118" data-node-color="red">${sub('I', 'out')}</text>`);
  }

  // Return duplicate (left K) + interactive data-port="return-rem"
  parts.push('  <polygon class="fig-accent" points="176 162 226 138 226 186"/>');
  parts.push('  <text class="fig-text fig-math" x="209" y="167" text-anchor="middle">K</text>');
  parts.push('  <text class="fig-text" x="202" y="122" text-anchor="middle">반송 복제</text>');
  parts.push('  <line class="fig-ink" x1="226" y1="162" x2="254" y2="162"/>');
  parts.push('  <g data-port="return-rem">');
  parts.push('    <ellipse cx="274" cy="184" rx="40" ry="44" fill="transparent" stroke="none"/>');
  parts.push('    <g data-port-view="open">');
  parts.push('      <line class="fig-ink" x1="254" y1="162" x2="270" y2="162"/>');
  parts.push('      <circle class="fig-ink" cx="275" cy="162" r="5"/>');
  parts.push('    </g>');
  parts.push('    <g data-port-view="short">');
  parts.push('      <line class="fig-ink" x1="254" y1="162" x2="274" y2="162"/>');
  parts.push('      <line class="fig-ink" x1="274" y1="162" x2="274" y2="176"/>');
  parts.push('      ' + gndSym(274, 176));
  parts.push('    </g>');
  parts.push('    <g class="port-chip">');
  parts.push('      <rect class="port-chip-bg" x="236" y="200" width="76" height="24" rx="6"/>');
  parts.push('      <text class="port-chip" x="274" y="216" text-anchor="middle">단락/접지</text>');
  parts.push('    </g>');
  parts.push('  </g>');

  // Sense duplicate (right K) + interactive data-port="sense-rem"
  parts.push('  <polygon class="fig-accent" points="434 162 484 138 484 186"/>');
  parts.push('  <text class="fig-text fig-math" x="467" y="167" text-anchor="middle">K</text>');
  parts.push('  <text class="fig-text" x="459" y="122" text-anchor="middle">감지 복제</text>');
  parts.push('  <line class="fig-ink" x1="434" y1="162" x2="406" y2="162"/>');
  parts.push('  <g data-port="sense-rem">');
  parts.push('    <ellipse cx="386" cy="184" rx="40" ry="44" fill="transparent" stroke="none"/>');
  parts.push('    <g data-port-view="open">');
  parts.push('      <line class="fig-ink" x1="406" y1="162" x2="390" y2="162"/>');
  parts.push('      <circle class="fig-ink" cx="385" cy="162" r="5"/>');
  parts.push('    </g>');
  parts.push('    <g data-port-view="short">');
  parts.push('      <line class="fig-ink" x1="406" y1="162" x2="386" y2="162"/>');
  parts.push('      <line class="fig-ink" x1="386" y1="162" x2="386" y2="176"/>');
  parts.push('      ' + gndSym(386, 176));
  parts.push('    </g>');
  parts.push('    <g class="port-chip">');
  parts.push('      <rect class="port-chip-bg" x="348" y="200" width="76" height="24" rx="6"/>');
  parts.push('      <text class="port-chip" x="386" y="216" text-anchor="middle">개방</text>');
  parts.push('    </g>');
  parts.push('  </g>');

  // Divider + Bottom MNA test bench
  parts.push('  <line class="plot-axis" x1="20" y1="238" x2="640" y2="238"/>');
  parts.push(`  <text class="fig-muted" x="165" y="258" text-anchor="middle">입력 측 반송 복제 시험 (${sub('R', 'load,in')})</text>`);
  parts.push(`  <text class="fig-muted" x="495" y="258" text-anchor="middle">출력 측 감지 복제 시험 (${sub('R', 'load,out')})</text>`);

  const srcSymLabel = inV || key === 'vc'
    ? (outV ? sub('V', 't') : sub('I', 't'))
    : sub('I', 't');
  const leftIsV = key === 'vv' || key === 'vc';
  const rightIsV = key === 'vv' || key === 'vc';
  const leftSrcText = leftIsV ? sub('V', 't') : sub('I', 't');
  const rightSrcText = rightIsV ? sub('V', 't') : sub('I', 't');
  void srcSymLabel;

  // Left subcircuit (return duplicate test)
  parts.push('  ' + testSourceSym(74, 356, leftIsV));
  parts.push(`  <text class="fig-text fig-math" x="42" y="360" text-anchor="end">${leftSrcText}</text>`);
  parts.push('  <circle class="fig-dot" data-node="ret_in" data-node-color="blue" cx="74" cy="320" r="4"/>');
  parts.push('  ' + buildBenchNetwork(key, true));
  parts.push('  <g data-branch="ret_short">');
  parts.push('    <line class="fig-ink" x1="240" y1="320" x2="240" y2="392"/>');
  parts.push('    ' + gndSym(240, 392));
  parts.push('    <text class="fig-muted" x="260" y="370" text-anchor="start">접지</text>');
  parts.push('  </g>');
  parts.push('  <g data-branch="ret_open">');
  parts.push('    <line class="fig-ink" x1="240" y1="320" x2="266" y2="320"/>');
  parts.push('    <circle class="fig-ink" cx="271" cy="320" r="5"/>');
  parts.push('    <text class="fig-muted" x="292" y="324" text-anchor="start">개방</text>');
  parts.push('  </g>');

  // Right subcircuit (sense duplicate test)
  parts.push('  ' + testSourceSym(394, 356, rightIsV));
  parts.push(`  <text class="fig-text fig-math" x="362" y="360" text-anchor="end">${rightSrcText}</text>`);
  parts.push('  <circle class="fig-dot" data-node="sense_in" data-node-color="red" cx="394" cy="320" r="4"/>');
  parts.push('  ' + buildBenchNetwork(key, false));
  parts.push('  <g data-branch="sense_short">');
  parts.push('    <line class="fig-ink" x1="560" y1="320" x2="560" y2="392"/>');
  parts.push('    ' + gndSym(560, 392));
  parts.push('    <text class="fig-muted" x="580" y="370" text-anchor="start">접지</text>');
  parts.push('  </g>');
  parts.push('  <g data-branch="sense_open">');
  parts.push('    <line class="fig-ink" x1="560" y1="320" x2="586" y2="320"/>');
  parts.push('    <circle class="fig-ink" cx="591" cy="320" r="5"/>');
  parts.push('    <text class="fig-muted" x="612" y="324" text-anchor="start">개방</text>');
  parts.push('  </g>');

  parts.push('  <g data-badges>');
  parts.push('    <g data-badge-for="ret_in" transform="translate(165, 282)"></g>');
  parts.push('    <g data-badge-for="sense_in" transform="translate(495, 282)"></g>');
  parts.push('  </g>');
  parts.push('</svg>');
  return parts.join('\n');
}

const MODE_CONFIGS = {
  vv: {
    key: 'vv',
    label: 'V-V',
    title: 'V-V 전압 증폭기',
    ampBase: 'A',
    ampSub: '0',
    inV: true,
    outV: true,
    senseAnswer: 'open',
    returnAnswer: 'short',
    senseDef: 'short',
    returnDef: 'open',
    ariaLabel: 'V-V 전압-전압 귀환 루프 끊기 및 R1-R2 분배기 복제 종단 조립 회로도',
  },
  vc: {
    key: 'vc',
    label: 'V-C',
    title: 'V-C 트랜스임피던스',
    ampBase: 'R',
    ampSub: '0',
    inV: false,
    outV: true,
    senseAnswer: 'short',
    returnAnswer: 'short',
    senseDef: 'open',
    returnDef: 'open',
    ariaLabel: 'V-C 전압-전류 귀환 루프 끊기 및 RF 복제 종단 조립 회로도',
  },
  cv: {
    key: 'cv',
    label: 'C-V',
    title: 'C-V 트랜스컨덕턴스',
    ampBase: 'G',
    ampSub: 'm',
    inV: true,
    outV: false,
    senseAnswer: 'open',
    returnAnswer: 'open',
    senseDef: 'short',
    returnDef: 'short',
    ariaLabel: 'C-V 전류-전압 귀환 루프 끊기 및 RM 복제 종단 조립 회로도',
  },
  cc: {
    key: 'cc',
    label: 'C-C',
    title: 'C-C 전류 증폭기',
    ampBase: 'A',
    ampSub: 'I',
    inV: false,
    outV: false,
    senseAnswer: 'short',
    returnAnswer: 'open',
    senseDef: 'open',
    returnDef: 'short',
    ariaLabel: 'C-C 전류-전류 귀환 루프 끊기 및 RM-RF 복제 종단 조립 회로도',
  },
};

function makeModePorts(cfg) {
  return [
    {
      id: 'sense-rem',
      label: '감지 복제 남은 포트 (출력 측)',
      options: [
        { id: 'short', label: '단락/접지', shortLabel: '단락/접지' },
        { id: 'open', label: '개방', shortLabel: '개방' },
      ],
      def: cfg.senseDef,
      answer: cfg.senseAnswer,
      badOption: cfg.senseAnswer === 'open' ? 'short' : 'open',
    },
    {
      id: 'return-rem',
      label: '반송 복제 남은 포트 (입력 측)',
      options: [
        { id: 'short', label: '단락/접지', shortLabel: '단락/접지' },
        { id: 'open', label: '개방', shortLabel: '개방' },
      ],
      def: cfg.returnDef,
      answer: cfg.returnAnswer,
      badOption: cfg.returnAnswer === 'open' ? 'short' : 'open',
    },
  ];
}

function makeModePresets(cfg) {
  const wrongSense = cfg.senseAnswer === 'open' ? 'short' : 'open';
  const wrongRet = cfg.returnAnswer === 'open' ? 'short' : 'open';
  return [
    {
      id: `${cfg.key}-ok`,
      label: '정답 조립',
      ports: { 'sense-rem': cfg.senseAnswer, 'return-rem': cfg.returnAnswer },
    },
    {
      id: `${cfg.key}-bad-sense`,
      label: '감지만 오조립',
      ports: { 'sense-rem': wrongSense, 'return-rem': cfg.returnAnswer },
    },
    {
      id: `${cfg.key}-bad-ret`,
      label: '반송만 오조립',
      ports: { 'sense-rem': cfg.senseAnswer, 'return-rem': wrongRet },
    },
  ];
}

function formatOhms(ohms) {
  if (ohms === null) return '∞ (로딩 소실)';
  if (Math.abs(ohms) < 1e-6) return '0 Ω';
  if (Math.abs(ohms) >= 1000) {
    return `${(ohms / 1000).toFixed(2)} kΩ`;
  }
  return `${Math.round(ohms * 10) / 10} Ω`;
}

function formatOhmsShort(ohms) {
  if (ohms === null) return '∞ Ω';
  if (Math.abs(ohms) < 1e-6) return '0 Ω';
  if (Math.abs(ohms) >= 1000) return `${(ohms / 1000).toFixed(2)} kΩ`;
  return `${Math.round(ohms)} Ω`;
}

function formatOhmsTex(ohms) {
  if (ohms === null) return '\\infty';
  if (Math.abs(ohms) < 1e-6) return '0\\ \\Omega';
  if (Math.abs(ohms) >= 1000) return `${(ohms / 1000).toFixed(2)}\\text{ k}\\Omega`;
  return `${Math.round(ohms)}\\ \\Omega`;
}

function solveDuplicateBench(modeKey, params, senseTerm, returnTerm, mna) {
  const senseShort = senseTerm === 'short';
  const retShort = returnTerm === 'short';

  if (modeKey === 'vv') {
    const r1 = Number(params.vv_r1) * 1000;
    const r2 = Number(params.vv_r2) * 1000;
    const vt = Number(params.vt);
    const senseRes = mna.solveCircuit({
      elements: [
        { id: 'vs', type: 'vsrc', n1: 's_in', n2: '0', value: vt },
        { id: 'r1', type: 'R', n1: 's_in', n2: 's_rem', value: r1 },
        { id: 'r2', type: 'R', n1: 's_rem', n2: '0', value: r2 },
        senseShort ? { id: 'sw', type: 'short', n1: 's_rem', n2: '0' } : { id: 'sw', type: 'open', n1: 's_rem', n2: '0' },
      ],
    });
    const retRes = mna.solveCircuit({
      elements: [
        { id: 'vr', type: 'vsrc', n1: 'r_in', n2: '0', value: vt },
        { id: 'r2', type: 'R', n1: 'r_in', n2: '0', value: r2 },
        { id: 'r1', type: 'R', n1: 'r_in', n2: 'r_rem', value: r1 },
        retShort ? { id: 'sw', type: 'short', n1: 'r_rem', n2: '0' } : { id: 'sw', type: 'open', n1: 'r_rem', n2: '0' },
      ],
    });
    if (!senseRes.ok || !retRes.ok) return { ok: false, reason: senseRes.reason || retRes.reason };
    const iS = -senseRes.branches.vs.re;
    const iR = -retRes.branches.vr.re;
    return {
      ok: true,
      rLoadOut: vt / iS,
      rLoadIn: vt / iR,
      rTrueOut: r1 + r2,
      rTrueIn: (r1 * r2) / (r1 + r2),
      senseCurrentMa: iS * 1000,
      retCurrentMa: iR * 1000,
    };
  }

  if (modeKey === 'vc') {
    const rf = Number(params.vc_rf) * 1000;
    const vt = Number(params.vt);
    const senseRes = mna.solveCircuit({
      elements: [
        { id: 'vs', type: 'vsrc', n1: 's_in', n2: '0', value: vt },
        { id: 'rf', type: 'R', n1: 's_in', n2: 's_rem', value: rf },
        senseShort ? { id: 'sw', type: 'short', n1: 's_rem', n2: '0' } : { id: 'sw', type: 'open', n1: 's_rem', n2: '0' },
      ],
    });
    const retRes = mna.solveCircuit({
      elements: [
        { id: 'vr', type: 'vsrc', n1: 'r_in', n2: '0', value: vt },
        { id: 'rf', type: 'R', n1: 'r_in', n2: 'r_rem', value: rf },
        retShort ? { id: 'sw', type: 'short', n1: 'r_rem', n2: '0' } : { id: 'sw', type: 'open', n1: 'r_rem', n2: '0' },
      ],
    });
    if (!senseRes.ok || !retRes.ok) return { ok: false, reason: senseRes.reason || retRes.reason };
    const iS = -senseRes.branches.vs.re;
    const iR = -retRes.branches.vr.re;
    return {
      ok: true,
      rLoadOut: Math.abs(iS) > 1e-12 ? vt / iS : null,
      rLoadIn: Math.abs(iR) > 1e-12 ? vt / iR : null,
      rTrueOut: rf,
      rTrueIn: rf,
      senseCurrentMa: iS * 1000,
      retCurrentMa: iR * 1000,
    };
  }

  if (modeKey === 'cv') {
    const rm = Number(params.cv_rm) * 1000;
    const it = Number(params.it) * 1e-3;
    const senseRes = mna.solveCircuit({
      elements: [
        { id: 'is', type: 'isrc', n1: '0', n2: 's_in', value: it },
        { id: 'rm', type: 'R', n1: 's_in', n2: '0', value: rm },
        { id: 'ws', type: 'short', n1: 's_in', n2: 's_rem' },
        senseShort ? { id: 'sw', type: 'short', n1: 's_rem', n2: '0' } : { id: 'sw', type: 'open', n1: 's_rem', n2: '0' },
      ],
    });
    const retRes = mna.solveCircuit({
      elements: [
        { id: 'ir', type: 'isrc', n1: '0', n2: 'r_in', value: it },
        { id: 'rm', type: 'R', n1: 'r_in', n2: '0', value: rm },
        { id: 'wr', type: 'short', n1: 'r_in', n2: 'r_rem' },
        retShort ? { id: 'sw', type: 'short', n1: 'r_rem', n2: '0' } : { id: 'sw', type: 'open', n1: 'r_rem', n2: '0' },
      ],
    });
    if (!senseRes.ok || !retRes.ok) return { ok: false, reason: senseRes.reason || retRes.reason };
    const vS = senseRes.nodes.s_in.re;
    const vR = retRes.nodes.r_in.re;
    return {
      ok: true,
      rLoadOut: vS / it,
      rLoadIn: vR / it,
      rTrueOut: rm,
      rTrueIn: rm,
      senseVoltMv: vS * 1000,
      retVoltMv: vR * 1000,
    };
  }

  const rm = Number(params.cc_rm) * 1000;
  const rf = Number(params.cc_rf) * 1000;
  const it = Number(params.it) * 1e-3;
  const senseRes = mna.solveCircuit({
    elements: [
      { id: 'is', type: 'isrc', n1: '0', n2: 's_in', value: it },
      { id: 'rm', type: 'R', n1: 's_in', n2: '0', value: rm },
      { id: 'rf', type: 'R', n1: 's_in', n2: 's_rem', value: rf },
      senseShort ? { id: 'sw', type: 'short', n1: 's_rem', n2: '0' } : { id: 'sw', type: 'open', n1: 's_rem', n2: '0' },
    ],
  });
  const retRes = mna.solveCircuit({
    elements: [
      { id: 'ir', type: 'isrc', n1: '0', n2: 'r_in', value: it },
      { id: 'rf', type: 'R', n1: 'r_in', n2: 'r_rem', value: rf },
      { id: 'rm', type: 'R', n1: 'r_rem', n2: '0', value: rm },
      retShort ? { id: 'sw', type: 'short', n1: 'r_rem', n2: '0' } : { id: 'sw', type: 'open', n1: 'r_rem', n2: '0' },
    ],
  });
  if (!senseRes.ok || !retRes.ok) return { ok: false, reason: senseRes.reason || retRes.reason };
  const vS = senseRes.nodes.s_in.re;
  const vR = retRes.nodes.r_in.re;
  return {
    ok: true,
    rLoadOut: vS / it,
    rLoadIn: vR / it,
    rTrueOut: (rm * rf) / (rm + rf),
    rTrueIn: rf + rm,
    senseVoltMv: vS * 1000,
    retVoltMv: vR * 1000,
  };
}

function buildDiagnosis(cfg, senseOk, retOk, measured) {
  if (senseOk && retOk) {
    return {
      kind: 'ok',
      title: `${cfg.title} 양쪽 종단 정답`,
      text: `감지 복제는 ${cfg.inV ? '원래 전압 입력($\\infty$)이라 개방' : '원래 전류 입력($0$)이라 단락'}, 반송 복제는 ${cfg.outV ? '원래 전압 출력($0$)이라 단락' : '원래 전류 출력($\\infty$)이라 개방'}해 참값 $R_{\\text{load,in}}=${formatOhmsTex(measured.rTrueIn)}$ 및 $R_{\\text{load,out}}=${formatOhmsTex(measured.rTrueOut)}$이 그대로 남았어요.`,
    };
  }

  const msgs = [];
  if (!senseOk) {
    if (cfg.key === 'vv') {
      msgs.push(`감지 복제 남은 포트를 단락하면 원래 전압 입력($\\infty$) 조건을 어겨 $R_2$가 우회되고, 출력 로딩이 $${formatOhmsTex(measured.rTrueOut)}$ 대신 $${formatOhmsTex(measured.rLoadOut)}$로 줄어들어 $A_{v,\\text{open}}$이 과소평가돼요.`);
    } else if (cfg.key === 'vc') {
      msgs.push('감지 복제 남은 포트를 개방하면 원래 전류 입력($0$) 조건을 어겨 $R_F$에 전류가 흐르지 않으므로 출력 로딩 $R_F$가 통째로 빠져 $R_{\\text{out,open}}$이 과대평가돼요.');
    } else if (cfg.key === 'cv') {
      msgs.push('감지 복제 남은 포트를 접지로 단락하면 원래 전압 입력($\\infty$) 조건을 어겨 $R_M$이 우회되므로 직렬 출력 로딩이 $0\\ \\Omega$으로 사라져요. (교과서 보충)');
    } else {
      msgs.push(`감지 복제 남은 포트를 개방하면 원래 전류 입력($0$) 조건을 어겨 $R_F$ 경로가 끊기므로 출력 로딩이 $R_M\\parallel R_F=${formatOhmsTex(measured.rTrueOut)}$ 대신 $R_M=${formatOhmsTex(measured.rLoadOut)}$으로 커져요. (교과서 보충)`);
    }
  }
  if (!retOk) {
    if (cfg.key === 'vv') {
      msgs.push(`반송 복제 남은 포트를 개방하면 원래 전압 출력($0$) 조건을 어겨 $R_1$이 열리므로 입력 측 로딩이 $R_1\\parallel R_2=${formatOhmsTex(measured.rTrueIn)}$ 대신 $R_2=${formatOhmsTex(measured.rLoadIn)}$로 왜곡돼요.`);
    } else if (cfg.key === 'vc') {
      msgs.push('반송 복제 남은 포트를 개방하면 원래 전압 출력($0$) 조건을 어겨 $R_F$가 열리므로 입력 로딩이 사라져 $R_{\\text{in,open}}$이 $(1/g_{m1})\\parallel R_F$가 아닌 $1/g_{m1}$로 왜곡돼요.');
    } else if (cfg.key === 'cv') {
      msgs.push('반송 복제 남은 포트를 단락하면 원래 전류 출력($\\infty$) 조건을 어겨 $R_M$이 접지로 우회되므로 입력 직렬 로딩이 $0\\ \\Omega$이 돼요. (교과서 보충)');
    } else {
      msgs.push(`반송 복제 남은 포트를 단락하면 원래 전류 출력($\\infty$) 조건을 어겨 $R_M$이 접지로 빠져 입력 로딩이 $R_F+R_M=${formatOhmsTex(measured.rTrueIn)}$ 대신 $R_F=${formatOhmsTex(measured.rLoadIn)}$로 줄어요. (교과서 보충)`);
    }
  }

  return {
    kind: !senseOk && !retOk ? 'bad' : 'warn',
    title: !senseOk && !retOk ? '양쪽 종단 오조립' : (!senseOk ? '감지 복제(출력 측) 오조립' : '반송 복제(입력 측) 오조립'),
    text: msgs.join(' '),
  };
}

function buildEquations(cfg, params) {
  const senseRule = cfg.inV ? 'Z_{\\text{in,ideal}}=\\infty \\;\\Rightarrow\\; \\text{개방}' : 'Z_{\\text{in,ideal}}=0 \\;\\Rightarrow\\; \\text{단락}';
  const retRule = cfg.outV ? 'Z_{\\text{out,ideal}}=0 \\;\\Rightarrow\\; \\text{단락}' : 'Z_{\\text{out,ideal}}=\\infty \\;\\Rightarrow\\; \\text{개방}';
  let loadTex;
  if (cfg.key === 'vv') {
    loadTex = `$$\\begin{aligned}R_{\\text{load,out}}&=R_1+R_2=${(Number(params.vv_r1) + Number(params.vv_r2)).toFixed(2)}\\ \\text{k}\\Omega\\\\R_{\\text{load,in}}&=R_1\\parallel R_2=${((Number(params.vv_r1) * Number(params.vv_r2)) / (Number(params.vv_r1) + Number(params.vv_r2))).toFixed(2)}\\ \\text{k}\\Omega\\end{aligned}$$`;
  } else if (cfg.key === 'vc') {
    loadTex = `$$R_{\\text{load,out}}=R_{\\text{load,in}}=R_F=${Number(params.vc_rf).toFixed(1)}\\ \\text{k}\\Omega$$`;
  } else if (cfg.key === 'cv') {
    loadTex = `$$R_{\\text{load,out}}=R_{\\text{load,in}}=R_M=${Math.round(Number(params.cv_rm) * 1000)}\\ \\Omega$$`;
  } else {
    const rm = Number(params.cc_rm);
    const rf = Number(params.cc_rf);
    loadTex = `$$\\begin{aligned}R_{\\text{load,out}}&=R_M\\parallel R_F=${((rm * rf) / (rm + rf)).toFixed(2)}\\ \\text{k}\\Omega\\\\R_{\\text{load,in}}&=R_F+R_M=${(rf + rm).toFixed(2)}\\ \\text{k}\\Omega\\end{aligned}$$`;
  }
  return [
    { name: '종단 판정 규칙 (원래 붙어 있던 포트)', tex: `$$\\begin{aligned}\\text{감지}:\\;&${senseRule}\\\\\\text{반송}:\\;&${retRule}\\end{aligned}$$` },
    { name: '정답 조립 기준 로딩 임피던스', tex: loadTex },
  ];
}

const spec = {
  id: 'feedback-four-terminations-bench',
  title: '네 가지 귀환 복제 종단 조립',
  archetype: 'bench',
  modes: ['vv', 'vc', 'cv', 'cc'].map((k) => {
    const cfg = MODE_CONFIGS[k];
    return {
      key: cfg.key,
      label: cfg.label,
      svg: buildModeSvg(cfg),
      ariaLabel: cfg.ariaLabel,
      ports: makeModePorts(cfg),
      presets: makeModePresets(cfg),
    };
  }),
  predict: {
    prompt: 'V–V 귀환에서 감지 복제의 남은 포트를 단락에서 개방으로 바꾸면 출력 쪽에서 보이는 저항은 어떻게 될까요?',
    options: [
      { id: 'up', label: '커져요' },
      { id: 'down', label: '작아져요' },
      { id: 'same', label: '그대로예요' },
    ],
    answerId: 'up',
    explain: '단락할 때 우회되던 $R_2$에 다시 전류가 흘러요. 그래서 출력에서 보는 저항에 $R_2$가 더해져요.',
    mode: 'vv',
    check: {
      before: { ports: { 'sense-rem': 'short' } },
      after: { ports: { 'sense-rem': 'open' } },
      tiles: ['출력측 감지 로딩'],
    },
  },
  params: [
    { key: 'vv_r1', mode: 'vv', label: '상단 저항 R1', min: 1, max: 10, step: 0.5, unit: 'kΩ', def: 3 },
    { key: 'vv_r2', mode: 'vv', label: '하단 저항 R2', min: 0.5, max: 5, step: 0.5, unit: 'kΩ', def: 1 },
    { key: 'vc_rf', mode: 'vc', label: '귀환 저항 RF', min: 1, max: 50, step: 1, unit: 'kΩ', def: 10 },
    { key: 'cv_rm', mode: 'cv', label: '감지 저항 RM', min: 0.1, max: 2.0, step: 0.1, unit: 'kΩ', def: 0.5 },
    { key: 'cc_rm', mode: 'cc', label: '감지 저항 RM', min: 0.5, max: 5, step: 0.5, unit: 'kΩ', def: 1.5 },
    { key: 'cc_rf', mode: 'cc', label: '귀환 저항 RF', min: 0.5, max: 10, step: 0.5, unit: 'kΩ', def: 3 },
    { key: 'vt', modes: ['vv', 'vc'], label: '시험 전압 Vt', min: 0.5, max: 5, step: 0.5, unit: 'V', def: 1 },
    { key: 'it', modes: ['cv', 'cc'], label: '시험 전류 It', min: 0.5, max: 5, step: 0.5, unit: 'mA', def: 1 },
  ],
  steps: [
    {
      mode: 'vv',
      title: '1. 원래 연결 위치 확인',
      who: '감지→전압 입력(∞) · 반송→전압 출력(0)',
      text: '감지 복제의 남은 포트는 원래 전압 입력(∞)에, 반송 복제의 남은 포트는 원래 전압 출력(0)에 붙어 있었어요. 초기 상태처럼 반대로 꽂으면 양쪽 로딩이 모두 틀어져요.',
      params: { vv_r1: 3, vv_r2: 1, vt: 1 },
      ports: { 'sense-rem': 'short', 'return-rem': 'open' },
    },
    {
      mode: 'vv',
      title: '2. V-V 정답 종단 조립',
      who: '감지 개방 · 반송 단락',
      text: '감지 복제를 개방하면 출력 로딩 R1 + R2 = 4.00 kΩ, 반송 복제를 단락하면 입력 로딩 R1 ∥ R2 = 750 Ω이 정확히 남아요.',
      params: { vv_r1: 3, vv_r2: 1, vt: 1 },
      ports: { 'sense-rem': 'open', 'return-rem': 'short' },
    },
    {
      mode: 'vc',
      title: '1. 둘 다 개방했을 때의 함정',
      who: 'RF 전류 경로 차단 → 로딩 소실',
      text: 'V-V처럼 감지 복제를 개방하면 RF에 전류가 0이 되어 출력·입력 로딩이 모두 ∞로 사라져요.',
      params: { vc_rf: 10, vt: 1 },
      ports: { 'sense-rem': 'open', 'return-rem': 'open' },
    },
    {
      mode: 'vc',
      title: '2. V-C 정답 종단 조립',
      who: '감지 단락 · 반송 단락',
      text: '원래 전류 입력(0)과 전압 출력(0) 자리이므로 두 복제본 모두 접지로 단락해 양쪽 모두 RF = 10.0 kΩ 로딩을 남겨요.',
      params: { vc_rf: 10, vt: 1 },
      ports: { 'sense-rem': 'short', 'return-rem': 'short' },
    },
    {
      mode: 'cv',
      title: '1. 둘 다 접지했을 때의 단락 왜곡',
      who: 'RM이 우회되어 0 Ω',
      text: 'C-V에서 남은 포트를 접지로 단락하면 RM 양단이 접지되어 직렬 로딩이 0 Ω으로 사라져요. (교과서 보충: Razavi 예제 12.30)',
      params: { cv_rm: 0.5, it: 1 },
      ports: { 'sense-rem': 'short', 'return-rem': 'short' },
    },
    {
      mode: 'cv',
      title: '2. C-V 정답 종단 조립',
      who: '감지 개방 · 반송 개방',
      text: '원래 전압 입력(∞)과 전류 출력(∞) 자리이므로 두 복제본 모두 개방해 직렬 로딩 RM = 500 Ω을 유지해요.',
      params: { cv_rm: 0.5, it: 1 },
      ports: { 'sense-rem': 'open', 'return-rem': 'open' },
    },
    {
      mode: 'cc',
      title: '1. 달린 쪽 기준으로 반대 조립한 오답',
      who: '감지 개방 · 반송 단락 (반대)',
      text: '감지 복제가 출력 쪽이라고 개방하고 반송 복제를 입력 쪽이라고 단락하면 출력 로딩은 +50%, 입력 로딩은 −33.3% 왜곡돼요. (교과서 보충: Razavi 예제 12.32)',
      params: { cc_rm: 1.5, cc_rf: 3, it: 1 },
      ports: { 'sense-rem': 'open', 'return-rem': 'short' },
    },
    {
      mode: 'cc',
      title: '2. C-C 정답 종단 조립',
      who: '감지 단락 · 반송 개방',
      text: '감지 복제는 원래 전류 입력(0)이라 단락해 RM ∥ RF = 1.00 kΩ, 반송 복제는 원래 전류 출력(∞)이라 개방해 RF + RM = 4.50 kΩ이 돼요.',
      params: { cc_rm: 1.5, cc_rf: 3, it: 1 },
      ports: { 'sense-rem': 'short', 'return-rem': 'open' },
    },
  ],
  toggles: [['labels', '노드 배지', true]],
  mistakes: {
    vv: [
      {
        title: '감지 복제를 출력(V) 기준으로 단락',
        text: '감지 복제는 출력 쪽에 달지만 남은 포트는 원래 전방 증폭기의 전압 입력($\\infty$)에 붙어 있었으므로 개방해야 해요. 단락하면 $R_2$가 빠져 $R_{\\text{load,out}}$이 $R_1$으로 줄어요.',
      },
      {
        title: '반송 복제를 입력(V) 기준으로 개방',
        text: '반송 복제의 남은 포트는 원래 전방 증폭기의 전압 출력($0$)에 붙어 있었으므로 단락해야 해요. 개방하면 $R_1$ 경로가 끊겨 $R_1\\parallel R_2$가 아니라 $R_2$만 보여요.',
      },
      {
        title: '실제 포트 저항과 이상적 임피던스의 혼동',
        text: '유한한 비이상 임피던스(예: BJT 베이스 $r_\\pi$나 드레인 출력 저항 $R_D$)가 있어도 복제 종단은 포트의 이상값($R_{\\text{in}}\\approx\\infty\\Rightarrow$ 개방, $R_{\\text{out}}\\approx 0\\Rightarrow$ 단락)으로 근사해요. 참고로 V-V CG 단에서는 귀환이 게이트($\\infty$)로 들어가며, $1/g_m$은 V-C/C-C의 전류 입력(이상값 $0$)에 해당해요.',
      },
    ],
    vc: [
      {
        title: 'V-V를 외워 감지 복제를 개방',
        text: 'V-C의 입력은 전류 입력(이상적 임피던스 $0$)이에요. 감지 복제를 개방하면 $R_F$에 전류가 흐르지 않아 출력 로딩 $R_{D2}\\parallel R_F$가 통째로 빠져 버려요.',
      },
      {
        title: '반송 복제를 개방해 입력 로딩 누락',
        text: 'V-C의 출력은 전압 출력(이상적 임피던스 $0$)이므로 반송 복제도 단락해야 해요. 개방하면 입력 쪽 $R_F$ 로딩이 사라져 $R_{\\text{in,open}}$을 과대 계산해요.',
      },
      {
        title: '입력·출력 저항 증감 방향 혼동',
        text: 'V-C는 출력 전압을 병렬 감지하고 입력 전류를 병렬 반송하므로, 폐루프에서는 $R_{\\text{in,closed}}$와 $R_{\\text{out,closed}}$가 모두 $(1+KR_0)$로 나뉘어 줄어요.',
      },
    ],
    cv: [
      {
        title: '남은 포트를 습관적으로 모두 접지',
        text: 'C-V의 감지·반송 복제는 각각 전압 입력($\\infty$)과 전류 출력($\\infty$)에 붙어 있었으므로 둘 다 개방해야 해요. 접지로 단락하면 $R_M$이 우회되어 $0\\ \\Omega$이 돼요.',
      },
      {
        title: '직렬 감지 저항 R_M의 로딩 무시',
        text: '$R_M$이 작지 않으면(Razavi 예제 12.30) 감지 복제가 개방된 채 출력 경로에 직렬로 남아 $R_{\\text{out,open}}=r_{O1}+R_M$으로 직렬 로딩을 줘요. (교과서 보충)',
      },
      {
        title: '전류 출력의 이상적 임피던스를 0 Ω으로 착각',
        text: '이상적인 전류원은 출력 임피던스가 $\\infty$여야 전류를 일정하게 내보내요. 그래서 전류 출력에 붙어 있던 반송 복제는 개방으로 종단해요.',
      },
    ],
    cc: [
      {
        title: '달린 쪽(출력/입력)만 보고 반대로 조립',
        text: '복제의 남은 포트는 자신이 달린 쪽이 아니라 반대편에 원래 붙어 있던 포트(감지→전류 입력 $0$ 단락, 반송→전류 출력 $\\infty$ 개방)를 따라가요.',
      },
      {
        title: '출력 로딩을 R_M + R_F 직렬로 계산',
        text: '감지 복제의 남은 포트를 단락하면 출력에서 접지로 $R_M$과 $R_F$가 병렬로 보여 $R_M\\parallel R_F$가 돼요. 직렬이 되는 쪽은 반송 복제($R_F+R_M$)예요. (교과서 보충)',
      },
      {
        title: '폐루프 입·출력 저항의 (1+KA_I) 방향 혼동',
        text: 'C-C는 입력 병렬 전류 반송이라 $R_{\\text{in,closed}}$는 $(1+KA_I)$로 줄고, 출력 직렬 전류 감지라 $R_{\\text{out,closed}}$는 $(1+KA_I)$배로 커져요.',
      },
    ],
  },
  evaluate(state, mna) {
    const cfg = MODE_CONFIGS[state.mode] || MODE_CONFIGS.vv;
    const senseTerm = state.ports['sense-rem'] === 'short' ? 'short' : 'open';
    const returnTerm = state.ports['return-rem'] === 'short' ? 'short' : 'open';
    const senseOk = senseTerm === cfg.senseAnswer;
    const retOk = returnTerm === cfg.returnAnswer;

    const measured = solveDuplicateBench(cfg.key, state.params, senseTerm, returnTerm, mna);
    if (!measured.ok) {
      return {
        tiles: [{ label: '상태', val: '특이 회로' }],
        diagnosis: { kind: 'bad', singular: true, title: '회로 해석 실패', text: measured.reason || '회로 행렬이 특이해졌습니다.' },
      };
    }

    const errInPct = measured.rLoadIn === null
      ? null
      : ((measured.rLoadIn - measured.rTrueIn) / measured.rTrueIn) * 100;
    const errOutPct = measured.rLoadOut === null
      ? null
      : ((measured.rLoadOut - measured.rTrueOut) / measured.rTrueOut) * 100;

    let statusVal = '양쪽 정답 (0%)';
    if (!senseOk && !retOk) statusVal = '양쪽 오조립';
    else if (!senseOk) statusVal = errOutPct === null ? '감지 로딩 소실' : `감지 ${errOutPct >= 0 ? '+' : ''}${errOutPct.toFixed(0)}%`;
    else if (!retOk) statusVal = errInPct === null ? '반송 로딩 소실' : `반송 ${errInPct >= 0 ? '+' : ''}${errInPct.toFixed(0)}%`;

    const retIsShort = returnTerm === 'short';
    const senseIsShort = senseTerm === 'short';

    const inErrText = (retOk || errInPct === null) ? '' : `, 오차 ${errInPct >= 0 ? '+' : ''}${errInPct.toFixed(1)}%`;
    const outErrText = (senseOk || errOutPct === null) ? '' : `, 오차 ${errOutPct >= 0 ? '+' : ''}${errOutPct.toFixed(1)}%`;
    const inSummary = measured.rLoadIn === null
      ? '전류가 흐르지 않아 입력 로딩 임피던스가 $\\infty$로 소실됐어요'
      : `입력 측 반송 로딩은 $${formatOhmsTex(measured.rLoadIn)}$ (참값 $${formatOhmsTex(measured.rTrueIn)}$${inErrText})예요`;
    const outSummary = measured.rLoadOut === null
      ? '전류가 흐르지 않아 출력 로딩 임피던스가 $\\infty$로 소실됐어요'
      : `출력 측 감지 로딩은 $${formatOhmsTex(measured.rLoadOut)}$ (참값 $${formatOhmsTex(measured.rTrueOut)}$${outErrText})예요`;

    return {
      tiles: [
        { label: '입력측 반송 로딩', val: formatOhms(measured.rLoadIn) },
        { label: '출력측 감지 로딩', val: formatOhms(measured.rLoadOut) },
        { label: '종단 판정', val: statusVal },
      ],
      diagnosis: buildDiagnosis(cfg, senseOk, retOk, measured),
      equations: buildEquations(cfg, state.params),
      summary: `${inSummary}. ${outSummary}.`,
      nodes: {
        ret_in: { badge: formatOhmsShort(measured.rLoadIn), hot: retOk, bad: !retOk },
        sense_in: { badge: formatOhmsShort(measured.rLoadOut), hot: senseOk, bad: !senseOk },
      },
      branches: {
        ret_short: { hot: retIsShort && retOk, bad: retIsShort && !retOk, dim: !retIsShort },
        ret_open: { hot: !retIsShort && retOk, bad: !retIsShort && !retOk, dim: retIsShort },
        sense_short: { hot: senseIsShort && senseOk, bad: senseIsShort && !senseOk, dim: !senseIsShort },
        sense_open: { hot: !senseIsShort && senseOk, bad: !senseIsShort && !senseOk, dim: senseIsShort },
      },
      ports: {
        'return-rem': { ok: retOk, bad: !retOk },
        'sense-rem': { ok: senseOk, bad: !senseOk },
      },
    };
  },
};

module.exports = spec;
