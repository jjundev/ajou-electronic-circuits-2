# 인터랙티브 브리프 03: 예제 II CG+CS R_F 로딩과 반송 부호

- **제목:** CG+CS 귀환 RF 로딩과 반송 부호
- **저장 파일명:** `인터렉티브_03_CG_CS_RF_로딩과_반송_부호.html` (단순명 `CG_CS_RF_로딩과_반송_부호`)
- **아키타입:** `approx`
- **선정 점수:** 6/7
  - 입력 반송 복제(`rf-in`)와 출력 감지 복제(`rf-out`)를 회로도에서 직접 ON/OFF 하며 각 복제가 $R_{\text{in,open}}$, $R_{\text{out,open}}$, $R_0$, $R_{\text{closed}}$에 미치는 로딩 비중을 대조 (+2)
  - $R_F = 1\text{–}100\ \text{k}\Omega$ 로그 스윕 그래프에서 정확 로딩 개루프 $|R_0|$와 로딩 생략 근사 곡선을 실시간 대조하고 `10%` 근사 붕괴 경계($R_F \approx 21.1\ \text{k}\Omega$) 및 2포트 일방성 vs MNA 직접 피드스루 한계 확인 (+2)
  - $K$ 측정 회로(`fig-vc-k`)에서 실제 전류 방향($V_1 \to R_F \to \text{접지}$)과 정의된 반송 전류 기준 화살표 $I_F$가 반대임을 `+ΔV_1` 3박자 인과로 추적해 $K = -1/R_F < 0$ 및 음귀환 $KR_0 > 0$ 부호 오개념 해소 (+2)
- **기존 정리노트 `.widget` 대비 확장점:** `정리노트_1120_Nonideal_IO_Feedback.html`의 `#widget-s3-rf`는 $R_F \in \{1, 10, 100\}\ \text{k}\Omega$ 막대만 보여 주는 정적 비율 위젯이고, `#s3-vc-sign`에는 정적 SVG(`fig-vc-k`)만 있다. 본 `approx` 실험실은 (1) 회로도의 입력·출력 $R_F$ 복제 소자를 직접 클릭해 끄고 켜며 개루프 $|R_0|$와 2포트·정확 MNA 폐루프가 어떻게 달라지는지 연속 로그 그래프와 `10%` 붕괴 배지로 실험하고, (2) $K = -1/R_F$ 측정 회로에서 시험 전압 $V_1$ 슬라이더와 3박자 `+ΔV_1` 펄스로 실제 전류 대 기준 화살표 $I_F$의 부호 반전을 직접 검증하도록 확장한다.

## 1. 기준 회로 및 수치 진리표 (`s3-vc-open`, `s3-vc-sign`, `s3-vc-closed`)

- **수업 기본값 ($\lambda = 0$, $r_O$ 무시):** $g_{m1} = 10\ \text{mS}$ ($1/g_{m1} = 100\ \Omega$), $g_{m2} = 10\ \text{mS}$, $R_{D1} = 5\ \text{k}\Omega$, $R_{D2} = 2\ \text{k}\Omega$, $R_F = 10\ \text{k}\Omega$, $I_{\text{in}} = 1\ \mu\text{A}$.
- **이상적 무로딩 개루프 (`rf-in` OFF, `rf-out` OFF):**
  - $R_{\text{in,ideal}} = 1/g_{m1} = 100.00\ \Omega$, $R_{\text{out,ideal}} = R_{D2} = 2.00\ \text{k}\Omega$
  - $R_{0,\text{ideal}} = -g_{m2} R_{D1} R_{D2} = -100.00\ \text{k}\Omega$ (정확 로딩 개루프 대비 $+21.2\%$ 과대)
  - 무로딩 폐루프(2포트 공식): $-100 / (1 + 10) = -9.09\ \text{k}\Omega$
- **로딩 포함 개루프 (`rf-in` ON, `rf-out` ON, $R_F = 10\ \text{k}\Omega$):**
  - $R_{\text{in,open}} = (1/g_{m1}) \parallel R_F = 100 \parallel 10000 = 99.01\ \Omega$ ($v_{s1} = +99.01\ \mu\text{V}$, 입력 전류의 $99.01\%$만 $M_1$에 전달)
  - $V_X = +4.95\ \text{mV}$ ($V_X / I_{\text{in}} = 4.95\ \text{k}\Omega$)
  - $R_{\text{out,open}} = R_{D2} \parallel R_F = 2000 \parallel 10000 = 1.67\ \text{k}\Omega$ ($5/3\ \text{k}\Omega$, 출력 부하 $16.7\%$ 감소)
  - $R_0 = -\frac{R_F R_{D1}}{R_F + 1/g_{m1}} \cdot g_{m2}(R_{D2} \parallel R_F) = -100\ \text{k}\Omega \cdot \frac{100}{101} \cdot \frac{5}{6} = -82.51\ \text{k}\Omega$ ($v_{\text{out,open}} = -82.51\ \text{mV}$)
