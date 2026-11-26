import sympy as sp

sp.init_printing()

# Symbols (all positive small-signal parameters)
g_m1, g_m2 = sp.symbols("g_m1 g_m2", positive=True)
R_D, R_L, R_M = sp.symbols("R_D R_L R_M", positive=True)
v_in = sp.symbols("v_in")

print("=== P1 (2021-1 Final Q4): CG M1 + SF M2, lambda = 0 ===")

# ---------------------------------------------------------------------------
# 1. Open-loop 2-port feedback decomposition (Current-Voltage / series-series)
# Feedback network is R_M:
#   Port 1 (current sense): I_1 = I_out enters V_F; Port 2 (voltage return): V_2 = V_F at M1 gate (I_2 = 0)
#   Open-loop input loading (open Port 1 -> I_1 = 0): R_M in series with M1 gate (I_G1 = 0 => V_G1 = 0)
#   Open-loop output loading (open Port 2 -> I_2 = 0): R_M in series with Laser R_L
# ---------------------------------------------------------------------------

# Stage 1: M1 Common-Gate with V_G1 = 0, source = v_in, drain = X, load = R_D (lambda = 0)
v_X_ol = sp.symbols("v_X_ol")
# KCL at X: v_X / R_D + g_m1 * (0 - v_in) = 0
sol_s1 = sp.solve([v_X_ol / R_D + g_m1 * (0 - v_in)], [v_X_ol])
VX_over_Vin_ol = sp.simplify(sol_s1[v_X_ol] / v_in)
print("Open-loop Stage 1 (VX / Vin):", VX_over_Vin_ol)

# Input impedance open-loop: current i_in enters M1 source at v_in with V_G1 = 0
# i_in = -i_d1 = -g_m1 * (0 - v_in) = g_m1 * v_in
i_in_ol = g_m1 * (v_in - 0)
R_in_open = sp.simplify(v_in / i_in_ol)
print("R_in_open:", R_in_open)

# Stage 2: M2 Source Follower with gate = v_X_ol, drain = 0 (VDD), source = v_S2, load = R_L + R_M
v_S2_ol = sp.symbols("v_S2_ol")
sol_s2 = sp.solve([g_m2 * (v_X_ol - v_S2_ol) - v_S2_ol / (R_L + R_M)], [v_S2_ol])
v_S2_expr = sp.simplify(sol_s2[v_S2_ol])
i_out_s2_kcl = sp.simplify(v_S2_expr / (R_L + R_M))
Iout_over_VX_kcl = sp.simplify(i_out_s2_kcl / v_X_ol)

# Chain-rule product check requested:
# (V_S2 / V_X) * (I_out / V_S2) with R_L -> R_L + R_M
R_eff = R_L + R_M
VS2_over_VX_sf = R_eff / (1 / g_m2 + R_eff)
Iout_over_VS2 = 1 / R_eff
Iout_over_VX_chain = sp.simplify(VS2_over_VX_sf * Iout_over_VS2)

diff_sf_chain = sp.simplify(Iout_over_VX_chain - Iout_over_VX_kcl)
print("Open-loop Stage 2 (Iout / VX) KCL:  ", sp.factor(Iout_over_VX_kcl))
print("Open-loop Stage 2 (Iout / VX) chain:", sp.factor(Iout_over_VX_chain))
print("SF chain-rule vs KCL difference:    ", diff_sf_chain)
assert diff_sf_chain == 0

A_open = sp.simplify(VX_over_Vin_ol * Iout_over_VX_kcl)
print("Open-loop gain G_m_open = Iout/Vin:", sp.factor(A_open))

# Open-loop output impedance seen by Laser (test source V_t between S2 and V_F, V_in = 0, V_G1 = 0)
V_t, I_t, v_S2_t, v_F_t = sp.symbols("V_t I_t v_S2_t v_F_t")
# Test source injects I_t into S2 and draws I_t out of V_F, V_t = v_S2_t - v_F_t
# With V_in = 0, V_G1 = 0 => v_X = 0.
# KCL at S2: I_t + g_m2 * (0 - v_S2_t) = 0
# KCL at V_F: -I_t - v_F_t / R_M = 0
sol_rout_ol = sp.solve(
    [I_t + g_m2 * (0 - v_S2_t), -I_t - v_F_t / R_M, V_t - (v_S2_t - v_F_t)],
    [v_S2_t, v_F_t, V_t],
)
R_out_open = sp.simplify(sol_rout_ol[V_t] / I_t)
print("R_out_open (seen by Laser):", R_out_open)

