import sympy as sp


def par(a, b):
    return (a * b) / (a + b)


def main():
    I_in, g_m1, g_m2, R_D, R_M, R_F = sp.symbols(
        "I_in g_m1 g_m2 R_D R_M R_F", positive=True
    )
    V_S1, V_X, V_out = sp.symbols("V_S1 V_X V_out")

    # 1. Open-loop circuit (2021-1_기말-Q3):
    # M1: NMOS CG with R_D drain load (lambda = 0)
    # M2: NMOS Source Follower (CD), drain at V_DD (AC GND), gate at X, source at V_out, R_M to GND (lambda = 0)
    eq_open = [
        sp.Eq(I_in, V_S1 / R_F + g_m1 * V_S1),
        sp.Eq(V_X / R_D - g_m1 * V_S1, 0),
        sp.Eq(V_out / R_M + V_out / R_F - g_m2 * (V_X - V_out), 0),
    ]
    sol_open = sp.solve(eq_open, [V_S1, V_X, V_out])

    V_X_kcl = sp.simplify(sol_open[V_X])
    R_0 = sp.simplify(sol_open[V_out] / I_in)

    # 2. Norton-to-Thevenin verification on input node:
    R_p = R_F
    V_in_th = I_in * R_p
    V_S1_th, V_X_th = sp.symbols("V_S1_th V_X_th")
    eq_th = [
        sp.Eq((V_in_th - V_S1_th) / R_p, g_m1 * V_S1_th),
        sp.Eq(V_X_th / R_D - g_m1 * V_S1_th, 0),
    ]
    sol_th = sp.solve(eq_th, [V_S1_th, V_X_th])
    V_X_thev = sp.simplify(sol_th[V_X_th])
    diff_thev = sp.simplify(V_X_kcl / I_in - V_X_thev / I_in)
    assert diff_thev == 0, f"Norton-Thevenin mismatch: {diff_thev}"

    # 3. Open-loop input & output impedances
    V_t, I_t = sp.symbols("V_t I_t")
    sol_rin = sp.solve([sp.Eq(I_t, V_t / R_F + g_m1 * V_t)], [I_t])
    R_in_open = sp.simplify(V_t / sol_rin[I_t])

    sol_rout = sp.solve([sp.Eq(I_t, V_t / R_M + V_t / R_F + g_m2 * V_t)], [I_t])
    R_out_open = sp.simplify(V_t / sol_rout[I_t])

    # 4. Feedback factor K
    V_1, I_2 = sp.symbols("V_1 I_2")
    sol_k = sp.solve([sp.Eq(I_2 + (V_1 - 0) / R_F, 0)], [I_2])
    K = sp.simplify(sol_k[I_2] / V_1)

    # 5. Loop gain and positive feedback verification: KR_0 = -T < 0, denom = 1 - T
    KR_0 = sp.simplify(K * R_0)
    T = sp.simplify(-KR_0)
    assert T.is_positive, f"Expected T > 0 for positive feedback, got T = {T}"
    assert KR_0.is_negative, f"Expected KR_0 < 0 for positive feedback, got KR_0 = {KR_0}"

    denom = sp.simplify(1 + KR_0)
    denom_1_minus_T = sp.simplify(1 - T)
    assert sp.simplify(denom - denom_1_minus_T) == 0

    R_closed = sp.simplify(R_0 / denom)
    R_in_closed = sp.simplify(R_in_open / denom)
    R_out_closed = sp.simplify(R_out_open / denom)

    # 6. Verify compact forms match sympy.solve identically
    R_L_out = par(R_M, R_F)
    A_v2 = g_m2 * R_L_out / (1 + g_m2 * R_L_out)
    R_0_compact = (g_m1 * R_F / (1 + g_m1 * R_F)) * R_D * A_v2
    R_in_open_compact = par(R_F, 1 / g_m1)
    R_out_open_compact = par(1 / g_m2, R_L_out)
    T_compact = (g_m1 * R_D / (1 + g_m1 * R_F)) * A_v2
    assert sp.simplify(R_0 - R_0_compact) == 0
    assert sp.simplify(R_in_open - R_in_open_compact) == 0
    assert sp.simplify(R_out_open - R_out_open_compact) == 0
    assert sp.simplify(K - (-1 / R_F)) == 0
    assert sp.simplify(T - T_compact) == 0
    assert sp.simplify(KR_0 - (-T_compact)) == 0

    # 7. Exact unbroken closed-loop KCL for comparison
    V_S1_ex, V_X_ex, V_out_ex = sp.symbols("V_S1_ex V_X_ex V_out_ex")
    eq_exact = [
        sp.Eq(I_in, (V_S1_ex - V_out_ex) / R_F + g_m1 * V_S1_ex),
        sp.Eq(V_X_ex / R_D - g_m1 * V_S1_ex, 0),
        sp.Eq(V_out_ex / R_M + (V_out_ex - V_S1_ex) / R_F - g_m2 * (V_X_ex - V_out_ex), 0),
    ]
    sol_exact = sp.solve(eq_exact, [V_S1_ex, V_X_ex, V_out_ex])
    R_closed_exact = sp.simplify(sol_exact[V_out_ex] / I_in)
    R_in_exact = sp.simplify(sol_exact[V_S1_ex] / I_in)

    eq_ro_exact = [
        sp.Eq(0, (V_S1_ex - V_t) / R_F + g_m1 * V_S1_ex),
        sp.Eq(V_X_ex / R_D - g_m1 * V_S1_ex, 0),
        sp.Eq(I_t, V_t / R_M + (V_t - V_S1_ex) / R_F - g_m2 * (V_X_ex - V_t)),
    ]
    sol_ro_exact = sp.solve(eq_ro_exact, [V_S1_ex, V_X_ex, I_t])
    R_out_exact = sp.simplify(V_t / sol_ro_exact[I_t])

    subs_num = {g_m1: 1e-3, g_m2: 2e-3, R_D: 500.0, R_M: 5e3, R_F: 10e3}

    print("=== p9: 2021-1_기말-Q3 (NMOS Source Follower M2, positive feedback, lambda = 0) ===")
    print(f"V_X/I_in (direct KCL)      = {sp.simplify(V_X_kcl / I_in)}")
    print(f"V_X/I_in (Norton->Thevenin)= {sp.simplify(V_X_thev / I_in)}")
    print(f"diff(KCL - Thevenin)       = {diff_thev}")
    print(f"R_0 (open-loop transimp)   = {R_0}")
    print(f"R_in_open                  = {R_in_open}")
    print(f"R_out_open                 = {R_out_open}")
    print(f"[Part 1] K                 = {K}")
    print(f"KR_0 = -T                  = {KR_0}")
    print(f"T = -KR_0 (> 0 verified)   = {T}")
    print(f"1 + KR_0 = 1 - T           = {sp.factor(denom)}")
    print(f"[Part 1] R_closed          = {R_closed}")
    print(f"[Part 2] R_in_closed       = {R_in_closed}")
    print(f"[Part 2] R_out_closed      = {R_out_closed}")
    print("Compact textbook form & positive feedback assertions: ALL PASSED (diff == 0)")
    print("--- Exact unbroken KCL comparison ---")
    print(f"R_closed_exact             = {R_closed_exact}")
    print(f"R_in_exact                 = {R_in_exact}")
    print(f"R_out_exact                = {R_out_exact}")
    print(
        f"Numeric check (gm1=1m,gm2=2m,RD=500,RM=5k,RF=10k): "
        f"KR_0={float(KR_0.subs(subs_num)):.4f}, T={float(T.subs(subs_num)):.4f}, "
        f"R_closed_fb={float(R_closed.subs(subs_num)):.2f}, "
        f"R_closed_exact={float(R_closed_exact.subs(subs_num)):.2f}"
    )


if __name__ == "__main__":
    main()
