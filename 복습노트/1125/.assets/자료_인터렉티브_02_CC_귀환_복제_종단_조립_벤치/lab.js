// Lab 02: C-C 귀환 복제 종단 조립 벤치 (archetype: 'bench')
// 1125 수업 예제 IV (CG M1 + PMOS CS M2 + R_L + R_F, R_M)

const CC_BREAK_SVG = [
  '<svg viewBox="0 0 540 310" role="img" aria-label="C-C 귀환 개루프 복제 종단 조립 회로도">',
  '  <line class="fig-ink" x1="56" y1="150" x2="56" y2="184"/>',
  '  <line class="fig-ink" x1="56" y1="216" x2="56" y2="262"/>',
  '  <g class="sym" data-symbol="isrc">',
  '    <circle class="fig-ink" cx="56" cy="200" r="16"/>',
  '    <path class="fig-ink" d="M56 210V190M51 196l5-6 5 6"/>',
  '  </g>',
  '  <g class="sym" data-symbol="gnd">',
  '    <line class="fig-ink" x1="44" y1="262" x2="68" y2="262"/>',
  '    <line class="fig-ink" x1="48" y1="268" x2="64" y2="268"/>',
  '    <line class="fig-ink" x1="52" y1="274" x2="60" y2="274"/>',
  '  </g>',
  '  <text class="fig-text fig-math" x="24" y="204" text-anchor="middle">I<tspan baseline-shift="sub" font-size="78%">in</tspan></text>',
  '  <line class="fig-ink" data-branch="in_bus" x1="56" y1="150" x2="210" y2="150"/>',
  '  <circle class="fig-dot" data-node="s1" data-node-color="blue" cx="132" cy="150" r="3.5"/>',
  '  <text class="fig-text fig-math" data-node="s1" data-node-color="blue" x="132" y="126" text-anchor="middle">S<tspan baseline-shift="sub" font-size="78%">1</tspan></text>',
  // Input replica: R_F -> node p_in -> R_M -> GND, with port in_term at p_in
  '  <line class="fig-ink" x1="132" y1="150" x2="132" y2="164"/>',
  '  <g class="sym" data-symbol="resistor">',
  '    <path class="fig-ink" d="M132 164v4l-5 3 10 4-10 4 10 4-10 4 10 4-5 3v4"/>',
  '  </g>',
  '  <text class="fig-text fig-math" x="108" y="185" text-anchor="end">R<tspan baseline-shift="sub" font-size="78%">F</tspan></text>',
  '  <line class="fig-ink" x1="132" y1="198" x2="132" y2="218"/>',
  '  <circle class="fig-dot" cx="132" cy="208" r="3"/>',
  '  <g class="sym" data-symbol="resistor">',
  '    <path class="fig-ink" d="M132 218v4l-5 3 10 4-10 4 10 4-10 4 10 4-5 3v4"/>',
  '  </g>',
  '  <text class="fig-text fig-math" x="108" y="240" text-anchor="end">R<tspan baseline-shift="sub" font-size="78%">M</tspan></text>',
  '  <line class="fig-ink" x1="132" y1="252" x2="132" y2="262"/>',
  '  <g class="sym" data-symbol="gnd">',
  '    <line class="fig-ink" x1="120" y1="262" x2="144" y2="262"/>',
  '    <line class="fig-ink" x1="124" y1="268" x2="140" y2="268"/>',
  '    <line class="fig-ink" x1="128" y1="274" x2="136" y2="274"/>',
  '  </g>',
  '  <line class="fig-ink" x1="132" y1="208" x2="162" y2="208"/>',
  '  <g data-port="in_term">',
  '    <g class="port-chip">',
  '      <rect class="port-chip-bg" x="162" y="195" width="84" height="26" rx="6"/>',
  '      <text class="port-chip" x="204" y="212" text-anchor="middle">개방</text>',
  '    </g>',
  '    <g data-port-view="open"></g>',
  '    <g data-port-view="gnd">',
  '      <g class="sym" data-symbol="gnd">',
  '        <line class="fig-danger" x1="204" y1="221" x2="204" y2="236"/>',
  '        <line class="fig-danger" x1="194" y1="236" x2="214" y2="236"/>',
  '        <line class="fig-danger" x1="198" y1="241" x2="210" y2="241"/>',
  '      </g>',
  '    </g>',
  '  </g>',
  '  <text class="fig-muted" x="204" y="182" text-anchor="middle">입력 복제 종단</text>',
  // M1 CG stage
  '  <line class="fig-ink" x1="210" y1="74" x2="210" y2="110"/>',
  '  <g class="sym" data-symbol="nmos">',
  '    <line class="fig-ink" x1="195" y1="110" x2="195" y2="146"/>',
  '    <line class="fig-ink" x1="200" y1="110" x2="200" y2="146"/>',
  '    <line class="fig-ink" x1="200" y1="114" x2="210" y2="114"/>',
  '    <line class="fig-ink" x1="200" y1="142" x2="210" y2="142"/>',
  '    <line class="fig-ink" x1="210" y1="142" x2="210" y2="150"/>',
  '    <line class="fig-ink" x1="180" y1="128" x2="195" y2="128"/>',
  '  </g>',
  '  <text class="fig-muted fig-math" x="166" y="132" text-anchor="end">V<tspan baseline-shift="sub" font-size="78%">b</tspan></text>',
  '  <text class="fig-text fig-math" x="234" y="132" text-anchor="start">M<tspan baseline-shift="sub" font-size="78%">1</tspan></text>',
  '  <line class="fig-ink" x1="210" y1="74" x2="250" y2="74"/>',
  '  <g class="sym" data-symbol="resistor">',
  '    <path class="fig-ink" d="M250 74h5l3-5 4 10 4-10 4 10 4-10 4 10 3-5h5"/>',
  '  </g>',
  '  <line class="fig-ink" x1="286" y1="74" x2="300" y2="74"/>',
  '  <g class="sym" data-symbol="gnd">',
  '    <line class="fig-ink" x1="300" y1="64" x2="300" y2="84"/>',
  '    <line class="fig-ink" x1="305" y1="68" x2="305" y2="80"/>',
  '  </g>',
  '  <text class="fig-text fig-math" x="268" y="60" text-anchor="middle">R<tspan baseline-shift="sub" font-size="78%">D</tspan></text>',
  // Node X to M2 PMOS
  '  <line class="fig-ink" data-branch="vx_line" x1="210" y1="98" x2="345" y2="98"/>',
  '  <circle class="fig-dot" data-node="x" data-node-color="red" cx="210" cy="98" r="3.5"/>',
  '  <text class="fig-text fig-math" data-node="x" data-node-color="red" x="328" y="78" text-anchor="end">V<tspan baseline-shift="sub" font-size="78%">X</tspan></text>',
  '  <line class="fig-ink" x1="365" y1="64" x2="365" y2="82"/>',
  '  <g class="sym" data-symbol="gnd">',
  '    <line class="fig-ink" x1="353" y1="64" x2="377" y2="64"/>',
  '  </g>',
  '  <text class="fig-muted fig-math" x="392" y="68" text-anchor="start">V<tspan baseline-shift="sub" font-size="78%">DD</tspan></text>',
  '  <g class="sym" data-symbol="pmos">',
  '    <line class="fig-ink" x1="350" y1="82" x2="350" y2="116"/>',
  '    <line class="fig-ink" x1="355" y1="82" x2="355" y2="116"/>',
  '    <line class="fig-ink" x1="355" y1="86" x2="365" y2="86"/>',
  '    <line class="fig-ink" x1="355" y1="112" x2="365" y2="112"/>',
  '    <circle class="fig-ink" cx="346" cy="98" r="3"/>',
  '  </g>',
  '  <text class="fig-text fig-math" x="386" y="102" text-anchor="start">M<tspan baseline-shift="sub" font-size="78%">2</tspan></text>',
  // M2 drain -> r_O2 (right) and R_L (down)
  '  <line class="fig-ink" data-branch="i_out" x1="365" y1="112" x2="365" y2="146"/>',
  '  <circle class="fig-dot" data-node="d2" data-node-color="blue" cx="365" cy="130" r="3.5"/>',
  '  <line class="fig-ink" x1="365" y1="130" x2="465" y2="130"/>',
  '  <line class="fig-ink" x1="465" y1="130" x2="465" y2="148"/>',
  '  <g class="sym" data-symbol="resistor">',
  '    <path class="fig-ink" d="M465 148v4l-5 3 10 4-10 4 10 4-10 4 10 4-5 3v4"/>',
  '  </g>',
  '  <text class="fig-text fig-math" x="488" y="170" text-anchor="start">r<tspan baseline-shift="sub" font-size="78%">O2</tspan></text>',
  '  <line class="fig-ink" x1="465" y1="182" x2="465" y2="200"/>',
  '  <g class="sym" data-symbol="gnd">',
  '    <line class="fig-ink" x1="453" y1="200" x2="477" y2="200"/>',
  '    <line class="fig-ink" x1="457" y1="206" x2="473" y2="206"/>',
  '  </g>',
  // R_L to node P
  '  <g class="sym" data-symbol="resistor">',
  '    <path class="fig-ink" d="M365 146v4l-5 3 10 4-10 4 10 4-10 4 10 4-5 3v4"/>',
  '  </g>',
  '  <text class="fig-text fig-math" x="342" y="168" text-anchor="end">R<tspan baseline-shift="sub" font-size="78%">L</tspan></text>',
  '  <line class="fig-ink" x1="365" y1="180" x2="365" y2="214"/>',
  '  <circle class="fig-dot" data-node="p" data-node-color="red" cx="365" cy="198" r="3.5"/>',
  '  <text class="fig-text fig-math" data-node="p" data-node-color="red" x="344" y="202" text-anchor="end">P</text>',
  // Output replica: R_M to gnd, and R_F to port out_term
  '  <g class="sym" data-symbol="resistor">',
  '    <path class="fig-ink" d="M365 214v4l-5 3 10 4-10 4 10 4-10 4 10 4-5 3v4"/>',
  '  </g>',
  '  <text class="fig-text fig-math" x="342" y="236" text-anchor="end">R<tspan baseline-shift="sub" font-size="78%">M</tspan></text>',
  '  <line class="fig-ink" x1="365" y1="248" x2="365" y2="262"/>',
  '  <g class="sym" data-symbol="gnd">',
  '    <line class="fig-ink" x1="353" y1="262" x2="377" y2="262"/>',
  '    <line class="fig-ink" x1="357" y1="268" x2="373" y2="268"/>',
  '    <line class="fig-ink" x1="361" y1="274" x2="369" y2="274"/>',
  '  </g>',
  '  <line class="fig-ink" x1="365" y1="198" x2="394" y2="198"/>',
  '  <g class="sym" data-symbol="resistor">',
  '    <path class="fig-ink" d="M394 198h4l3-5 4 10 4-10 4 10 4-10 4 10 3-5h4"/>',
  '  </g>',
  '  <text class="fig-text fig-math" x="411" y="224" text-anchor="middle">R<tspan baseline-shift="sub" font-size="78%">F</tspan></text>',
  '  <line class="fig-ink" x1="428" y1="198" x2="438" y2="198"/>',
  '  <g data-port="out_term">',
  '    <g class="port-chip">',
  '      <rect class="port-chip-bg" x="438" y="230" width="88" height="26" rx="6"/>',
  '      <text class="port-chip" x="482" y="247" text-anchor="middle">접지</text>',
  '    </g>',
  '    <g data-port-view="gnd">',
  '      <line class="fig-accent" x1="438" y1="198" x2="438" y2="230"/>',
  '      <g class="sym" data-symbol="gnd">',
  '        <line class="fig-accent" x1="482" y1="256" x2="482" y2="270"/>',
  '        <line class="fig-accent" x1="472" y1="270" x2="492" y2="270"/>',
  '        <line class="fig-accent" x1="476" y1="275" x2="488" y2="275"/>',
  '      </g>',
  '    </g>',
  '    <g data-port-view="open">',
  '      <line class="fig-danger" x1="438" y1="198" x2="438" y2="230"/>',
  '    </g>',
  '  </g>',
  '  <text class="fig-muted" x="482" y="294" text-anchor="middle">출력 복제 종단</text>',
  '  <g data-badges>',
  '    <g data-badge-for="s1" transform="translate(80, 26)"></g>',
  '    <g data-badge-for="x" transform="translate(210, 26)"></g>',
  '    <g data-badge-for="d2" transform="translate(340, 26)"></g>',
  '    <g data-badge-for="p" transform="translate(465, 26)"></g>',
  '  </g>',
  '</svg>',
].join('\n');

