# 전자회로2 복습 1007 문제설명

주어진 조건을 읽고, 첫 줄을 쓰고, 이유를 따라가며 답을 확인해요.

문제의 첫 줄부터 검산까지 설명해요.

**목차**

- [문항별 설명](#problems)
  - [P1. MOS 차동쌍의 공통 모드 이득](#p1)
  - [P2. 전류원 부하의 공통 모드 이득](#p2)
  - [P3. 캐스코드 테일의 DM·CM 이득](#p3)
  - [P4. 공통 모드 제거와 부하 불일치](#p4)
  - [P5. MOS 차동쌍의 입력 범위와 CMRR](#p5)
  - [P6. CMRR로 정하는 부하 오차](#p6)
  - [P7. 테일 폭 변경과 CMRR](#p7)
  - [P8. 직렬 테일 저항과 CMRR](#p8)
  - [P9. 캐스코드 부하의 DM·CM 이득](#p9)
  - [P10. 전류 거울의 면적비와 이득](#p10)
  - [P11. 전류 거울의 출력 변화](#p11)
  - [P12. MOS 차동쌍의 부하별 이득](#p12)
  - [P13. BJT 차동쌍의 부하별 이득](#p13)
  - [P14. 목표 이득과 Early 전압](#p14)

<a id="problems"></a>

## 문항별 설명

<a id="p1"></a>

### P1. MOS 차동쌍의 공통 모드 이득

P10.67 · 장말문제 10.67 · [원 문제 보기](../%EB%B3%B5%EC%8A%B5%EB%AC%B8%EC%A0%9C_1007_Differential_Amplifiers-%EB%AC%B8%EC%A0%9C.pdf)

#### 주어진 조건

- $M_1$, $M_2$: $\lambda = 0$
- $M_3$: $\lambda \neq 0$
- $(V_{GS} - V_{TH})_{eq.}$: $M_1$, $M_2$의 평형(equilibrium) 오버드라이브
- $I_{SS}$는 그림에 라벨이 없음. $M_3$가 흘리는 테일 전류로 보임

#### 구할 것

- 공통 모드 이득을 계산하고 다음을 증명

  $$
  A_{CM} = \frac{-R_D I_{SS}}{\dfrac{2}{\lambda} + (V_{GS} - V_{TH})_{eq.}} \qquad (10.224)
  $$

![그림 P10.67](figures_%EB%AC%B8%EC%A0%9C%EC%84%A4%EB%AA%85_1007_Differential_Amplifiers/b9fde612bff67b34-fig10-88.png)

<details><summary>원문 보기</summary>

Compute the common-mode gain of the MOS differential pair shown in Fig. 10.88. Assume $\lambda = 0$ for $M_1$ and $M_2$ but $\lambda \neq 0$ for $M_3$. Prove

$$
A_{CM} = \frac{-R_D I_{SS}}{\dfrac{2}{\lambda} + (V_{GS} - V_{TH})_{eq.}}, \qquad (10.224)
$$

where $(V_{GS} - V_{TH})_{eq.}$ denotes the equilibrium overdrive of $M_1$ and $M_2$.

</details>

#### 1. 회로 분석 및 등가 저항

- **대칭 공통 모드(CM) 반회로**: 테일 전류원 $M_3$의 소신호 저항 $r_{O3} = \frac{1}{\lambda I_{SS}}$을 반쪽마다 **$2r_{O3} = \frac{2}{\lambda I_{SS}}$**로 분할하여 소스 노드 아래에 연결합니다.
- **소신호 파라미터**: $M_1, M_2$는 $\lambda = 0$이므로 $r_{o1,2} = \infty$.
- **평형 오버드라이브**: 가지 전류 $I_{D1} = I_{SS}/2$이므로 $g_{m1} = \frac{2(I_{SS}/2)}{(V_{GS}-V_{TH})_{eq.}} = \frac{I_{SS}}{V_{ov}}$.

#### 2. 핵심 수식 전개 ($G_m \cdot R_{out}$)

- **단락 전달 컨덕턴스 ($G_m$)**: 소스 축퇴 반회로의 입력 변환율
$$G_m = \frac{1}{\frac{1}{g_{m1}} + 2r_{O3}} = \frac{1}{\frac{V_{ov}}{I_{SS}} + \frac{2}{\lambda I_{SS}}} = \frac{I_{SS}}{V_{ov} + \frac{2}{\lambda}}$$

- **출력 저항 ($R_{out}$)**: 드레인 부하 저항
$$R_{out} = R_D$$

- **단일 종단 공통 모드 이득 ($A_{CM}$)**:
$$A_{CM} = -G_m R_{out} = \frac{-R_D I_{SS}}{\frac{2}{\lambda} + (V_{GS}-V_{TH})_{eq.}}$$

#### 3. 완성 답 및 주의할 점

- **완성 답**:
$$\boxed{A_{CM} = \frac{-R_D I_{SS}}{\frac{2}{\lambda} + (V_{GS}-V_{TH})_{eq.}}}$$
- ⚠️ **반회로 테일 저항**: 반쪽 전류가 절반($I_{SS}/2$)이므로 원래 소스 전압 $v_P$를 재현하려면 $r_{O3}/2$가 아니라 반드시 **$2r_{O3}$**를 써야 합니다.
- ⚠️ **출력 기준 구분**: 완전 대칭 회로에서 양쪽 출력의 차를 취한 차동 공통 모드 이득은 $(v_X - v_Y)/v_{CM} = 0$입니다. 이 문제의 $A_{CM}$은 한쪽 출력(단일 종단) 기준입니다.

---

### P2. 전류원 부하의 공통 모드 이득

P10.68 · 장말문제 10.68 · [원 문제 보기](../%EB%B3%B5%EC%8A%B5%EB%AC%B8%EC%A0%9C_1007_Differential_Amplifiers-%EB%AC%B8%EC%A0%9C.pdf)

#### 주어진 조건

- $\lambda > 0$
- $g_m r_O \gg 1$
- $A_v = -G_m R_{out}$ 관계를 사용

#### 구할 것

- 회로의 공통 모드 이득

![그림 P10.68](figures_%EB%AC%B8%EC%A0%9C%EC%84%A4%EB%AA%85_1007_Differential_Amplifiers/d93bd8d61a274e40-fig10-89.png)

<details><summary>원문 보기</summary>

Calculate the common-mode gain of the circuit depicted in Fig. 10.89. Assume $\lambda > 0$, $g_m r_O \gg 1$, and use the relationship $A_v = -G_m R_{out}$.

</details>

#### 1. 회로 분석 및 등가 저항

- **대칭 CM 반회로 테일**: 테일 $M_5$를 반쪽마다 **$R_S = 2r_{o5}$**로 분할.
- **능동 부하 임피던스**: $M_3, M_4$는 게이트가 $V_{b1}$(AC 접지)에 묶인 전류원이므로 상단 부하는 **$r_{o3}$** (또는 $r_{o4}$).
- **하단 축퇴 임피던스**: $M_1$의 소스 축퇴로 올려다본 저항은 $R_{down} \approx 2 g_{m1} r_{o1} r_{o5} \gg r_{o3}$.

#### 2. 핵심 수식 전개 ($G_m \cdot R_{out}$)

- **단락 전달 컨덕턴스 ($G_m$)**:
$$G_m = \frac{1}{\frac{1}{g_{m1}} + 2r_{o5}} \approx \frac{1}{2r_{o5}} \quad (2g_{m1}r_{o5} \gg 1)$$

- **출력 저항 ($R_{out}$)**: 상단 부하와 하단 저항의 병렬
$$R_{out} = r_{o3} \parallel R_{down} = r_{o3} \parallel (2 g_{m1} r_{o1} r_{o5}) \approx r_{o3}$$

- **단일 종단 공통 모드 이득 ($A_{CM,SE}$)**:
$$A_{CM,SE} = -G_m R_{out} \approx -\frac{r_{o3}}{2r_{o5}}$$

#### 3. 완성 답 및 주의할 점

- **완성 답**:
$$\boxed{A_{CM,SE} \approx -\frac{r_{o3}}{2r_{o5}}}$$
- ⚠️ **$\lambda > 0$ 조건**: $g_m r_o \gg 1$이어도 부하 저항 $r_{o3}$는 유한하므로 무한대로 두지 않고 남겨야 이득이 결정됩니다.
- ⚠️ **차동 출력 기준**: 완전 대칭 시 두 출력이 똑같이 흔들리므로 차동 출력 기준 공통 모드 전달은 $A_{CM,DM} = 0$입니다.

---

### P3. 캐스코드 테일의 DM·CM 이득

2018-2_중간-Q3 · 기출 3 · [원 문제 보기](../%EB%B3%B5%EC%8A%B5%EB%AC%B8%EC%A0%9C_1007_Differential_Amplifiers-%EB%AC%B8%EC%A0%9C.pdf)

#### 주어진 조건

- $V_{DD} = 1.8\ \text{V}$
- $I_{D5} = I_{D6} = 1\ \text{mA}$
- $(W/L)_{1,2} = 200/0.2$, $(W/L)_{3,4} = 400/0.2$, $(W/L)_{5,6} = 400/0.2$
- $\mu_n C_{ox} = 100\ \mu\text{A/V}^2$, $\mu_p C_{ox} = 50\ \mu\text{A/V}^2$
- $\lambda_n = \lambda_p = 0.1\ \text{V}^{-1}$
- $g_m r_o \gg 1$로 가정
- 바이어스 전압 $V_{b1}$–$V_{b3}$ 값은 주어지지 않음

#### 구할 것

- (1) 차동 전압 이득
- (2) Common-mode 이득 $A_{CM} = \Delta V_{out,CM}/\Delta V_{in,CM}$

![그림 2018-2_중간-Q3](figures_%EB%AC%B8%EC%A0%9C%EC%84%A4%EB%AA%85_1007_Differential_Amplifiers/d6e21119d9b2f5cc-fig-Q3.png)

<details><summary>원문 보기</summary>

다음 회로에 대해 주어진 조건을 이용하여 질문에 답하시오.

: $V_{DD} = 1.8\ \text{V}$, $I_{D5} = I_{D6} = 1\ \text{mA}$, $(W/L)_{1,2} = 200/0.2$, $(W/L)_{3,4} = 400/0.2$, $(W/L)_{5,6} = 400/0.2$, $\mu_n C_{ox} = 100\ \mu\text{A/V}^2$, $\mu_p C_{ox} = 50\ \mu\text{A/V}^2$, $\lambda_n = \lambda_p = 0.1\ \text{V}^{-1}$. 이 때, $g_m r_o \gg 1$로 가정한다.

(1) 차동 전압 이득을 구하시오.

(2) Common-mode 이득($A_{CM} = \Delta V_{out,CM}/\Delta V_{in,CM}$)을 구하시오.

</details>

#### 1. 회로 분석 및 등가 저항

- **평형 DC 바이어스 및 소신호 파라미터**:
  - 테일 전류: $I_{D5} = I_{D6} = 1\,\text{mA} \implies$ 가지 전류 $I_{D1\sim 4} = 0.5\,\text{mA}$.
  - 입력쌍 ($M_1, M_2$): $g_{m1} = \sqrt{2(0.1)(1000)(0.5)} = 10\,\text{mS}$, $r_{o1\sim 4} = \frac{1}{0.1 \times 0.5} = 20\,\text{k}\Omega$.
  - 테일 캐스코드 ($M_5, M_6$): $g_{m5} = \sqrt{2(0.1)(2000)(1)} = 20\,\text{mS}$, $r_{o5,6} = \frac{1}{0.1 \times 1} = 10\,\text{k}\Omega$.
- **캐스코드 테일 저항 ($R_{SS}$)**:
$$R_{SS} \approx g_{m5} r_{o5} r_{o6} = (20\,\text{mS})(10\,\text{k}\Omega)(10\,\text{k}\Omega) = 2000\,\text{k}\Omega = 2\,\text{M}\Omega$$

#### 2. 핵심 수식 전개 ($G_m \cdot R_{out}$)

- **(1) 차동 전압 이득 ($A_{DM}$)**:
  - DM 반회로에서 공통 소스 노드는 **가상 접지**입니다.
  - 출력 저항: $R_{out,DM} = r_{o1} \parallel r_{o3} = 20\,\text{k}\Omega \parallel 20\,\text{k}\Omega = 10\,\text{k}\Omega$.
$$A_{DM} = -g_{m1}(r_{o1} \parallel r_{o3}) = -(10\,\text{mS})(10\,\text{k}\Omega) = \mathbf{-100}$$

- **(2) 공통 모드 이득 ($A_{CM}$)**:
  - CM 반회로 소스 아래 저항: $2R_{SS} = 4\,\text{M}\Omega = 4000\,\text{k}\Omega$.
  - $G_m \approx \frac{1}{2R_{SS}}$, $R_{out} \approx r_{o3} = 20\,\text{k}\Omega$.
$$A_{CM} \approx -\frac{r_{o3}}{2R_{SS}} = -\frac{20\,\text{k}\Omega}{4000\,\text{k}\Omega} = \mathbf{-5 \times 10^{-3}}$$

#### 3. 완성 답 및 주의할 점

- **완성 답**:
$$\boxed{(1)\ A_{DM} = -100,\qquad (2)\ A_{CM} \approx -5 \times 10^{-3}}$$
- ⚠️ **가지 전류 착오 주의**: $g_{m1}$과 $r_{o1}$ 계산 시 전체 테일 전류($1\,\text{mA}$)가 아니라 가지 전류 $0.5\,\text{mA}$를 넣어야 합니다.
- ⚠️ **CM 테일 저항**: 반회로 소스 아래에는 캐스코드 저항의 2배인 $2R_{SS} = 4\,\text{M}\Omega$가 들어갑니다.

---

### P4. 공통 모드 제거와 부하 불일치

2018-2_중간-Q4 · 기출 4 · [원 문제 보기](../%EB%B3%B5%EC%8A%B5%EB%AC%B8%EC%A0%9C_1007_Differential_Amplifiers-%EB%AC%B8%EC%A0%9C.pdf)

#### 주어진 조건

- $V_{DD} = 1.8\ \text{V}$, $I_{D3} = 1\ \text{mA}$
- $(W/L)_{1,2} = 200/0.2$, $(W/L)_3 = 400/0.2$
- $R_D = 1\ \text{k}\Omega$, $\Delta R_D = 0.02R_D = 20\ \Omega$
- $\mu_n C_{ox} = 100\ \mu\text{A/V}^2$, $\lambda_n = 0.1\ \text{V}^{-1}$
- $r_o \gg R_D$이고 $g_m r_o \gg 1$로 가정
- (1)은 회로 값을 쓰지 않는 서술형 소문항
- 바이어스 전압 $V_{b1}$ 값은 주어지지 않음

#### 구할 것

- (1) Differential pair에서 "common-mode (CM) rejection" 특성의 의미를 설명. 그리고 실제 회로에서 CM rejection 특성이 제한되는 이유 2가지를 설명
- (2) Common-mode input to differential-mode output 이득 $A_{CM-DM} = \Delta V_{out}/\Delta V_{in,CM}$

![그림 2018-2_중간-Q4](figures_%EB%AC%B8%EC%A0%9C%EC%84%A4%EB%AA%85_1007_Differential_Amplifiers/957d17e1975ffce7-fig-Q4.png)

<details><summary>원문 보기</summary>

다음 회로에 대해 주어진 조건을 이용하여 질문에 답하시오.

: $V_{DD} = 1.8\ \text{V}$, $I_{D3} = 1\ \text{mA}$, $(W/L)_{1,2} = 200/0.2$, $(W/L)_3 = 400/0.2$, $R_D = 1\ \text{k}\Omega$, $\Delta R_D = 0.02R_D = 20\ \Omega$, $\mu_n C_{ox} = 100\ \mu\text{A/V}^2$, $\lambda_n = 0.1\ \text{V}^{-1}$, $r_o \gg R_D$이고 $g_m r_o \gg 1$로 가정한다.

(1) Differential pair에서 "common-mode (CM) rejection" 특성의 의미를 설명하고, 실제 회로에서 CM rejection 특성이 제한되는 이유 2가지를 설명하시오.

(2) Common-mode input to differential-mode output 이득($A_{CM-DM} = \Delta V_{out}/\Delta V_{in,CM}$)을 구하시오.

</details>

#### 1. 회로 분석 및 등가 저항

- **(1) 서술 요약**:
  - **CM Rejection의 의미**: 두 입력에 동일하게 더해진 동상 잡음·간섭이 차동 출력에 나타나지 않도록 억제하는 특성.
  - **제한되는 이유 2가지**:
    1. **테일 전류원의 유한한 출력 임피던스**: $R_{SS} < \infty$이므로 CM 입력 변동 시 바이어스 전류 자체가 흔들림.
    2. **좌우 소자 및 부하의 불일치(Mismatch)**: $\Delta R_D, \Delta g_m, \Delta V_{TH} \neq 0$로 인해 동일한 전류 변화가 서로 다른 전압 강하를 유발하여 차동 누출 발생.
- **(2) 회로 파라미터**:
  - $I_D = 0.5\,\text{mA}$, $g_m = 10\,\text{mS}$, $R_{SS} = r_{o3} = \frac{1}{0.1 \times 1\,\text{mA}} = 10\,\text{k}\Omega$.

#### 2. 핵심 수식 전개 ($G_m \cdot R_{out}$)

- **공통 모드 가지 전류 변화**: $r_o \gg R_D$ 가정으로 좌우 CM 전류 증분은 동일
$$\Delta i = \frac{v_{CM}}{\frac{1}{g_m} + 2R_{SS}} \approx \frac{v_{CM}}{2R_{SS}}$$

- **차동 출력 전압 ($v_{od} = v_{o1} - v_{o2}$)**:
$$v_{o1} = -R_D \Delta i,\qquad v_{o2} = -(R_D + \Delta R_D)\Delta i$$
$$v_{od} = v_{o1} - v_{o2} = \Delta R_D \Delta i$$

- **CM-to-DM 변환 이득 ($A_{CM-DM}$)**:
$$A_{CM-DM} = \frac{v_{od}}{v_{CM}} \approx \frac{\Delta R_D}{2R_{SS}} = \frac{20\,\Omega}{2 \times 10\,\text{k}\Omega} = \frac{0.02\,\text{k}\Omega}{20\,\text{k}\Omega} = \mathbf{+10^{-3}}$$

#### 3. 완성 답 및 주의할 점

- **완성 답**:
$$\boxed{A_{CM-DM} \approx +10^{-3}\ (\text{또는 } +10^{-3}\,\text{V/V})}$$
- ⚠️ **누출의 원인**: 테일 저항이 유한해도 부하가 완벽히 대칭($\Delta R_D = 0$)이면 $A_{CM-DM} = 0$입니다. 불일치가 곱해져야만 차동 출현이 일어납니다.

---

### P5. MOS 차동쌍의 입력 범위와 CMRR

2023-1_중간-Q4 · 기출 4 · [원 문제 보기](../%EB%B3%B5%EC%8A%B5%EB%AC%B8%EC%A0%9C_1007_Differential_Amplifiers-%EB%AC%B8%EC%A0%9C.pdf)

#### 주어진 조건

- $V_{DD} = 1.8\ \text{V}$, $I_{D3} = 1\ \text{mA}$
- $R_D = 1\ \text{k}\Omega$, $\Delta R_D = 20\ \Omega$
- $(W/L)_{1,2} = 200/0.2$, $(W/L)_3 = 400/0.2$
- $V_{TH,n} = 0.4\ \text{V}$, $\mu_n C_{ox} = 100\ \mu\text{A/V}^2$, $\lambda_n = 0.1\ \text{V}^{-1}$
- $g_m r_o \gg 1$로 가정
- 바이어스 전압 $V_{b1}$ 값은 주어지지 않음

#### 구할 것

- (1) 입력 common-mode level $V_{CM,in}$의 최대값과 최소값
- (2) Common-mode 이득 $A_{CM}$과 common-mode to differential-mode 변환 이득 $A_{CM-DM}$
- (3) Common-mode rejection ratio (CMRR)

![그림 2023-1_중간-Q4](figures_%EB%AC%B8%EC%A0%9C%EC%84%A4%EB%AA%85_1007_Differential_Amplifiers/d6de05b6f97931dd-fig-Q4.png)

<details><summary>원문 보기</summary>

다음 차동 증폭기에 대해 주어진 조건을 이용하여 질문에 답하시오.

: $V_{DD} = 1.8\ \text{V}$, $I_{D3} = 1\ \text{mA}$, $R_D = 1\ \text{k}\Omega$, $\Delta R_D = 20\ \Omega$, $(W/L)_{1,2} = 200/0.2$, $(W/L)_3 = 400/0.2$, $V_{TH,n} = 0.4\ \text{V}$, $\mu_n C_{ox} = 100\ \mu\text{A/V}^2$, $\lambda_n = 0.1\ \text{V}^{-1}$. 단, $g_m r_o \gg 1$로 가정한다.

(1) 입력 common-mode level($V_{CM,in}$)의 최대값과 최소값을 각각 구하시오.

(2) Common-mode 이득($A_{CM}$)과 common-mode to differential-mode 변환 이득($A_{CM-DM}$)을 각각 구하시오.

(3) Common-mode rejection ratio(CMRR)를 구하시오.

</details>

#### 1. 회로 분석 및 등가 저항

- **소자 파라미터 및 오버드라이브**:
  - 가지 전류: $I_D = 0.5\,\text{mA}$, 테일 $I_{D3} = 1\,\text{mA}$.
  - $g_m = 10\,\text{mS}$, $R_{SS} = r_{o3} = 10\,\text{k}\Omega$.
  - $V_{OV3} = \sqrt{\frac{2(1)}{(0.1)(2000)}} = 0.1\,\text{V}$, $V_{OV1} = \sqrt{\frac{2(0.5)}{(0.1)(1000)}} = 0.1\,\text{V}$.
  - $V_{gs1} = V_{TH} + V_{OV1} = 0.4 + 0.1 = 0.5\,\text{V}$.

#### 2. 핵심 수식 전개 ($G_m \cdot R_{out}$)

- **(1) 입력 CM 레벨 허용 범위 ($V_{CM,in}$)**:
  - **하한 ($M_3$ 포화 유지)**: 공통 소스 $V_P \ge V_{OV3} = 0.1\,\text{V}$.
$$V_{CM,in,min} = V_P + V_{gs1} = 0.1\,\text{V} + 0.5\,\text{V} = \mathbf{0.6\,\text{V}}$$
  - **상한 ($M_2$ 포화 유지)**: 부하가 더 큰 오른쪽 드레인 $V_{D2} = 1.8 - (0.5\,\text{mA})(1.02\,\text{k}\Omega) = 1.29\,\text{V}$.
$$V_{CM,in,max} = V_{D2} + V_{TH} = 1.29\,\text{V} + 0.4\,\text{V} = \mathbf{1.69\,\text{V}} \quad (\text{대칭 기준 } 1.7\,\text{V})$$

- **(2) CM 이득 및 차동 누출 이득**:
$$A_{CM,1} \approx -\frac{R_D}{2R_{SS}} = -\frac{1\,\text{k}\Omega}{20\,\text{k}\Omega} = \mathbf{-0.05}$$
$$A_{CM-DM} \approx \frac{\Delta R_D}{2R_{SS}} = \frac{20\,\Omega}{20\,\text{k}\Omega} = \mathbf{+10^{-3}}$$

- **(3) CMRR (Common-Mode Rejection Ratio)**:
  - 대칭 차동 이득: $A_{DM} \approx -g_m R_D = -(10\,\text{mS})(1\,\text{k}\Omega) = -10$.
$$\mathrm{CMRR} = \frac{|A_{DM}|}{|A_{CM-DM}|} \approx \frac{10}{10^{-3}} = \mathbf{10000} \quad (\mathbf{80\,\text{dB}})$$

#### 3. 완성 답 및 주의할 점

- **완성 답**:
$$\boxed{0.6\,\text{V} \le V_{CM,in} \le 1.69\,\text{V},\quad A_{CM} \approx -0.05,\quad A_{CM-DM} \approx +10^{-3},\quad \mathrm{CMRR} \approx 10000\ (80\,\text{dB})}$$
- ⚠️ **$V_{CM,min}$ 계산 오류 주의**: 단순히 $V_{gs} \ge V_{TH}$가 아니라, 도통 전류를 흘리기 위해 $V_{gs} = V_{TH} + V_{OV} = 0.5\,\text{V}$가 필요하며 소스 전압 $V_P(=0.1\,\text{V})$를 더한 **$0.6\,\text{V}$**가 되어야 합니다.
- ⚠️ **CMRR 정의식 주의**: 분자는 $A_{CM}$이 아니라 반드시 차동 이득 **$|A_{DM}|$**입니다!

---

### P6. CMRR로 정하는 부하 오차

2015-1_중간-Q4 · 기출 4 · [원 문제 보기](../%EB%B3%B5%EC%8A%B5%EB%AC%B8%EC%A0%9C_1007_Differential_Amplifiers-%EB%AC%B8%EC%A0%9C.pdf)

#### 주어진 조건

- $\mu_n C_{ox} = 100\ \mu\text{A/V}^2$, $\mu_p C_{ox} = 50\ \mu\text{A/V}^2$ (원문 표기는 uA/V²)
- $\lambda_n = 0.1\ \text{V}^{-1}$, $\lambda_p = 0.2\ \text{V}^{-1}$
- $V_{TH,N} = 0.4\ \text{V}$
- $R_D = 10\ \text{k}\Omega$, $I_{D3} = 0.2\ \text{mA}$
- $(W/L)_1 = (W/L)_2 = 50$
- 2) 전용: $\Delta R_D = 0$
- 3) 전용: $\Delta R_D = 0$
- 4) 전용: $\Delta R_D = 100\ \Omega$
- 5) 전용: common-mode rejection ratio (CMRR) $= 30000$
- $V_{DD}$, 바이어스 전압 $V_{b1}$, $(W/L)_3$ 값은 주어지지 않음

#### 구할 것

- 1) (W/L)를 두 배로 하면 차동 입력 범위가 늘어나는지 O / X로 답함
- 2) $\Delta R_D = 0$일 때 차동 이득 $A_{DM}$
- 3) $\Delta R_D = 0$일 때 common-mode 이득 $A_{CM}$
- 4) $\Delta R_D = 100\ \Omega$일 때 common-mode to differential 이득 $A_{CM-DM}$
- 5) CMRR이 30000이 되는 $\Delta R_D$

![그림 2015-1_중간-Q4](figures_%EB%AC%B8%EC%A0%9C%EC%84%A4%EB%AA%85_1007_Differential_Amplifiers/3a32452fade661f8-fig-Q4.png)

<details><summary>원문 보기</summary>

With device parameters,

$\mu_n C_{ox} = 100\ \text{uA/V}^2$, $\mu_p C_{ox} = 50\ \text{uA/V}^2$, $\lambda_n=0.1\ \text{V}^{-1}$, $\lambda_p=0.2\ \text{V}^{-1}$, $V_{TH,N} =0.4\text{V}$, $R_D=10\text{kohm}$, $I_{D3}=0.2\text{mA}$

$(W/L)_1=(W/L)_2=50$

1) Doubling (W/L) increases differential input range ( O / X ) (5pt)

2) Calculate differential gain $A_{DM}$ when $\Delta R_D=0$ (5pt)

3) Calculate common-mode gain $A_{CM}$ when $\Delta R_D=0$ (5pt)

4) Calculate common-mode to differential gain $A_{CM-DM}$ when $\Delta R_D=100\text{ohm}$ (5pt)

5) Calculate $\Delta R_D$ if common-mode rejection ratio is 30000. (10pt)

</details>

#### 1. 회로 분석 및 등가 저항

- **소자 파라미터**:
  - $I_{SS} = 0.2\,\text{mA} \implies I_D = 0.1\,\text{mA}$.
  - $g_m = \sqrt{2(0.1)(50)(0.1)} = 1\,\text{mS}$.
  - $r_o = \frac{1}{0.1 \times 0.1} = 100\,\text{k}\Omega$, $R_{SS} = r_{o3} = \frac{1}{0.1 \times 0.2} = 50\,\text{k}\Omega$, $R_D = 10\,\text{k}\Omega$.

#### 2. 핵심 수식 전개 ($G_m \cdot R_{out}$)

- **1) $(W/L)$ 2배 시 차동 입력 범위**:
$$|v_{id}|_{cutoff} = \sqrt{\frac{2I_{SS}}{\mu_n C_{ox}(W/L)}} \propto \frac{1}{\sqrt{W/L}} \implies \mathbf{X} \quad (\text{범위가 오히려 줄어듦})$$

