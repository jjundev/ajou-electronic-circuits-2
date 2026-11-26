import sympy as sp

# Problem 5 (E12.28): Two-stage CS + CS amplifier with source feedback
# Assumptions: lambda = 0. Compare Razavi Sec. 12.7.1 two-port feedback vs exact KCL.

g_m1, g_m2, R_D1, R_D2, R_1, R_2 = sp.symbols('g_m1 g_m2 R_D1 R_D2 R_1 R_2', positive=True, finite=True)
v_in, v_out, v_s1, v_x, v_t, i_t = sp.symbols('v_in v_out v_s1 v_x v_t i_t')
v_1, v_2, v_m, i_test, v_test = sp.symbols('v_1 v_2 v_m i_test v_test')

print("=== p5 (E12.28) SymPy Verification ===")

# Step 1 & 2: Two-port feedback network impedances (Fig 12.53(a))
eq_sense_m = sp.Eq((v_m - v_test) / R_1 + v_m / R_2, 0)
eq_sense_i = sp.Eq(i_test, (v_test - v_m) / R_1)
sol_sense = sp.solve([eq_sense_m, eq_sense_i], [v_m, i_test])
R_sense = sp.simplify(v_test / sol_sense[i_test])

eq_ret = sp.Eq(i_test, v_test / R_1 + v_test / R_2)
R_return = sp.simplify(v_test / sp.solve(eq_ret, i_test)[0])

# Step 3 & 4: Open-loop circuit
# M1 source connected to ground via R_return = R_1 || R_2
# M2 drain (V_out) loaded by R_D2 || R_sense = R_D2 || (R_1 + R_2)
# KCL at v_s1: v_s1 / R_return = g_m1 * (v_in - v_s1)
# KCL at v_x (drain of M1 = gate of M2): v_x / R_D1 + g_m1 * (v_in - v_s1) = 0
# KCL at v_out: v_out / R_D2 + v_out / R_sense + g_m2 * v_x = 0
eq_s1_ol = sp.Eq(v_s1 / R_return - g_m1 * (v_in - v_s1), 0)
eq_x_ol = sp.Eq(v_x / R_D1 + g_m1 * (v_in - v_s1), 0)
eq_out_ol = sp.Eq(v_out / R_D2 + v_out / R_sense + g_m2 * v_x, 0)
sol_ol = sp.solve([eq_s1_ol, eq_x_ol, eq_out_ol], [v_s1, v_x, v_out])

A_v_open = sp.simplify(sol_ol[v_out] / v_in)
R_in_open = sp.oo  # Gate of M1 draws zero current

# Open-loop R_out: v_in = 0, test source v_t, i_t at V_out
eq_rout_s1 = sp.Eq(v_s1 / R_return - g_m1 * (0 - v_s1), 0)
eq_rout_x = sp.Eq(v_x / R_D1 + g_m1 * (0 - v_s1), 0)
eq_rout_out = sp.Eq(i_t, v_t / R_D2 + v_t / R_sense + g_m2 * v_x)
sol_rout_ol = sp.solve([eq_rout_s1, eq_rout_x, eq_rout_out], [v_s1, v_x, i_t])
R_out_open = sp.simplify(v_t / sol_rout_ol[i_t])

# Step 5: Feedback factor K (Fig 12.54(a))
eq_K = sp.Eq((v_2 - v_1) / R_1 + v_2 / R_2, 0)
K = sp.simplify(sp.solve(eq_K, v_2)[0] / v_1)
T = sp.simplify(K * A_v_open)

# Step 6: Closed-loop via two-port feedback formulas
eq_cl_fb = sp.Eq(v_out, A_v_open * (v_in - K * v_out))
A_v_closed_fb = sp.simplify(sp.solve(eq_cl_fb, v_out)[0] / v_in)
R_in_closed_fb = sp.oo
R_out_closed_fb = sp.simplify(R_out_open / (1 + T))

