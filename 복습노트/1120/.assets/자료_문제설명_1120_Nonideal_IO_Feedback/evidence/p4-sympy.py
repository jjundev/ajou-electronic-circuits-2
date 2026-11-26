import sympy as sp

# Problem 4 (P12.42): Bipolar common-base stage with resistive divider feedback
# Conditions: R1+R2 not very large, 1 << beta < oo, V_A = oo.
# Derive via Razavi Sec. 12.7.1 two-port breaking rules AND compare against exact full KCL.

g_m, beta, R_C, R_1, R_2 = sp.symbols('g_m beta R_C R_1 R_2', positive=True, finite=True)
r_pi = beta / g_m
v_in, v_out, v_b, i_in, v_x, i_x = sp.symbols('v_in v_out v_b i_in v_x i_x')
v_1, v_2, v_m, i_test, v_test = sp.symbols('v_1 v_2 v_m i_test v_test')

print("=== p4 (P12.42) SymPy Verification ===")

# Step 1 & 2: Two-port feedback loading impedances (Fig 12.53(a))
eq_sense_m = sp.Eq((v_m - v_test) / R_1 + v_m / R_2, 0)
eq_sense_i = sp.Eq(i_test, (v_test - v_m) / R_1)
sol_sense = sp.solve([eq_sense_m, eq_sense_i], [v_m, i_test])
R_sense = sp.simplify(v_test / sol_sense[i_test])

eq_ret = sp.Eq(i_test, v_test / R_1 + v_test / R_2)
R_return = sp.simplify(v_test / sp.solve(eq_ret, i_test)[0])

# Step 3 & 4: Open-loop circuit (collector loaded by R_C || R_sense, base grounded via R_return)
# Base KCL: v_b / R_return + (v_b - v_in) / r_pi = 0
# Collector KCL: v_out / R_C + v_out / R_sense + g_m * (v_b - v_in) = 0
# Emitter input current: i_in = -(g_m + 1/r_pi) * (v_b - v_in)
eq_b_ol = sp.Eq(v_b / R_return + (v_b - v_in) / r_pi, 0)
eq_c_ol = sp.Eq(v_out / R_C + v_out / R_sense + g_m * (v_b - v_in), 0)
eq_iin_ol = sp.Eq(i_in, -(g_m + 1 / r_pi) * (v_b - v_in))
sol_ol = sp.solve([eq_b_ol, eq_c_ol, eq_iin_ol], [v_b, v_out, i_in])

A_v_open = sp.simplify(sol_ol[v_out] / v_in)
R_in_open = sp.simplify(v_in / sol_ol[i_in])

# Open-loop R_out: v_in = 0, test source v_x, i_x at V_out
eq_rout_ol_b = sp.Eq(v_b / R_return + v_b / r_pi, 0)
eq_rout_ol_c = sp.Eq(i_x, v_x / R_C + v_x / R_sense + g_m * v_b)
sol_rout_ol = sp.solve([eq_rout_ol_b, eq_rout_ol_c], [v_b, i_x])
R_out_open = sp.simplify(v_x / sol_rout_ol[i_x])

# Step 5: Feedback factor K (Fig 12.54(a))
eq_K = sp.Eq((v_2 - v_1) / R_1 + v_2 / R_2, 0)
K = sp.simplify(sp.solve(eq_K, v_2)[0] / v_1)
T = sp.simplify(K * A_v_open)

# Step 6: Closed-loop via two-port feedback formulas
eq_cl_fb = sp.Eq(v_out, A_v_open * (v_in - K * v_out))
A_v_closed_fb = sp.simplify(sp.solve(eq_cl_fb, v_out)[0] / v_in)
R_in_closed_fb = sp.simplify(R_in_open * (1 + T))
R_out_closed_fb = sp.simplify(R_out_open / (1 + T))

# Also apply 1 << beta approximation (beta + 1 -> beta in i_e = (1+1/beta)*i_c ~ i_c, keeping r_pi = beta/g_m)
# Wait: specifically i_in ~ -g_m*(v_b - v_in), i.e., alpha = beta/(beta+1) ~ 1
eq_iin_ol_approx = sp.Eq(i_in, -g_m * (v_b - v_in))
sol_ol_approx = sp.solve([eq_b_ol, eq_c_ol, eq_iin_ol_approx], [v_b, v_out, i_in])
R_in_open_approx = sp.simplify(v_in / sol_ol_approx[i_in])
R_in_closed_fb_approx = sp.simplify(R_in_open_approx * (1 + T))