- **2) $\Delta R_D = 0$일 때 차동 이득 ($A_{DM}$)**:
$$A_{DM} = -g_m(R_D \parallel r_o) = -(1\,\text{mS})(10 \parallel 100\,\text{k}\Omega) = -\frac{100}{11} \approx \mathbf{-9.09} \quad (r_o \text{ 무시 시 } -10)$$

- **3) $\Delta R_D = 0$일 때 공통 모드 이득 ($A_{CM}$)**:
$$A_{CM} \approx -\frac{R_D}{2R_{SS}} = -\frac{10\,\text{k}\Omega}{100\,\text{k}\Omega} = \mathbf{-0.1}$$

- **4) $\Delta R_D = 100\,\Omega$일 때 CM-to-DM 이득 ($A_{CM-DM}$)**:
$$A_{CM-DM} \approx \frac{\Delta R_D}{2R_{SS}(1 + R_D/r_o)} = \frac{0.1\,\text{k}\Omega}{100\,\text{k}\Omega(1.1)} \approx \mathbf{9.09 \times 10^{-4}} \quad (r_o \text{ 무시 시 } 10^{-3})$$

- **5) $\mathrm{CMRR} = 30000$이 되는 허용 부하 오차 ($\Delta R_D$)**:
$$\mathrm{CMRR} \approx \frac{2g_m R_{SS} R_D}{|\Delta R_D|} = 30000 \implies |\Delta R_D| = \frac{2(1)(50)(10)}{30000}\,\text{k}\Omega = \frac{100}{3}\,\Omega \approx \mathbf{33.33\,\Omega}$$