const CC_K_SVG = [
  '<svg viewBox="0 0 500 270" role="img" aria-label="C-C 귀환 계수 K 측정 포트 조립 회로도">',
  // Return port on left
  '  <g data-port="ret_port">',
  '    <g class="port-chip">',
  '      <rect class="port-chip-bg" x="34" y="138" width="88" height="26" rx="6"/>',
  '      <text class="port-chip" x="78" y="155" text-anchor="middle">접지</text>',
  '    </g>',
  '    <g data-port-view="gnd">',
  '      <g class="sym" data-symbol="gnd">',
  '        <line class="fig-accent" x1="78" y1="164" x2="78" y2="206"/>',
  '        <line class="fig-accent" x1="66" y1="206" x2="90" y2="206"/>',
  '        <line class="fig-accent" x1="70" y1="212" x2="86" y2="212"/>',
  '        <line class="fig-accent" x1="74" y1="218" x2="82" y2="218"/>',
  '      </g>',
  '    </g>',
  '    <g data-port-view="open"></g>',
  '  </g>',
  '  <text class="fig-muted" x="78" y="122" text-anchor="middle">반송 포트</text>',
  '  <line class="fig-ink" data-branch="if_wire" x1="122" y1="151" x2="184" y2="151"/>',
  '  <circle class="fig-dot" data-node="ret" data-node-color="blue" cx="152" cy="151" r="3.5"/>',
  '  <text class="fig-text fig-math" data-node="ret" data-node-color="blue" x="152" y="176" text-anchor="middle">I<tspan baseline-shift="sub" font-size="78%">F</tspan> →</text>',
  // R_F
  '  <g class="sym" data-symbol="resistor">',
  '    <path class="fig-ink" d="M184 151h6l3-6 5 12 5-12 5 12 5-12 5 12 3-6h6"/>',
  '  </g>',
  '  <text class="fig-text fig-math" x="205" y="124" text-anchor="middle">R<tspan baseline-shift="sub" font-size="78%">F</tspan></text>',
  '  <line class="fig-ink" x1="227" y1="151" x2="290" y2="151"/>',
  '  <circle class="fig-dot" data-node="p" data-node-color="red" cx="290" cy="151" r="3.5"/>',
  '  <text class="fig-text fig-math" data-node="p" data-node-color="red" x="290" y="126" text-anchor="middle">노드 P</text>',
  // R_M to ground
  '  <line class="fig-ink" x1="290" y1="151" x2="290" y2="170"/>',
  '  <g class="sym" data-symbol="resistor">',
  '    <path class="fig-ink" d="M290 170v5l-6 3 12 5-12 5 12 5-12 5 12 5-6 3v5"/>',
  '  </g>',
  '  <text class="fig-text fig-math" x="260" y="196" text-anchor="end">R<tspan baseline-shift="sub" font-size="78%">M</tspan></text>',
  '  <line class="fig-ink" x1="290" y1="211" x2="290" y2="232"/>',
  '  <g class="sym" data-symbol="gnd">',
  '    <line class="fig-ink" x1="278" y1="232" x2="302" y2="232"/>',
  '    <line class="fig-ink" x1="282" y1="238" x2="298" y2="238"/>',
  '    <line class="fig-ink" x1="286" y1="244" x2="294" y2="244"/>',
  '  </g>',
  // Sense port on right
  '  <line class="fig-ink" data-branch="iout_wire" x1="290" y1="151" x2="366" y2="151"/>',
  '  <g data-port="sense_port">',
  '    <g class="port-chip">',
  '      <rect class="port-chip-bg" x="366" y="138" width="98" height="26" rx="6"/>',
  '      <text class="port-chip" x="415" y="155" text-anchor="middle">전류원</text>',
  '    </g>',
  '    <g data-port-view="isrc">',
  '      <g class="sym" data-symbol="isrc">',
  '        <line class="fig-accent" x1="415" y1="164" x2="415" y2="178"/>',
  '        <circle class="fig-accent" cx="415" cy="194" r="16"/>',
  '        <path class="fig-accent" d="M415 204V184M410 190l5-6 5 6"/>',
  '        <line class="fig-accent" x1="415" y1="210" x2="415" y2="232"/>',
  '      </g>',
  '      <g class="sym" data-symbol="gnd">',
  '        <line class="fig-accent" x1="403" y1="232" x2="427" y2="232"/>',
  '        <line class="fig-accent" x1="407" y1="238" x2="423" y2="238"/>',
  '      </g>',
  '    </g>',
  '    <g data-port-view="gnd">',
  '      <g class="sym" data-symbol="gnd">',
  '        <line class="fig-danger" x1="415" y1="164" x2="415" y2="206"/>',
  '        <line class="fig-danger" x1="403" y1="206" x2="427" y2="206"/>',
  '        <line class="fig-danger" x1="407" y1="212" x2="423" y2="212"/>',
  '      </g>',
  '    </g>',
  '  </g>',
  '  <text class="fig-muted" x="415" y="122" text-anchor="middle">감지 포트 P</text>',
  '  <g data-badges>',
  '    <g data-badge-for="ret" transform="translate(150, 26)"></g>',
  '    <g data-badge-for="p" transform="translate(340, 26)"></g>',
  '  </g>',
  '</svg>',
].join('\n');