# Feedback factor K: V_F = K * I_out
K = R_M
print("Feedback factor K = V_F / I_out:", K)

# Loop gain T (verify sign directly by breaking loop at M1 gate)
# Inject v_test at M1 gate (with v_in = 0), measure v_F returned:
v_test, v_X_lg, v_S2_lg, v_F_lg = sp.symbols("v_test v_X_lg v_S2_lg v_F_lg")
sol_lg = sp.solve(
    [
        v_X_lg / R_D + g_m1 * (v_test - 0),
        g_m2 * (v_X_lg - v_S2_lg) - (v_S2_lg - v_F_lg) / R_L,
        (v_S2_lg - v_F_lg) / R_L - v_F_lg / R_M,
    ],
    [v_X_lg, v_S2_lg, v_F_lg],
)
L_return = sp.simplify(sol_lg[v_F_lg] / v_test)
T_from_KA = sp.simplify(K * A_open)
print("Direct loop return v_F / v_test:    ", sp.factor(L_return))
print("Loop gain T = -v_F/v_test = K*A_open:", sp.factor(T_from_KA))
assert sp.simplify(L_return + T_from_KA) == 0

T_0 = sp.simplify(T_from_KA.subs(R_L, 0))
print("T_0 (with R_L = 0):                 ", sp.factor(T_0))

# 2-port closed-loop formulas
A_closed_2p = sp.simplify(A_open / (1 + T_from_KA))
R_in_closed_2p = sp.simplify(R_in_open * (1 + T_from_KA))
R_out_closed_2p = sp.simplify(R_out_open * (1 + T_0))

print("\n--- 2-Port Feedback Results ---")
print("A_closed (2-port):    ", sp.factor(A_closed_2p))
print("R_in_closed (2-port): ", sp.factor(R_in_closed_2p))
print("R_out_closed (2-port):", sp.simplify(R_out_closed_2p))

# ---------------------------------------------------------------------------
# 2. Exact closed-loop KCL/KVL verification (no feedback approximations)
# ---------------------------------------------------------------------------
v_X, v_S2, v_F = sp.symbols("v_X v_S2 v_F")
sol_cl = sp.solve(
    [
        v_X / R_D + g_m1 * (v_F - v_in),
        g_m2 * (v_X - v_S2) - (v_S2 - v_F) / R_L,
        (v_S2 - v_F) / R_L - v_F / R_M,
    ],
    [v_X, v_S2, v_F],
)
i_out_exact = sp.simplify((sol_cl[v_S2] - sol_cl[v_F]) / R_L)
A_closed_exact = sp.simplify(i_out_exact / v_in)

# Input current entering M1 source from v_in: i_in = -i_d1 = -g_m1 * (v_F - v_in)
i_in_exact = sp.simplify(-g_m1 * (sol_cl[v_F] - v_in))
R_in_closed_exact = sp.simplify(v_in / i_in_exact)

# Closed-loop output impedance seen by Laser (replace R_L with test source V_t, I_t; v_in = 0)
v_X_o, v_S2_o, v_F_o = sp.symbols("v_X_o v_S2_o v_F_o")
sol_rout_cl = sp.solve(
    [
        v_X_o / R_D + g_m1 * (v_F_o - 0),
        I_t + g_m2 * (v_X_o - v_S2_o),
        -I_t - v_F_o / R_M,
        V_t - (v_S2_o - v_F_o),
    ],
    [v_X_o, v_S2_o, v_F_o, V_t],
)
R_out_closed_exact = sp.simplify(sol_rout_cl[V_t] / I_t)

print("\n--- Exact KCL Verification ---")
print("A_closed (exact KCL):    ", sp.factor(A_closed_exact))
print("R_in_closed (exact KCL): ", sp.factor(R_in_closed_exact))
print("R_out_closed (exact KCL):", sp.simplify(R_out_closed_exact))

diff_A = sp.simplify(A_closed_2p - A_closed_exact)
diff_Rin = sp.simplify(R_in_closed_2p - R_in_closed_exact)
diff_Rout = sp.simplify(R_out_closed_2p - R_out_closed_exact)
print("diff A_closed:    ", diff_A)
print("diff R_in_closed: ", diff_Rin)
print("diff R_out_closed:", diff_Rout)

assert diff_A == 0
assert diff_Rin == 0
assert diff_Rout == 0
print("ALL P1 CHECKS PASSED (differences == 0).")