#### 3. 완성 답 및 주의할 점

- **완성 답**:
$$\boxed{\text{1) X},\quad \text{2) } -9.09,\quad \text{3) } -0.1,\quad \text{4) } 9.09 \times 10^{-4},\quad \text{5) } 33.33\,\Omega}$$
- ⚠️ **입력쌍 폭 변경의 영향**: 테일 전류가 고정된 상태에서는 폭을 넓히면 트랜스컨덕턴스는 커지지만 전류를 한쪽으로 조향하는 데 필요한 전압 폭은 좁아집니다.

---

### P7. 테일 폭 변경과 CMRR

2015-2_중간-Q3 · 기출 3 · [원 문제 보기](../%EB%B3%B5%EC%8A%B5%EB%AC%B8%EC%A0%9C_1007_Differential_Amplifiers-%EB%AC%B8%EC%A0%9C.pdf)

#### 주어진 조건

- $\mu_n C_{ox} = 100\ \mu\text{A/V}^2$, $\mu_p C_{ox} = 50\ \mu\text{A/V}^2$ (원문 표기는 "uA/V²")
- $\lambda_n = 0.1\ \text{V}^{-1}$, $\lambda_p = 0.2\ \text{V}^{-1}$
- $V_{TH,N} = 0.4\ \text{V}$
- $R_D = 10\ \text{k}\Omega$
- $V_{b1} = 0.6\ \text{V}$
- $(W/L)_1 = (W/L)_2 = 50$, $(W/L)_3 = 100$
- 2) 전용: $\Delta R_D = 0$
- 3) 전용: $\Delta R_D = 0$
- 4) 전용: $\Delta R_D / R_D = 1\%$
- 6) 전용: $(W/L)_3$를 두 배로 함
- $V_{DD}$ 값은 주어지지 않음

