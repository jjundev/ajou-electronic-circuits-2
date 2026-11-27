#!/usr/bin/env python3
"""P12.04: direct loop returns from the four Fig. 12.80 circuits."""
from sympy import Eq, factor, simplify, solve, symbols

A1, K, R1, R2, RD, gm1, gm3 = symbols(
    "A_1 K R_1 R_2 R_D g_m1 g_m3", positive=True
)
vt, vr, vf, vd = symbols("v_test v_return v_div v_d")
beta = R2 / (R1 + R2)
h = gm1 * R2 / (1 + gm1 * R2)

# X = 0. The output cut is at op-amp output. In (d) this is the
# MOS gate, since Y is the source and the gate draws no current.
divider_kcl = Eq((vf - vt) / R1 + vf / R2, 0)
cases = {
    "a": ([divider_kcl, Eq(vr, -A1 * K * vf)], (vf, vr), A1 * K * beta),
    "b": (
        [divider_kcl, Eq(vd / RD + gm3 * vf, 0), Eq(vr, A1 * vd)],
        (vf, vd, vr),
        A1 * gm3 * RD * beta,
    ),
    "c": ([Eq(vd / RD + gm3 * vt, 0), Eq(vr, A1 * vd)], (vd, vr), A1 * gm3 * RD),
    "d": (
        [Eq(vf / R2, gm1 * (vt - vf)), Eq(vr, -A1 * vf)],
        (vf, vr),
        A1 * h,
    ),
}

print("P12.04, Fig. 12.80: X = 0, direct signed return v_return/v_test")
print("Loop gain T is defined by v_return/v_test = -T.")
for panel, (equations, unknowns, expected_t) in cases.items():
    solved = solve(equations, unknowns, dict=True)[0]
    signed_return = factor(solved[vr] / vt)
    assert simplify(signed_return + expected_t) == 0
    print(f"({panel})")
    for equation in equations:
        print(f"  {equation}")
    print(f"  signed return = {signed_return}; T = {-signed_return}")
print("PASS: all four symbolic loop returns agree.")
