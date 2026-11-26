import sympy as sp

sp.init_printing()

# Symbols
g_m1, g_m3, g_m4, g_m5, g_m6 = sp.symbols("g_m1 g_m3 g_m4 g_m5 g_m6", positive=True)
r_o1, r_o3, r_o4, r_o5, r_o6 = sp.symbols("r_o1 r_o3 r_o4 r_o5 r_o6", positive=True)
R_L, R_M = sp.symbols("R_L R_M", positive=True)
v_in = sp.symbols("v_in")

print("=== P2 (2023-1 Final Q3): 5T OTA (M3-M6) + PMOS CS M1, lambda > 0 ===")

# ---------------------------------------------------------------------------
# 1. Exact KCL of the 5-Transistor OTA (ideal tail current source I_SS)
# Nodes: v_S (tail), v_A (M4/M6 diode-connected node), v_X (M3/M5 drain)
# Inputs: v_G3 = v_in, v_G4 = v_F (v_F = 0 for open-loop)
# ---------------------------------------------------------------------------
def solve_5t_ota(v_G3, v_G4, matched=False):
    v_S, v_A, v_X = sp.symbols("v_S v_A v_X")
    # Downward drain currents in M3, M4 (NMOS) and M5, M6 (PMOS, S at VDD=0)
    i_d3 = g_m3 * (v_G3 - v_S) + (v_X - v_S) / r_o3
    i_d4 = g_m4 * (v_G4 - v_S) + (v_A - v_S) / r_o4
    i_d5 = g_m5 * (0 - v_A) + (0 - v_X) / r_o5
    i_d6 = g_m6 * (0 - v_A) + (0 - v_A) / r_o6
    eqs = [
        i_d3 + i_d4,  # KCL at tail node (ideal I_SS => sum of drain currents = 0)
        i_d6 - i_d4,  # KCL at diode node A
        i_d5 - i_d3,  # KCL at output node X (M1 gate draws 0)
    ]
    sol = sp.solve(eqs, [v_S, v_A, v_X])
    v_X_expr = sp.simplify(sol[v_X])
    if matched:
        v_X_expr = sp.simplify(
            v_X_expr.subs({g_m4: g_m3, r_o4: r_o3, g_m6: g_m5, r_o6: r_o5})
        )
    return v_X_expr

v_X_ota_gen = solve_5t_ota(v_in, 0, matched=False)
v_X_ota_matched = solve_5t_ota(v_in, 0, matched=True)
Av1_exact_matched = sp.simplify(v_X_ota_matched / v_in)

print("Exact 5T-OTA v_X/v_in (matched M3=M4, M5=M6):")
print(" ", sp.factor(Av1_exact_matched))

# High-gain asymptotic check (scale r_o -> r_o / eps and take eps -> 0 for ratio with g_m*r_o >> 1)
eps = sp.symbols("eps", positive=True)
Av1_scaled = sp.simplify(
    Av1_exact_matched.subs({r_o3: r_o3 / eps, r_o5: r_o5 / eps}) * eps
)
Av1_asymp = sp.limit(Av1_scaled, eps, 0) / eps
# Wait: easier: divide by (r_o3*r_o5/(r_o3+r_o5)) and let r_o -> oo via eps
par_35 = (r_o3 * r_o5) / (r_o3 + r_o5)
ratio_to_textbook = sp.simplify(
    (Av1_exact_matched / (-g_m3 * par_35)).subs({r_o3: r_o3 / eps, r_o5: r_o5 / eps})
)
limit_ratio = sp.limit(ratio_to_textbook, eps, 0)
print("Ratio Av1_exact / (-g_m3*(r_o3||r_o5)) as g_m*r_o -> oo:", limit_ratio)
assert limit_ratio == 1

# Also check common-mode gain A_cm and differential gain A_dm of matched 5T-OTA
v_cm, v_dm = sp.symbols("v_cm v_dm")
v_X_cm = solve_5t_ota(v_cm, v_cm, matched=True)
A_cm_exact = sp.simplify(v_X_cm / v_cm)
v_X_dm = solve_5t_ota(v_dm / 2, -v_dm / 2, matched=True)
A_dm_exact = sp.simplify(v_X_dm / v_dm)
print("Matched 5T-OTA exact A_dm:", sp.factor(A_dm_exact))
print("Matched 5T-OTA exact A_cm:", sp.factor(A_cm_exact))
print(
    "A_cm asymptotic order (r_o -> r_o/eps as eps->0):",
    sp.series(A_cm_exact.subs({r_o3: r_o3 / eps, r_o5: r_o5 / eps}), eps, 0, 2),
)

