import sympy as sp

# Problem 6 (E12.27): 5-transistor OTA with resistive voltage divider feedback
# Conditions: R1 + R2 not >> (r_OP || r_ON).
# Derive open-loop and closed-loop via BOTH exact 3-node KCL of the 5-T OTA AND Razavi macro-model!

g_mN, g_mP, r_ON, r_OP, R_1, R_2 = sp.symbols('g_mN g_mP r_ON r_OP R_1 R_2', positive=True, finite=True)
v_in, v_out, v_s, v_x, v_g2, v_t, i_t = sp.symbols('v_in v_out v_s v_x v_g2 v_t i_t')
v_1, v_2, v_m, i_test, v_test = sp.symbols('v_1 v_2 v_m i_test v_test')

print("=== p6 (E12.27) SymPy Verification ===")

# Two-port feedback network loading (Fig 12.53(a))
eq_sense_m = sp.Eq((v_m - v_test) / R_1 + v_m / R_2, 0)
eq_sense_i = sp.Eq(i_test, (v_test - v_m) / R_1)
sol_sense = sp.solve([eq_sense_m, eq_sense_i], [v_m, i_test])
R_sense = sp.simplify(v_test / sol_sense[i_test])

eq_ret = sp.Eq(i_test, v_test / R_1 + v_test / R_2)
R_return = sp.simplify(v_test / sp.solve(eq_ret, i_test)[0])

# Feedback factor K (Fig 12.54(a))
eq_K = sp.Eq((v_2 - v_1) / R_1 + v_2 / R_2, 0)
K = sp.simplify(sp.solve(eq_K, v_2)[0] / v_1)

# --- Method A: Exact 3-node Small-Signal KCL for Open-Loop 5-T OTA ---
# M1, M2: NMOS with g_mN, r_ON; M3, M4: PMOS with g_mP, r_OP; ideal tail current source I_SS
# Gate of M2 connected to ground through R_return (since i_g2 = 0 -> v_g2 = 0).
# Drain of M2/M4 (V_out) loaded by R_sense = R_1 + R_2.
# i_d1 = g_mN*(v_in - v_s) + (v_x - v_s)/r_ON
# i_d2 = g_mN*(0 - v_s) + (v_out - v_s)/r_ON
# KCL at v_s: i_d1 + i_d2 = 0
# KCL at v_x (diode-connected M3): i_d1 + g_mP*v_x + v_x/r_OP = 0
# KCL at v_out: i_d2 + g_mP*v_x + v_out/r_OP + v_out/R_sense = 0
i_d1_ol = g_mN * (v_in - v_s) + (v_x - v_s) / r_ON
i_d2_ol = g_mN * (0 - v_s) + (v_out - v_s) / r_ON
eq_ol_s = sp.Eq(i_d1_ol + i_d2_ol, 0)
eq_ol_x = sp.Eq(i_d1_ol + g_mP * v_x + v_x / r_OP, 0)
eq_ol_out = sp.Eq(i_d2_ol + g_mP * v_x + v_out / r_OP + v_out / R_sense, 0)
sol_ol_exact = sp.solve([eq_ol_s, eq_ol_x, eq_ol_out], [v_s, v_x, v_out])
A_v_open_exact3 = sp.simplify(sol_ol_exact[v_out] / v_in)

# Exact 3-node Open-Loop R_out (v_in = 0, v_g2 = 0, test v_t, i_t at V_out)
i_d1_ro = g_mN * (0 - v_s) + (v_x - v_s) / r_ON
i_d2_ro = g_mN * (0 - v_s) + (v_t - v_s) / r_ON
eq_ro_s = sp.Eq(i_d1_ro + i_d2_ro, 0)
eq_ro_x = sp.Eq(i_d1_ro + g_mP * v_x + v_x / r_OP, 0)
eq_ro_out = sp.Eq(i_t, i_d2_ro + g_mP * v_x + v_t / r_OP + v_t / R_sense)
sol_ro_exact = sp.solve([eq_ro_s, eq_ro_x, eq_ro_out], [v_s, v_x, i_t])
R_out_open_exact3 = sp.simplify(v_t / sol_ro_exact[i_t])

