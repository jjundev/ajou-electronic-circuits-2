# v2 회로 내용·독립 수치 검토 계약

브리프의 근거 절(`notes`, `stts`)·강의노트·교재를 먼저 읽고 `lab.js`와 `scripts/steps.cjs` 출력을 대조한다.

## 1. 독립 검산 원칙 (`mna.js` 재호출 금지)

- **`lab.js` 내부에서 `assets/mna.js`(`solveCircuit`)를 호출하거나, 검산 스크립트에서 `mna.js`를 다시 호출해 같다고 확인하는 것은 독립 검산이 아니다.**
- 반드시 **별도의 해석식**(소신호 이득·임피던스 공식, 복소수 전달함수 $H(j\omega)$, KCL/노드방정식 직접 연립)을 손계산 또는 독립 계산 스크립트로 작성해 `lab.js` (`evaluate` 결과)와 비교한다.
- **`mna.js` 자체를 검증할 때도** 동일한 원칙을 적용한다: 넷리스트의 KCL/KVL 방정식을 독립적으로 세워 `solveCircuit`의 노드 전압·가지 전류가 허용 오차 내에서 일치하는지 확인한다.

## 2. 필수 검산 상태 4범주

모든 주제에 대해 아래 4가지 범주를 독립 해석식으로 대조한다:
1. **기본 상태:** 초기 매개변수·기본 포트·모든 기본 소자 활성 상태
2. **대표 설정:** `presets` 및 `steps`가 가리키는 동작점·특정 주파수·대표 부하 상태
3. **파라미터 끝값:** `params`의 `min`/`max` 조합 및 `elems`를 끈(`disabledElems`) 상태
4. **오조립·경계 상태:**
   - `bench`: `ports` 오조립 상태 및 단락/개방 특이(`singular: true`) 발생 조건이 실제 KVL/KCL 모순(전압원 단락, 부유 노드 등)과 일치하는지 검증
   - `approx`: `exact` 곡선, `approx` 곡선, `errPct`가 근사 성립 영역과 붕괴 경계에서 해석식과 일치하는지 검증

## 3. 회로·수치 세부 체크리스트

1. **넷리스트와 회로도 일치:** SVG 회로도와 `mna.js` 넷리스트·해석식의 소신호 연결, `vccs` 제어·전류 방향(`n1 → n2 = gm·(V(cp) - V(cn))`), AC 접지, $g_m$·$r_o$·기생 커패시턴스·복제 귀환망 가정이 모두 같은지 확인한다.
2. **단위·전달함수·극점 검증:** $\omega = 2\pi f$ (Hz와 rad/s 구분), 전압 크기 $\text{dB} = 20\log_{10}|H|$, 단일 극점 주파수에서 $-3.0103\text{ dB}$·$-45^\circ$, 동일 이중 극점에서 $-6.0206\text{ dB}$와 전체 $-3\text{ dB}$ 대역폭 차이를 검증한다.
3. **부호와 위상 기준:** CS/반전 증폭기의 $-180^\circ$ 반전 부호와 위상 wrap(`-225° ≡ +135°`)을 확인하고, 수업 밖 보충에는 `(교과서 보충)` 표기를 확인한다.
4. **상태 일관성과 유한값:** 모든 조작 상태에서 SVG 배지(`nodes`), 가지 강조(`branches`), `tiles`, `diagnosis`, `plotData`, `summary`가 같은 상태를 모순 없이 설명하며 `NaN`/`Infinity`가 노출되지 않는지 확인한다.
5. **모델 한계 명시:** 소신호 선형 모델·클리핑 미포함·로딩 분리 근사 등 단순화 가정을 패널이나 진단 문구에 명확히 드러낸다.

## 4. 결함 처리 및 `validation.json` 기록

- Critical/Important 결함을 모아 수정한 뒤 `scripts/check.cjs`, `scripts/steps.cjs`, 독립 수치 검산, `scripts/probe_interactive.py`를 다시 실행한다. 해결하지 못한 결함이 남은 주제는 보류한다.
- `validation.json`에는 `lab.js`의 현재 `source_sha256`, 근거 자료, 독립 해석식·기준값 비교 결과, 발견·수정 내역, 4개 검증 게이트(`machine`, `numeric_independent`, `probe`, `browser`)의 `pass | fail | not_run`과 실제 증거를 기록한다.
