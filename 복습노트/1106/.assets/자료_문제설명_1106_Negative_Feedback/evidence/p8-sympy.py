#!/usr/bin/env python3
"""P12.05: closed-loop nodal solution and loop-gain identity for Fig. 12.80."""
from sympy import Eq, factor, limit, oo, simplify, solve, symbols

A1, K, R1, R2, RD, gm1, gm3 = symbols(
    "A_1 K R_1 R_2 R_D g_m1 g_m3", positive=True
)
x, y, vf, vd, vg = symbols("X Y v_div v_d v_g")
beta = R2 / (R1 + R2)
h = gm1 * R2 / (1 + gm1 * R2)
divider_kcl = Eq((vf - y) / R1 + vf / R2, 0)

# Each entry gives the intact circuit, its unknown nodes, the directly
# propagated input gain, and the positive T in the denominator 1 + T.
cases = {
    "a": ([divider_kcl, Eq(y, A1 * (x - K * vf))], (vf, y), A1, A1 * K * beta),
    "b": (
        [divider_kcl, Eq(vd / RD + gm3 * vf, 0), Eq(y, A1 * (vd - x))],
        (vf, vd, y),
        -A1,
        A1 * gm3 * RD * beta,
    ),
    "c": (
        [Eq(vd / RD + gm3 * y, 0), Eq(y, A1 * (vd - x))],
        (vd, y),
        -A1,
        A1 * gm3 * RD,
    ),
    "d": (
        [Eq(y / R2, gm1 * (vg - y)), Eq(vg, A1 * (x - y))],
        (vg, y),
        A1 * h,
        A1 * h,
    ),
}

print("P12.05, Fig. 12.80: solve the intact loop by op-amp laws and KCL")
for panel, (equations, unknowns, forward_gain, loop_gain) in cases.items():
    solved = solve(equations, unknowns, dict=True)[0]
    closed_gain = factor(solved[y] / x)
    assert simplify(closed_gain - forward_gain / (1 + loop_gain)) == 0
    print(f"({panel})")
    for equation in equations:
        print(f"  {equation}")
    print(f"  forward gain = {forward_gain}; T = {loop_gain}")
    print(f"  closed-loop Y/X = {closed_gain}")
    print(f"  limit as A_1 -> infinity = {factor(limit(closed_gain, A1, oo))}")
print("PASS: all four intact-loop gains agree with forward gain/(1 + T).")
