// Lab 03: C-C 귀환 신호 경로와 루프 이득 부호 (archetype: 'probe')
// 1125 수업 예제 IV (CG M1 + PMOS CS M2 + R_L + R_F, R_M)

const CC_OPEN_PATH_SVG = [
  '<svg viewBox="0 0 520 290" role="img" aria-label="C-C 귀환 개루프 2단 전류 경로 소신호 회로도">',
  '  <g data-causal-step="1">',
  '    <line class="fig-ink" x1="56" y1="146" x2="56" y2="178"/>',
  '    <line class="fig-ink" x1="56" y1="210" x2="56" y2="248"/>',
  '    <g class="sym" data-symbol="isrc">',
  '      <circle class="fig-ink" cx="56" cy="194" r="16"/>',
  '      <path class="fig-ink" d="M56 204V184M51 190l5-6 5 6"/>',
  '    </g>',
  '    <g class="sym" data-symbol="gnd">',
  '      <line class="fig-ink" x1="44" y1="248" x2="68" y2="248"/>',
  '      <line class="fig-ink" x1="48" y1="254" x2="64" y2="254"/>',
  '      <line class="fig-ink" x1="52" y1="260" x2="60" y2="260"/>',
  '    </g>',
  '    <text class="fig-text fig-math" x="24" y="198" text-anchor="middle">I<tspan baseline-shift="sub" font-size="78%">in</tspan></text>',
  '    <line class="fig-ink" data-branch="i_in_bus" x1="56" y1="146" x2="200" y2="146"/>',
  '    <circle class="fig-dot" data-node="s1" data-node-color="blue" cx="130" cy="146" r="3.5"/>',
  '    <text class="fig-text fig-math" data-node="s1" data-node-color="blue" x="130" y="130" text-anchor="middle">S<tspan baseline-shift="sub" font-size="78%">1</tspan></text>',
  '    <line class="fig-ink" x1="130" y1="146" x2="130" y2="176"/>',
  '    <g class="sym" data-symbol="resistor">',
  '      <path class="fig-ink" d="M130 176v5l-6 3 12 5-12 5 12 5-12 5 12 5-6 3v5"/>',
  '    </g>',
  '    <line class="fig-ink" x1="130" y1="217" x2="130" y2="248"/>',
  '    <g class="sym" data-symbol="gnd">',
  '      <line class="fig-ink" x1="118" y1="248" x2="142" y2="248"/>',
  '      <line class="fig-ink" x1="122" y1="254" x2="138" y2="254"/>',
  '      <line class="fig-ink" x1="126" y1="260" x2="134" y2="260"/>',
  '    </g>',
  '    <text class="fig-muted fig-math" x="156" y="200" text-anchor="start">R<tspan baseline-shift="sub" font-size="78%">F</tspan>+R<tspan baseline-shift="sub" font-size="78%">M</tspan></text>',
  '  </g>',
  '  <g data-causal-step="2">',
  '    <line class="fig-ink" x1="200" y1="74" x2="200" y2="108"/>',
  '    <g class="sym" data-symbol="nmos">',
  '      <line class="fig-ink" x1="185" y1="108" x2="185" y2="144"/>',
  '      <line class="fig-ink" x1="190" y1="108" x2="190" y2="144"/>',
  '      <line class="fig-ink" x1="190" y1="112" x2="200" y2="112"/>',
  '      <line class="fig-ink" x1="190" y1="140" x2="200" y2="140"/>',
  '      <line class="fig-ink" x1="200" y1="140" x2="200" y2="146"/>',
  '      <line class="fig-ink" x1="170" y1="126" x2="185" y2="126"/>',
  '    </g>',
  '    <text class="fig-muted fig-math" x="166" y="114" text-anchor="middle">V<tspan baseline-shift="sub" font-size="78%">b</tspan></text>',
  '    <text class="fig-text fig-math" x="224" y="130" text-anchor="start">M<tspan baseline-shift="sub" font-size="78%">1</tspan></text>',
  '    <line class="fig-ink" x1="200" y1="74" x2="244" y2="74"/>',
  '    <g class="sym" data-symbol="resistor">',
  '      <path class="fig-ink" d="M244 74h5l3-5 4 10 4-10 4 10 4-10 4 10 3-5h5"/>',
  '    </g>',
  '    <line class="fig-ink" x1="280" y1="74" x2="294" y2="74"/>',
  '    <g class="sym" data-symbol="gnd">',
  '      <line class="fig-ink" x1="294" y1="64" x2="294" y2="84"/>',
  '      <line class="fig-ink" x1="299" y1="68" x2="299" y2="80"/>',
  '    </g>',
  '    <text class="fig-text fig-math" x="262" y="60" text-anchor="middle">R<tspan baseline-shift="sub" font-size="78%">D</tspan></text>',
  '    <line class="fig-ink" data-branch="vx_line" x1="200" y1="98" x2="340" y2="98"/>',
  '    <circle class="fig-dot" data-node="x" data-node-color="red" cx="200" cy="98" r="3.5"/>',
  '    <text class="fig-text fig-math" data-node="x" data-node-color="red" x="322" y="78" text-anchor="end">V<tspan baseline-shift="sub" font-size="78%">X</tspan></text>',
  '  </g>',
  '  <g data-causal-step="3">',
  '    <line class="fig-ink" x1="360" y1="64" x2="360" y2="82"/>',
  '    <g class="sym" data-symbol="gnd">',
  '      <line class="fig-ink" x1="348" y1="64" x2="372" y2="64"/>',
  '    </g>',
  '    <text class="fig-muted fig-math" x="386" y="68" text-anchor="start">V<tspan baseline-shift="sub" font-size="78%">DD</tspan></text>',
  '    <g class="sym" data-symbol="pmos">',
  '      <line class="fig-ink" x1="345" y1="82" x2="345" y2="116"/>',
  '      <line class="fig-ink" x1="350" y1="82" x2="350" y2="116"/>',
  '      <line class="fig-ink" x1="350" y1="86" x2="360" y2="86"/>',
  '      <line class="fig-ink" x1="350" y1="112" x2="360" y2="112"/>',
  '      <circle class="fig-ink" cx="341" cy="98" r="3"/>',
  '    </g>',
  '    <text class="fig-text fig-math" x="382" y="102" text-anchor="start">M<tspan baseline-shift="sub" font-size="78%">2</tspan></text>',
  '    <line class="fig-ink" data-branch="i_star" x1="360" y1="112" x2="360" y2="136"/>',
  '    <circle class="fig-dot" data-node="d2" data-node-color="blue" cx="360" cy="136" r="3.5"/>',
  '  </g>',
  '  <g data-causal-step="4">',
  '    <line class="fig-ink" x1="360" y1="136" x2="452" y2="136"/>',
  '    <line class="fig-ink" data-branch="i_ro2" x1="452" y1="136" x2="452" y2="162"/>',
  '    <g class="sym" data-symbol="resistor">',
  '      <path class="fig-ink" d="M452 162v5l-6 3 12 5-12 5 12 5-12 5 12 5-6 3v5"/>',
  '    </g>',
  '    <text class="fig-text fig-math" x="478" y="186" text-anchor="start">r<tspan baseline-shift="sub" font-size="78%">O2</tspan></text>',
  '    <line class="fig-ink" x1="452" y1="203" x2="452" y2="248"/>',
  '    <g class="sym" data-symbol="gnd">',
  '      <line class="fig-ink" x1="440" y1="248" x2="464" y2="248"/>',
  '      <line class="fig-ink" x1="444" y1="254" x2="460" y2="254"/>',
  '    </g>',
  '    <line class="fig-ink" data-branch="i_out" x1="360" y1="136" x2="360" y2="152"/>',
  '    <g class="sym" data-symbol="resistor">',
  '      <path class="fig-ink" d="M360 152v4l-5 3 10 4-10 4 10 4-10 4 10 4-5 3v4"/>',
  '    </g>',
  '    <text class="fig-text fig-math" x="336" y="172" text-anchor="end">R<tspan baseline-shift="sub" font-size="78%">L</tspan></text>',
  '    <line class="fig-ink" x1="360" y1="186" x2="360" y2="204"/>',
  '    <circle class="fig-dot" data-node="p" data-node-color="red" cx="360" cy="196" r="3.5"/>',
  '    <text class="fig-text fig-math" data-node="p" data-node-color="red" x="336" y="200" text-anchor="end">P</text>',
  '    <g class="sym" data-symbol="resistor">',
  '      <path class="fig-ink" d="M360 204v4l-5 3 10 4-10 4 10 4-10 4 10 4-5 3v4"/>',
  '    </g>',
  '    <text class="fig-muted fig-math" x="336" y="226" text-anchor="end">R<tspan baseline-shift="sub" font-size="78%">F</tspan>‖R<tspan baseline-shift="sub" font-size="78%">M</tspan></text>',
  '    <line class="fig-ink" x1="360" y1="238" x2="360" y2="248"/>',
  '    <g class="sym" data-symbol="gnd">',
  '      <line class="fig-ink" x1="348" y1="248" x2="372" y2="248"/>',
  '      <line class="fig-ink" x1="352" y1="254" x2="368" y2="254"/>',
  '    </g>',
  '  </g>',
  '  <g data-badges>',
  '    <g data-badge-for="s1" transform="translate(80, 26)"></g>',
  '    <g data-badge-for="x" transform="translate(205, 26)"></g>',
  '    <g data-badge-for="d2" transform="translate(335, 26)"></g>',
  '    <g data-badge-for="p" transform="translate(455, 26)"></g>',
  '  </g>',
  '</svg>',
].join('\n');