#### 구할 것

- 1) $(W/L)_3$를 두 배로 하면 차동 입력 범위가 늘어나는지 O / X로 답함
- 2) $\Delta R_D = 0$일 때 차동 이득 $A_{DM}$
- 3) $\Delta R_D = 0$일 때 공통 모드 이득 $A_{CM}$
- 4) $\Delta R_D / R_D = 1\%$일 때 공통 모드 입력에서 차동 출력으로의 이득 $A_{CM-DM}$
- 5) CMRR
- 6) $(W/L)_3$를 두 배로 했을 때의 CMRR

![그림 2015-2_중간-Q3](figures_%EB%AC%B8%EC%A0%9C%EC%84%A4%EB%AA%85_1007_Differential_Amplifiers/4229e80202226b98-fig-Q3.png)

<details><summary>원문 보기</summary>

With device parameters,

$\mu_n C_{ox} = 100\ \text{uA/V}^2$, $\mu_p C_{ox} = 50\ \text{uA/V}^2$, $\lambda_n=0.1\ \text{V}^{-1}$, $\lambda_p=0.2\ \text{V}^{-1}$, $V_{TH,N}=0.4\text{V}$, $R_D=10\text{kohm}$, $V_{b1}=0.6\text{V}$, $(W/L)_1=(W/L)_2=50$, $(W/L)_3=100$

1) Doubling $(W/L)_3$ increases differential input range ( O / X ) (5pt)

2) Calculate differential gain $A_{DM}$ when $\Delta R_D=0$ (5pt)

3) Calculate common-mode gain $A_{CM}$ when $\Delta R_D=0$ (5pt)

4) Calculate common-mode input to differential output gain $A_{CM-DM}$ when $\Delta R_D/R_D=1\%$ (5pt)

5) Calculate CMRR (5pt)

6) Calculate CMRR if $(W/L)_3$ is doubled. (5pt)

</details>

#### 1. 회로 분석 및 등가 저항

- **초기 동작점 ($V_{b1} = 0.6\,\text{V}$ 고정)**:
  - 테일 전류: $I_{SS} = \frac{1}{2}(0.1)(100)(0.6 - 0.4)^2 = 0.2\,\text{mA} \implies I_D = 0.1\,\text{mA}$.
  - $g_m = 1\,\text{mS}$, $r_{o3} = \frac{1}{0.1 \times 0.2} = 50\,\text{k}\Omega$, $R_D = 10\,\text{k}\Omega$.

#### 2. 핵심 수식 전개 ($G_m \cdot R_{out}$)

- **1) $(W/L)_3$ 2배 시 차동 입력 범위**:
  - $V_{b1}$ 고정이므로 $I_{SS} \propto (W/L)_3$로 2배 증가. $|v_{id}|_{cutoff} \propto \sqrt{I_{SS}}$이므로 $\sqrt{2}$배 증가 $\implies$ **O**.