- **반송 부호 $K$ 및 폐루프 비교 ($R_F = 10\ \text{k}\Omega$):**
  - $K = I_F / V_1 = -1/R_F = -0.100\ \text{mS}$ (예: $V_1 = +1\ \text{V}$일 때 실제 전류 $+0.100\ \text{mA}$는 $V_1 \to R_F \to \text{접지}$ 방향이지만, 기준 $I_F$는 단락선에서 $R_F$로 들어가는 반대 방향이므로 $I_F = -0.100\ \text{mA}$)
  - $KR_0 = (-0.1\ \text{mS})(-82.508\ \text{k}\Omega) = +8.2508 > 0$ (음귀환) $\Rightarrow 1 + KR_0 = 9.2508 \approx 9.25$
  - **2포트 폐루프:** $R_{\text{closed,2port}} = \frac{R_0}{1+KR_0} = -8.9190\ \text{k}\Omega \approx -8.92\ \text{k}\Omega$, $R_{\text{in,closed}} = \frac{99.01}{9.2508} = 10.70\ \Omega$, $R_{\text{out,closed}} = \frac{1666.67}{9.2508} = 180.16\ \Omega = 0.18\ \text{k}\Omega$
  - **정확 MNA 폐루프(단일 $R_F$ 직접 연결):** $R_{\text{closed,exact}} = -8.9188\ \text{k}\Omega$ (2포트 공식과 직접 피드스루 $+1/R_F$ 차이 $0.002\%$), $R_{\text{in,closed,exact}} = 10.70\ \Omega$, $R_{\text{out,closed,exact}} = 180.20\ \Omega$
- **끝값 및 생략 비교:**
  - `rf-out`만 OFF ($R_F = 10\ \text{k}\Omega$): $R_0 = -99.01\ \text{k}\Omega$ (정확 개루프 대비 $+20.0\%$ 오차 → `10%` 초과 붕괴)
  - `rf-in`만 OFF ($R_F = 10\ \text{k}\Omega$): $R_0 = -83.33\ \text{k}\Omega$ ($+1.0\%$ 오차 → `10%` 이내)
  - $R_F = 1\ \text{k}\Omega$: 로딩 개루프 $R_0 = -30.30\ \text{k}\Omega$ vs 무로딩 $-100.0\ \text{k}\Omega$ ($+230.0\%$ 오차), 정확 폐루프 $-968.0\ \Omega$ vs 2포트 $-968.1\ \Omega$
  - $R_F = 100\ \text{k}\Omega$: 로딩 개루프 $R_0 = -97.94\ \text{k}\Omega$ vs 무로딩 $-100.0\ \text{k}\Omega$ ($+2.1\%$ 오차 → `10%` 이내), 정확 폐루프 $-49.48\ \text{k}\Omega$
  - 약한 전방단 ($g_{m1}=g_{m2}=2\ \text{mS}, R_{D1}=1\ \text{k}\Omega, R_{D2}=0.5\ \text{k}\Omega, R_F=1\ \text{k}\Omega$): 양쪽 로딩을 다 넣어도 2포트 폐루프 $-307.7\ \Omega$ vs 정확 MNA 폐루프 $-250.0\ \Omega$ ($+23.1\%$ 차이, 직접 피드스루 $1/R_F$ 한계)

## 2. 모드·조작·대표 설정·단계

- **모드 (`modes`, 2개):**
  1. `loading`: `로딩·근사` — `fig-vc-open` 기반 회로도에서 `data-elem="rf-in"`, `data-elem="rf-out"` ON/OFF 토글 + 연동 로그 스윕 SVG 그래프(`exact` vs `approx`, `errPct`, `thresholdPct: 10`) + 2포트 대 정확 MNA 폐루프 비교
  2. `sign`: `반송 부호 K` — `fig-vc-k` 기반 회로도에서 시험 전압원 $V_1$ 슬라이더(`-2..+2 V`), `R_F` 슬라이더(`1..100 kΩ`), 3박자 `+ΔV1` 인과 펄스(`data-causal-step="1..3"`)로 실제 전류 방향 대 $I_F$ 기준 화살표 반전 확인
