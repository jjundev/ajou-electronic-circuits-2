# 인터랙티브 브리프 02: 예제 I CG 단 V-V 귀환 +Δv 인과와 분배기 로딩

- **제목:** CG 단 V-V 귀환 +Δv 인과와 분배기 로딩
- **저장 파일명:** `인터렉티브_02_CG_VV_귀환_인과와_로딩.html` (단순명 `CG_VV_귀환_인과와_로딩`)
- **아키타입:** `probe`
- **선정 점수:** 6/7
  - 입력 $v_{\text{in}}$, 분배기 크기 $R_1+R_2$, $g_{m1}$, $R_D$ 변화에 따른 노드 전압·가지 전류·이득 변화 추적 (+2)
  - `+Δv` 인과 도미노 4박자($v_{\text{in}} \uparrow \to v_{gs} \downarrow \to i_{D1} \downarrow \to v_{\text{out}} \uparrow \text{ 및 } v_G \uparrow$)로 공통 게이트 부귀환 억제 원리 단계별 추적 (+2)
  - 폐루프 실제 귀환($A_{v,\text{closed}}=8/3\approx 2.67$)과 분배기 로딩 무시 오답($16/5=3.20$, $+20.0\%$) 및 복제 달린 개루프($R_{\text{out,open}}=2\ \text{k}\Omega$, $A_{v,\text{open}}=8$) 직접 대조로 오개념 해소 (+2)
- **기존 정리노트 `.widget` 대비 확장점:** `#s2-vv-ideal`, `#s2-vv-open`, `#s2-vv-closed`, `#s4-procedure`에는 정적 SVG 그림과 수식 단계만 있고, 입력 전압 $+Δv_{\text{in}}$에 따라 전류·노드 전압이 어떻게 움직이고 $R_1+R_2$ 크기에 따라 로딩 오차가 얼마나 커지는지 직접 탐침하는 위젯이 없다. 본 `probe` 실험실은 MNA 소신호 해석기로 폐루프와 복제 달린 개루프의 모든 노드 전압($v_{\text{in}}, v_G, v_{\text{out}}$)·가지 전류($i_{D1}, i_{R_D}, i_{\text{div}}$)를 실시간 계산해 SVG 배지에 표시하고 4박자 `+Δv` 인과 도미노를 재생한다.

## 1. 기준 회로 및 수치 진리표 (`s4-procedure` 수업 기본값)

- **수업 기본값:** $g_{m1} = 4\ \text{mS}$, $R_D = 4\ \text{k}\Omega$, $R_1 = 3\ \text{k}\Omega$, $R_2 = 1\ \text{k}\Omega$ ($R_1+R_2 = 4\ \text{k}\Omega$, $R_1:R_2 = 3:1$ 고정으로 $K = \frac{R_2}{R_1+R_2} = 0.25$), $v_{\text{in}} = +10\ \text{mV}$ ($\lambda = 0$, $r_O$ 무시).
- **폐루프 (`closed`) 기본값:**
  - $v_{\text{in}} = +10.00\ \text{mV}$, $v_G = +6.67\ \text{mV}$, $v_{gs} = v_G - v_{\text{in}} = -3.33\ \text{mV}$
  - $i_{D1} = g_{m1} v_{gs} = -13.33\ \mu\text{A}$, $i_{R_D} = -6.67\ \mu\text{A}$ (위쪽 $V_{DD}$ 접지로 $6.67\ \mu\text{A}$ 유출), $i_{\text{div}} = +6.67\ \mu\text{A}$
  - $v_{\text{out,closed}} = +26.67\ \text{mV}$, $A_{v,\text{closed}} = 8/3 \approx 2.667\ \text{V/V}$
  - **로딩 무시 오답:** $A_{0,\text{no-load}} = g_{m1}R_D = 16$, $A_{v,\text{no-load}} = \frac{16}{1 + 0.25\times 16} = \frac{16}{5} = 3.20\ \text{V/V}$ (실제 대비 $+20.0\%$ 과대평가)
- **복제 달린 개루프 (`open`) 기본값:**
  - $R_{\text{out,open}} = R_D \parallel (R_1+R_2) = 4\parallel 4 = 2.00\ \text{k}\Omega$, $A_{v,\text{open}} = g_{m1}R_{\text{out,open}} = 8.00\ \text{V/V}$, $1 + KA_{v,\text{open}} = 3.00$
  - $v_{\text{in}} = +10.00\ \text{mV}$, $v_G = 0.00\ \text{mV}$ ($i_G=0$이므로 반송 복제 $R_1\parallel R_2$에 신호 전류 없음), $v_{gs} = -10.00\ \text{mV}$
  - $i_{D1} = -40.00\ \mu\text{A}$, $i_{R_D} = -20.00\ \mu\text{A}$, $i_{\text{div}} = +20.00\ \mu\text{A}$, $v_{\text{out,open}} = +80.00\ \text{mV}$, $v_{\text{sense,mid}} = +20.00\ \text{mV}$ (개방)

## 2. 모드·조작 범위·인과 단계·대표 설정