- **2) $\Delta R_D = 0$일 때 $A_{DM}$**:
$$A_{DM} = -g_m R_D = -(1\,\text{mS})(10\,\text{k}\Omega) = \mathbf{-10}$$
- **3) $\Delta R_D = 0$일 때 $A_{CM}$**:
$$A_{CM} \approx -\frac{R_D}{2r_{o3}} = -\frac{10\,\text{k}\Omega}{100\,\text{k}\Omega} = \mathbf{-0.1}$$
- **4) $\Delta R_D/R_D = 1\% = 0.1\,\text{k}\Omega$일 때 $A_{CM-DM}$**:
$$A_{CM-DM} \approx \frac{\Delta R_D}{2r_{o3}} = \frac{0.1\,\text{k}\Omega}{100\,\text{k}\Omega} = \mathbf{+0.001}$$
- **5) 초기 상태 CMRR**:
$$\mathrm{CMRR} = \frac{|A_{DM}|}{|A_{CM-DM}|} = \frac{10}{0.001} = \mathbf{10000} \quad (\mathbf{80\,\text{dB}})$$
- **6) $(W/L)_3$ 2배 변경 후 CMRR**:
  - $I_{SS}' = 0.4\,\text{mA} \implies g_m' = \sqrt{2}\,\text{mS}$, $r_{o3}' = 25\,\text{k}\Omega$.
$$\mathrm{CMRR}' \approx \frac{2g_m' r_{o3}' R_D}{\Delta R_D} = \frac{1}{\sqrt{2}}\mathrm{CMRR} = \frac{10000}{\sqrt{2}} \approx \mathbf{7071.07} \quad (\mathbf{76.99\,\text{dB}})$$

#### 3. 완성 답 및 주의할 점

- **완성 답**:
$$\boxed{\text{1) O},\quad \text{2) } -10,\quad \text{3) } -0.1,\quad \text{4) } +0.001,\quad \text{5) } 10000,\quad \text{6) } 7071.07}$$
- ⚠️ **CMRR 트레이드오프**: 테일 폭을 늘리면 테일 전류 증가로 입력 범위는 넓어지지만, 테일 저항이 절반으로 떨어져 CMRR은 $1/\sqrt{2}$배로 악화됩니다.

---

### P8. 직렬 테일 저항과 CMRR

2017-1_중간_C030-Q2 · 기출 2 · [원 문제 보기](../%EB%B3%B5%EC%8A%B5%EB%AC%B8%EC%A0%9C_1007_Differential_Amplifiers-%EB%AC%B8%EC%A0%9C.pdf)

#### 주어진 조건

- $V_{DD} = 3\ \text{V}$
- 그림에는 전원이 $V_{CC}$로 인쇄됨. 문제 문장의 $V_{DD}$를 이 전원 값으로 봄
- $\mu_n C_{ox} = 100\ \mu\text{A/V}^2$ (원문 표기는 uA/V²)
- $V_{TH,N} = 0.4\ \text{V}$, $\lambda_n = 0.1\ \text{V}^{-1}$
- $I_{D1} = 100\ \mu\text{A}$ (원문 표기는 100uA)
- $(W/L)_1 = 50$, $(W/L)_2 = (W/L)_3 = 25$ (원문 표기 $(W/L)_{2,3} = 25$)
- $R_E = R_C = 10\ \text{k}\Omega$ (원문 표기 $R_c$ = 10 kohm, 그림 라벨은 $R_C$)
- 3), 4) 전용: $\Delta R_C = 0$
- 5) 전용: $\Delta R_C = 10\ \Omega$ (원문 표기 10ohm)
- 바이어스 전압 $V_{b1}$ 값은 주어지지 않음

#### 구할 것

- 1) $V_{in1,2}$ 공통 모드 입력의 입력 범위
- 2) 차동 입력 $V_{in1} - V_{in2}$의 입력 범위
- 3) $\Delta R_C = 0$일 때 소신호 차동 이득 $A_{DM} = V_{out}/(V_{in1} - V_{in2})$
- 4) $\Delta R_C = 0$일 때 공통 모드 이득 $A_{CM}$
- 5) $\Delta R_C = 10\ \Omega$일 때 공통 모드 입력에서 차동 출력으로의 이득 $A_{CM-DM}$
- 6) CMRR

![그림 2017-1_중간_C030-Q2](figures_%EB%AC%B8%EC%A0%9C%EC%84%A4%EB%AA%85_1007_Differential_Amplifiers/482116614420740f-fig-Q2.png)

<details><summary>원문 보기</summary>

$V_{DD}=3\text{V}$, $\mu_n C_{ox} = 100\ \text{uA/V}^2$, $V_{TH,N} =0.4\text{V}$, $\lambda_n=0.1\ \text{V}^{-1}$,

$I_{D1}=100\text{uA}$, $(W/L)_1=50$, $(W/L)_{2,3} = 25$ , $R_E=R_c=10\ \text{kohm}$

1) Calculate input range of common-mode input of $V_{in1,2}$ (5pt)

2) Calculate input range of differential input ($V_{in1}$-$V_{in2}$) (5pt)

3) Calculate small signal differential gain $A_{DM}$ ($V_{out}/(V_{in1}$-$V_{in2}$)) when $\Delta R_C=0$ (5pt)

4) Calculate common-mode gain $A_{CM}$ when $\Delta R_C=0$ (5pt)

5) Calculate common-mode input to differential output gain $A_{CM-DM}$ when $\Delta R_C = 10\text{ohm}$ (5pt)

6) Calculate CMRR (5pt)

</details>

#### 1. 회로 분석 및 등가 저항

- **테일 저항의 올바른 식별**: 저항 $R_E$는 $M_1$의 소스가 아닌 **드레인 위쪽에 직렬**로 연결되어 있습니다.
$$R_{SS} = R_E + r_{o1} = 10\,\text{k}\Omega + 100\,\text{k}\Omega = 110\,\text{k}\Omega$$
- **소자 파라미터**:
  - $I_{D1} = 0.1\,\text{mA} \implies I_{D2,3} = 0.05\,\text{mA}$.
  - $g_{m2,3} = 0.5\,\text{mS}$, $r_{o2,3} = 200\,\text{k}\Omega$, $r_{o1} = 100\,\text{k}\Omega$.
  - $V_{OV1} = 0.2\,\text{V}$, $V_{OV2,3} = 0.2\,\text{V}$.

#### 2. 핵심 수식 전개 ($G_m \cdot R_{out}$)

- **1) 입력 CM 범위 ($V_{CM}$)**:
  - 하한 ($M_1$ 포화): $V_{CM,min} = V_{OV1} + I_{D1}R_E + V_{OV2} + V_{TH} = 0.2 + (0.1)(10) + 0.2 + 0.4 = \mathbf{1.8\,\text{V}}$.
  - 상한 ($M_2$ 포화): $V_D = 3 - (0.05)(10) = 2.5\,\text{V} \implies V_{CM,max} = 2.5 + 0.4 = \mathbf{2.9\,\text{V}}$.
- **2) 차동 입력 범위**:
$$|v_{id}|_{cutoff} = \sqrt{\frac{2(0.1)}{(0.1)(25)}} = \sqrt{0.08} \approx \mathbf{\pm 0.28\,\text{V}}$$
- **3) 소신호 차동 이득 ($A_{DM}$)**:
$$A_{DM} = -g_m(R_C \parallel r_o) = -(0.5)(10 \parallel 200\,\text{k}\Omega) = -\frac{100}{21} \approx \mathbf{-4.76}$$
- **4) 공통 모드 이득 ($A_{CM}$)**:
$$A_{CM,SE} \approx -\frac{R_C}{2R_{SS}} = -\frac{10\,\text{k}\Omega}{220\,\text{k}\Omega} \approx \mathbf{-4.55 \times 10^{-2}} \quad (\text{차동 출력은 } 0)$$
- **5) CM-to-DM 이득 ($A_{CM-DM}, \Delta R_C = 10\,\Omega$)**:
$$A_{CM-DM} \approx \frac{\Delta R_C}{2R_{SS}(1 + R_C/r_o)} = \frac{0.01\,\text{k}\Omega}{220\,\text{k}\Omega(1.05)} \approx \mathbf{+4.33 \times 10^{-5}}$$
- **6) CMRR**:
$$\mathrm{CMRR} \approx \frac{2g_m R_{SS} R_C}{|\Delta R_C|} = \frac{2(0.5)(110)(10)}{0.01} = \mathbf{110000} \quad (\mathbf{100.83\,\text{dB}})$$

#### 3. 완성 답 및 주의할 점