# ---------------------------------------------------------------------------
# 2. Stage 2 (PMOS M1 Common-Source with r_o1 driving R_L + R_M)
# ---------------------------------------------------------------------------
v_X_sym, v_D1_ol = sp.symbols("v_X_sym v_D1_ol")
# M1 (PMOS, S=VDD=0, G=X, D=D1): downward current from S to D1 is g_m1*(0 - v_X) + (0 - v_D1)/r_o1
# KCL at D1 with load (R_L + R_M) to ground: g_m1*(-v_X) - v_D1/r_o1 = v_D1/(R_L + R_M)
sol_m1 = sp.solve([g_m1 * (-v_X_sym) - v_D1_ol / r_o1 - v_D1_ol / (R_L + R_M)], [v_D1_ol])
i_out_m1 = sp.simplify(sol_m1[v_D1_ol] / (R_L + R_M))
Gm2_eff = sp.simplify(i_out_m1 / v_X_sym)
print("\nStage 2 (I_out / V_X):", sp.factor(Gm2_eff))
assert sp.simplify(Gm2_eff - (-g_m1 * r_o1 / (r_o1 + R_L + R_M))) == 0

# Standard high-gain 2-port feedback open-loop parameters (matching Razavi / exam key):
Av1_std = -g_m3 * par_35
A_open_std = sp.simplify(Av1_std * Gm2_eff)
A_open_exact_ota = sp.simplify(Av1_exact_matched * Gm2_eff)

print("A_open (standard OTA gain):", sp.factor(A_open_std))
print("R_in_open: oo (MOSFET gate draws 0 current)")
print("R_in_closed: oo (MOSFET gate draws 0 current)")

# R_out_open (test source V_t, I_t across Laser port between D1 and V_F; v_in=0, V_G4=0 -> v_X=0)
V_t, I_t, v_D1_t, v_F_t = sp.symbols("V_t I_t v_D1_t v_F_t")
sol_rout_ol = sp.solve(
    [I_t + g_m1 * 0 - v_D1_t / r_o1, -I_t - v_F_t / R_M, V_t - (v_D1_t - v_F_t)],
    [v_D1_t, v_F_t, V_t],
)
R_out_open = sp.simplify(sol_rout_ol[V_t] / I_t)
print("R_out_open (seen by Laser):", R_out_open)
assert sp.simplify(R_out_open - (r_o1 + R_M)) == 0

# Feedback factor K = V_F / I_out = R_M
K = R_M
T_std = sp.simplify(K * A_open_std)
T_0_std = sp.simplify(T_std.subs(R_L, 0))
T_exact_ota = sp.simplify(K * A_open_exact_ota)
T_0_exact_ota = sp.simplify(T_exact_ota.subs(R_L, 0))

# Direct loop-break verification at M4 gate (v_in = 0, inject v_test at M4 gate, measure returned v_F)
v_test, v_D1_lg, v_F_lg = sp.symbols("v_test v_D1_lg v_F_lg")
v_X_lg = solve_5t_ota(0, v_test, matched=True)
sol_lg = sp.solve(
    [
        g_m1 * (-v_X_lg) - v_D1_lg / r_o1 - (v_D1_lg - v_F_lg) / R_L,
        (v_D1_lg - v_F_lg) / R_L - v_F_lg / R_M,
    ],
    [v_D1_lg, v_F_lg],
)
L_return = sp.simplify(sol_lg[v_F_lg] / v_test)
assert sp.simplify(L_return + T_exact_ota) == 0

print("Feedback factor K:", K)
print("Direct loop return v_F/v_test (exact OTA) == -T_exact_ota verified.")
print("Loop gain T (std):", sp.factor(T_std))
print("Loop gain T_0 (std, R_L=0):", sp.factor(T_0_std))

# 2-port closed-loop formulas (standard)
A_closed_2p_std = sp.simplify(A_open_std / (1 + T_std))
R_out_closed_2p_std = sp.simplify(R_out_open * (1 + T_0_std))

# Also note what happens if A_open (with R_L != 0) were wrongly used in R_out_closed:
R_out_closed_wrong_RL = sp.simplify(R_out_open * (1 + T_std))

