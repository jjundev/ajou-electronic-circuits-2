import sympy as sp

# Problem 3 (P12.41): Common-gate stage with ideal current source load
# Repeat Example 12-26 (lambda = 0) taking loading of R1, R2 into account.
# Also check exact KCL and finite r_O1 sensitivity.

g_m1, R_1, R_2, r_O1 = sp.symbols('g_m1 R_1 R_2 r_O1', positive=True, finite=True)
v_in, v_out, v_g, i_in, v_x, i_x = sp.symbols('v_in v_out v_g i_in v_x i_x')
v_1, v_2, v_m, i_test, v_test = sp.symbols('v_1 v_2 v_m i_test v_test')

print("=== p3 (P12.41) SymPy Verification ===")

# Two-port feedback network loading (Fig 12.53(a))
eq_sense_m = sp.Eq((v_m - v_test) / R_1 + v_m / R_2, 0)
eq_sense_i = sp.Eq(i_test, (v_test - v_m) / R_1)
sol_sense = sp.solve([eq_sense_m, eq_sense_i], [v_m, i_test])
R_sense = sp.simplify(v_test / sol_sense[i_test])

eq_ret = sp.Eq(i_test, v_test / R_1 + v_test / R_2)
R_return = sp.simplify(v_test / sp.solve(eq_ret, i_test)[0])

# Open-loop circuit (ideal current source -> infinite load impedance in parallel with R_sense; lambda = 0)
eq_gate_ol = sp.Eq(v_g / R_return, 0)
eq_out_ol = sp.Eq(v_out / R_sense + g_m1 * (v_g - v_in), 0)
eq_iin_ol = sp.Eq(i_in, -g_m1 * (v_g - v_in))
sol_ol = sp.solve([eq_gate_ol, eq_out_ol, eq_iin_ol], [v_g, v_out, i_in])

A_v_open = sp.simplify(sol_ol[v_out] / v_in)
R_in_open = sp.simplify(v_in / sol_ol[i_in])

# Open-loop output impedance (v_in = 0, lambda = 0)
eq_rout_ol_g = sp.Eq(v_g / R_return, 0)
eq_rout_ol_x = sp.Eq(i_x, v_x / R_sense + g_m1 * (v_g - 0))
sol_rout_ol = sp.solve([eq_rout_ol_g, eq_rout_ol_x], [v_g, i_x])
R_out_open = sp.simplify(v_x / sol_rout_ol[i_x])

# Feedback factor K (Fig 12.54(a))
eq_K = sp.Eq((v_2 - v_1) / R_1 + v_2 / R_2, 0)
K = sp.simplify(sp.solve(eq_K, v_2)[0] / v_1)
T = sp.simplify(K * A_v_open)

# Closed-loop via feedback formulas
eq_cl_fb = sp.Eq(v_out, A_v_open * (v_in - K * v_out))
A_v_closed_fb = sp.simplify(sp.solve(eq_cl_fb, v_out)[0] / v_in)
R_in_closed_fb = sp.simplify(R_in_open * (1 + T))
R_out_closed_fb = sp.simplify(R_out_open / (1 + T))

# Independent Exact Small-Signal KCL (lambda = 0)
eq_ex_g = sp.Eq((v_g - v_out) / R_1 + v_g / R_2, 0)
eq_ex_out = sp.Eq((v_out - v_g) / R_1 + g_m1 * (v_g - v_in), 0)
eq_ex_iin = sp.Eq(i_in, -g_m1 * (v_g - v_in))
sol_ex = sp.solve([eq_ex_g, eq_ex_out, eq_ex_iin], [v_g, v_out, i_in])

A_v_closed_exact = sp.simplify(sol_ex[v_out] / v_in)
R_in_closed_exact = sp.simplify(v_in / sol_ex[i_in])

eq_ex_rout_g = sp.Eq((v_g - v_x) / R_1 + v_g / R_2, 0)
eq_ex_rout_x = sp.Eq(i_x, (v_x - v_g) / R_1 + g_m1 * (v_g - 0))
sol_ex_rout = sp.solve([eq_ex_rout_g, eq_ex_rout_x], [v_g, i_x])
R_out_closed_exact = sp.simplify(v_x / sol_ex_rout[i_x])

assert sp.simplify(A_v_closed_fb - A_v_closed_exact) == 0
assert sp.simplify(R_in_closed_fb - R_in_closed_exact) == 0
assert sp.simplify(R_out_closed_fb - R_out_closed_exact) == 0

print("R_sense =", R_sense)
print("R_return =", R_return)
print("A_v_open     =", sp.factor(A_v_open))
print("R_in_open    =", R_in_open)
print("R_out_open   =", R_out_open)
print("K            =", K)
print("Loop gain T  =", T)
print("A_v_closed   =", sp.factor(A_v_closed_fb))
print("R_in_closed  =", sp.simplify(R_in_closed_fb), "=", sp.apart(R_in_closed_fb, g_m1))
print("R_out_closed =", sp.factor(R_out_closed_fb))
print("Exact KCL vs Feedback Method difference == 0: ASSERT PASSED")

# Sensitivity check: what if r_O1 < oo?
eq_ro_g = sp.Eq((v_g - v_out) / R_1 + v_g / R_2, 0)
eq_ro_out = sp.Eq((v_out - v_g) / R_1 + g_m1 * (v_g - v_in) + (v_out - v_in) / r_O1, 0)
eq_ro_iin = sp.Eq(i_in, -g_m1 * (v_g - v_in) - (v_out - v_in) / r_O1)
sol_ro = sp.solve([eq_ro_g, eq_ro_out, eq_ro_iin], [v_g, v_out, i_in])
Av_ro = sp.simplify(sol_ro[v_out] / v_in)
Rin_ro = sp.simplify(v_in / sol_ro[i_in])
assert sp.simplify(sp.limit(Av_ro, r_O1, sp.oo) - A_v_closed_exact) == 0
assert sp.simplify(sp.limit(Rin_ro, r_O1, sp.oo) - R_in_closed_exact) == 0
print("\nFinite r_O1 cross-check (reduces to primary as r_O1 -> oo):")
print("  Exact A_v_closed(r_O1)  =", sp.factor(Av_ro))
print("  Exact R_in_closed(r_O1) =", sp.factor(Rin_ro))