- **완성 답**:
$$\boxed{1.8\,\text{V} \le V_{CM} \le 2.9\,\text{V},\quad \pm 0.28\,\text{V},\quad -4.76,\quad -4.55 \times 10^{-2},\quad 4.33 \times 10^{-5},\quad 110000}$$
- ⚠️ **축퇴 저항 착오 방지**: $R_E$가 $M_1$ 소스 아래에 있으면 $g_{m1} r_{o1} R_E$로 증폭되지만, 드레인 위에 있으면 단순 직렬 저항 $R_E + r_{o1}$입니다.

---

### P9. 캐스코드 부하의 DM·CM 이득

2019-1_중간-Q4 · 기출 4 · [원 문제 보기](../%EB%B3%B5%EC%8A%B5%EB%AC%B8%EC%A0%9C_1007_Differential_Amplifiers-%EB%AC%B8%EC%A0%9C.pdf)

#### 주어진 조건

- $V_{DD} = 1.8\ \text{V}$, $I_{D7} = 2\ \text{mA}$
- $(W/L)_{1,2} = 100/0.2$, $(W/L)_{3,4} = (W/L)_{5,6} = 200/0.2$, $(W/L)_7 = 200/0.2$
- $\mu_n C_{ox} = 100\ \mu\text{A/V}^2$, $\mu_p C_{ox} = 50\ \mu\text{A/V}^2$
- $\lambda_n = \lambda_p = 0.1\ \text{V}^{-1}$
- $g_m r_o \gg 1$로 가정
- 바이어스 전압 $V_{b1}$, $V_{b2}$, $V_{b3}$ 값은 주어지지 않음

#### 구할 것

- (1) 차동 전압 이득
- (2) Common-mode 이득 $A_{CM}$

![그림 2019-1_중간-Q4](figures_%EB%AC%B8%EC%A0%9C%EC%84%A4%EB%AA%85_1007_Differential_Amplifiers/dafeb615173c3160-fig-Q4.png)

<details><summary>원문 보기</summary>

다음 회로에 대해 주어진 조건을 이용하여 질문에 답하시오.

: $V_{DD} = 1.8\ \text{V}$, $I_{D7} = 2\ \text{mA}$, $(W/L)_{1,2} = 100/0.2$, $(W/L)_{3,4} = (W/L)_{5,6} = 200/0.2$, $(W/L)_7 = 200/0.2$, $\mu_n C_{ox} = 100\ \mu\text{A/V}^2$, $\mu_p C_{ox} = 50\ \mu\text{A/V}^2$, $\lambda_n = \lambda_p = 0.1\ \text{V}^{-1}$, $g_m r_o \gg 1$로 가정한다.

(1) 차동 전압 이득을 구하시오.

(2) Common-mode 이득($A_{CM}$)을 구하시오.

</details>

#### 1. 회로 분석 및 등가 저항

- **소자 파라미터**:
  - 가지 전류 $1\,\text{mA}$, $g_{m1} = g_{m3} = 10\,\text{mS}$, $r_{o1,3,5} = 10\,\text{k}\Omega$, 테일 $r_{o7} = 5\,\text{k}\Omega$.
- **상단 PMOS 캐스코드 부하 저항 ($R_{up}$)**:
$$R_{up} \approx g_{m3} r_{o3} r_{o5} = (10\,\text{mS})(10\,\text{k}\Omega)(10\,\text{k}\Omega) = 1000\,\text{k}\Omega = 1\,\text{M}\Omega$$
- **하단 소스 축퇴 출력 저항 ($R_{dn}$, CM 반회로)**:
$$R_{dn} \approx g_{m1} r_{o1} (2r_{o7}) = (10\,\text{mS})(10\,\text{k}\Omega)(10\,\text{k}\Omega) = 1000\,\text{k}\Omega = 1\,\text{M}\Omega$$

#### 2. 핵심 수식 전개 ($G_m \cdot R_{out}$)

- **(1) 차동 전압 이득 ($A_{DM}$)**:
  - DM 반회로에서 소스는 가상 접지이므로 하단 저항은 축퇴 없는 $r_{o1}$입니다.
$$R_{out,DM} = r_{o1} \parallel R_{up} = 10\,\text{k}\Omega \parallel 1000\,\text{k}\Omega \approx 9.9\,\text{k}\Omega$$
$$A_{DM} = -g_{m1}(r_{o1} \parallel R_{up}) \approx -(10\,\text{mS})(9.9\,\text{k}\Omega) = \mathbf{-99.01}$$

- **(2) 공통 모드 이득 ($A_{CM}$)**:
  - $R_{up}$과 $R_{dn}$이 모두 $1000\,\text{k}\Omega$로 동일 차수이므로 둘의 병렬을 유지해야 합니다.
$$R_{out,CM} = R_{up} \parallel R_{dn} = 1000\,\text{k}\Omega \parallel 1000\,\text{k}\Omega = 500\,\text{k}\Omega$$
$$G_{m,CM} \approx \frac{1}{2r_{o7}} = \frac{1}{10\,\text{k}\Omega} = 0.1\,\text{mS}$$
$$A_{CM} = -G_{m,CM} R_{out,CM} \approx -\frac{500\,\text{k}\Omega}{10\,\text{k}\Omega} = \mathbf{-50}$$

#### 3. 완성 답 및 주의할 점

- **완성 답**:
$$\boxed{A_{DM} \approx -99.01,\qquad A_{CM} \approx -50}$$
- ⚠️ **하단 출력 저항 병렬 필수**: 캐스코드 부하가 매우 크므로 하단 소스 축퇴 저항 $R_{dn} \approx g_{m1}r_{o1}(2r_{o7})$과의 병렬을 놓치고 $-R_{up}/(2r_{o7}) = -100$으로 풀면 2배의 오차가 발생합니다.

---

### P10. 전류 거울의 면적비와 이득

P10.71 · 장말문제 10.71 · [원 문제 보기](../%EB%B3%B5%EC%8A%B5%EB%AC%B8%EC%A0%9C_1007_Differential_Amplifiers-%EB%AC%B8%EC%A0%9C.pdf)

#### 주어진 조건

- $(W/L)_3 = N(W/L)_4$
- 채널 길이 변조 무시
- $i_1$은 $I_1$의 소신호 성분으로 보임

#### 구할 것

- 소신호 이득 $v_{out}/i_1$

![그림 P10.71](figures_%EB%AC%B8%EC%A0%9C%EC%84%A4%EB%AA%85_1007_Differential_Amplifiers/80011cc16d445340-fig10-92.png)

<details><summary>원문 보기</summary>

Determine the small-signal gain $v_{out}/i_1$ in the circuit of Fig. 10.92 if $(W/L)_3 = N(W/L)_4$. Neglect channel-length modulation.

</details>

#### 1. 회로 분석 및 등가 저항

- **다이오드 연결 $M_3$의 게이트 전압**: $i_1$이 아래로 유출될 때 게이트 전압은 음으로 하강.
$$v_g = -\frac{i_1}{g_{m3}}$$
- **전류 거울 복사 전류 ($i_4$)**:
$$i_4 = -g_{m4} v_g = \frac{g_{m4}}{g_{m3}} i_1$$

#### 2. 핵심 수식 전개 ($G_m \cdot R_{out}$)

- **면적비와 $g_m$ 비의 관계**: 동일 $V_{OV}$에서 $g_m$ 비는 면적비와 정확히 일치
$$\frac{g_{m4}}{g_{m3}} = \frac{(W/L)_4}{(W/L)_3} = \frac{1}{N} \implies i_4 = \frac{i_1}{N}$$

- **출력 전압 및 트랜스임피던스 ($v_{out}/i_1$)**:
  - $R_L$로 유입되는 전류는 $i_4$이므로
$$v_{out} = i_4 R_L = \frac{R_L}{N} i_1$$
$$\frac{v_{out}}{i_1} = \mathbf{+\frac{R_L}{N}\ [\Omega]}$$

#### 3. 완성 답 및 주의할 점

- **완성 답**:
$$\boxed{\frac{v_{out}}{i_1} = +\frac{R_L}{N}\ [\Omega]}$$
- ⚠️ **부호 확인**: $i_1$이 아래로 증가하면 $v_g$가 낮아져 PMOS 소스-게이트 전압이 커지고 공급 전류 $i_4$가 증가하므로 출력 전압은 상승(+)합니다.

---

### P11. 전류 거울의 출력 변화

P10.72 · 장말문제 10.72 · [원 문제 보기](../%EB%B3%B5%EC%8A%B5%EB%AC%B8%EC%A0%9C_1007_Differential_Amplifiers-%EB%AC%B8%EC%A0%9C.pdf)

#### 주어진 조건

- $I_1$은 $I_0$에서 $I_0 + \Delta I$로, $I_2$는 $I_0$에서 $I_0 - \Delta I$로 바뀜
- 채널 길이 변조 무시

#### 구할 것

