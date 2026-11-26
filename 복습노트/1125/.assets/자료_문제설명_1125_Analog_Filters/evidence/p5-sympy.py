import sympy as sp

sp.init_printing()

# Symbols
g_m1, g_m2 = sp.symbols("g_m1 g_m2", positive=True)
r_o2, R_D, R_F, R_M = sp.symbols("r_o2 R_D R_F R_M", positive=True)
I_in = sp.symbols("I_in")

def par(a, b):
    return (a * b) / (a + b)

def par3(a, b, c):
    return 1 / (1 / a + 1 / b + 1 / c)

print("=== P5 (Example 12.33, Fig 12.62(a)): Voltage-Current Feedback ===")

# ---------------------------------------------------------------------------
# 1. Input stage open-loop (Fig 12.62(b)): Norton-to-Thevenin vs Direct KCL
# Return replica input port (V_out) shorted to ground -> R_F from S1 to ground
# ---------------------------------------------------------------------------
V_th = I_in * R_F
I_s1_thev = V_th / (R_F + 1 / g_m1)
VX_over_Iin_thev = sp.simplify((I_s1_thev * R_D) / I_in)

v_S1_ol, v_X_ol = sp.symbols("v_S1_ol v_X_ol")
sol_in_kcl = sp.solve(
    [
        I_in - v_S1_ol / R_F - g_m1 * v_S1_ol,
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
assert sp.simplify(R_in_open - par(1 / g_m1, R_F)) == 0
print("R_in_open (eq 12.176):", sp.factor(R_in_open))

# ---------------------------------------------------------------------------
# 2. Output stage open-loop (finite r_o2 and r_o2 -> oo limit)
# Sense replica output port (S1) shorted to ground -> R_F || R_M at V_out
# ---------------------------------------------------------------------------
v_X_sym, v_out_ol = sp.symbols("v_X_sym v_out_ol")
sol_out_ol = sp.solve(
    [g_m2 * (0 - v_X_sym) - v_out_ol / r_o2 - v_out_ol / R_M - v_out_ol / R_F],
    [v_out_ol],
)
Vout_over_VX_ol = sp.simplify(sol_out_ol[v_out_ol] / v_X_sym)
R_O_finite = sp.simplify(VX_over_Iin_kcl * Vout_over_VX_ol)
R_O_inf = sp.limit(R_O_finite, r_o2, sp.oo)
eq12_175 = (R_F * R_D / (R_F + 1 / g_m1)) * (-g_m2 * par(R_F, R_M))
assert sp.simplify(R_O_inf - eq12_175) == 0

# Open-loop output impedance (test current I_X into V_out, I_in=0 => V_X=0, S1 shorted)
I_X, v_out_t = sp.symbols("I_X v_out_t")
sol_rout_ol = sp.solve(
    [I_X - v_out_t / r_o2 - v_out_t / R_M - v_out_t / R_F],
    [v_out_t],
)
R_out_open_finite = sp.simplify(sol_rout_ol[v_out_t] / I_X)
R_out_open_inf = sp.limit(R_out_open_finite, r_o2, sp.oo)
assert sp.simplify(R_out_open_finite - par3(r_o2, R_F, R_M)) == 0
assert sp.simplify(R_out_open_inf - par(R_F, R_M)) == 0

# Feedback factor K (voltage-current feedback: V_1 at output, I_2 at shorted S1 => K = I_2/V_1 = -1/R_F)
V_1_fb, I_2_fb = sp.symbols("V_1_fb I_2_fb")
# With S1 shorted (V_2 = 0) and V_1 applied at output node: current I_2 enters S1 from R_F => I_2 + (0 - V_1)/R_F?
# Wait: current leaving shorted S1 into R_F is (0 - V_1)/R_F = -V_1/R_F
sol_fb = sp.solve([I_2_fb - (0 - V_1_fb) / R_F], [I_2_fb])
K = sp.simplify(sol_fb[I_2_fb] / V_1_fb)
assert sp.simplify(K - (-1 / R_F)) == 0
T_finite = sp.simplify(K * R_O_finite)  # -R_O / R_F > 0
T_inf = sp.limit(T_finite, r_o2, sp.oo)

# 2-port closed-loop formulas (finite r_o2 and r_o2 -> oo)
R_closed_2p_finite = sp.simplify(R_O_finite / (1 + T_finite))
R_in_closed_2p_finite = sp.simplify(R_in_open / (1 + T_finite))
R_out_closed_2p_finite = sp.simplify(R_out_open_finite / (1 + T_finite))

R_closed_2p_inf = sp.simplify(sp.limit(R_closed_2p_finite, r_o2, sp.oo))
R_in_closed_2p_inf = sp.simplify(sp.limit(R_in_closed_2p_finite, r_o2, sp.oo))
R_out_closed_2p_inf = sp.simplify(sp.limit(R_out_closed_2p_finite, r_o2, sp.oo))

assert sp.simplify(R_closed_2p_inf - eq12_175 / (1 - eq12_175 / R_F)) == 0
assert sp.simplify(R_in_closed_2p_inf - par(1 / g_m1, R_F) / (1 - eq12_175 / R_F)) == 0
assert sp.simplify(R_out_closed_2p_inf - par(R_F, R_M) / (1 - eq12_175 / R_F)) == 0

print("\n--- 2-Port Feedback Results (finite r_o2 & r_o2 -> oo limit) ---")
print("R_O (finite r_o2):          ", sp.factor(R_O_finite))
print("R_O (r_o2 -> oo, eq 12.175):", sp.factor(R_O_inf))
print("R_out_open (finite r_o2):   ", sp.factor(R_out_open_finite))
print("R_out_open (r_o2 -> oo):    ", sp.factor(R_out_open_inf))
print("K (eq 12.180):              ", K)
print("T (finite r_o2):            ", sp.factor(T_finite))
print("T (r_o2 -> oo, = T_0):      ", sp.factor(T_inf))
print("R_closed (finite r_o2):     ", sp.factor(R_closed_2p_finite))
print("R_in_closed (finite r_o2):  ", sp.factor(R_in_closed_2p_finite))
print("R_out_closed (finite r_o2): ", sp.factor(R_out_closed_2p_finite))
print("R_closed (r_o2 -> oo):      ", sp.factor(R_closed_2p_inf))
print("R_in_closed (r_o2 -> oo):   ", sp.factor(R_in_closed_2p_inf))
print("R_out_closed (r_o2 -> oo):  ", sp.factor(R_out_closed_2p_inf))

# ---------------------------------------------------------------------------
# 3. Exact Full-Circuit KCL (finite r_o2 and r_o2 -> oo limit)
# ---------------------------------------------------------------------------
v_S1, v_X, v_out = sp.symbols("v_S1 v_X v_out")
sol_exact = sp.solve(
    [
        I_in - g_m1 * v_S1 - (v_S1 - v_out) / R_F,
        v_X / R_D - g_m1 * v_S1,
        g_m2 * (0 - v_X) - v_out / r_o2 - v_out / R_M - (v_out - v_S1) / R_F,
    ],
    [v_S1, v_X, v_out],
)
R_closed_exact_finite = sp.simplify(sol_exact[v_out] / I_in)
R_in_closed_exact_finite = sp.simplify(sol_exact[v_S1] / I_in)

# Exact R_out_closed (I_in = 0, test current I_X injected into V_out)
v_S1_o, v_X_o, v_out_o = sp.symbols("v_S1_o v_X_o v_out_o")
sol_rout_exact = sp.solve(
    [
        0 - g_m1 * v_S1_o - (v_S1_o - v_out_o) / R_F,
        v_X_o / R_D - g_m1 * v_S1_o,
        I_X + g_m2 * (0 - v_X_o) - v_out_o / r_o2 - v_out_o / R_M - (v_out_o - v_S1_o) / R_F,
    ],
    [v_S1_o, v_X_o, v_out_o],
)
R_out_closed_exact_finite = sp.simplify(sol_rout_exact[v_out_o] / I_X)

R_closed_exact_inf = sp.limit(R_closed_exact_finite, r_o2, sp.oo)
R_in_closed_exact_inf = sp.limit(R_in_closed_exact_finite, r_o2, sp.oo)
R_out_closed_exact_inf = sp.limit(R_out_closed_exact_finite, r_o2, sp.oo)

print("\n--- Exact Full-Circuit KCL (finite r_o2 & r_o2 -> oo) ---")
print("R_closed (exact, finite r_o2):    ", sp.factor(R_closed_exact_finite))
print("R_closed (exact, r_o2 -> oo):     ", sp.factor(R_closed_exact_inf))
print("R_in_closed (exact, r_o2 -> oo):  ", sp.factor(R_in_closed_exact_inf))
print("R_out_closed (exact, r_o2 -> oo): ", sp.factor(R_out_closed_exact_inf))

print("\nBilateral R_F forward feedthrough (y_12 = -1/R_F) differences (r_o2 -> oo):")
print("  R_closed_exact - R_closed_2p:    ", sp.factor(sp.simplify(R_closed_exact_inf - R_closed_2p_inf)))
print("  R_in_closed_exact - R_in_closed_2p:", sp.factor(sp.simplify(R_in_closed_exact_inf - R_in_closed_2p_inf)))
print("  R_out_closed_exact - R_out_closed_2p:", sp.factor(sp.simplify(R_out_closed_exact_inf - R_out_closed_2p_inf)))
print("ALL P5 CHECKS PASSED.")
