import sympy as sp


def par2(a, b):
    return (a * b) / (a + b)


def par3(a, b, c):
    return 1 / (1 / a + 1 / b + 1 / c)


def main():
    I_in, g_m, r_pi, r_O, R_C, R_F = sp.symbols(
        "I_in g_m r_pi r_O R_C R_F", positive=True
    )
    beta = sp.symbols("beta", positive=True)
    V_B, V_out = sp.symbols("V_B V_out")

    # 1. Open-loop circuit (P12.49, Fig. 12.112):
    eq_open = [
        sp.Eq(I_in, V_B / r_pi + V_B / R_F),
        sp.Eq(V_out / R_C + V_out / r_O + V_out / R_F + g_m * V_B, 0),
    ]
    sol_open = sp.solve(eq_open, [V_B, V_out])
    R_0 = sp.simplify(sol_open[V_out] / I_in)

    # 2. Open-loop input & output impedances
    V_t, I_t = sp.symbols("V_t I_t")
    sol_rin = sp.solve([sp.Eq(I_t, V_t / r_pi + V_t / R_F)], [I_t])
    R_in_open = sp.simplify(V_t / sol_rin[I_t])

    sol_rout = sp.solve([sp.Eq(I_t, V_t / R_C + V_t / r_O + V_t / R_F)], [I_t])
    R_out_open = sp.simplify(V_t / sol_rout[I_t])

    # 3. Feedback factor K
    V_1, I_2 = sp.symbols("V_1 I_2")
    sol_k = sp.solve([sp.Eq(I_2 + (V_1 - 0) / R_F, 0)], [I_2])
    K = sp.simplify(sol_k[I_2] / V_1)

    # 4. Loop gain and closed-loop quantities
    KR_0 = sp.simplify(K * R_0)
    denom = sp.simplify(1 + KR_0)
    R_closed = sp.simplify(R_0 / denom)
    R_in_closed = sp.simplify(R_in_open / denom)
    R_out_closed = sp.simplify(R_out_open / denom)

    # 5. Verify compact parallel forms match sympy.solve identically
    R_in_open_compact = par2(r_pi, R_F)
    R_out_open_compact = par3(r_O, R_C, R_F)
    R_0_compact = -g_m * R_in_open_compact * R_out_open_compact
    KR_0_compact = (g_m * r_pi / (r_pi + R_F)) * R_out_open_compact
    assert sp.simplify(R_in_open - R_in_open_compact) == 0
    assert sp.simplify(R_out_open - R_out_open_compact) == 0
    assert sp.simplify(R_0 - R_0_compact) == 0
    assert sp.simplify(K - (-1 / R_F)) == 0
    assert sp.simplify(KR_0 - KR_0_compact) == 0

    R_0_beta = sp.simplify(R_0.subs(g_m, beta / r_pi))
    KR_0_beta = sp.simplify(KR_0.subs(g_m, beta / r_pi))
    R_closed_beta = sp.simplify(R_closed.subs(g_m, beta / r_pi))

    # 6. Exact unbroken closed-loop KCL for comparison
    V_B_ex, V_out_ex = sp.symbols("V_B_ex V_out_ex")
    eq_exact = [
        sp.Eq(I_in, V_B_ex / r_pi + (V_B_ex - V_out_ex) / R_F),
        sp.Eq(V_out_ex / R_C + V_out_ex / r_O + (V_out_ex - V_B_ex) / R_F + g_m * V_B_ex, 0),
    ]
    sol_exact = sp.solve(eq_exact, [V_B_ex, V_out_ex])
    R_closed_exact = sp.simplify(sol_exact[V_out_ex] / I_in)
    R_in_exact = sp.simplify(sol_exact[V_B_ex] / I_in)

    eq_ro_exact = [
        sp.Eq(0, V_B_ex / r_pi + (V_B_ex - V_t) / R_F),
        sp.Eq(I_t, V_t / R_C + V_t / r_O + (V_t - V_B_ex) / R_F + g_m * V_B_ex),
    ]
    sol_ro_exact = sp.solve(eq_ro_exact, [V_B_ex, I_t])
    R_out_exact = sp.simplify(V_t / sol_ro_exact[I_t])

    subs_num = {g_m: 1 / 26.0, r_pi: 2600.0, r_O: 100e3, R_C: 5e3, R_F: 20e3}

    print("=== p10: P12.49 (Fig. 12.112, BJT Shunt-Shunt TIA, V_A < inf) ===")
    print(f"R_0 (open-loop transimp)   = {R_0}")
    print(f"R_0 (using beta=g_m*r_pi)  = {R_0_beta}")
    print(f"R_in_open                  = {R_in_open}")
    print(f"R_out_open                 = {R_out_open}")
    print(f"K                          = {K}")
    print(f"KR_0 (loop gain)           = {KR_0}")
    print(f"KR_0 (using beta=g_m*r_pi) = {KR_0_beta}")
    print(f"1 + KR_0                   = {sp.factor(denom)}")
    print(f"R_closed (feedback)        = {R_closed}")
    print(f"R_closed (beta form)       = {R_closed_beta}")
    print(f"R_in_closed (feedback)     = {R_in_closed}")
    print(f"R_out_closed (feedback)    = {R_out_closed}")
    print("Compact parallel-combination assertions: ALL PASSED (diff == 0)")
    print("--- Exact unbroken KCL comparison ---")
    print(f"R_closed_exact             = {R_closed_exact}")
    print(f"R_in_exact                 = {R_in_exact}")
    print(f"R_out_exact                = {R_out_exact}")
    print(
        f"Numeric check (gm=38.46m,rpi=2.6k,rO=100k,RC=5k,RF=20k): "
        f"KR_0={float(KR_0.subs(subs_num)):.4f}, "
        f"R_closed_fb={float(R_closed.subs(subs_num)):.2f}, "
        f"R_closed_exact={float(R_closed_exact.subs(subs_num)):.2f}"
    )


if __name__ == "__main__":
    main()