- **매개변수 (`params`):**
  - 공통: `rf` ($1\text{..}100\ \text{k}\Omega$, 로그 스케일, 기본 `10 kΩ`)
  - `loading` 전용: `gm1` ($2\text{..}20\ \text{mS}$, 기본 `10`), `gm2` ($2\text{..}20\ \text{mS}$, 기본 `10`), `rd1` ($1\text{..}10\ \text{k}\Omega$, 기본 `5`), `rd2` ($0.5\text{..}5\ \text{k}\Omega$, 기본 `2`), `iin` ($-5\text{..}+5\ \mu\text{A}$, 기본 `+1`)
  - `sign` 전용: `v1` ($-2\text{..}+2\ \text{V}$, 기본 `+1 V`)
- **대표 설정 (`presets`) & 단계별 살펴보기 (`steps`):**
  - `loading` 6개 프리셋/6단계: 수업 기본(양쪽 ON), 출력 복제 생략(`rf-out` OFF, $+20.0\%$), 이상적 무로딩(둘 다 OFF, $+21.2\%$), 강한 로딩 붕괴($R_F=1\ \text{k}\Omega$, $+230.0\%$), 큰 $R_F$ 허용($R_F=100\ \text{k}\Omega$, $+2.1\%$), 약한 전방단 피드스루 한계(2포트 vs MNA $+23.1\%$).
  - `sign` 4개 프리셋/2단계: 기본 $+1\ \text{V}$, 음의 $-1\ \text{V}$, 작은 $R_F=1\ \text{k}\Omega$, 영 입력 $V_1=0\ \text{V}$.

## 3. 예측 질문 (`predict`) 및 모드별 오개념 3개

- **예측 질문:** "예제 II(기본값: $R_{D2}=2\ \text{k}\Omega$, $1/g_{m1}=100\ \Omega$, $R_F=10\ \text{k}\Omega$)에서 $R_F$ 로딩은 어느 쪽에서 더 크게 나타날까요?"
  - 정답: `출력 쪽 감지 복제 (RD2 ∥ RF)` (`10 kΩ`은 `100 Ω`의 100배라 입력 감소는 `1%`뿐이지만 `2 kΩ`의 5배뿐이라 출력 부하가 `16.7%` 줄어듦)
- **오개념 (`mistakes`, 모드별 3개):**
  - `loading`: (1) 조건 없이 무로딩 $R_0$ 적용, (2) 입력·출력 로딩 비중 동일시, (3) V-C 폐루프 입력저항 $R_{\text{in,closed}}$ 증감 방향 혼동.
  - `sign`: (1) 슬라이드 $i_{RF}$ 화살표 그대로 $K>0$ 오해, (2) $K<0$만 보고 양귀환 오인, (3) 반송 포트를 개방해 전류가 0이 되는 실수.

## 4. 모델 가정·근거·연결 계획

- **모델 가정:** 수업 예제(`s3-vc-ideal`–`s3-vc-closed`)와 동일하게 $\lambda = 0$ ($r_O = \infty$) 선형 소신호 모델을 사용하며, 클리핑이나 바이어스 이동은 포함하지 않는다. 개루프 복제 종단은 각 포트의 이상적 임피던스($Z_{\text{in}}=0$, $Z_{\text{out}}=0 \Rightarrow$ 양쪽 단락/접지)를 쓰며, 약한 전방단 조건에서는 2포트 일방성 가정(직접 피드스루 $1/R_F$ 무시)의 오차까지 정확 MNA와 나란히 보여 준다.
- **근거:** `복습노트/1120/정리노트_1120_Nonideal_IO_Feedback.html` (`#s3-vc-ideal`, `#s3-vc-open`, `#s3-vc-sign`, `#s3-vc-closed`, `#fig-vc-open`, `#fig-vc-k`, `#widget-s3-rf`), `STT/1120 전회2.md` Part 10–12.
- **정리노트 연결 계획:** `복습노트/1120/정리노트_1120_Nonideal_IO_Feedback.html` `#s3-vc-sign` (연결 일괄 작업 시 `s0-four-terminations`→01, `s2-vv-open`→02, `s3-vc-sign`→03).