- 변화 전과 후의 $V_{out}$을 다음 각 경우에 계산
- (a) $(W/L)_3 = (W/L)_4$
- (b) $(W/L)_3 = 2(W/L)_4$

![그림 P10.72](figures_%EB%AC%B8%EC%A0%9C%EC%84%A4%EB%AA%85_1007_Differential_Amplifiers/7cbdd14825907ca5-fig10-93.png)

<details><summary>원문 보기</summary>

In the circuit shown in Fig. 10.93, $I_1$ changes from $I_0$ to $I_0 + \Delta I$ and $I_2$ from $I_0$ to $I_0 - \Delta I$. Neglecting channel-length modulation, calculate $V_{out}$ before and after the change if

(a) $(W/L)_3 = (W/L)_4$.

(b) $(W/L)_3 = 2(W/L)_4$.

</details>

#### 1. 회로 분석 및 등가 저항

- **출력 노드 KCL**: $M_4$ 공급 전류 $I_4$와 $I_2$ 흡수 전류의 차이가 $R_L$로 흐름
$$V_{out} = R_L(I_4 - I_2) = R_L(k I_1 - I_2), \quad \text{where } k = \frac{(W/L)_4}{(W/L)_3}$$

#### 2. 핵심 수식 전개 ($G_m \cdot R_{out}$)

- **(a) 동일 크기 ($k = 1$)**:
  - **변화 전** ($I_1 = I_0, I_2 = I_0$):
$$V_{out,\text{전}} = R_L(I_0 - I_0) = \mathbf{0}$$
  - **변화 후** ($I_1 = I_0 + \Delta I, I_2 = I_0 - \Delta I$):
$$V_{out,\text{후}} = R_L[(I_0 + \Delta I) - (I_0 - \Delta I)] = \mathbf{2\Delta I R_L}$$

- **(b) 기준 소자가 2배 ($k = 1/2$)**:
  - **변화 전**:
$$V_{out,\text{전}} = R_L\left(\frac{I_0}{2} - I_0\right) = \mathbf{-\frac{1}{2}I_0 R_L}$$
  - **변화 후**:
$$V_{out,\text{후}} = R_L\left[\frac{I_0 + \Delta I}{2} - (I_0 - \Delta I)\right] = \mathbf{\frac{3\Delta I - I_0}{2} R_L}$$
  - *(참고: 출력 순변화량 $\Delta V_{out} = V_{out,\text{후}} - V_{out,\text{전}} = \frac{3}{2}\Delta I R_L$)*

#### 3. 완성 답 및 주의할 점

- **완성 답**:
$$\boxed{\text{(a) 전: } 0,\ \text{후: } 2\Delta I R_L \qquad\vert\qquad \text{(b) 전: } -\frac{1}{2}I_0 R_L,\ \text{후: } \frac{3\Delta I - I_0}{2} R_L}$$
- ⚠️ **(b)번 오프셋 주의**: 변화 전 전압은 $-\frac{1}{2}\Delta I R_L$이 아니라 바이어스 전류 $I_0$에 의한 **$-\frac{1}{2}I_0 R_L$**이며, 변화 후 전압은 이 초기 오프셋에 변화량 $\frac{3}{2}\Delta I R_L$을 더한 값입니다.

---

### P12. MOS 차동쌍의 부하별 이득

2013-1_중간-Q4 · 기출 4 · [원 문제 보기](../%EB%B3%B5%EC%8A%B5%EB%AC%B8%EC%A0%9C_1007_Differential_Amplifiers-%EB%AC%B8%EC%A0%9C.pdf)

#### 주어진 조건

- $I_{SS} = 2\ \text{mA}$
- $(W/L)_{1,2} = 500$, $(W/L)_{3,4} = 1000$
- $R_{DD} = 1\ \text{k}\Omega$, $R_{SS} = 200\ \Omega$
- $\mu_n C_{ox} = 100\ \mu\text{A/V}^2$, $\mu_p C_{ox} = 50\ \mu\text{A/V}^2$
- $\lambda_n = 0.1\ \text{V}^{-1}$, $\lambda_p = 0.1\ \text{V}^{-1}$
- (4) 전용 (회로 (c)): $I_{DS1} = I_{DS2} = 1\ \text{mA}$
- $V_{DD}$ 값과 (c)의 네 전류원 값은 주어지지 않음

#### 구할 것

- (1) 그림 (a) 회로의 차동 전압 이득 $v_{out}/(v_{in1} - v_{in2})$의 식
- (2) 주어진 조건으로 그림 (a) 회로의 차동 전압 이득 값
- (3) 주어진 조건으로 그림 (b) 회로의 차동 전압 이득 값
- (4) 주어진 조건으로 그림 (c) 회로의 차동 전압 이득 값

![그림 2013-1_중간-Q4](figures_%EB%AC%B8%EC%A0%9C%EC%84%A4%EB%AA%85_1007_Differential_Amplifiers/6bed1b92aee8ee4e-fig-Q4.png)

<details><summary>원문 보기</summary>

다음 차동증폭단에 대해 다음 조건을 이용하여 질문에 답하시오.

$I_{SS} = 2\ \text{mA}$, $(W/L)_{1,2} = 500$, $(W/L)_{3,4} = 1000$, $R_{DD} = 1\ \text{k}\Omega$, $R_{SS} = 200\ \Omega$,

$\mu_n C_{ox} = 100\ \mu\text{A/V}^2$, $\mu_p C_{ox} = 50\ \mu\text{A/V}^2$, $\lambda_n = 0.1\ \text{V}^{-1}$, $\lambda_p = 0.1\ \text{V}^{-1}$

(1) 그림(a) 회로의 차동 전압이득($v_{out}/(v_{in1} - v_{in2})$) 식을 구하시오.

(2) 주어진 조건을 이용하여 그림(a) 회로의 차동 전압이득 값을 구하시오.

(3) 주어진 조건을 이용하여 그림(b) 회로의 차동 전압이득 값을 구하시오.

(4) 주어진 조건을 이용하여 그림(c) 회로의 차동 전압이득 값을 구하시오. ($I_{DS1} = I_{DS2} = 1\ \text{mA}$)

</details>

#### 1. 회로 분석 및 등가 저항

- **공통 소신호 파라미터**:
  - 가지 전류 $I_D = 1\,\text{mA}$.
  - $g_{m1\sim 4} = \sqrt{2(0.1)(500)(1)} = 10\,\text{mS}$, $r_{o1\sim 4} = \frac{1}{0.1 \times 1} = 10\,\text{k}\Omega$.

#### 2. 핵심 수식 전개 ($G_m \cdot R_{out}$)

- **(1, 2) 회로 (a) - 능동 전류 거울 부하**:
  - 거울에 의해 두 경로의 신호 전류가 오른쪽 단일 출력에 합산됨.
$$A_a \approx +g_{m1}(r_{o2} \parallel r_{o4}) = +(10\,\text{mS})(10 \parallel 10\,\text{k}\Omega) = \mathbf{+50}$$

- **(3) 회로 (b) - 다이오드 연결 부하**:
  - DM 가상 접지 반회로: 부하는 $1/g_{m3} \approx 0.1\,\text{k}\Omega$로 매우 작음.
$$A_b = -\frac{g_{m1}}{g_{m3} + 1/r_{o1} + 1/r_{o3}} = -\frac{10}{10 + 0.1 + 0.1} \approx \mathbf{-0.98} \quad (\text{주항 } -1)$$

- **(4) 회로 (c) - 소스 축퇴 및 드레인 저항 부하**:
  - DM 가상 접지: $R_D = R_{DD}/2 = 0.5\,\text{k}\Omega$, $R_S = R_{SS}/2 = 0.1\,\text{k}\Omega$.
  - $g_m R_S = (10\,\text{mS})(0.1\,\text{k}\Omega) = 1$ (강한 축퇴 아님 $\implies$ 분모 1 유지!).
$$A_c = -\frac{g_m R_D r_o}{r_o + R_D + R_S + g_m r_o R_S} = -\frac{(10)(0.5)(10)}{10 + 0.5 + 0.1 + 10} = -\frac{50}{20.6} \approx \mathbf{-2.43}$$
  - *(단순 축퇴식 근사: $-\frac{R_D}{1/g_m + R_S} = -\frac{0.5}{0.1 + 0.1} = -2.5$)*

#### 3. 완성 답 및 주의할 점

- **완성 답**:
$$\boxed{A_a \approx +50,\qquad A_b \approx -0.98,\qquad A_c \approx -2.43}$$
- ⚠️ **회로 (a) 부호**: 왼쪽 입력을 올리면 거울 공급이 늘고 오른쪽 흡수가 줄어 오른쪽 출력이 상승하므로 **양수(+)**입니다.
- ⚠️ **회로 (c) 축퇴 주의**: $g_m R_S = 1$이므로 $1/g_m$을 무시하면 2배의 오차가 생깁니다.