const GM1_MS = 2; // 1/gm1 = 0.5 kOhm
const RD_K = 10;
const GM2_MS = 5;
const RO2_K = 50;
const RL_K = 1;

const spec = {
  id: 'cc-feedback-termination-bench',
  title: 'C-C 귀환 복제 종단 조립 벤치',
  archetype: 'bench',
  modes: [
    {
      key: 'open_break',
      label: '개루프 복제 종단',
      svg: CC_BREAK_SVG,
      ariaLabel: 'C-C 귀환 개루프 복제 종단 조립 회로도',
      viewBox: '0 0 540 310',
      ports: [
        {
          id: 'in_term',
          label: '입력 쪽 복제 감지 포트',
          options: [
            { id: 'open', label: '개방 (전류 출력 ∞, 정답)', shortLabel: '개방' },
            { id: 'gnd', label: '접지 (단락 오조립)', shortLabel: '접지' },
          ],
          def: 'open',
          answer: 'open',
          badOption: 'gnd',
        },
        {
          id: 'out_term',
          label: '출력 쪽 복제 반송 포트',
          options: [
            { id: 'gnd', label: '접지 (전류 입력 0, 정답)', shortLabel: '접지' },
            { id: 'open', label: '개방 (오조립)', shortLabel: '개방' },
          ],
          def: 'gnd',
          answer: 'gnd',
          badOption: 'open',
        },
      ],
      presets: [
        { id: 'correct_break', label: '정답 조립 (개방 / 접지)', params: { rf: 10, rm: 1 }, ports: { in_term: 'open', out_term: 'gnd' } },
        { id: 'both_open', label: '오조립: 둘 다 개방', params: { rf: 10, rm: 1 }, ports: { in_term: 'open', out_term: 'open' } },
        { id: 'both_gnd', label: '오조립: 둘 다 접지', params: { rf: 10, rm: 1 }, ports: { in_term: 'gnd', out_term: 'gnd' } },
      ],
    },
    {
      key: 'k_measure',
      label: '귀환 계수 K 측정',
      svg: CC_K_SVG,
      ariaLabel: 'C-C 귀환 계수 K 측정 포트 조립 회로도',
      viewBox: '0 0 500 270',
      ports: [
        {
          id: 'sense_port',
          label: '감지 포트 P 입력',
          options: [
            { id: 'isrc', label: '전류원 I_out 인가 (정답)', shortLabel: '전류원' },
            { id: 'gnd', label: '접지 단락 (오조립)', shortLabel: '접지 단락' },
          ],
          def: 'isrc',
          answer: 'isrc',
          badOption: 'gnd',
        },
        {
          id: 'ret_port',
          label: '반송 포트 종단',
          options: [
            { id: 'gnd', label: '접지 단락해 I_F 측정 (정답)', shortLabel: '접지' },
            { id: 'open', label: '개방 (전류 0 오조립)', shortLabel: '개방' },
          ],
          def: 'gnd',
          answer: 'gnd',
          badOption: 'open',
        },
      ],
      presets: [
        { id: 'k_ok', label: '정답 조립 (I_out / 접지)', params: { rf: 10, rm: 1 }, ports: { sense_port: 'isrc', ret_port: 'gnd' } },
        { id: 'k_open_ret', label: '오조립: 반송 포트 개방', params: { rf: 10, rm: 1 }, ports: { sense_port: 'isrc', ret_port: 'open' } },
        { id: 'k_gnd_sense', label: '오조립: 감지 포트 단락', params: { rf: 10, rm: 1 }, ports: { sense_port: 'gnd', ret_port: 'gnd' } },
      ],
    },
  ],
  predict: {
    mode: 'open_break',
    prompt: 'C-C 귀환에서 출력 쪽 복제의 반송 포트를 접지 대신 잘못 **개방**하면, 출력 쪽 복제 저항은 정답($R_F \\parallel R_M$)보다 어떻게 바뀔까요?',
    options: [
      { id: 'larger', label: 'R_M만 남아 더 커진다' },
      { id: 'smaller', label: '0에 가까워져 더 작아진다' },
      { id: 'same', label: '변하지 않는다' },
    ],
    answerId: 'larger',
    explain: '출력 쪽 복제의 반송 포트를 개방하면 $R_F$로 전류가 흐르지 못해 $R_F \\parallel R_M$ 대신 $R_M$만 남습니다($0.91\\text{ k}\\Omega \\to 1.00\\text{ k}\\Omega$).',
    check: {
      before: { params: { rf: 10, rm: 1 }, ports: { in_term: 'open', out_term: 'gnd' } },
      after: { ports: { in_term: 'open', out_term: 'open' } },
      tiles: ['출력 복제 저항', '개루프 전류 이득'],
    },
  },
  params: [
    { key: 'rf', label: '귀환 저항 R_F', min: 1, max: 50, step: 0.5, unit: 'kΩ', def: 10 },
    { key: 'rm', label: '감지 저항 R_M', min: 0.1, max: 10, step: 0.1, unit: 'kΩ', def: 1 },
  ],
  toggles: [['labels', '노드 배지', true]],
  mistakes: {
    open_break: [
      {
        title: 'C-V 습관대로 두 복제를 모두 개방',
        text: 'C-C 귀환의 반송 쪽은 원래 전류 입력(이상 임피던스 $0$)에 붙어 있었으므로 출력 쪽 복제는 반드시 접지해야 $R_F \\parallel R_M$이 됩니다.',
      },
      {
        title: '입력 쪽 복제를 접지해 R_M을 단락시킴',
        text: '입력 쪽 복제의 감지 포트는 원래 전류 출력(이상 임피던스 $\\infty$)에 붙어 있었으므로 개방해야 $R_F + R_M$이 남습니다.',
      },
      {
        title: '출력 임피던스에서 r_O2와 R_F‖R_M을 병렬로 계산',
        text: '부하 $R_L$ 양단에서 위쪽 $r_{O2}$와 아래쪽 $R_F \\parallel R_M$은 같은 AC 접지로 이어지므로 직렬 합 $r_{O2} + R_F \\parallel R_M$입니다.',
      },
    ],
    k_measure: [
      {
        title: '전류 반송 포트를 개방하고 I_F를 측정하려 함',
        text: '반송량이 전류이므로 반송 포트를 접지(단락)해야 전류 $I_F$가 흐릅니다. 개방하면 $I_F = 0$이 되어 $K = 0$으로 잘못 구해집니다.',
      },
      {
        title: 'I_F의 양의 방향을 노드 P에서 나가는 쪽으로 혼동',
        text: '$I_F$는 원래 회로에서 입력 노드로부터 빠지는 방향(반송 포트 $\\to P$)을 양으로 정의하므로 $K = -R_M/(R_F+R_M) < 0$이 됩니다.',
      },
      {
        title: 'K < 0만 보고 양의 귀환이라고 단정',
        text: 'PMOS 둘째 단 때문에 $A_{I,\\text{open}} < 0$이므로 루프 이득 $K A_{I,\\text{open}} > 0$이 되어 음의 귀환입니다.',
      },
    ],
  },
  evaluate(state, mna) {
    const rfK = Number(state.params.rf);
    const rmK = Number(state.params.rm);
    const rf = rfK * 1e3;
    const rm = rmK * 1e3;

    if (state.mode === 'open_break') {
      const inTerm = state.ports.in_term || 'open';
      const outTerm = state.ports.out_term || 'gnd';
      const iInA = 1e-6; // 1 uA test input

      const elements = [
        // Input current source I_in into s1
        { id: 'iin', type: 'isrc', n1: '0', n2: 's1', value: iInA },
        // Input replica: s1 --R_F--> pin --R_M--> 0; if in_term=='gnd', short pin to 0
        { id: 'rf_in', type: 'R', n1: 's1', n2: 'pin', value: rf },
        { id: 'rm_in', type: 'R', n1: 'pin', n2: '0', value: rm },
        inTerm === 'gnd'
          ? { id: 'in_short', type: 'short', n1: 'pin', n2: '0' }
          : { id: 'in_short', type: 'open', n1: 'pin', n2: '0' },
        // M1 CG: gate=0, source=s1, drain=x
        { id: 'm1', type: 'vccs', n1: 'x', n2: 's1', cp: '0', cn: 's1', gm: GM1_MS * 1e-3 },
        { id: 'rd', type: 'R', n1: 'x', n2: '0', value: RD_K * 1e3 },
        // M2 PMOS CS: gate=x, source=0, drain=d2
        { id: 'm2', type: 'vccs', n1: '0', n2: 'd2', cp: '0', cn: 'x', gm: GM2_MS * 1e-3 },
        { id: 'ro2', type: 'R', n1: 'd2', n2: '0', value: RO2_K * 1e3 },
        { id: 'rl', type: 'R', n1: 'd2', n2: 'p', value: RL_K * 1e3 },
        // Output replica: R_M from p to 0, R_F from p to 0 (if gnd) or open
        { id: 'rm_out', type: 'R', n1: 'p', n2: '0', value: rm },
        outTerm === 'gnd'
          ? { id: 'rf_out', type: 'R', n1: 'p', n2: '0', value: rf }
          : { id: 'rf_out', type: 'open', n1: 'p', n2: '0' },
      ];

      const solved = mna.solveCircuit({ elements });
      if (!solved.ok) {
        return {
          tiles: [{ label: '상태', val: '특이(해석 불가)' }],
          diagnosis: { kind: 'bad', singular: true, title: '회로 특이 발생', text: solved.reason },
        };
      }

      const vS1Mv = solved.nodes.s1.re * 1e3;
      const vXMv = solved.nodes.x.re * 1e3;
      const vD2Mv = solved.nodes.d2.re * 1e3;
      const vPMv = solved.nodes.p.re * 1e3;
      const iOutUa = solved.branches.rl.re * 1e6;
      const aiOpen = solved.branches.rl.re / iInA;
      const rInOpenK = (solved.nodes.s1.re / iInA) * 1e-3;
      const rInRepK = inTerm === 'open' ? (rfK + rmK) : rfK;
      const rOutRepK = outTerm === 'gnd' ? (rfK * rmK) / (rfK + rmK) : rmK;
      const rOutOpenK = RO2_K + rOutRepK;

      const inOk = inTerm === 'open';
      const outOk = outTerm === 'gnd';
      let diag;
      if (inOk && outOk) {
        diag = {
          kind: 'ok',
          title: '정답 조립 완료 (입력 개방 · 출력 접지)',
          text: `입력 쪽 복제는 $R_F+R_M = ${rInRepK.toFixed(2)}\\text{ k}\\Omega$, 출력 쪽 복제는 $R_F \\parallel R_M = ${rOutRepK.toFixed(2)}\\text{ k}\\Omega$으로 정확히 반영되었습니다.`,
        };
      } else if (!inOk && !outOk) {
        diag = {
          kind: 'bad',
          title: '양쪽 포트 모두 오조립',
          text: '입력 쪽 복제를 접지해 $R_M$이 단락되었고($R_F$만 남음), 출력 쪽 복제를 개방해 $R_F$가 빠졌습니다($R_M$만 남음). 원래 상대의 이상 임피던스(전류 출력 $\\infty$, 전류 입력 $0$)로 종단하세요.',
        };
      } else if (!inOk) {
        diag = {
          kind: 'bad',
          title: '입력 복제 오조립 (접지됨)',
          text: `입력 쪽 감지 포트를 접지해 $R_M$이 단락되었습니다. 입력 복제 저항이 $R_F+R_M$ 대신 $R_F = ${rfK.toFixed(1)}\\text{ k}\\Omega$으로 줄어들었습니다.`,
        };
      } else {
        diag = {
          kind: 'bad',
          title: '출력 복제 오조립 (개방됨)',
          text: `출력 쪽 반송 포트를 개방해 $R_F$로 전류가 흐르지 못합니다. 출력 복제 저항이 $R_F\\parallel R_M$ 대신 $R_M = ${rmK.toFixed(2)}\\text{ k}\\Omega$으로 커졌습니다.`,
        };
      }

      return {
        tiles: [
          { label: '출력 복제 저항', val: `${rOutRepK.toFixed(2)} kΩ` },
          { label: '개루프 전류 이득', val: `${aiOpen.toFixed(2)} A/A` },
          { label: 'R_in / R_out', val: `${rInOpenK.toFixed(2)} / ${rOutOpenK.toFixed(2)} kΩ` },
        ],
        diagnosis: diag,
        formula: '$$\\begin{aligned}R_{\\text{in,open}} &= \\frac{1}{g_{m1}} \\parallel (R_F+R_M) \\\\ R_{\\text{out,open}} &= r_{O2} + (R_F \\parallel R_M)\\end{aligned}$$',
        summary: `현재 입력 복제는 $${rInRepK.toFixed(2)}\\text{ k}\\Omega$(${inOk ? '개방 정답' : '접지 오조립'}), 출력 복제는 $${rOutRepK.toFixed(2)}\\text{ k}\\Omega$(${outOk ? '접지 정답' : '개방 오조립'})입니다. $I_{\\text{in}}=1\\ \\mu\\text{A}$일 때 $I_{\\text{out}} = ${iOutUa.toFixed(2)}\\ \\mu\\text{A}$입니다.`,
        nodes: {
          s1: { v: Number(vS1Mv.toFixed(2)), unit: 'mV', hot: !inOk },
          x: { v: Number(vXMv.toFixed(2)), unit: 'mV' },
          d2: { v: Number(vD2Mv.toFixed(1)), unit: 'mV' },
          p: { v: Number(vPMv.toFixed(2)), unit: 'mV', bad: !outOk },
        },
        branches: {
          in_bus: { hot: true, dir: 'fwd' },
          vx_line: { hot: true, dir: 'fwd' },
          i_out: { hot: inOk && outOk, bad: !outOk, dir: 'rev' },
        },
        ports: {
          in_term: { ok: inOk, bad: !inOk },
          out_term: { ok: outOk, bad: !outOk },
        },
      };
    }

    // Mode 2: k_measure
    const sensePort = state.ports.sense_port || 'isrc';
    const retPort = state.ports.ret_port || 'gnd';
    const iTestMa = 1; // 1 mA into node P
    const iTestA = iTestMa * 1e-3;

    const elements = [
      { id: 'rm_k', type: 'R', n1: 'p', n2: '0', value: rm },
      retPort === 'gnd'
        ? { id: 'rf_k', type: 'R', n1: 'ret', n2: 'p', value: rf }
        : { id: 'rf_k', type: 'open', n1: 'ret', n2: 'p' },
      { id: 'ret_gnd', type: 'short', n1: 'ret', n2: '0' },
      sensePort === 'isrc'
        ? { id: 'is_k', type: 'isrc', n1: '0', n2: 'p', value: iTestA }
        : { id: 'is_k', type: 'short', n1: 'p', n2: '0' },
    ];

    const solved = mna.solveCircuit({ elements });
    if (!solved.ok) {
      return {
        tiles: [{ label: '상태', val: '특이(해석 불가)' }],
        diagnosis: { kind: 'bad', singular: true, title: '회로 특이 발생', text: solved.reason },
      };
    }

    const vPMv = solved.nodes.p.re * 1e3;
    // I_F positive direction is ret -> p (leaving input node toward P)
    const iFMa = solved.branches.rf_k.re * 1e3;
    const kVal = sensePort === 'isrc' ? (iFMa / iTestMa) : 0;
    const senseOk = sensePort === 'isrc';
    const retOk = retPort === 'gnd';

    let diag;
    if (senseOk && retOk) {
      diag = {
        kind: 'ok',
        title: '정답 K 측정 조립 완료',
        text: `감지 포트에 $I_{\\text{out}}=1\\text{ mA}$를 넣고 반송 포트를 접지해 $I_F = ${iFMa.toFixed(3)}\\text{ mA}$를 얻었습니다. 따라서 $K = I_F/I_{\\text{out}} = ${kVal.toFixed(4)}$입니다.`,
      };
    } else if (!senseOk) {
      diag = {
        kind: 'bad',
        title: '감지 포트 오조립 (접지 단락)',
        text: '감지 포트 $P$를 접지로 단락하면 $V_P = 0\\text{ V}$가 되어 전류 $I_{\\text{out}}$을 주입할 수 없고 $K$를 측정할 수 없습니다.',
      };
    } else {
      diag = {
        kind: 'bad',
        title: '반송 포트 오조립 (개방됨)',
        text: '전류를 반송하는 포트를 개방하면 $R_F$로 전류가 흐르지 못해 $I_F = 0$이 됩니다. 반송 포트는 반드시 접지(단락)해야 합니다.',
      };
    }

    return {
      tiles: [
        { label: '귀환 계수 K', val: senseOk ? `${kVal.toFixed(4)} A/A` : '측정 불가' },
        { label: '반송 전류 I_F', val: `${iFMa.toFixed(3)} mA` },
        { label: '노드 P 전압', val: `${vPMv.toFixed(1)} mV` },
      ],
      diagnosis: diag,
      formula: '$$\\begin{aligned}I_F &= -\\frac{R_M}{R_F + R_M} I_{\\text{out}} \\\\ K &= \\frac{I_F}{I_{\\text{out}}} = -\\frac{R_M}{R_F + R_M}\\end{aligned}$$',
      summary: senseOk && retOk
        ? `$P$로 들어온 $I_{\\text{out}} = 1\\text{ mA}$가 $R_M$과 $R_F$로 나뉘어 $R_F$ 쪽으로 $|I_F| = ${Math.abs(iFMa).toFixed(3)}\\text{ mA}$가 왼쪽으로 빠져나갑니다. 양의 방향(오른쪽)과 반대이므로 $K < 0$입니다.`
        : '포트 조립이 잘못되어 정상적인 $K$ 측정이 이루어지지 않습니다. 감지 포트는 전류 인가, 반송 포트는 접지로 맞춰 보세요.',
      nodes: {
        ret: { v: 0, unit: 'V', ok: retOk, bad: !retOk },
        p: { v: Number(vPMv.toFixed(1)), unit: 'mV', hot: senseOk && retOk, bad: !senseOk },
      },
      branches: {
        if_wire: { hot: senseOk && retOk, bad: !retOk, dir: iFMa >= 0 ? 'fwd' : 'rev' },
        iout_wire: { hot: senseOk, bad: !senseOk, dir: 'rev' },
      },
      ports: {
        sense_port: { ok: senseOk, bad: !senseOk },
        ret_port: { ok: retOk, bad: !retOk },
      },
    };
  },
};

module.exports = spec;