print("\n--- 2-Port Closed-Loop (Standard OTA) ---")
print("A_closed (std 2-port):          ", sp.factor(A_closed_2p_std))
print("R_out_closed (std 2-port, T_0): ", sp.simplify(R_out_closed_2p_std))

# ---------------------------------------------------------------------------
# 3. Exact Full-Circuit Closed-Loop KCL (including exact 5T-OTA A_cm & finite g_m*r_O)
# ---------------------------------------------------------------------------
v_F_cl, v_D1_cl = sp.symbols("v_F_cl v_D1_cl")
v_X_cl_expr = solve_5t_ota(v_in, v_F_cl, matched=True)
sol_cl_full = sp.solve(
    [
        g_m1 * (-v_X_cl_expr) - v_D1_cl / r_o1 - (v_D1_cl - v_F_cl) / R_L,
        (v_D1_cl - v_F_cl) / R_L - v_F_cl / R_M,
    ],
    [v_D1_cl, v_F_cl],
)
i_out_cl_exact = sp.simplify((sol_cl_full[v_D1_cl] - sol_cl_full[v_F_cl]) / R_L)
A_closed_exact_full = sp.simplify(i_out_cl_exact / v_in)

# Exact closed-loop output impedance (replace Laser with V_t, I_t; v_in = 0)
v_F_ro, v_D1_ro = sp.symbols("v_F_ro v_D1_ro")
v_X_ro_expr = solve_5t_ota(0, v_F_ro, matched=True)
sol_rout_cl_full = sp.solve(
    [
        I_t + g_m1 * (-v_X_ro_expr) - v_D1_ro / r_o1,
        -I_t - v_F_ro / R_M,
        V_t - (v_D1_ro - v_F_ro),
    ],
    [v_D1_ro, v_F_ro, V_t],
)
R_out_closed_exact_full = sp.simplify(sol_rout_cl_full[V_t] / I_t)

# Compare R_out_closed_exact_full with 2-port formula using exact v_X/v_F = A_dm - A_cm/2?
# Note: with v_in=0 and v_G4=v_F, v_X / v_F = -A_dm + A_cm/2!
Av_from_VF_exact = sp.simplify(solve_5t_ota(0, v_F_ro, matched=True) / v_F_ro)
T0_from_VF = sp.simplify(R_M * (Av_from_VF_exact) * (g_m1 * r_o1 / (r_o1 + R_M)))
# Note sign: v_F > 0 -> v_X > 0 -> i_out drops, so return ratio using v_G4 sensitivity is +T0_from_VF
R_out_closed_from_VF = sp.simplify((r_o1 + R_M) * (1 + T0_from_VF))
assert sp.simplify(R_out_closed_exact_full - R_out_closed_from_VF) == 0

# Compare A_closed_exact_full and R_out_closed_exact_full to standard 2-port results in g_m*r_o >> 1 limit:
ratio_A_cl = sp.simplify(
    (A_closed_exact_full / A_closed_2p_std).subs({r_o3: r_o3 / eps, r_o5: r_o5 / eps, r_o1: r_o1 / eps})
)
ratio_Rout_cl = sp.simplify(
    (R_out_closed_exact_full / R_out_closed_2p_std).subs({r_o3: r_o3 / eps, r_o5: r_o5 / eps, r_o1: r_o1 / eps})
)
print("\n--- Exact Full-Circuit KCL vs Standard 2-Port ---")
print("A_closed_exact / A_closed_std (g_m*r_o -> oo):", sp.limit(ratio_A_cl, eps, 0))
print("R_out_closed_exact / R_out_closed_std (g_m*r_o -> oo):", sp.limit(ratio_Rout_cl, eps, 0))
print(
    "Asymptotic check of R_out_closed_exact (r_o -> oo at 1st order in 1/eps):",
    sp.limit(
        (R_out_closed_exact_full / R_out_closed_2p_std).subs(
            {r_o3: r_o3 / eps, r_o5: r_o5 / eps}
        ),
        eps,
        0,
    ),
)
assert sp.limit(ratio_A_cl, eps, 0) == 1
assert sp.limit(ratio_Rout_cl, eps, 0) == 1
assert sp.simplify(R_out_closed_wrong_RL - R_out_closed_2p_std) != 0
print("Confirmed: R_out_closed uses T_0 (R_L = 0), NOT T(R_L != 0).")
print("ALL P2 CHECKS PASSED.")