const CC_CLOSED_PATH_SVG = [
  '<svg viewBox="0 0 520 295" role="img" aria-label="C-C 귀환 폐루프 음의 귀환 부호 추적 회로도">',
  '  <g data-causal-step="1,5">',
  '    <line class="fig-ink" x1="56" y1="146" x2="56" y2="178"/>',
  '    <line class="fig-ink" x1="56" y1="210" x2="56" y2="252"/>',
  '    <g class="sym" data-symbol="isrc">',
  '      <circle class="fig-ink" cx="56" cy="194" r="16"/>',
  '      <path class="fig-ink" d="M56 204V184M51 190l5-6 5 6"/>',
  '    </g>',
  '    <g class="sym" data-symbol="gnd">',
  '      <line class="fig-ink" x1="44" y1="252" x2="68" y2="252"/>',
  '      <line class="fig-ink" x1="48" y1="258" x2="64" y2="258"/>',
  '      <line class="fig-ink" x1="52" y1="264" x2="60" y2="264"/>',
  '    </g>',
  '    <text class="fig-text fig-math" x="24" y="198" text-anchor="middle">I<tspan baseline-shift="sub" font-size="78%">in</tspan></text>',
  '    <line class="fig-ink" data-branch="i_in_bus" x1="56" y1="146" x2="200" y2="146"/>',
  '    <circle class="fig-dot" data-node="s1" data-node-color="blue" cx="128" cy="146" r="3.5"/>',
  '    <text class="fig-text fig-math" data-node="s1" data-node-color="blue" x="128" y="128" text-anchor="middle">S<tspan baseline-shift="sub" font-size="78%">1</tspan></text>',
  '  </g>',
  '  <g data-causal-step="2">',
  '    <line class="fig-ink" x1="200" y1="74" x2="200" y2="108"/>',
  '    <g class="sym" data-symbol="nmos">',
  '      <line class="fig-ink" x1="185" y1="108" x2="185" y2="144"/>',
  '      <line class="fig-ink" x1="190" y1="108" x2="190" y2="144"/>',
  '      <line class="fig-ink" x1="190" y1="112" x2="200" y2="112"/>',
  '      <line class="fig-ink" x1="190" y1="140" x2="200" y2="140"/>',
  '      <line class="fig-ink" x1="200" y1="140" x2="200" y2="146"/>',
  '      <line class="fig-ink" x1="170" y1="126" x2="185" y2="126"/>',
  '    </g>',
  '    <text class="fig-muted fig-math" x="166" y="114" text-anchor="middle">V<tspan baseline-shift="sub" font-size="78%">b</tspan></text>',
  '    <text class="fig-text fig-math" x="224" y="130" text-anchor="start">M<tspan baseline-shift="sub" font-size="78%">1</tspan></text>',
  '    <line class="fig-ink" x1="200" y1="74" x2="244" y2="74"/>',
  '    <g class="sym" data-symbol="resistor">',
  '      <path class="fig-ink" d="M244 74h5l3-5 4 10 4-10 4 10 4-10 4 10 3-5h5"/>',
  '    </g>',
  '    <line class="fig-ink" x1="280" y1="74" x2="294" y2="74"/>',
  '    <g class="sym" data-symbol="gnd">',
  '      <line class="fig-ink" x1="294" y1="64" x2="294" y2="84"/>',
  '      <line class="fig-ink" x1="299" y1="68" x2="299" y2="80"/>',
  '    </g>',
  '    <text class="fig-text fig-math" x="262" y="60" text-anchor="middle">R<tspan baseline-shift="sub" font-size="78%">D</tspan></text>',
  '    <line class="fig-ink" data-branch="vx_line" x1="200" y1="98" x2="340" y2="98"/>',
  '    <circle class="fig-dot" data-node="x" data-node-color="red" cx="200" cy="98" r="3.5"/>',
  '    <text class="fig-text fig-math" data-node="x" data-node-color="red" x="322" y="78" text-anchor="end">V<tspan baseline-shift="sub" font-size="78%">X</tspan></text>',
  '  </g>',
  '  <g data-causal-step="3">',
  '    <line class="fig-ink" x1="360" y1="64" x2="360" y2="82"/>',
  '    <g class="sym" data-symbol="gnd">',
  '      <line class="fig-ink" x1="348" y1="64" x2="372" y2="64"/>',
  '    </g>',
  '    <text class="fig-muted fig-math" x="386" y="68" text-anchor="start">V<tspan baseline-shift="sub" font-size="78%">DD</tspan></text>',
  '    <g class="sym" data-symbol="pmos">',
  '      <line class="fig-ink" x1="345" y1="82" x2="345" y2="116"/>',
  '      <line class="fig-ink" x1="350" y1="82" x2="350" y2="116"/>',
  '      <line class="fig-ink" x1="350" y1="86" x2="360" y2="86"/>',
  '      <line class="fig-ink" x1="350" y1="112" x2="360" y2="112"/>',
  '      <circle class="fig-ink" cx="341" cy="98" r="3"/>',
  '    </g>',
  '    <text class="fig-text fig-math" x="382" y="102" text-anchor="start">M<tspan baseline-shift="sub" font-size="78%">2</tspan></text>',
  '    <line class="fig-ink" data-branch="i_out" x1="360" y1="112" x2="360" y2="150"/>',
  '    <circle class="fig-dot" data-node="d2" data-node-color="blue" cx="360" cy="134" r="3.5"/>',
  '    <line class="fig-ink" x1="360" y1="134" x2="452" y2="134"/>',
  '    <line class="fig-ink" x1="452" y1="134" x2="452" y2="160"/>',
  '    <g class="sym" data-symbol="resistor">',
  '      <path class="fig-ink" d="M452 160v5l-6 3 12 5-12 5 12 5-12 5 12 5-6 3v5"/>',
  '    </g>',
  '    <text class="fig-text fig-math" x="478" y="184" text-anchor="start">r<tspan baseline-shift="sub" font-size="78%">O2</tspan></text>',
  '    <line class="fig-ink" x1="452" y1="201" x2="452" y2="252"/>',
  '    <g class="sym" data-symbol="gnd">',
  '      <line class="fig-ink" x1="440" y1="252" x2="464" y2="252"/>',
  '      <line class="fig-ink" x1="444" y1="258" x2="460" y2="258"/>',
  '    </g>',
  '    <g class="sym" data-symbol="resistor">',
  '      <path class="fig-ink" d="M360 150v4l-5 3 10 4-10 4 10 4-10 4 10 4-5 3v4"/>',
  '    </g>',
  '    <text class="fig-text fig-math" x="336" y="172" text-anchor="end">R<tspan baseline-shift="sub" font-size="78%">L</tspan></text>',
  '  </g>',
  '  <g data-causal-step="4">',
  '    <line class="fig-ink" x1="360" y1="184" x2="360" y2="210"/>',
  '    <circle class="fig-dot" data-node="p" data-node-color="red" cx="360" cy="202" r="3.5"/>',
  '    <text class="fig-text fig-math" data-node="p" data-node-color="red" x="386" y="206" text-anchor="start">P</text>',
  '    <g class="sym" data-symbol="resistor">',
  '      <path class="fig-ink" d="M360 210v4l-5 3 10 4-10 4 10 4-10 4 10 4-5 3v4"/>',
  '    </g>',
  '    <text class="fig-text fig-math" x="386" y="232" text-anchor="start">R<tspan baseline-shift="sub" font-size="78%">M</tspan></text>',
  '    <line class="fig-ink" x1="360" y1="244" x2="360" y2="252"/>',
  '    <g class="sym" data-symbol="gnd">',
  '      <line class="fig-ink" x1="348" y1="252" x2="372" y2="252"/>',
  '      <line class="fig-ink" x1="352" y1="258" x2="368" y2="258"/>',
  '    </g>',
  '  </g>',
  '  <g data-causal-step="4,5">',
  '    <path class="fig-accent" data-branch="i_fb" d="M128 146V202H214"/>',
  '    <g class="sym" data-symbol="resistor">',
  '      <path class="fig-accent" d="M214 202h5l3-6 5 12 5-12 5 12 5-12 5 12 3-6h5"/>',
  '    </g>',
  '    <line class="fig-accent" x1="255" y1="202" x2="360" y2="202"/>',
  '    <text class="fig-text fig-math" x="234" y="228" text-anchor="middle">R<tspan baseline-shift="sub" font-size="78%">F</tspan> (I<tspan baseline-shift="sub" font-size="78%">F</tspan> →)</text>',
  '  </g>',
  '  <g data-badges>',
  '    <g data-badge-for="s1" transform="translate(80, 26)"></g>',
  '    <g data-badge-for="x" transform="translate(205, 26)"></g>',
  '    <g data-badge-for="d2" transform="translate(335, 26)"></g>',
  '    <g data-badge-for="p" transform="translate(455, 26)"></g>',
  '  </g>',
  '</svg>',
].join('\n');

