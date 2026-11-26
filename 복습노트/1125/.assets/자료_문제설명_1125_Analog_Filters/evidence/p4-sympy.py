import sympy as sp

sp.init_printing()

# Symbols
g_m1, g_m2 = sp.symbols("g_m1 g_m2", positive=True)
r_o2, R_D, R_F, R_L, R_M = sp.symbols("r_o2 R_D R_F R_L R_M", positive=True)
I_in = sp.symbols("I_in")

def par(a, b):
    return (a * b) / (a + b)

print("=== P4 (Exercise 12.32): Norton Equivalent Driving the Laser ===")

# ---------------------------------------------------------------------------
# 1. 2-Port Feedback Norton Equivalent (from E12.32 eqs 12.166, 12.171, 12.173)
# ---------------------------------------------------------------------------
A_I_open_RL = (
    ((R_F + R_M) * R_D / (R_F + R_M + 1 / g_m1))
    * (-g_m2 * r_o2 / (r_o2 + R_L + par(R_M, R_F)))
)
A_I_open_0 = sp.simplify(A_I_open_RL.subs(R_L, 0))
K = -R_M / (R_M + R_F)
T_RL = sp.simplify(K * A_I_open_RL)
T_0 = sp.simplify(K * A_I_open_0)

A_I_closed_RL = sp.simplify(A_I_open_RL / (1 + T_RL))
I_N_2p = sp.simplify((A_I_open_0 / (1 + T_0)) * I_in)
R_N_2p = sp.simplify((r_o2 + par(R_F, R_M)) * (1 + T_0))

# Norton current-divider check: I_N * R_N / (R_N + R_L) == A_I_closed(R_L) * I_in
I_out_from_norton_2p = sp.simplify(I_N_2p * R_N_2p / (R_N_2p + R_L))
diff_norton_2p = sp.simplify(I_out_from_norton_2p - A_I_closed_RL * I_in)

print("--- 2-Port Feedback Norton Equivalent ---")
print("I_N (2-port, R_L=0):", sp.factor(I_N_2p))
print("R_N (2-port, R_L=0):", sp.factor(R_N_2p))
print("I_N*R_N/(R_N+R_L) - A_I_closed(R_L)*I_in:", diff_norton_2p)
assert diff_norton_2p == 0

# Explicit check that leaving R_L inside R_out_closed (eq 12.173 literal) breaks Norton consistency
R_N_literal_with_RL = (r_o2 + par(R_F, R_M)) * (1 + T_RL)
diff_wrong = sp.simplify(I_N_2p * R_N_literal_with_RL / (R_N_literal_with_RL + R_L) - A_I_closed_RL * I_in)
assert diff_wrong != 0
print("Confirmed: R_N MUST evaluate A_I_open at R_L=0 (leaving R_L inside violates Norton identity).")

# ---------------------------------------------------------------------------
# 2. Exact Full-Circuit KCL Norton Equivalent (no 2-port h_12 omission)
# ---------------------------------------------------------------------------
v_S1, v_X, v_D2, v_P = sp.symbols("v_S1 v_X v_D2 v_P")
# Full closed-loop with arbitrary R_L
sol_RL = sp.solve(
    [
        I_in - g_m1 * v_S1 - (v_S1 - v_P) / R_F,
        v_X / R_D - g_m1 * v_S1,
        g_m2 * (0 - v_X) - v_D2 / r_o2 - (v_D2 - v_P) / R_L,
        (v_D2 - v_P) / R_L + (v_S1 - v_P) / R_F - v_P / R_M,
    ],
    [v_S1, v_X, v_D2, v_P],
)
I_out_exact_RL = sp.simplify((sol_RL[v_D2] - sol_RL[v_P]) / R_L)

# Short-circuit current I_N_exact (R_L = 0 => v_D2 = v_P, I_N flows from D2 into P)
v_S1_sc, v_X_sc, v_P_sc, I_N_sym = sp.symbols("v_S1_sc v_X_sc v_P_sc I_N_sym")
sol_sc = sp.solve(
    [
        I_in - g_m1 * v_S1_sc - (v_S1_sc - v_P_sc) / R_F,
        v_X_sc / R_D - g_m1 * v_S1_sc,
        g_m2 * (0 - v_X_sc) - v_P_sc / r_o2 - I_N_sym,
        I_N_sym + (v_S1_sc - v_P_sc) / R_F - v_P_sc / R_M,
    ],
    [v_S1_sc, v_X_sc, v_P_sc, I_N_sym],
)
I_N_exact = sp.simplify(sol_sc[I_N_sym])
assert sp.simplify(I_N_exact - sp.limit(I_out_exact_RL, R_L, 0)) == 0

# Exact Norton resistance R_N_exact (I_in = 0, test source V_t, I_t across D2 and P)
V_t, I_t, v_S1_o, v_X_o, v_D2_o, v_P_o = sp.symbols("V_t I_t v_S1_o v_X_o v_D2_o v_P_o")
sol_rn = sp.solve(
    [
        0 - g_m1 * v_S1_o - (v_S1_o - v_P_o) / R_F,
        v_X_o / R_D - g_m1 * v_S1_o,
        I_t + g_m2 * (0 - v_X_o) - v_D2_o / r_o2,
        -I_t + (v_S1_o - v_P_o) / R_F - v_P_o / R_M,
        V_t - (v_D2_o - v_P_o),
    ],
    [v_S1_o, v_X_o, v_D2_o, v_P_o, V_t],
)
R_N_exact = sp.simplify(sol_rn[V_t] / I_t)

# Exact Norton theorem verification
I_out_from_norton_exact = sp.simplify(I_N_exact * R_N_exact / (R_N_exact + R_L))
diff_norton_exact = sp.simplify(I_out_from_norton_exact - I_out_exact_RL)

print("\n--- Exact Full-Circuit KCL Norton Equivalent ---")
print("I_N (exact KCL):", sp.factor(I_N_exact))
print("R_N (exact KCL):", sp.factor(R_N_exact))
print("I_N_exact*R_N_exact/(R_N_exact+R_L) - I_out_exact(R_L):", diff_norton_exact)
assert diff_norton_exact == 0
print("ALL P4 CHECKS PASSED.")
