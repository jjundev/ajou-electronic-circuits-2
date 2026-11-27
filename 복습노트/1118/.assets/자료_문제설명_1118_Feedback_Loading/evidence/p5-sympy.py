#!/usr/bin/env python3
"""P12.33: intact-loop nodal solution and a direct loop return for Fig. 12.97."""
from sympy import Eq, factor, limit, oo, simplify, solve, symbols

R1, R2, RD, gm1, gm2 = symbols("R_1 R_2 R_D g_m1 g_m2", positive=True)
ii, it, vs, vo, vg, vt = symbols("I_in I_test v_s v_out v_g v_test")
divider_kcl = Eq((vg - vo) / R1 + vg / R2, 0)

# V_b, V_DD are small-signal grounds. M1 drain-to-source current
# is -gm1*vs, and the controlled drain current of M2 is gm2*vg.
input_kcl = Eq(gm1 * vs + gm2 * vg, ii)
output_kcl = Eq(vo / RD + (vo - vg) / R1 - gm1 * vs, it)
intact = solve([input_kcl, output_kcl, divider_kcl], (vs, vo, vg), dict=True)[0]

beta = R2 / (R1 + R2)
RL = 1 / (1 / RD + 1 / (R1 + R2))
T = gm2 * beta * RL
closed_gain = intact[vo].subs(it, 0) / ii
zin = intact[vs].subs(it, 0) / ii
zout = intact[vo].subs(ii, 0) / it

# Break only the M2 gate. The divider still loads the output, and
# with I_in = 0 and I_test = 0 the returned voltage is vg.
cut = solve(
    [input_kcl.subs({ii: 0, vg: vt}), output_kcl.subs(it, 0), divider_kcl],
    (vs, vo, vg),
    dict=True,
)[0]
signed_return = cut[vg] / vt
assert simplify(signed_return + T) == 0

scale, b = symbols("S beta", positive=True)
scaled_divider = {R1: (1 - b) * scale, R2: b * scale}
large_T = gm2 * b * RD

print("P12.33, Fig. 12.97: intact-loop KCL with a test current at the output")
for equation in (input_kcl, output_kcl, divider_kcl):
    print(f"  {equation}")
print(f"R_L = R_D || (R_1 + R_2) = {factor(RL)}; beta = {beta}")
print(f"Gate-cut signed return = {factor(signed_return)} = -g_m2*beta*R_L")
print("Take R_1 + R_2 -> infinity with beta fixed.")
for name, observed, expected, expected_large in (
    ("Vout/Iin (I_test=0)", closed_gain, RL / (1 + T), RD / (1 + large_T)),
    ("Zin (I_test=0)", zin, 1 / (gm1 * (1 + T)), 1 / (gm1 * (1 + large_T))),
    ("Zout (I_in=0)", zout, RL / (1 + T), RD / (1 + large_T)),
):
    assert simplify(observed - expected) == 0
    large_limit = factor(limit(observed.subs(scaled_divider), scale, oo))
    assert simplify(large_limit - expected_large) == 0
    print(f"{name} = {factor(observed)}; large-divider limit = {large_limit}")
print("PASS: signed return, three closed-loop quantities, and their limits agree.")
