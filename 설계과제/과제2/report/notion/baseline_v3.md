<table_of_contents color="gray"/>
<empty-block/>
# 설계 조건
주어진 조건을 이용하여 다음 cascode 증폭기를 설계하고, 주파수 응답 특성을 검증하시오.
- $`L = 0.18\ \mu\text{m}`$
- $`\mu_n C_{ox} = 100\ \mu\text{A/V}^2`$, $`\mu_p C_{ox} = 50\ \mu\text{A/V}^2`$
- $`\lambda_n = 0.1\ \text{V}^{-1}`$, $`\lambda_p = 0.2\ \text{V}^{-1}`$
- $`V_{THN} = 0.4\ \text{V}`$, $`V_{THP} = -0.4\ \text{V}`$
(주어지지 않은 parameter는 사양을 만족하도록 설계자가 결정함)
![]()
<table header-row="true">
<tr>
<td>Capacitance Parameters</td>
<td></td>
</tr>
<tr>
<td>$`C_{ox}`$</td>
<td>$`12\ \text{fF}/\mu\text{m}^2`$</td>
</tr>
<tr>
<td>$`C_{GS}`$</td>
<td>$`(2/3)WLC_{ox} + (0.3\ \text{fF}/\mu\text{m})\times W`$</td>
</tr>
<tr>
<td>$`C_{GD}`$</td>
<td>$`(0.3\ \text{fF}/\mu\text{m})\times W`$</td>
</tr>
<tr>
<td>$`C_{DB}`$</td>
<td>$`(0.4\ \text{fF}/\mu\text{m})\times W`$</td>
</tr>
<tr>
<td>$`C_{SB}`$</td>
<td>$`(0.4\ \text{fF}/\mu\text{m})\times W`$</td>
</tr>
</table>
<empty-block/>
<empty-block/>
# Design Problem
## (a) 이득·전력·극점 사양을 만족하는 설계
**(a) **$`V_{DD} = 1\ \text{V}`$**, **$`R_S = 500\ \Omega`$**, 최대 소모전력 **$`\le 0.5\ \text{mW}`$**, **$`I_{D2} = |I_{D3}|`$**인 조건에서, 저주파 전압 이득이 10이고, 모든 pole 주파수들이 1 GHz 이상이 되도록 회로를 설계하시오.**
$`M_1`$은 입력 common-source 단, $`M_2`$는 게이트가 $`V_{b1}`$에 고정된 common-gate cascode, $`M_3`$은 게이트가 $`V_{b2}`$에 고정된 PMOS 전류원으로 노드 $`Y`$에 전류를 넣는다. $`R_L`$은 $`V_{DD}`$와 $`V_{out}`$ 사이 부하, $`R_S`$는 신호원 저항이다. 계산에는 $`I_D = \tfrac12\mu C_{ox}\tfrac WL V_{ov}^2(1+\lambda V_{DS})`$, $`g_m = 2I_D/V_{ov}`$, $`r_o = (1+\lambda V_{DS})/(\lambda I_D)`$를 사용한다. body effect 계수가 주어지지 않았으므로 body effect는 무시한다 (SPICE 모델도 GAMMA = 0).
**① 전류 배분과 전력**
노드 $`Y`$에서 KCL을 쓰면 $`M_1`$의 전류는 $`M_2`$와 $`M_3`$이 나눠 공급한다. 조건 $`I_{D2} = |I_{D3}|`$에서 다음이 성립한다.
$$
I_{D1} = I_{D2} + |I_{D3}| = 2 I_{D2}, \qquad P = V_{DD}\,(I_{D2} + |I_{D3}|) = V_{DD}\, I_{D1}
$$
$`R_L`$을 흐르는 전류도 $`I_{D2}`$이므로 전원에서 나가는 전류는 $`I_{D1}`$ 하나다. $`I_{D1} = 400\ \mu\text{A}`$ ($`I_{D2} = |I_{D3}| = 200\ \mu\text{A}`$)로 정했고, 이때 $`P = 1\ \text{V} \times 400\ \mu\text{A} = 0.4\ \text{mW} \le 0.5\ \text{mW}`$ (만족, 상한의 80 %)다.
**② 이득식 유도 (**$`G_m`$**, **$`R_{out}`$**)**
저주파 이득은 $`A_0 = -G_m R_{out}`$으로 쓴다. $`G_m`$은 출력을 교류 접지($`v_{out} = 0`$)했을 때 출력에서 $`M_2`$로 흘러 들어가는 전류 $`i_{out}`$와 $`v_{in}`$의 비다. 저주파에서는 게이트 전류가 없으므로 $`v_x = v_{in}`$이다. $`r_{o1} \parallel r_{o3}`$를 $`r_{13}`$이라 하면, $`v_{out} = 0`$일 때 $`M_2`$의 드레인 전류는 $`i_{out} = -v_y(g_{m2} + g_{ds2})`$이고, 노드 $`Y`$에서 나가는 전류의 합은 $`g_{m1} v_{in} + v_y / r_{13} - i_{out} = 0`$이다. 두 식에서 $`v_y`$를 소거한다.
$$
v_y = -\frac{g_{m1} v_{in}}{1/r_{13} + g_{m2} + g_{ds2}}, \qquad G_m = \frac{i_{out}}{v_{in}} = g_{m1}\,\frac{r_{13}}{r_{13} + R_{in2,sc}}, \qquad R_{in2,sc} = \frac{1}{g_{m2} + g_{ds2}} = \frac{r_{o2}}{1 + g_{m2} r_{o2}}
$$
$`R_{in2,sc}`$는 출력을 단락했을 때 $`Y`$에서 $`M_2`$ 소스로 들여다본 저항이다. $`M_1`$의 소신호 전류 중 $`r_{13}`$으로 새는 몫이 있어 $`G_m < g_{m1}`$이 된다. 출력 저항은 $`R_L`$과, 소스가 $`r_{13}`$으로 degeneration된 $`M_2`$ 드레인 쪽 저항의 병렬이다.
$$
R_{cas} = r_{o2} + r_{13} + g_{m2} r_{o2} r_{13}, \qquad R_{out} = R_L \parallel R_{cas}, \qquad A_0 = -G_m R_{out}
$$
$`R_{cas}`$($`\approx 1.93\ \text{M}\Omega`$)가 $`R_L`$($`\approx 1.93\ \text{k}\Omega`$)의 약 1000배이므로 $`R_{out} \approx R_L`$, $`G_m \approx g_{m1}`$로 근사하면 다음과 같다.
$$
|A_0| \approx g_{m1} R_L = \frac{2 I_{D1}}{V_{ov1}} R_L = \frac{4 I_{D2} R_L}{V_{ov1}} \;\Rightarrow\; I_{D2} R_L \approx \frac{|A_0|\, V_{ov1}}{4}
$$
즉 $`|A_0| = 10`$이면 출력 DC 강하 $`I_{D2} R_L`$은 전류와 무관하게 $`V_{ov1}`$로 정해진다 ($`V_{ov1} = 0.15\ \text{V}`$이면 약 0.375 V).
**③ 전압 headroom 분배**
세 MOSFET이 모두 saturation이려면 $`V_Y \ge V_{ov1}`$, $`V_{out} - V_Y \ge V_{ov2}`$, $`V_{DD} - V_Y \ge |V_{ov3}|`$이어야 한다. ②에서 $`V_{out} = V_{DD} - I_{D2}R_L \approx 1 - 2.5\,V_{ov1}`$이므로 $`1 - 2.5\,V_{ov1} \ge V_{ov1} + V_{ov2}`$, 즉 $`3.5\,V_{ov1} + V_{ov2} \le 1\ \text{V}`$를 만족해야 한다. $`V_{ov1} = V_{ov2} = 0.15\ \text{V}`$이면 $`0.675 \le 1`$로 여유가 있고, 남는 전압은 세 MOSFET의 포화 여유로 나눴다 ($`M_1`$ 0.15 V, $`M_2`$ 0.164 V, $`M_3`$ 0.40 V).
<table header-row="true">
<tr>
<td>노드</td>
<td>설계값</td>
<td>근거</td>
</tr>
<tr>
<td>$`V_X`$ ($`= V_{in,DC}`$)</td>
<td>0.55 V</td>
<td>$`V_{TH} + V_{ov1} = 0.4 + 0.15`$</td>
</tr>
<tr>
<td>$`V_Y`$</td>
<td>0.30 V</td>
<td>$`V_{DS1} = 0.30 \ge V_{ov1} = 0.15`$, $`V_{SD3} = 0.70 \ge \lvert V_{ov3}\rvert = 0.30`$</td>
</tr>
<tr>
<td>$`V_{out}`$</td>
<td>0.6143 V</td>
<td>$`V_{DD} - I_{D2}R_L = 1\ \text{V} - 200\ \mu\text{A} \times 1928.53\ \Omega`$, $`V_{DS2} = 0.3143 \ge V_{ov2} = 0.15`$</td>
</tr>
</table>
$`|V_{ov3}| = 0.30\ \text{V}`$는 $`M_3`$의 W를 줄여 노드 $`Y`$의 커패시턴스를 작게 하려고 $`V_{SD3} = 0.70\ \text{V}`$ 안에서 크게 잡은 값이다.
**④ 전류와 **$`V_{ov}`$**를 정한 근거 (극점 사양)**
$`V_{ov}`$를 고정하면 W는 전류에 비례하고, 노드 저항은 다음과 같이 움직인다.
- $`f_X = 1/(2\pi R_S C_X)`$: $`R_S`$는 고정이고 $`C_X \propto W_1 \propto I_{D1}/V_{ov1}^2`$이므로 $`f_X \propto 1/I_{D1}`$이다. 세 극점 중 가장 낮고, 전류를 줄이거나 $`V_{ov1}`$을 키우면 올라간다.
- $`f_Y \approx g_{m2}/(2\pi C_Y)`$, $`f_{out} = 1/(2\pi R_L C_{out})`$: $`g_{m2}`$와 $`1/R_L`$이 전류에 비례하고 C도 전류에 비례하므로 전류와 거의 무관하다.
따라서 극점 사양은 $`M_1`$의 크기로 결정된다. $`V_{ov1}`$을 크게 하면 W1이 줄어 $`f_X`$가 오르지만 ③의 headroom이 줄어든다. $`V_{ov1} = 0.15\ \text{V}`$와 $`I_{D1} = 400\ \mu\text{A}`$에서 (c)의 최저 극점이 1.94 GHz가 된다. Miller 근사는 결합된 두 극점을 실제보다 가깝게 보므로 실제 최저 극점은 이보다 낮아질 수 있어, Miller 극점이 모두 1.5 GHz 이상이 되는 것을 설계 목표로 잡았다. 전류를 더 줄여도 사양은 만족하고 $`f_X`$는 더 오른다. 이 회로에서 전류는 사양으로 정해지지 않는 자유 변수이므로, 전력(상한의 80 %)과 극점(목표 1.5 GHz 대비 1.94 GHz) 양쪽에 여유가 남는 400 µA로 정했다.
**⑤ **$`R_L`$** 결정과 소신호 파라미터**
$`V_{out}`$이 $`R_L`$에 따라 바뀌어 $`r_{o2}`$도 바뀌므로, ②의 정확식으로 $`|A_0| = 10.000`$이 되도록 $`R_L`$을 반복 계산해 $`R_L = 1928.53\ \Omega`$을 얻었다.
<table header-row="true">
<tr>
<td>소신호 파라미터</td>
<td>식</td>
<td>값</td>
</tr>
<tr>
<td>$`g_{m1}`$</td>
<td>$`2(400\ \mu\text{A})/0.15\ \text{V}`$</td>
<td>5.333 mS</td>
</tr>
<tr>
<td>$`g_{m2}`$</td>
<td>$`2(200\ \mu\text{A})/0.15\ \text{V}`$</td>
<td>2.667 mS</td>
</tr>
<tr>
<td>$`g_{m3}`$</td>
<td>$`2(200\ \mu\text{A})/0.30\ \text{V}`$</td>
<td>1.333 mS</td>
</tr>
<tr>
<td>$`r_{o1}`$</td>
<td>$`(1+0.1 \times 0.30)/(0.1 \times 400\ \mu\text{A})`$</td>
<td>25.75 kΩ</td>
</tr>
<tr>
<td>$`r_{o2}`$</td>
<td>$`(1+0.1 \times 0.3143)/(0.1 \times 200\ \mu\text{A})`$</td>
<td>51.57 kΩ</td>
</tr>
<tr>
<td>$`r_{o3}`$</td>
<td>$`(1+0.2 \times 0.70)/(0.2 \times 200\ \mu\text{A})`$</td>
<td>28.50 kΩ</td>
</tr>
<tr>
<td>$`r_{13} = r_{o1} \parallel r_{o3}`$</td>
<td></td>
<td>13.53 kΩ</td>
</tr>
<tr>
<td>$`R_{in2,sc}`$</td>
<td>$`r_{o2}/(1+g_{m2} r_{o2})`$</td>
<td>372.3 Ω</td>
</tr>
<tr>
<td>$`G_m/g_{m1}`$</td>
<td>$`r_{13}/(r_{13} + R_{in2,sc})`$</td>
<td>0.9732</td>
</tr>
<tr>
<td>$`G_m`$</td>
<td></td>
<td>5.1905 mS</td>
</tr>
<tr>
<td>$`R_{cas}`$</td>
<td>$`r_{o2} + r_{13} + g_{m2} r_{o2} r_{13}`$</td>
<td>1.925 MΩ</td>
</tr>
<tr>
<td>$`R_{out}`$</td>
<td>$`R_L \parallel R_{cas}`$</td>
<td>1926.60 Ω</td>
</tr>
<tr>
<td>$`\lvert A_0\rvert`$ (설계값)</td>
<td>$`G_m R_{out}`$</td>
<td>**10.000**</td>
</tr>
</table>
근사식 $`g_{m1}R_L`$로는 10.29가 나오므로, $`G_m/g_{m1} = 0.9732`$를 넣은 정확식으로 $`R_L`$을 정했다. 같은 회로를 $`X`$, $`Y`$, $`V_{out}`$ 세 노드의 KCL 연립방정식으로 직접 풀어도 $`A_0 = -10.000`$이 나와 위 식과 일치한다.
<empty-block/>
## (b) DC 바이어스와 W/L 설계
**(b) 설계한 증폭기에서 모든 MOSFET이 saturation 영역에서 동작하기 위한 DC 바이어스 전압들과 각 MOSFET의 W/L들을 설계하시오.**
$`I_D`$ 식을 $`W`$에 대해 풀고, (a)에서 정한 $`I_D`$, $`V_{ov}`$, $`V_{DS}`$를 대입한다. W는 0.01 µm 단위로 반올림했다.
$$
\frac WL = \frac{2 I_D}{\mu C_{ox} V_{ov}^2 (1+\lambda \lvert V_{DS}\rvert)}, \qquad L = 0.18\ \mu\text{m}
$$
<table header-row="true">
<tr>
<td>MOSFET</td>
<td>식 (숫자 대입)</td>
<td>W/L</td>
<td>W</td>
</tr>
<tr>
<td>$`M_1`$</td>
<td>$`\dfrac{2(400\ \mu\text{A})}{100\ \mu\text{A/V}^2 \cdot 0.15^2 (1+0.1 \times 0.30)}`$</td>
<td>345.20</td>
<td>**62.14 µm**</td>
</tr>
<tr>
<td>$`M_2`$</td>
<td>$`\dfrac{2(200\ \mu\text{A})}{100\ \mu\text{A/V}^2 \cdot 0.15^2 (1+0.1 \times 0.3143)}`$</td>
<td>172.36</td>
<td>**31.02 µm**</td>
</tr>
<tr>
<td>$`M_3`$</td>
<td>$`\dfrac{2(200\ \mu\text{A})}{50\ \mu\text{A/V}^2 \cdot 0.30^2 (1+0.2 \times 0.70)}`$</td>
<td>77.97</td>
<td>**14.04 µm**</td>
</tr>
</table>
바이어스 전압은 노드 전압에 $`V_{GS} = V_{TH} + V_{ov}`$를 더해 정한다.
<table header-row="true">
<tr>
<td>바이어스</td>
<td>식</td>
<td>값</td>
</tr>
<tr>
<td>$`V_{in,DC}`$ ($`V_X`$)</td>
<td>$`V_{TH} + V_{ov1} = 0.4 + 0.15`$</td>
<td>**0.55 V**</td>
</tr>
<tr>
<td>$`V_{b1}`$</td>
<td>$`V_Y + V_{TH} + V_{ov2} = 0.30 + 0.4 + 0.15`$</td>
<td>**0.85 V**</td>
</tr>
<tr>
<td>$`V_{b2}`$</td>
<td>$`V_{DD} - \lvert V_{THP}\rvert - \lvert V_{ov3}\rvert = 1 - 0.4 - 0.30`$</td>
<td>**0.30 V**</td>
</tr>
<tr>
<td>$`R_L`$</td>
<td>(a) ⑤</td>
<td>**1928.53 Ω**</td>
</tr>
<tr>
<td>$`R_S`$</td>
<td>주어진 값</td>
<td>500 Ω</td>
</tr>
</table>
설계값 요약:
<table header-row="true">
<tr>
<td>MOSFET</td>
<td>$`I_D`$</td>
<td>$`\lvert V_{GS}\rvert`$</td>
<td>$`\lvert V_{DS}\rvert`$</td>
<td>W/L</td>
<td>W</td>
</tr>
<tr>
<td>$`M_1`$</td>
<td>400 µA</td>
<td>0.55 V</td>
<td>0.30 V</td>
<td>345.20</td>
<td>62.14 µm</td>
</tr>
<tr>
<td>$`M_2`$</td>
<td>200 µA</td>
<td>0.55 V</td>
<td>0.3143 V</td>
<td>172.36</td>
<td>31.02 µm</td>
</tr>
<tr>
<td>$`M_3`$</td>
<td>200 µA</td>
<td>0.70 V</td>
<td>0.70 V</td>
<td>77.97</td>
<td>14.04 µm</td>
</tr>
</table>
Saturation 조건 $`\lvert V_{DS}\rvert \ge \lvert V_{GS}\rvert - \lvert V_{TH}\rvert`$ (모두 $`\lvert V_{GS}\rvert > 0.4\ \text{V}`$):
- $`M_1`$: $`0.30 \ge 0.55 - 0.4 = 0.15`$ (만족, 여유 0.15 V)
- $`M_2`$: $`0.3143 \ge 0.55 - 0.4 = 0.15`$ (만족, 여유 0.164 V)
- $`M_3`$: $`0.70 \ge 0.70 - 0.4 = 0.30`$ (만족, 여유 0.40 V)
<empty-block/>
## (c) Miller 근사로 구한 pole 주파수
**(c) Miller's approximation을 적용하여 모든 pole 주파수를 구하시오.**
신호 경로의 노드는 $`X`$, $`Y`$, $`V_{out}`$ 세 개다. $`V_{b1}`$, $`V_{b2}`$, $`V_{DD}`$는 교류 접지이므로 $`M_3`$의 $`C_{GS3}`$, $`C_{SB3}`$와 $`M_1`$의 $`C_{SB1}`$은 양 끝이 모두 접지라 극점에 영향이 없다. 노드 $`X`$와 $`Y`$ 사이를 잇는 $`C_{GD1}`$에 Miller 근사를 적용한다.
**① **$`X`$**–**$`Y`$** 이득 **$`A_{XY}`$
$`Y`$에서 본 저항은 $`r_{o1}`$, $`r_{o3}`$, 그리고 $`M_2`$ 소스로 들여다본 저항(부하 $`R_L`$ 포함)의 병렬이다.
$$
R_{in2} = \frac{R_L + r_{o2}}{1 + g_{m2} r_{o2}} = 386.21\ \Omega, \qquad R_Y = r_{o1} \parallel r_{o3} \parallel R_{in2} = 375.49\ \Omega
$$
$$
A_{XY} = -g_{m1} R_Y = -5.333\ \text{mS} \times 375.49\ \Omega = -2.003
$$
강의의 근사 $`R_Y \approx 1/g_{m2}`$를 쓰면 $`A_{XY} \approx -g_{m1}/g_{m2} = -2.00`$으로 거의 같다.
**② 각 소자의 커패시턴스 (과제 표 값, W는 µm, 단위 fF)**
<table header-row="true">
<tr>
<td>MOSFET</td>
<td>$`C_{GS} = \tfrac23 W L C_{ox} + 0.3W`$</td>
<td>$`C_{GD} = 0.3W`$</td>
<td>$`C_{DB} = 0.4W`$</td>
<td>$`C_{SB} = 0.4W`$</td>
</tr>
<tr>
<td>$`M_1`$ ($`W = 62.14`$)</td>
<td>108.12</td>
<td>18.64</td>
<td>24.86</td>
<td>24.86</td>
</tr>
<tr>
<td>$`M_2`$ ($`W = 31.02`$)</td>
<td>53.97</td>
<td>9.31</td>
<td>12.41</td>
<td>12.41</td>
</tr>
<tr>
<td>$`M_3`$ ($`W = 14.04`$)</td>
<td>24.43</td>
<td>4.21</td>
<td>5.62</td>
<td>5.62</td>
</tr>
</table>
**③ 노드별 커패시턴스와 저항**
$$
C_X = C_{GS1} + (1 - A_{XY})\,C_{GD1} = 108.12 + 3.003 \times 18.64 = 164.10\ \text{fF}, \qquad R_X = R_S = 500\ \Omega
$$
$$
C_Y = C_{DB1} + \left(1 - \frac{1}{A_{XY}}\right) C_{GD1} + C_{GS2} + C_{SB2} + C_{DB3} + C_{GD3} = 24.86 + 1.499 \times 18.64 + 53.97 + 12.41 + 5.62 + 4.21 = 129.02\ \text{fF}
$$
$$
C_{out} = C_{DB2} + C_{GD2} = 12.41 + 9.31 = 21.71\ \text{fF}, \qquad R_{out} = R_L \parallel R_{cas} = 1926.60\ \Omega
$$
$`R_Y = 375.49\ \Omega`$이다. $`M_2`$의 게이트가 교류 접지이므로 출력 노드는 다른 노드와 커패시턴스로 연결되지 않는다.
**④ Pole 주파수**
<table header-row="true">
<tr>
<td>노드</td>
<td>$`R`$</td>
<td>$`C`$</td>
<td>$`f_p = 1/(2\pi R C)`$</td>
<td>1 GHz 이상</td>
</tr>
<tr>
<td>$`X`$</td>
<td>500.00 Ω</td>
<td>164.10 fF</td>
<td>**1.940 GHz**</td>
<td>만족</td>
</tr>
<tr>
<td>$`Y`$</td>
<td>375.49 Ω</td>
<td>129.02 fF</td>
<td>**3.285 GHz**</td>
<td>만족</td>
</tr>
<tr>
<td>$`V_{out}`$</td>
<td>1926.60 Ω</td>
<td>21.71 fF</td>
<td>**3.804 GHz**</td>
<td>만족</td>
</tr>
</table>
세 pole이 모두 1 GHz 이상이고, Miller 근사에서 지배 pole은 입력 노드 $`X`$ ($`R_S`$와 Miller 증배된 $`C_{GD1}`$)다. $`C_{GD1}`$은 $`X`$에서 $`Y`$로의 앞먹임 경로도 만들어 우반면 영점 $`g_{m1}/(2\pi C_{GD1}) = 45.5\ \text{GHz}`$가 생긴다. (d)에서 영점을 포함한 응답도 비교한다.
<empty-block/>
## (d) 전달 함수와 Bode magnitude plot
**(d) 전달 함수 H(s)를 구하고, Bode magnitude plot을 그리시오.**
(a)의 저주파 이득과 (c)의 세 pole로 전달 함수를 쓴다 ($`\omega_p = 2\pi f_p`$).
$$
H(s) = \frac{A_0}{\left(1 + \dfrac{s}{\omega_X}\right)\left(1 + \dfrac{s}{\omega_Y}\right)\left(1 + \dfrac{s}{\omega_{out}}\right)}, \qquad A_0 = -10
$$
$$
\omega_X = 1.219 \times 10^{10}\ \text{rad/s}, \quad \omega_Y = 2.064 \times 10^{10}\ \text{rad/s}, \quad \omega_{out} = 2.390 \times 10^{10}\ \text{rad/s}
$$
$$
H(s) = \frac{-10}{\left(1 + \dfrac{s}{1.219 \times 10^{10}}\right)\left(1 + \dfrac{s}{2.064 \times 10^{10}}\right)\left(1 + \dfrac{s}{2.390 \times 10^{10}}\right)}
$$
같은 세 Miller pole에 우반면 영점을 포함하면 분자가 $`-10\,(1 - s/\omega_z)`$, $`\omega_z = g_{m1}/C_{GD1} = 2.861 \times 10^{11}\ \text{rad/s}`$ (45.5 GHz)가 된다. 두 전달 함수의 크기 응답을 같은 주파수 범위에 그렸다.
![설계 Bode magnitude plot. 세 Miller pole의 응답과 우반면 영점을 포함한 응답을 비교한다.]()
저주파 이득은 20 dB다. 세 pole만 고려한 점근선은 1.94, 3.29, 3.80 GHz에서 차례로 −20, −40, −60 dB/dec로 바뀐다. −3 dB 대역폭은 세 pole만 포함할 때 1.374 GHz, 영점을 포함할 때 1.375 GHz다. 대역폭 부근에서는 차이가 약 0.004 dB지만, 100 GHz에서는 영점을 포함한 응답이 약 7.65 dB 높다.
<empty-block/>
<empty-block/>
# Spice Problem
**SPICE를 사용하여 simulation을 확인하고 설명하시오.**
과제 제공 모델(MOSFET_model.lib의 CMOSN, CMOSP)로 LTspice에서 DC(.op)와 AC 해석을 했다. NMOS body는 GND, PMOS body는 $`V_{DD}`$에 연결했다. 접합 커패시턴스가 들어가도록 모든 MOSFET에 $`AD = AS = 0.49\ \mu\text{m} \times W`$, $`PD = PS = W`$를 지정했다. 이 값이면 영 바이어스 접합 커패시턴스가 NMOS에서 $`C_J \cdot 0.49 + C_{JSW} = 0.57 \times 0.49 + 0.12 = 0.40\ \text{fF}/\mu\text{m} \times W`$로 과제 표의 $`C_{DB}, C_{SB}`$와 같아진다.
<empty-block/>
## (a) 회로도와 DC 동작점
**(a) 설계한 회로의 schematic을 보이고, 각 MOFET과 노드의 DC 바이어스 전압, 전류를 표시하시오. (DC simulation)**
회로도와 DC 동작점 (.op):
![LTspice 회로도 (.op 라벨, 학번·이름 표기)]()
바이어스는 Design Problem (b)의 손계산 값($`V_{in,DC} = 0.55`$, $`V_{b1} = 0.85`$, $`V_{b2} = 0.30\ \text{V}`$, $`R_L = 1928.53\ \Omega`$)을 조정 없이 그대로 넣었다.
<table header-row="true">
<tr>
<td>노드</td>
<td>설계값 \[V\]</td>
<td>SPICE \[V\]</td>
</tr>
<tr>
<td>$`V_{DD}`$</td>
<td>1.0000</td>
<td>1.0000</td>
</tr>
<tr>
<td>$`V_{in}`$, $`V_X`$</td>
<td>0.5500</td>
<td>0.5500</td>
</tr>
<tr>
<td>$`V_Y`$</td>
<td>0.3000</td>
<td>0.2999</td>
</tr>
<tr>
<td>$`V_{out}`$</td>
<td>0.6143</td>
<td>0.6005</td>
</tr>
<tr>
<td>$`V_{b1}`$ / $`V_{b2}`$</td>
<td>0.8500 / 0.3000</td>
<td>0.8500 / 0.3000</td>
</tr>
</table>
각 MOSFET의 드레인 전류와 전원 전류는 다음과 같다.
<table header-row="true">
<tr>
<td>전류</td>
<td>설계값</td>
<td>SPICE</td>
</tr>
<tr>
<td>$`I_{D1}`$</td>
<td>400.00 µA</td>
<td>414.40 µA</td>
</tr>
<tr>
<td>$`I_{D2}`$</td>
<td>200.00 µA</td>
<td>207.14 µA</td>
</tr>
<tr>
<td>$`\lvert I_{D3}\rvert`$</td>
<td>200.00 µA</td>
<td>207.26 µA</td>
</tr>
<tr>
<td>$`I_{VDD}`$</td>
<td>400.00 µA</td>
<td>414.40 µA</td>
</tr>
</table>
회로도의 $`M_3`$ 전류가 −207.26 µA로 표시된 것은 LTspice가 드레인으로 들어가는 전류를 +로 표시하기 때문이다 (PMOS 전류는 드레인에서 나온다). 회로도 아래쪽의 550.00001 mV는 노드 $`X`$의 전압이고, 게이트 전류가 없으므로 $`V_{in}`$과 같다.
전원 전류로 계산한 전력은 $`P = 1\ \text{V} \times 414.40\ \mu\text{A} = 0.4144\ \text{mW} \le 0.5\ \text{mW}`$ (만족)다. 손계산에서는 $`I_{D2} = \lvert I_{D3}\rvert = 200\ \mu\text{A}`$로 설계했다. LTspice에서는 각각 207.13623 µA와 207.26450 µA였으며, 반올림 전 값의 차이는 0.128 µA ($`I_{D2}`$ 대비 0.0619 %)다. SPICE 결과에는 이만큼의 전류 차이가 남았다.
모델의 $`C_{ox} = \varepsilon_{ox}/t_{ox} = 3.9 \times 8.854\ \text{pF/m} / 4\ \text{nm} = 8.63\ \text{fF}/\mu\text{m}^2`$다. 이에 따라 $`\mu_n C_{ox} = 103.6\ \mu\text{A/V}^2`$, $`\mu_p C_{ox} = 51.8\ \mu\text{A/V}^2`$로, 둘 다 과제 값보다 약 3.6 % 크다. 세 드레인 전류도 각각 약 3.6 % 증가했다. $`V_Y`$는 약 0.092 mV 낮아져 $`M_2`$의 overdrive가 약 0.092 mV 늘었다. 전압 변화는 주로 $`V_{out}`$에서 나타났으며, $`1\ \text{V} - 207.14\ \mu\text{A} \times 1928.53\ \Omega = 0.6005\ \text{V}`$로 설계값보다 약 13.8 mV 낮다.
<empty-block/>
## (b) Saturation 동작 검증
**(b) 모든 MOSFET이 saturation 영역에서 동작하는지를 검증하시오.**
조건은 $`\lvert V_{GS}\rvert > \lvert V_{TH}\rvert`$이고 $`\lvert V_{DS}\rvert \ge \lvert V_{GS}\rvert - \lvert V_{TH}\rvert`$이다 ($`\lvert V_{TH}\rvert = 0.4\ \text{V}`$, GAMMA = 0이라 body effect 없음). 아래 값은 SPICE 동작점이다.
<table header-row="true">
<tr>
<td>MOSFET</td>
<td>$`I_D`$ \[µA\]</td>
<td>$`\lvert V_{GS}\rvert`$ \[V\]</td>
<td>$`\lvert V_{GS}\rvert - \lvert V_{TH}\rvert`$ \[V\]</td>
<td>$`\lvert V_{DS}\rvert`$ \[V\]</td>
<td>여유 \[V\]</td>
<td>영역</td>
</tr>
<tr>
<td>$`M_1`$</td>
<td>414.40</td>
<td>0.5500</td>
<td>0.1500</td>
<td>0.2999</td>
<td>0.1499</td>
<td>saturation</td>
</tr>
<tr>
<td>$`M_2`$</td>
<td>207.14</td>
<td>0.5501</td>
<td>0.1501</td>
<td>0.3006</td>
<td>0.1505</td>
<td>saturation</td>
</tr>
<tr>
<td>$`M_3`$</td>
<td>207.26</td>
<td>0.7000</td>
<td>0.3000</td>
<td>0.7001</td>
<td>0.4001</td>
<td>saturation</td>
</tr>
</table>
- $`M_1`$: $`0.2999 \ge 0.1500`$ (만족)
- $`M_2`$: $`0.3006 \ge 0.1501`$ (만족)
- $`M_3`$: $`0.7001 \ge 0.3000`$ (만족)
세 MOSFET이 모두 saturation에서 동작한다. 여유가 가장 작은 것은 $`M_1`$(0.1499 V)이다. $`M_2`$의 여유는 설계 0.1643 V에서 SPICE 0.1505 V로 줄었다.
<empty-block/>
## (c) 주파수 응답과 전압 이득 비교
**(c) 주파수 응답(magnitude & phase response)을 plot 하시오. (AC simulation) 그리고, 전압 이득을 설계값과 비교하시오.**
입력에 AC 1 V를 넣고 1 MHz부터 100 GHz까지 100점/decade로 해석해 V(out)/V(in)의 크기와 위상을 구했다.
![LTspice AC 파형. 실선은 이득(왼쪽 축), 점선은 위상(오른쪽 축)이다.]()
![LTspice 1 MHz 커서. 전압 이득 20.306626 dB(10.359 V/V), 위상 179.95222°.]()
![LTspice SPICE Output Log의 .meas 결과. -3 dB 대역폭은 1.686 GHz다.]()
<table header-row="true">
<tr>
<td>방법</td>
<td>전압 이득의 크기</td>
<td>설계값 대비 오차</td>
</tr>
<tr>
<td>설계값</td>
<td>10.000 (20.00 dB)</td>
<td>기준</td>
</tr>
<tr>
<td>LTspice AC (1 MHz)</td>
<td>10.359 (20.31 dB)</td>
<td>+3.59 %</td>
</tr>
<tr>
<td>LTspice 동작점의 gm, gds로 계산</td>
<td>10.359</td>
<td>+3.59 %</td>
</tr>
</table>
이득은 설계값보다 3.59 % 크다. 이 차이는 모델의 μCox 증가(+3.6 %)에 따른 gm 증가와 일치한다.
−3 dB 대역폭은 세 Miller pole 근사에서 1.374 GHz(우반면 영점 포함 시 1.375 GHz), LTspice에서 1.686 GHz였다.
<empty-block/>
## (d) 극점 주파수 비교
**(d) Pole 주파수들을 각각 구하고, 설계값과 비교하시오.**
각 MOSFET의 DC 바이어스에서 한 단자에 AC 1 V를 인가하고 단자 전류를 1 MHz에서 측정했다. 이를 회로의 X, Y, Vout 노드에 합산해 어드미턴스 행렬 $`Y(j\omega)`$를 구했다. $`G=\mathrm{Re}(Y)`$, $`C=\mathrm{Im}(Y)/(2\pi f)`$다.
![극점 계산에 사용한 LTspice SPICE Output Log. 모든 어드미턴스 항목은 1 MHz에서 측정했다.]()
<table header-row="true">
<tr>
<td>G (mS)</td>
<td>X</td>
<td>Y</td>
<td>Vout</td>
</tr>
<tr>
<td>X</td>
<td>2.00000</td>
<td>0</td>
<td>0</td>
</tr>
<tr>
<td>Y</td>
<td>5.52534</td>
<td>2.85682</td>
<td>-0.02011</td>
</tr>
<tr>
<td>Vout</td>
<td>0</td>
<td>-2.78023</td>
<td>0.53864</td>
</tr>
</table>
<empty-block/>
<table header-row="true">
<tr>
<td>C (fF)</td>
<td>X</td>
<td>Y</td>
<td>Vout</td>
</tr>
<tr>
<td>X</td>
<td>62.063</td>
<td>-24.856</td>
<td>0</td>
</tr>
<tr>
<td>Y</td>
<td>-24.856</td>
<td>81.428</td>
<td>0</td>
</tr>
<tr>
<td>Vout</td>
<td>0</td>
<td>0</td>
<td>22.152</td>
</tr>
</table>
입력을 0으로 둔 소신호 KCL은 $`(G+sC)\mathbf{v}=0`$이다. $`\det(G+sC)=0`$의 근을 구한 뒤 각 근의 절댓값을 $`2\pi`$로 나눠 극점 주파수로 환산했다.
<table header-row="true">
<tr>
<td>극점 순서</td>
<td>Miller 설계값 (GHz)</td>
<td>과제 표 C 정확해 (GHz)</td>
<td>LTspice 계산값 (GHz)</td>
</tr>
<tr>
<td>1</td>
<td>1.940</td>
<td>1.590</td>
<td>2.065</td>
</tr>
<tr>
<td>2</td>
<td>3.285</td>
<td>3.786</td>
<td>3.926</td>
</tr>
<tr>
<td>3</td>
<td>3.804</td>
<td>5.959</td>
<td>15.012</td>
</tr>
</table>
주파수의 오름차순으로 비교했다. 최저 극점은 2.065 GHz이며, 세 극점 모두 1 GHz 이상이다. 1 MHz \~ 100 GHz에서 재구성한 응답과 LTspice의 차이는 0.001 dB, 0.001° 이하였다.
<empty-block/>
## (e) 노드 등가 커패시턴스 비교
**(e) 구한 pole 주파수들을 이용하여 각 노드의 등가 capacitance를 각각 계산하고, 설계값과 비교하시오.**
X, Y, Vout에 각각 1 fF씩 더한 뒤 극점을 다시 계산하고, 주파수 변화율의 절댓값을 비교했다.
<table header-row="true">
<tr>
<td>1 fF를 더한 노드</td>
<td>2.065 GHz</td>
<td>3.926 GHz</td>
<td>15.012 GHz</td>
</tr>
<tr>
<td>X</td>
<td>0.424 %</td>
<td>0.078 %</td>
<td>1.308 %</td>
</tr>
<tr>
<td>Y</td>
<td>0.321 %</td>
<td>0.005 %</td>
<td>1.058 %</td>
</tr>
<tr>
<td>Vout</td>
<td>0.297 %</td>
<td>4.011 %</td>
<td>0.024 %</td>
</tr>
</table>
Vout은 3.926 GHz에서, X와 Y는 둘 다 15.012 GHz에서 변화율이 가장 컸다. 세 노드에 서로 다른 극점을 하나씩 배정하면서 선택된 변화율의 합을 최대화하면, X에는 15.012 GHz, Y에는 2.065 GHz, Vout에는 3.926 GHz가 배정된다.
각 노드의 저항 $`R`$은 $`G`$의 역행렬 대각 성분이다. 배정한 극점 $`f_p`$로 $`C_{eq}=1/(2\pi f_p R)`$을 구했다.
<table header-row="true">
<tr>
<td>노드</td>
<td>배정 fp (GHz)</td>
<td>R (Ω)</td>
<td>설계 C (fF)</td>
<td>등가 Ceq (fF)</td>
<td>설계 대비</td>
</tr>
<tr>
<td>X</td>
<td>15.012</td>
<td>500.0</td>
<td>164.1</td>
<td>21.2</td>
<td>-87.1 %</td>
</tr>
<tr>
<td>Y</td>
<td>2.065</td>
<td>363.2</td>
<td>129.0</td>
<td>212.2</td>
<td>+64.5 %</td>
</tr>
<tr>
<td>Vout</td>
<td>3.926</td>
<td>1926.5</td>
<td>21.7</td>
<td>21.0</td>
<td>-3.1 %</td>
</tr>
</table>
예를 들어 X는 R = 500 Ω, fp = 15.012 GHz이므로 Ceq = 21.2 fF다. 설계 대비 변화율은 반올림 전 값으로 계산했다. Vout의 등가값은 설계값에 가깝다. X와 Y의 극점을 서로 바꾸는 차선 배정은 민감도 합이 5.493 %로, 현재 배정의 5.640 %와 0.147 %p 차이다. 이때 X와 Y의 등가값은 각각 154.17 fF와 29.19 fF로 바뀐다. 표의 등가 커패시턴스는 선택한 극점과 노드 저항에서 환산한 값이다. 따라서 X와 Y의 등가값을 비교할 때는 어떤 극점 배정을 사용했는지 함께 밝혀야 한다.