- **모드 (`modes`, 2개):**
  1. `closed`: `폐루프 (실제 귀환)` — $M_1$ + $R_D$ + $R_1$–$R_2$ 분배기가 게이트로 연결된 전체 귀환 회로
  2. `open`: `복제 달린 개루프` — 반송 복제(게이트, $R_1$ 상단 접지)와 감지 복제(출력, 중간 단자 개방)가 달린 개루프 회로
- **슬라이더 (`params`, 4개):**
  - `vin`: $-20\text{..}+20\ \text{mV}$ (`step: 1`, 기본 `+10 mV`; `0 mV`도 `1 V` 단위 시험 해석과 병행해 유한 이득 계산)
  - `rdiv`: 분배기 합 $R_1+R_2$ ($1\text{..}40\ \text{k}\Omega$, `step: 1`, 기본 `4 kΩ`; $R_1=0.75 R_{\text{div}}$, $R_2=0.25 R_{\text{div}}$)
  - `gm1`: $2\text{..}10\ \text{mS}$ (`step: 0.5`, 기본 `4 mS`)
  - `rd`: $1\text{..}8\ \text{k}\Omega$ (`step: 0.5`, 기본 `4 kΩ`)
- **4박자 `+Δv` 인과 도미노 (`causalSteps`, `data-causal-step="1..4"`):**
  1. `소스에 입력 vin 인가` (`vin` 변동)
  2. `vgs = vG − vin 반대 변화` (게이트 고정 시 소스가 오르면 `vgs` 감소)
  3. `드레인 전류 iD1 감소` (출력 노드에서 끌어내리는 전류 감소 → 출력으로 전류 밀어냄)
  4. `vout 상승과 귀환 vG 억제` (`vout` 상승 → 폐루프에서는 분배기 `vG = K·vout` 상승이 `vgs` 변동을 억제; 개루프에서는 `vG = 0` 유지)
- **대표 설정 (`presets`, 4개):** 수업 기본(`Rdiv=4 kΩ`), 무거운 로딩(`Rdiv=1 kΩ`, $A_v=1.778$ vs 오답 $3.20$ $+80\%$), 가벼운 로딩(`Rdiv=40 kΩ`, $A_v=3.137$ vs 오답 $3.20$ $+2\%$), 음의 입력(`vin=-10 mV`)
- **단계별 살펴보기 (`steps`, 9개):** 폐루프 1–4박자 도미노·로딩 비교(`1 kΩ`, `40 kΩ`) + 개루프 복제 종단·로딩·음 입력 반전 확인 (모든 항목에 명시적 `params` 포함)

## 3. 예측 질문 (`predict`) 및 모드별 오개념 3개

- **예측 질문:** "V-V 귀환 CG 단에서 분배기 로딩($R_1+R_2$)을 빼고 개루프를 $g_{m1}R_D$로 계산하면, 폐루프 이득은 실제보다 어떻게 나올까요?"
  - 보기: `실제보다 크게 나온다 (과대평가)` [정답] / `실제보다 작게 나온다 (과소평가)` / `로딩과 무관하게 같다`
- **오개념 (`mistakes`, 모드별 3개):**
  - `closed`: (1) 분배기 $R_1+R_2$ 로딩을 빼고 $g_{m1}R_D$만 써서 $+20\%$ 과대 계산, (2) 게이트를 입력으로 착각해 CG 반전/비반전 부호 혼동, (3) 루프 이득 $KA_{v,\text{open}}=2$인데 바로 $1/K=4$로 근사
  - `open`: (1) 반송 복제가 입력저항 $1/g_{m1}$을 바꾼다고 오해($i_G=0$이라 불변), (2) 감지 복제 가운데 단자를 접지로 단락, (3) 개루프에서도 $v_G$가 따라 올라간다고 혼동

## 4. 모델 가정·근거 및 정리노트 연결 계획

- **소신호 모델 가정:** 슬라이드 예제(`정리노트_1120` `#s2-vv-open`, `#s4-procedure`)와 동일하게 $\lambda = 0$($r_O$ 무시), 선형 소신호 모델(클리핑·바이어스 포화 미포함), $R_1:R_2 = 3:1$($K = 0.25$ 고정) 조건을 따른다.
- **근거:**
  - `복습노트/1120/정리노트_1120_Nonideal_IO_Feedback.html` `#s2-vv-ideal`, `#s2-vv-open` (`fig-s2-vv-open`), `#s2-vv-closed`, `#s4-procedure`, `#s5-cheatsheet`
  - `STT/1120 전회2.md` Part 05–09
- **정리노트 연결 계획 (후속 연결용):**
  - `noteHtml`: `복습노트/1120/정리노트_1120_Nonideal_IO_Feedback.html`
  - `sectionId`: `s4-procedure` (또는 `s2-vv-open` / `s2-vv-closed`)
  - 관찰 포인트: `v_in` 변화가 `v_gs` → `i_D1` → `v_out` → `v_G`로 전파되는 4박자 `+Δv` 인과와 분배기 로딩 포함/무시 이득 차이를 직접 확인한다.