---

### P13. BJT 차동쌍의 부하별 이득

2015-1_중간-Q3 · 기출 3 · [원 문제 보기](../%EB%B3%B5%EC%8A%B5%EB%AC%B8%EC%A0%9C_1007_Differential_Amplifiers-%EB%AC%B8%EC%A0%9C.pdf)

#### 주어진 조건

- 1) 전용: $I_{EE} = 2\ \text{mA}$, $V_{A,p} = 10\ \text{V}$, $V_{A,n} = 10\ \text{V}$, $R_1 = R_2 = 10\ \text{k}\Omega$ (원문 표기 $R_{1,2}$ = 10kohm), $\beta = 100$
- 2) 전용: $I_{EE} = 0.2\ \text{mA}$, $V_{A,p} = 4\ \text{V}$, $V_{A,n} = 5\ \text{V}$, $\beta = 100$
- 3) 전용: $I_{EE} = 0.1\ \text{mA}$, $V_{A,n} = 10\ \text{V}$, $R_C = 1\ \text{k}\Omega$, $R_E = 5\ \text{k}\Omega$, $\beta = 100$
- 3) 전용: 그림의 두 전류원은 모두 $I_{EE}$로 인쇄됨
- 열전압 $V_T$와 $V_{CC}$ 값은 주어지지 않음

#### 구할 것

- 1) 그림 Q3 회로의 차동 전압 이득
- 2) 그림 Q3-2 회로의 차동 전압 이득
- 3) 그림 Q3-3 회로의 차동 전압 이득

![그림 2015-1_중간-Q3](figures_%EB%AC%B8%EC%A0%9C%EC%84%A4%EB%AA%85_1007_Differential_Amplifiers/12e832520417c9f9-fig-Q3.png)

![그림 2015-1_중간-Q3](figures_%EB%AC%B8%EC%A0%9C%EC%84%A4%EB%AA%85_1007_Differential_Amplifiers/e2f086d4e57863fd-fig-Q3-2.png)

![그림 2015-1_중간-Q3](figures_%EB%AC%B8%EC%A0%9C%EC%84%A4%EB%AA%85_1007_Differential_Amplifiers/de290f9ea1166a62-fig-Q3-3.png)

<details><summary>원문 보기</summary>

Calculate differential voltage gain of following circuits.

1) $I_{EE}=2\text{mA}$, $V_{A,p}=10\text{V}$, $V_{A,n}=10\text{V}$, $R_{1,2} = 10\text{kohm}$, $\beta=100$ (10pt)

2) $I_{EE}=0.2\text{mA}$, $V_{A,p}=4\text{V}$, $V_{A,n}=5\text{V}$, $\beta=100$ (5pt)

3) $I_{EE}=0.1\text{mA}$, $V_{A,n}=10\text{V}$, $R_C=1\text{kohm}$, $R_E=5\text{kohm}$, $\beta=100$ (5pt)

</details>

#### 1. 회로 분석 및 등가 저항

- **공통 가정**: $V_T = 26\,\text{mV}$.
- **(1) 그림 Q3 자기 B–C 귀환 부하 임피던스**:
  - PNP 에미터/컬렉터에서 본 등가 저항:
$$R_{load} \approx \frac{R_1 + r_\pi}{\beta + 1} \approx \frac{R_1}{\beta} + \frac{1}{g_{m3}}$$
  - $I_C = 1\,\text{mA} \implies g_m = 38.46\,\text{mS}$, $r_\pi = 2.6\,\text{k}\Omega$, $r_{o1,3} = 10\,\text{k}\Omega$.
  - $R_{load} = \frac{10 + 2.6}{101}\,\text{k}\Omega \approx 0.125\,\text{k}\Omega$.

#### 2. 핵심 수식 전개 ($G_m \cdot R_{out}$)

- **1) 그림 Q3 차동 전압 이득**:
$$R_{out,1} = r_{o1} \parallel r_{o3} \parallel R_{load} \approx 0.122\,\text{k}\Omega$$
$$A_{v1} = -g_{m1} R_{out,1} \approx -(38.46\,\text{mS})(0.122\,\text{k}\Omega) \approx \mathbf{-4.68}$$

- **2) 그림 Q3-2 전류 거울 능동 부하 이득**:
  - 가지 전류 $I_C = 0.1\,\text{mA} \implies g_m = 3.85\,\text{mS}$, $r_{o2} = 50\,\text{k}\Omega$, $r_{o4} = 40\,\text{k}\Omega$.
$$R_{out,2} = r_{o2} \parallel r_{o4} = \frac{200}{9}\,\text{k}\Omega$$
$$A_{v2} \approx +g_m(r_{o2} \parallel r_{o4}) = +(3.85)\left(\frac{200}{9}\right) \approx \mathbf{+85.47}$$

- **3) 그림 Q3-3 이미터 축퇴 저항 회로 이득**:
  - 각 가지 전류 $I_{EE} = 0.1\,\text{mA}$, DM 반회로 축퇴 저항 $R_{E,반} = R_E/2 = 2.5\,\text{k}\Omega$.
  - $g_m R_{E,반} = (3.85)(2.5) \approx 9.62 \gg 1$ (강한 축퇴 주항 적용).
$$A_{v3} \approx -\frac{R_C}{R_E/2} = -\frac{1\,\text{k}\Omega}{2.5\,\text{k}\Omega} = \mathbf{-0.4} \quad (1/g_m \text{ 포함 시 } -0.36)$$

#### 3. 완성 답 및 주의할 점

- **완성 답**:
$$\boxed{A_{v1} \approx -4.68,\qquad A_{v2} \approx +85.47,\qquad A_{v3} \approx -0.4}$$
- ⚠️ **그림 Q3 부하 연결**: $Q_3, Q_4$는 베이스가 묶인 전류 거울이 아니며, 각자 자기 B–C 저항을 단 다이오드형 귀환 부하입니다.

---

### P14. 목표 이득과 Early 전압

P10.75 · 장말문제 10.75 · [원 문제 보기](../%EB%B3%B5%EC%8A%B5%EB%AC%B8%EC%A0%9C_1007_Differential_Amplifiers-%EB%AC%B8%EC%A0%9C.pdf)

#### 주어진 조건

- 목표 전압 이득 100
- $V_{A,n} = 5\ \text{V}$

#### 구할 것

- pnp 트랜지스터에 필요한 Early 전압

![그림 P10.75](figures_%EB%AC%B8%EC%A0%9C%EC%84%A4%EB%AA%85_1007_Differential_Amplifiers/4ae920e792c52166-fig10-96.png)

<details><summary>원문 보기</summary>

We wish to design the stage shown in Fig. 10.96 for a voltage gain of 100. If $V_{A,n} = 5\ \text{V}$, what is the required Early voltage for the pnp transistors?

</details>

#### 1. 회로 분석 및 등가 저항

- **능동 부하 증폭기 전압 이득식**:
$$A_v = g_m(r_{o2} \parallel r_{o4}) = \frac{I_C}{V_T}\left(\frac{V_{A,n}}{I_C} \parallel \frac{V_{A,p}}{I_C}\right) = \frac{1}{V_T}\frac{V_{A,n} V_{A,p}}{V_{A,n} + V_{A,p}}$$
- 바이어스 전류 $I_C$가 자동 소거되므로 $V_T$와 Early 전압만으로 결정됩니다 ($V_T = 26\,\text{mV}$ 가정).

#### 2. 핵심 수식 전개 ($G_m \cdot R_{out}$)

- **역수로 분리하여 $V_{A,p}$ 역산**:
$$\frac{1}{A_v} = \frac{V_T}{V_{A,n}} + \frac{V_T}{V_{A,p}}$$
$$\frac{1}{100} = \frac{0.026\,\text{V}}{5\,\text{V}} + \frac{0.026\,\text{V}}{V_{A,p}}$$
$$0.01 = 0.0052 + \frac{0.026\,\text{V}}{V_{A,p}}$$
$$\frac{0.026\,\text{V}}{V_{A,p}} = 0.0048 \implies V_{A,p} = \frac{0.026}{0.0048} = \frac{65}{12}\,\text{V} \approx \mathbf{5.42\,\text{V}}$$

#### 3. 완성 답 및 주의할 점

- **완성 답**:
$$\boxed{V_{A,p} = \frac{65}{12}\,\text{V} \approx 5.42\,\text{V}}$$
- ⚠️ **이득 한계 검산**: PNP Early 전압이 무한대($V_{A,p} \to \infty$)여도 NPN 자체의 고유 한계 $|A_v|_{limit} = \frac{V_{A,n}}{V_T} = \frac{5}{0.026} \approx 192.3$을 넘을 수 없습니다. 목표 100은 달성 가능 영역 내에 있습니다.

---