const GM1_MS = 2;
const RD_K = 10;
const GM2_MS = 5;
const RL_K = 1;

const spec = {
  id: 'cc-feedback-signal-sign-probe',
  title: 'C-C 귀환 신호 경로와 루프 이득 부호',
  archetype: 'probe',
  modes: [
    {
      key: 'open_path',
      label: '개루프 2단 경로',
      svg: CC_OPEN_PATH_SVG,
      ariaLabel: 'C-C 귀환 개루프 2단 전류 경로 소신호 회로도',
      viewBox: '0 0 520 290',
      causalSteps: [
        { id: 1, label: '입력 전류 분배 (테브난)', detail: 'I_in이 입력 복제(R_F+R_M)와 M1 소스(1/g_m1)로 나뉩니다.' },
        { id: 2, label: 'CG 단 V_X 상승', detail: 'M1 소스로 들어간 전류가 R_D를 지나며 V_X를 올립니다.' },
        { id: 3, label: 'PMOS M2 반전 전류 I*', detail: 'V_X가 오르면 PMOS V_SG2가 줄어 아래 방향 전류 I* = -g_m2 V_X가 음수가 됩니다.' },
        { id: 4, label: 'r_O2·부하 전류 분배', detail: 'I*가 r_O2(I\')와 부하 경로(R_L + R_F‖R_M)로 나뉘어 I_out이 정해집니다.' },
      ],
      presets: [
        { id: 'ex_open', label: '수업 예시 (A_I,open ≈ -46.07)', params: { iin: 1, rf: 10, rm: 1, ro2: 50 } },
        { id: 'low_ro2', label: '낮은 r_O2 (5 kΩ, 분배 손실)', params: { iin: 1, rf: 10, rm: 1, ro2: 5 } },
        { id: 'low_rf', label: '낮은 R_F (2 kΩ, 입력 분배 손실)', params: { iin: 1, rf: 2, rm: 1, ro2: 50 } },
      ],
    },
    {
      key: 'closed_path',
      label: '폐루프 음의 귀환',
      svg: CC_CLOSED_PATH_SVG,
      ariaLabel: 'C-C 귀환 폐루프 음의 귀환 부호 추적 회로도',
      viewBox: '0 0 520 295',
      causalSteps: [
        { id: 1, label: '입력 전류 I_in 인가 (↑)', detail: '양의 입력 전류 I_in이 M1 소스 노드 S1으로 들어옵니다.' },
        { id: 2, label: '드레인 전압 V_X 상승 (↑)', detail: '공통 게이트 M1이 입력 전류를 받아 노드 X 전압 V_X를 올립니다.' },
        { id: 3, label: 'PMOS 출력 I_out 하강 (↓)', detail: 'PMOS M2가 반전 동작해 부하 전류 I_out이 음수 방향으로 내려갑니다.' },
        { id: 4, label: '노드 P 하강(↓) → I_F 상승(↑)', detail: 'V_P가 내려가면서 S1에서 R_F를 통해 P로 빠지는 귀환 전류 I_F가 양수로 커집니다.' },
        { id: 5, label: '입력 KCL I_S1 = I_in - I_F 감소', detail: '빠지는 I_F가 커져 M1으로 들어가는 I_S1을 줄이므로 음의 귀환이 완성됩니다.' },
      ],
      presets: [
        { id: 'ex_closed', label: '수업 예시 (KA ≈ 4.19)', params: { iin: 1, rf: 10, rm: 1, ro2: 50 } },
        { id: 'strong_fb', label: '강한 귀환 (R_M = 3 kΩ)', params: { iin: 1, rf: 10, rm: 3, ro2: 50 } },
        { id: 'neg_in', label: '반대 입력 (I_in = -2 μA)', params: { iin: -2, rf: 10, rm: 1, ro2: 50 } },
      ],
    },
  ],
  predict: {
    mode: 'closed_path',
    prompt: 'C-C 폐루프 회로에서 귀환 계수 $K = -R_M/(R_F+R_M)$은 음수입니다. 입력 전류 $I_{\\text{in}}$을 양의 방향으로 키우면 입력 노드에서 빠지는 귀환 전류 $I_F$는 어떻게 변할까요?',
    options: [
      { id: 'inc', label: '양의 방향으로 커져 I_S1을 줄인다 (음의 귀환)' },
      { id: 'dec', label: '음의 방향으로 흘러 I_S1을 더 키운다 (양의 귀환)' },
      { id: 'zero', label: '0으로 유지된다' },
    ],
    answerId: 'inc',
    explain: 'PMOS $M_2$ 때문에 $I_{\\text{out}}$이 음수로 내려가고 노드 $P$ 전압 $V_P$가 낮아져, 입력 노드 $S_1$에서 $R_F$를 통해 빠지는 $I_F$가 양수로 커집니다. 따라서 $I_{S1} = I_{\\text{in}} - I_F$가 억제되는 음의 귀환입니다.',
    check: {
      before: { params: { iin: 0, rf: 10, rm: 1, ro2: 50 } },
      after: { params: { iin: 2 }, causalStep: 5 },
      tiles: ['귀환 전류 I_F', '출력 전류 I_out'],
    },
  },
  params: [
    { key: 'iin', label: '입력 전류 I_in', min: -5, max: 5, step: 0.5, unit: 'μA', def: 1 },
    { key: 'rf', label: '귀환 저항 R_F', min: 2, max: 50, step: 1, unit: 'kΩ', def: 10 },
    { key: 'rm', label: '감지 저항 R_M', min: 0.2, max: 5, step: 0.2, unit: 'kΩ', def: 1 },
    { key: 'ro2', label: 'M2 출력저항 r_O2', min: 5, max: 100, step: 5, unit: 'kΩ', def: 50 },
  ],
  toggles: [['labels', '노드 배지', true]],
  mistakes: {
    open_path: [
      {
        title: 'PMOS 둘째 단의 반전 부호 누락',
        text: '$M_2$는 PMOS 공통 소스이므로 $V_X$가 오르면 $V_{SG2}$가 줄어 $I^* = -g_{m2}V_X$가 음수가 됩니다. 따라서 $A_{I,\\text{open}} < 0$입니다.',
      },
      {
        title: 'r_O2로 빠지는 전류 분배 손실 무시',
        text: '$M_2$ 드레인 전류 $I^*$는 $r_{O2}$와 부하 경로($R_L + R_F \\parallel R_M$)로 나뉘므로 $r_{O2}$가 작아질수록 $I_{\\text{out}}$ 비율이 줄어듭니다.',
      },
      {
        title: '입력 복제 R_F+R_M과 1/g_m1의 분배 관계 혼동',
        text: '입력 전류 $I_{\\text{in}}$은 $1/g_{m1}$과 $(R_F+R_M)$으로 나뉘므로 $R_F+R_M$이 작아질수록 $M_1$으로 들어가는 전류가 줄어듭니다.',
      },
    ],
    closed_path: [
      {
        title: 'K < 0만 보고 양의 귀환으로 오판',
        text: '귀환의 종류는 $K$의 부호가 아니라 루프 이득 $K A_{I,\\text{open}}$의 부호로 판단합니다. 음수 × 음수 = 양수이므로 음의 귀환입니다.',
      },
      {
        title: 'I_F 방향을 입력으로 들어오는 쪽으로 혼동',
        text: '$I_F$는 입력 노드에서 빠지는 방향($S_1 \\to P$)을 양으로 잡습니다. 그래서 $I_{S1} = I_{\\text{in}} - I_F$가 됩니다.',
      },
      {
        title: '폐루프 입력 임피던스가 커진다고 착각',
        text: '전류를 같은 노드에서 병렬로 빼는 반송이므로 폐루프 입력 임피던스는 $(1+K A_{I,\\text{open}})$로 나눠져 더 작아집니다.',
      },
    ],
  },
  evaluate(state, mna) {
    const iinUa = Number(state.params.iin);
    const iinA = iinUa * 1e-6;
    const rfK = Number(state.params.rf);
    const rmK = Number(state.params.rm);
    const ro2K = Number(state.params.ro2);
    const rf = rfK * 1e3;
    const rm = rmK * 1e3;
    const ro2 = ro2K * 1e3;
    const invGm1K = 1 / GM1_MS; // 0.5 kOhm

    // Analytical open-loop gain & K (always finite even when iin == 0)
    const rInRepK = rfK + rmK;
    const rOutRepK = (rfK * rmK) / (rfK + rmK);
    const stage1K = (rInRepK * RD_K) / (rInRepK + invGm1K);
    const stage2Ms = (-GM2_MS * ro2K) / (ro2K + RL_K + rOutRepK);
    const aiOpenFormula = stage1K * stage2Ms;
    const kVal = -rmK / (rfK + rmK);
    const loopGain = kVal * aiOpenFormula;
    const aiClosed2Port = aiOpenFormula / (1 + loopGain);

    if (state.mode === 'open_path') {
      const solved = mna.solveCircuit({
        elements: [
          { id: 'iin', type: 'isrc', n1: '0', n2: 's1', value: iinA },
          { id: 'r_in_rep', type: 'R', n1: 's1', n2: '0', value: rf + rm },
          { id: 'm1', type: 'vccs', n1: 'x', n2: 's1', cp: '0', cn: 's1', gm: GM1_MS * 1e-3 },
          { id: 'rd', type: 'R', n1: 'x', n2: '0', value: RD_K * 1e3 },
          { id: 'm2', type: 'vccs', n1: '0', n2: 'd2', cp: '0', cn: 'x', gm: GM2_MS * 1e-3 },
          { id: 'ro2', type: 'R', n1: 'd2', n2: '0', value: ro2 },
          { id: 'rl', type: 'R', n1: 'd2', n2: 'p', value: RL_K * 1e3 },
          { id: 'r_out_rep', type: 'R', n1: 'p', n2: '0', value: (rf * rm) / (rf + rm) },
        ],
      });

      if (!solved.ok) {
        return {
          tiles: [{ label: '상태', val: '오류' }],
          diagnosis: { kind: 'bad', title: '회로 해석 실패', text: solved.reason },
        };
      }

      const vS1Mv = solved.nodes.s1.re * 1e3;
      const vXMv = solved.nodes.x.re * 1e3;
      const vD2Mv = solved.nodes.d2.re * 1e3;
      const vPMv = solved.nodes.p.re * 1e3;
      const iOutUa = solved.branches.rl.re * 1e6;
      const iRo2Ua = solved.branches.ro2.re * 1e6;
      const loadSharePct = (ro2K / (ro2K + RL_K + rOutRepK)) * 100;
      const aiOpenVal = Math.abs(iinA) > 1e-15 ? (solved.branches.rl.re / iinA) : aiOpenFormula;

      const dirS1 = vS1Mv > 1e-4 ? 'up' : (vS1Mv < -1e-4 ? 'down' : undefined);
      const dirX = vXMv > 1e-4 ? 'up' : (vXMv < -1e-4 ? 'down' : undefined);
      const dirP = vPMv > 1e-4 ? 'up' : (vPMv < -1e-4 ? 'down' : undefined);

      return {
        tiles: [
          { label: '개루프 전류 이득', val: `${aiOpenVal.toFixed(2)} A/A` },
          { label: '출력 전류 I_out', val: `${iOutUa.toFixed(2)} μA` },
          { label: '부하 분배율', val: `${loadSharePct.toFixed(1)} %` },
        ],
        diagnosis: Math.abs(iinUa) < 1e-9
          ? { kind: 'info', title: '입력 전류 0 μA (무신호)', text: '소신호 입력 $I_{\\text{in}}=0$이라 모든 노드 전압이 $0\\text{ mV}$입니다. $I_{\\text{in}}$을 움직여 신호 경로를 관찰하세요.' }
          : {
              kind: 'ok',
              title: '2단 반전 전류 증폭 (A_I,open < 0)',
              text: `첫 단 $V_X/I_{\\text{in}} = ${stage1K.toFixed(2)}\\text{ k}\\Omega$, 둘째 단 $I_{\\text{out}}/V_X = ${stage2Ms.toFixed(2)}\\text{ mS}$가 곱해져 $A_{I,\\text{open}} = ${aiOpenVal.toFixed(2)}$이 됩니다.`,
            },
        formula: '$$\\begin{aligned}A_{I,\\text{open}} &= \\frac{(R_F+R_M)R_D}{R_F+R_M+1/g_{m1}} \\\\ &\\times \\frac{-g_{m2}r_{O2}}{r_{O2}+R_L+R_F\\parallel R_M}\\end{aligned}$$',
        summary: `현재 $I_{\\text{in}} = ${iinUa.toFixed(1)}\\ \\mu\\text{A}$일 때 $V_X = ${vXMv.toFixed(2)}\\text{ mV}$가 되고, $M_2$ 드레인 전류 중 $${loadSharePct.toFixed(1)}\\%$가 부하 경로로 가 $I_{\\text{out}} = ${iOutUa.toFixed(2)}\\ \\mu\\text{A}$($r_{O2}$ 가지 $${iRo2Ua.toFixed(2)}\\ \\mu\\text{A}$)가 됩니다.`,
        nodes: {
          s1: { v: Number(vS1Mv.toFixed(2)), unit: 'mV', dir: dirS1, hot: state.causalStep === 1 },
          x: { v: Number(vXMv.toFixed(2)), unit: 'mV', dir: dirX, hot: state.causalStep === 2 },
          d2: { v: Number(vD2Mv.toFixed(1)), unit: 'mV', dir: dirP, hot: state.causalStep === 3 },
          p: { v: Number(vPMv.toFixed(2)), unit: 'mV', dir: dirP, hot: state.causalStep === 4 },
        },
        branches: {
          i_in_bus: { hot: state.causalStep === 1, dir: iinUa >= 0 ? 'fwd' : 'rev' },
          vx_line: { hot: state.causalStep === 2, dir: vXMv >= 0 ? 'fwd' : 'rev' },
          i_star: { hot: state.causalStep === 3, dir: iOutUa >= 0 ? 'fwd' : 'rev' },
          i_ro2: { hot: state.causalStep === 4, dir: iRo2Ua >= 0 ? 'fwd' : 'rev' },
          i_out: { hot: state.causalStep === 4, dir: iOutUa >= 0 ? 'fwd' : 'rev' },
        },
      };
    }

    // Mode 2: closed_path (exact closed-loop MNA)
    const solved = mna.solveCircuit({
      elements: [
        { id: 'iin', type: 'isrc', n1: '0', n2: 's1', value: iinA },
        { id: 'm1', type: 'vccs', n1: 'x', n2: 's1', cp: '0', cn: 's1', gm: GM1_MS * 1e-3 },
        { id: 'rd', type: 'R', n1: 'x', n2: '0', value: RD_K * 1e3 },
        { id: 'm2', type: 'vccs', n1: '0', n2: 'd2', cp: '0', cn: 'x', gm: GM2_MS * 1e-3 },
        { id: 'ro2', type: 'R', n1: 'd2', n2: '0', value: ro2 },
        { id: 'rl', type: 'R', n1: 'd2', n2: 'p', value: RL_K * 1e3 },
        { id: 'rm', type: 'R', n1: 'p', n2: '0', value: rm },
        { id: 'rf', type: 'R', n1: 's1', n2: 'p', value: rf },
      ],
    });

    if (!solved.ok) {
      return {
        tiles: [{ label: '상태', val: '오류' }],
        diagnosis: { kind: 'bad', title: '회로 해석 실패', text: solved.reason },
      };
    }

    const vS1Mv = solved.nodes.s1.re * 1e3;
    const vXMv = solved.nodes.x.re * 1e3;
    const vD2Mv = solved.nodes.d2.re * 1e3;
    const vPMv = solved.nodes.p.re * 1e3;
    const iOutUa = solved.branches.rl.re * 1e6;
    const iFUa = solved.branches.rf.re * 1e6; // s1 -> p (leaving input node)
    const iS1Ua = iinUa - iFUa;
    const aiClosedExact = Math.abs(iinA) > 1e-15 ? (solved.branches.rl.re / iinA) : aiClosed2Port;

    const dirS1 = vS1Mv > 1e-4 ? 'up' : (vS1Mv < -1e-4 ? 'down' : undefined);
    const dirX = vXMv > 1e-4 ? 'up' : (vXMv < -1e-4 ? 'down' : undefined);
    const dirP = vPMv > 1e-4 ? 'up' : (vPMv < -1e-4 ? 'down' : undefined);

    return {
      tiles: [
        { label: '귀환 전류 I_F', val: `${iFUa.toFixed(3)} μA` },
        { label: '출력 전류 I_out', val: `${iOutUa.toFixed(2)} μA` },
        { label: '루프 이득 KA', val: `+${loopGain.toFixed(2)}` },
      ],
      diagnosis: Math.abs(iinUa) < 1e-9
        ? {
            kind: 'info',
            title: '입력 전류 0 μA (무신호)',
            text: `$K = ${kVal.toFixed(3)} < 0$, $A_{I,\\text{open}} = ${aiOpenFormula.toFixed(2)} < 0$이므로 루프 이득 $KA = +${loopGain.toFixed(2)} > 0$인 음의 귀환입니다. $I_{\\text{in}}$을 올려 보세요.`,
          }
        : {
            kind: 'ok',
            title: '음의 귀환 확인 (K < 0, A_I,open < 0 → KA > 0)',
            text: `폐루프 MNA 이득은 $${aiClosedExact.toFixed(2)}$(2포트 공식 $${aiClosed2Port.toFixed(2)}$, $R_F$ 미소 순방향 포함)입니다. $I_F$가 $I_{\\text{in}}$과 같은 부호로 빠져나가 $I_{S1} = ${iS1Ua.toFixed(3)}\\ \\mu\\text{A}$로 억제합니다.`,
          },
      formula: '$$\\begin{aligned}K &= -\\frac{R_M}{R_F+R_M} < 0 \\\\ A_{I,\\text{open}} &< 0 \\implies K A_{I,\\text{open}} > 0\\end{aligned}$$',
      summary: `입력 $I_{\\text{in}} = ${iinUa.toFixed(1)}\\ \\mu\\text{A}$ 중 $I_F = ${iFUa.toFixed(3)}\\ \\mu\\text{A}$가 $R_F$로 빠져나가고 $I_{S1} = ${iS1Ua.toFixed(3)}\\ \\mu\\text{A}$만 $M_1$에 들어갑니다. 2포트 공식은 $R_F$ 순방향을 생략하지만 MNA는 이를 포함해 실제 폐루프를 풉니다.`,
      nodes: {
        s1: { v: Number(vS1Mv.toFixed(3)), unit: 'mV', dir: dirS1, hot: state.causalStep === 1 || state.causalStep === 5 },
        x: { v: Number(vXMv.toFixed(2)), unit: 'mV', dir: dirX, hot: state.causalStep === 2 },
        d2: { v: Number(vD2Mv.toFixed(1)), unit: 'mV', dir: dirP, hot: state.causalStep === 3 },
        p: { v: Number(vPMv.toFixed(2)), unit: 'mV', dir: dirP, hot: state.causalStep === 4 },
      },
      branches: {
        i_in_bus: { hot: state.causalStep === 1 || state.causalStep === 5, dir: iinUa >= 0 ? 'fwd' : 'rev' },
        vx_line: { hot: state.causalStep === 2, dir: vXMv >= 0 ? 'fwd' : 'rev' },
        i_out: { hot: state.causalStep === 3, dir: iOutUa >= 0 ? 'fwd' : 'rev' },
        i_fb: { hot: state.causalStep === 4 || state.causalStep === 5, dir: iFUa >= 0 ? 'fwd' : 'rev' },
      },
    };
  },
};

module.exports = spec;