# Asymptotic limit of exact 3-node open-loop as intrinsic gains mu_N = g_mN*r_ON -> oo, mu_P = g_mP*r_OP -> oo
# Rewrite g_mP = mu / r_OP and check R_out_open as mu -> oo (and for A_v_open, factor out g_mN first):
mu = sp.symbols('mu', positive=True)
R_out_open_asymp = sp.simplify(sp.limit(
    R_out_open_exact3.subs({g_mN: mu / r_ON, g_mP: mu / r_OP}), mu, sp.oo
))
# For A_v_open, keep g_mN independent by setting r_ON_var -> r_ON while scaling g_mP -> oo and checking G_m = A_v_open / R_out_open!
G_m_open_exact3 = sp.simplify(A_v_open_exact3 / R_out_open_exact3)
# Wait: with g_mN fixed, check limit as g_mP -> oo (i.e. 1/(g_mP*r_OP) -> 0) and 1/(g_mN*r_ON) -> 0?
# Let's substitute g_mN = G_mN_val, and in A_v_open divide by g_mN then take g_mN_inner = mu/r_ON:
A_v_ratio = sp.simplify(A_v_open_exact3 / g_mN)
# Wait: A_v_open_exact3 still contains g_mN in g_mN*r_ON terms! Separate via mu_N = g_mN * r_ON:
mu_N, mu_P = sp.symbols('mu_N mu_P', positive=True)
# Solve with g_mN_factor explicit: i_d1 = g_mN_in*(v_in - v_s) + ... -> actually just take limit mu_N, mu_P -> oo on R_out and G_m:
# Keep g_mN in numerator, set r_ON = mu / g_mN_dummy? Even cleaner: evaluate G_m_open_exact3 / g_mN!
G_m_norm = sp.simplify((G_m_open_exact3 / g_mN).subs({g_mN: mu / r_ON, g_mP: mu / r_OP}))
G_m_norm_limit = sp.limit(G_m_norm, mu, sp.oo)

# --- Method B: Razavi Macro-model (G_m = g_mN, R_out_core = r_ON || r_OP) ---
R_core = (r_ON * r_OP) / (r_ON + r_OP)
R_out_open_macro = sp.simplify((R_core * R_sense) / (R_core + R_sense))
A_v_open_macro = sp.simplify(g_mN * R_out_open_macro)
R_in_open = sp.oo
T_macro = sp.simplify(K * A_v_open_macro)

eq_cl_fb = sp.Eq(v_out, A_v_open_macro * (v_in - K * v_out))
A_v_closed_macro = sp.simplify(sp.solve(eq_cl_fb, v_out)[0] / v_in)
R_in_closed = sp.oo
R_out_closed_macro = sp.simplify(R_out_open_macro / (1 + T_macro))

# --- Exact 3-node Closed-Loop KCL (with v_g2 = K * v_out directly!) ---
# Note: gate of M2 draws 0 current, so v_g2 = K * v_out and divider draws v_out / (R_1 + R_2) EXACTLY!
i_d1_cl = g_mN * (v_in - v_s) + (v_x - v_s) / r_ON
i_d2_cl = g_mN * (K * v_out - v_s) + (v_out - v_s) / r_ON
eq_cl_s = sp.Eq(i_d1_cl + i_d2_cl, 0)
eq_cl_x = sp.Eq(i_d1_cl + g_mP * v_x + v_x / r_OP, 0)
eq_cl_out = sp.Eq(i_d2_cl + g_mP * v_x + v_out / r_OP + v_out / (R_1 + R_2), 0)
sol_cl_exact = sp.solve([eq_cl_s, eq_cl_x, eq_cl_out], [v_s, v_x, v_out])
A_v_closed_exact3 = sp.simplify(sol_cl_exact[v_out] / v_in)

