import sympy as sp

sp.init_printing()

# Symbols
g_m1, g_m2 = sp.symbols("g_m1 g_m2", positive=True)
r_o2, R_D, R_F, R_L, R_M = sp.symbols("r_o2 R_D R_F R_L R_M", positive=True)
I_in = sp.symbols("I_in")

def par(a, b):
    return (a * b) / (a + b)

print("=== P3 (Example 12.32, Fig 12.61(a)): Current-Current Feedback ===")

# ---------------------------------------------------------------------------
# 1. Input stage open-loop (Fig 12.61(b)): Norton-to-Thevenin vs Direct KCL
# ---------------------------------------------------------------------------
# Norton-to-Thevenin conversion:
# I_in || (R_F + R_M) -> V_th = I_in * (R_F + R_M) in series with (R_F + R_M) driving M1 source (1/g_m1)
V_th = I_in * (R_F + R_M)
I_s1_thev = V_th / (R_F + R_M + 1 / g_m1)
# Current I_s1 enters M1 source => V_S1 = I_s1 / g_m1 => V_X = g_m1 * R_D * V_S1 = I_s1 * R_D
VX_over_Iin_thev = sp.simplify((I_s1_thev * R_D) / I_in)

# Direct KCL on open-loop input stage (node S1 and node X):
v_S1_ol, v_X_ol = sp.symbols("v_S1_ol v_X_ol")
sol_in_kcl = sp.solve(
    [
        I_in - v_S1_ol / (R_F + R_M) - g_m1 * v_S1_ol,
        v_X_ol / R_D - g_m1 * v_S1_ol,
    ],
    [v_S1_ol, v_X_ol],
)
VX_over_Iin_kcl = sp.simplify(sol_in_kcl[v_X_ol] / I_in)
diff_vx_iin = sp.simplify(VX_over_Iin_thev - VX_over_Iin_kcl)
print("Input stage V_X / I_in (Norton->Thevenin):", sp.factor(VX_over_Iin_thev))
print("Input stage V_X / I_in (Direct KCL):      ", sp.factor(VX_over_Iin_kcl))
print("Difference (simplify == 0):               ", diff_vx_iin)
assert diff_vx_iin == 0

R_in_open = sp.simplify(sol_in_kcl[v_S1_ol] / I_in)
print("R_in_open:", sp.factor(R_in_open))
assert sp.simplify(R_in_open - par(1 / g_m1, R_F + R_M)) == 0

# ---------------------------------------------------------------------------
# 2. Output stage open-loop (Fig 12.61(b)) & 2-Port Feedback Results
# M2 (PMOS, S=0, G=X, D=D2) with r_o2 drives R_L in series with (R_M || R_F)
# ---------------------------------------------------------------------------
v_D2_ol, v_X_sym = sp.symbols("v_D2_ol v_X_sym")
R_P_ol = par(R_M, R_F)
sol_out_ol = sp.solve(
    [g_m2 * (0 - v_X_sym) - v_D2_ol / r_o2 - v_D2_ol / (R_L + R_P_ol)],
    [v_D2_ol],
)
i_out_ol = sp.simplify(sol_out_ol[v_D2_ol] / (R_L + R_P_ol))
Iout_over_VX_ol = sp.simplify(i_out_ol / v_X_sym)
print("Output stage I_out / V_X (open-loop):", sp.factor(Iout_over_VX_ol))

A_I_open = sp.simplify(VX_over_Iin_kcl * Iout_over_VX_ol)
eq12_166 = ((R_F + R_M) * R_D / (R_F + R_M + 1 / g_m1)) * (-g_m2 * r_o2 / (r_o2 + R_L + par(R_M, R_F)))
assert sp.simplify(A_I_open - eq12_166) == 0
print("A_I_open (matches eq 12.166):", sp.factor(A_I_open))

# R_out_open seen by Laser (test source V_t, I_t across D2 and P; I_in=0, feedback return open => V_X=0, S1 shorted in sense replica)
V_t, I_t, v_D2_t, v_P_t = sp.symbols("V_t I_t v_D2_t v_P_t")
sol_rout_ol = sp.solve(
    [I_t - v_D2_t / r_o2, -I_t - v_P_t / R_P_ol, V_t - (v_D2_t - v_P_t)],
    [v_D2_t, v_P_t, V_t],
)
R_out_open = sp.simplify(sol_rout_ol[V_t] / I_t)
assert sp.simplify(R_out_open - (r_o2 + par(R_F, R_M))) == 0
print("R_out_open (matches eq 12.168):", sp.factor(R_out_open))