# Independent Exact Full Small-Signal KCL (including direct feedforward through R_1)
eq_ex_s1 = sp.Eq((v_s1 - v_out) / R_1 + v_s1 / R_2 - g_m1 * (v_in - v_s1), 0)
eq_ex_x = sp.Eq(v_x / R_D1 + g_m1 * (v_in - v_s1), 0)
eq_ex_out = sp.Eq(v_out / R_D2 + (v_out - v_s1) / R_1 + g_m2 * v_x, 0)
sol_ex = sp.solve([eq_ex_s1, eq_ex_x, eq_ex_out], [v_s1, v_x, v_out])
A_v_closed_exact = sp.simplify(sol_ex[v_out] / v_in)

eq_ex_rout_s1 = sp.Eq((v_s1 - v_t) / R_1 + v_s1 / R_2 - g_m1 * (0 - v_s1), 0)
eq_ex_rout_x = sp.Eq(v_x / R_D1 + g_m1 * (0 - v_s1), 0)
eq_ex_rout_out = sp.Eq(i_t, v_t / R_D2 + (v_t - v_s1) / R_1 + g_m2 * v_x)
sol_ex_rout = sp.solve([eq_ex_rout_s1, eq_ex_rout_x, eq_ex_rout_out], [v_s1, v_x, i_t])
R_out_closed_exact = sp.simplify(v_t / sol_ex_rout[i_t])

R_par = R_1 * R_2 / (R_1 + R_2)
R_L2 = R_D2 * (R_1 + R_2) / (R_D2 + R_1 + R_2)
A_v_open_canon = (g_m1 * R_D1 / (1 + g_m1 * R_par)) * g_m2 * R_L2
T_canon = (g_m1 * R_D1 / (1 + g_m1 * R_par)) * (g_m2 * R_D2 * R_2 / (R_D2 + R_1 + R_2))
A_v_closed_canon = A_v_open_canon / (1 + T_canon)
R_out_closed_canon = R_L2 / (1 + T_canon)
assert sp.simplify(A_v_open - A_v_open_canon) == 0
assert sp.simplify(T - T_canon) == 0
assert sp.simplify(A_v_closed_fb - A_v_closed_canon) == 0
assert sp.simplify(R_out_closed_fb - R_out_closed_canon) == 0

print("R_sense =", R_sense)
print("R_return =", R_return)
print("\n--- Two-Port Feedback Method ---")
print("A_v_open          =", A_v_open_canon)
print("R_in_open         =", R_in_open)
print("R_out_open        =", sp.factor(R_out_open))
print("K                 =", K)
print("Loop gain T       =", T_canon)
print("A_v_closed (fb)   =", sp.factor(A_v_closed_fb))
print("R_in_closed (fb)  =", R_in_closed_fb)
print("R_out_closed (fb) =", sp.factor(R_out_closed_fb))
print("Canonical forms match SymPy solve: ASSERT PASSED")

print("\n--- Exact Full Small-Signal KCL (including direct feedforward through R_1) ---")
print("A_v_closed (exact)   =", sp.factor(A_v_closed_exact))
print("R_out_closed (exact) =", sp.factor(R_out_closed_exact))
print("Ratio A_v_exact / A_v_fb =", sp.simplify(A_v_closed_exact / A_v_closed_fb))

# Numerical check showing how close two-port feedback vs exact KCL are when g_m2*R_D1 >> 1
vals = {g_m1: sp.Rational(1, 200), g_m2: sp.Rational(1, 100), R_D1: 2000, R_D2: 2000, R_1: 3000, R_2: 1000}
print("\nNumerical check (g_m1=5mS, g_m2=10mS, R_D1=2k, R_D2=2k, R_1=3k, R_2=1k):")
for label, expr in [
    ("A_v_open", A_v_open), ("K", K), ("T", T),
    ("A_v_closed (fb)", A_v_closed_fb),
    ("A_v_closed (exact KCL)", A_v_closed_exact),
    ("R_out_open", R_out_open),
    ("R_out_closed (fb)", R_out_closed_fb),
    ("R_out_closed (exact KCL)", R_out_closed_exact),
]:
    print(f"  {label:25s} = {sp.N(expr.subs(vals), 6)}")