i_d1_cl_ro = g_mN * (0 - v_s) + (v_x - v_s) / r_ON
i_d2_cl_ro = g_mN * (K * v_t - v_s) + (v_t - v_s) / r_ON
eq_cl_ro_s = sp.Eq(i_d1_cl_ro + i_d2_cl_ro, 0)
eq_cl_ro_x = sp.Eq(i_d1_cl_ro + g_mP * v_x + v_x / r_OP, 0)
eq_cl_ro_out = sp.Eq(i_t, i_d2_cl_ro + g_mP * v_x + v_t / r_OP + v_t / (R_1 + R_2))
sol_cl_ro_exact = sp.solve([eq_cl_ro_s, eq_cl_ro_x, eq_cl_ro_out], [v_s, v_x, i_t])
R_out_closed_exact3 = sp.simplify(v_t / sol_cl_ro_exact[i_t])

assert sp.simplify(R_out_open_asymp - R_out_open_macro) == 0
assert sp.simplify(G_m_norm_limit - 1) == 0

R_out_open_par = 1 / (1 / r_ON + 1 / r_OP + 1 / (R_1 + R_2))
A_v_open_par = g_mN * R_out_open_par
A_v_closed_par = g_mN / (1 / r_ON + 1 / r_OP + 1 / (R_1 + R_2) + g_mN * R_2 / (R_1 + R_2))
R_out_closed_par = 1 / (1 / r_ON + 1 / r_OP + 1 / (R_1 + R_2) + g_mN * R_2 / (R_1 + R_2))
assert sp.simplify(R_out_open_macro - R_out_open_par) == 0
assert sp.simplify(A_v_open_macro - A_v_open_par) == 0
assert sp.simplify(A_v_closed_macro - A_v_closed_par) == 0
assert sp.simplify(R_out_closed_macro - R_out_closed_par) == 0

print("R_sense =", R_sense)
print("R_return =", R_return)
print("K =", K)
print("\n--- Razavi Macro-Model (g_m * r_O >> 1, matching E12.27 symbols g_mN, r_ON, r_OP) ---")
print("A_v_open     =", sp.factor(A_v_open_macro))
print("R_in_open    =", R_in_open)
print("R_out_open   =", sp.factor(R_out_open_macro))
print("Loop gain T  =", sp.factor(T_macro))
print("A_v_closed   =", sp.factor(A_v_closed_macro))
print("R_in_closed  =", R_in_closed)
print("R_out_closed =", sp.factor(R_out_closed_macro))
print("Parallel-conductance canonical forms verified: ASSERT PASSED")

print("\n--- Exact 3-node KCL Verification ---")
print("Asymptotic limit (g_m*r_O -> oo) R_out_open == macro-model: ASSERT PASSED")
print("Asymptotic limit (g_m*r_O -> oo) G_m / g_mN == 1: ASSERT PASSED")

vals = {g_mN: sp.Rational(1, 100), g_mP: sp.Rational(1, 100), r_ON: 50000, r_OP: 50000, R_1: 30000, R_2: 10000}
print("\nNumerical comparison (g_mN=g_mP=10mS, r_ON=r_OP=50k => g_m*r_O=500, R_1=30k, R_2=10k):")
for label, expr in [
    ("A_v_open (macro)", A_v_open_macro),
    ("A_v_open (exact 3-node)", A_v_open_exact3),
    ("R_out_open (macro)", R_out_open_macro),
    ("R_out_open (exact 3-node)", R_out_open_exact3),
    ("A_v_closed (macro)", A_v_closed_macro),
    ("A_v_closed (exact 3-node)", A_v_closed_exact3),
    ("R_out_closed (macro)", R_out_closed_macro),
    ("R_out_closed (exact 3-node)", R_out_closed_exact3),
]:
    print(f"  {label:28s} = {sp.N(expr.subs(vals), 6)}")