# Feedback factor K (Fig 12.61(c), standard 2-port port-1/port-2 current convention matching eq 12.170):
# In Fig 12.61(a), I_out enters node P; in the 2-port feedback model, Port-1 input current I_1 enters node P
# (note: Fig 12.61(c) draws I_1 arrow downward as a minor textbook arrow-convention quirk, while eq 12.170
# uses I_1 entering P and I_2 entering Port 2 rightward into R_F with S1 shorted V_2 = 0).
v_P_fb, I_1_fb, I_2_fb = sp.symbols("v_P_fb I_1_fb I_2_fb")
sol_fb = sp.solve(
    [
        I_1_fb - v_P_fb / R_M - v_P_fb / R_F,  # KCL at node P with I_1 entering P
        I_2_fb - (0 - v_P_fb) / R_F,           # I_2 entering R_F from shorted Port 2 (V_2 = 0)
    ],
    [v_P_fb, I_2_fb],
)
K = sp.simplify(sol_fb[I_2_fb] / I_1_fb)
assert sp.simplify(K - (-R_M / (R_M + R_F))) == 0
# Since A_I_open < 0 and K < 0, K * A_I_open > 0, and return ratio T = -L = -(R_M/(R_M+R_F))*A_I_open = +K*A_I_open > 0
# Note Razavi writes 1 - (R_M/(R_M+R_F))*A_I_open = 1 + K*A_I_open = 1 + T
T = sp.simplify(K * A_I_open)
T_0 = sp.simplify(T.subs(R_L, 0))
print("Feedback factor K (eq 12.170):", K)
print("Loop gain magnitude T = K*A_I_open = -(R_M/(R_M+R_F))*A_I_open > 0:")
print(" ", sp.factor(T))
print("T_0 (with R_L = 0):", sp.factor(T_0))

A_I_closed_2p = sp.simplify(A_I_open / (1 + T))
R_in_closed_2p = sp.simplify(R_in_open / (1 + T))
R_out_closed_2p = sp.simplify(R_out_open * (1 + T_0))

print("\n--- 2-Port Feedback Results (Razavi eqs 12.171-12.173) ---")
print("A_I_closed (eq 12.171):              ", sp.factor(A_I_closed_2p))
print("R_in_closed (eq 12.172):             ", sp.factor(R_in_closed_2p))
print("R_out_closed (eq 12.173 with R_L=0): ", sp.factor(R_out_closed_2p))

# ---------------------------------------------------------------------------
# 3. Exact Full-Circuit KCL (including bilateral feedthrough h_12 through R_F)
# ---------------------------------------------------------------------------
v_S1, v_X, v_D2, v_P = sp.symbols("v_S1 v_X v_D2 v_P")
sol_exact = sp.solve(
    [
        I_in - g_m1 * v_S1 - (v_S1 - v_P) / R_F,
        v_X / R_D - g_m1 * v_S1,
        g_m2 * (0 - v_X) - v_D2 / r_o2 - (v_D2 - v_P) / R_L,
        (v_D2 - v_P) / R_L + (v_S1 - v_P) / R_F - v_P / R_M,
    ],
    [v_S1, v_X, v_D2, v_P],
)
I_out_exact = sp.simplify((sol_exact[v_D2] - sol_exact[v_P]) / R_L)
A_I_closed_exact = sp.simplify(I_out_exact / I_in)
R_in_closed_exact = sp.simplify(sol_exact[v_S1] / I_in)

# Exact R_out_closed (replace R_L with V_t, I_t; I_in = 0)
v_S1_o, v_X_o, v_D2_o, v_P_o = sp.symbols("v_S1_o v_X_o v_D2_o v_P_o")
sol_rout_exact = sp.solve(
    [
        0 - g_m1 * v_S1_o - (v_S1_o - v_P_o) / R_F,
        v_X_o / R_D - g_m1 * v_S1_o,
        I_t + g_m2 * (0 - v_X_o) - v_D2_o / r_o2,
        -I_t + (v_S1_o - v_P_o) / R_F - v_P_o / R_M,
        V_t - (v_D2_o - v_P_o),
    ],
    [v_S1_o, v_X_o, v_D2_o, v_P_o, V_t],
)
R_out_closed_exact = sp.simplify(sol_rout_exact[V_t] / I_t)

# Check exact closed-loop R_out decomposition
R_out_exact_expected = (
    r_o2
    + par(R_M, R_F + 1 / g_m1)
    + (g_m2 * r_o2 * R_D * R_M) / (R_F + R_M + 1 / g_m1)
)
assert sp.simplify(R_out_closed_exact - R_out_exact_expected) == 0

print("\n--- Exact Full-Circuit KCL vs 2-Port Feedback Comparison ---")
print("A_I_closed (exact KCL):   ", sp.factor(A_I_closed_exact))
print("R_in_closed (exact KCL):  ", sp.factor(R_in_closed_exact))
print("R_out_closed (exact KCL): ", sp.factor(R_out_closed_exact))
print("Note on bilateral h_12 feedthrough:")
print("  R_out_closed_exact - R_out_closed_2p =", sp.simplify(R_out_closed_exact - R_out_closed_2p))
print("  (i.e. R_M||(R_F + 1/g_m1) in exact KCL vs R_M||R_F in 2-port unilateral approximation)")
print("  A_I_closed_exact - A_I_closed_2p     =", sp.factor(sp.simplify(A_I_closed_exact - A_I_closed_2p)))
print("  R_in_closed_exact - R_in_closed_2p   =", sp.factor(sp.simplify(R_in_closed_exact - R_in_closed_2p)))
print("ALL P3 CHECKS PASSED.")
