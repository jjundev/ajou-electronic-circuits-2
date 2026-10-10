# 1. Design Problem (설계과정 필수)

**(a) 굵은 문단: 전체 전력소모 $\le 1\ \text{mW}$를 만족하도록 설계하시오.**

▶ 풀이 문단: 이득은 $g_{m1} r_{o6}$ 로 정해진다.

$$
A_v = g_m R_{out}, \qquad R_{out} = r_{o6} \parallel R_{cas}
$$

| MOSFET | $\lvert V_{DS}\rvert$ | W |
|---|---|---|
| $M_1$ | 0.15 V | $\dfrac{2(100\ \mu)}{100\ \mu \cdot 0.0736^2}$ |

![그림](figs/a.png)

- $M_1$: $0.15 \ge 0.0736$ ✔