# Independent Exact Full Small-Signal KCL (no feedback decomposition, includes base current through R1)
eq_ex_b = sp.Eq((v_b - v_out) / R_1 + v_b / R_2 + (v_b - v_in) / r_pi, 0)
eq_ex_c = sp.Eq(v_out / R_C + (v_out - v_b) / R_1 + g_m * (v_b - v_in), 0)
eq_ex_iin = sp.Eq(i_in, -(g_m + 1 / r_pi) * (v_b - v_in))
sol_ex = sp.solve([eq_ex_b, eq_ex_c, eq_ex_iin], [v_b, v_out, i_in])

A_v_closed_exact = sp.simplify(sol_ex[v_out] / v_in)
R_in_closed_exact = sp.simplify(v_in / sol_ex[i_in])

eq_ex_rout_b = sp.Eq((v_b - v_x) / R_1 + v_b / R_2 + v_b / r_pi, 0)
eq_ex_rout_c = sp.Eq(i_x, v_x / R_C + (v_x - v_b) / R_1 + g_m * v_b)
sol_ex_rout = sp.solve([eq_ex_rout_b, eq_ex_rout_c], [v_b, i_x])
R_out_closed_exact = sp.simplify(v_x / sol_ex_rout[i_x])

# Compare exact KCL vs two-port feedback formula & verify compact canonical forms
R_par = R_1 * R_2 / (R_1 + R_2)
R_L = R_C * (R_1 + R_2) / (R_C + R_1 + R_2)
denom_deg = 1 + R_par / r_pi

A_v_open_canon = g_m * R_L / denom_deg
R_in_open_approx_canon = 1 / g_m + R_par / beta
T_canon = g_m * R_C * R_2 / (denom_deg * (R_C + R_1 + R_2))
A_v_closed_canon = (g_m * R_L) / (denom_deg + g_m * R_C * R_2 / (R_C + R_1 + R_2))
R_in_closed_approx_canon = 1 / g_m + R_par / beta + R_C * R_2 / (R_C + R_1 + R_2)
R_out_closed_canon = R_L / (1 + T_canon)

assert sp.simplify(A_v_open - A_v_open_canon) == 0
assert sp.simplify(R_in_open_approx - R_in_open_approx_canon) == 0
assert sp.simplify(T - T_canon) == 0
assert sp.simplify(A_v_closed_fb - A_v_closed_canon) == 0
assert sp.simplify(R_in_closed_fb_approx - R_in_closed_approx_canon) == 0
assert sp.simplify(R_out_closed_fb - R_out_closed_canon) == 0

print("R_sense =", R_sense)
print("R_return =", R_return)
print("\n--- Two-Port Feedback Method (exact beta & 1<<beta canonical) ---")
print("A_v_open            =", sp.factor(A_v_open))
print("R_in_open (exact b) =", sp.factor(R_in_open))
print("R_in_open (1<<b)    =", R_in_open_approx_canon)
print("R_out_open          =", sp.factor(R_out_open))
print("K                   =", K)
print("Loop gain T         =", sp.factor(T))
print("A_v_closed (fb)     =", A_v_closed_canon)
print("R_in_closed (fb, b) =", sp.factor(R_in_closed_fb))
print("R_in_closed (1<<b)  =", R_in_closed_approx_canon)
print("R_out_closed (fb)   =", R_out_closed_canon)
print("Canonical forms match SymPy solve: ASSERT PASSED")

print("\n--- Exact Full Small-Signal KCL (including i_b feedforward through R1) ---")
print("A_v_closed (exact)  =", sp.factor(A_v_closed_exact))
print("R_in_closed (exact) =", sp.factor(R_in_closed_exact))
print("R_out_closed(exact) =", sp.factor(R_out_closed_exact))

# Check that exact KCL differs from two-port feedback ONLY by O(1/beta) terms (K/beta feedforward and 1/beta in alpha):
# Specifically, if we track exact KCL with i_c + K*i_b -> i_c (drop K/beta) and i_e -> i_c (drop 1/beta):
vals = {g_m: sp.Rational(1, 25), beta: 100, R_C: 2000, R_1: 3000, R_2: 1000}
print("\nNumerical comparison (g_m=40mS, beta=100 => r_pi=2.5k, R_C=2k, R_1=3k, R_2=1k):")
for label, expr in [
    ("A_v_closed (fb)", A_v_closed_fb),
    ("A_v_closed (exact)", A_v_closed_exact),
    ("R_in_closed (fb, exact beta)", R_in_closed_fb),
    ("R_in_closed (fb, 1<<beta)", R_in_closed_fb_approx),
    ("R_in_closed (exact KCL)", R_in_closed_exact),
    ("R_out_closed (fb)", R_out_closed_fb),
    ("R_out_closed (exact KCL)", R_out_closed_exact),
]:
    print(f"  {label:30s} = {sp.N(expr.subs(vals), 6)}")
