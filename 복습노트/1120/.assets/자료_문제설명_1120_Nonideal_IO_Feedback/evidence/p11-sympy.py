import sympy as sp


def par(a, b):
    return (a * b) / (a + b)


def main():
    i_in, g_m1, g_m2, r_O1, r_O2, R_D1, R_1, R_2, R_F = sp.symbols(
        "i_in g_m1 g_m2 r_O1 r_O2 R_D1 R_1 R_2 R_F", positive=True
    )
    v_S1, v_X, v_out = sp.symbols("v_S1 v_X v_out")

    # Returning replica at input (Port 1 at v_out shorted to GND): R_p = R_F + (R_1 || R_2)
    R_p = sp.simplify(R_F + par(R_1, R_2))

    # Sensing replica at output (Port 2 at S1 shorted to GND): R_fb_out = R_1 + (R_2 || R_F)
    R_fb_out = sp.simplify(R_1 + par(R_2, R_F))

    # 1. Exact lambda > 0 CG input resistance R_S1 looking into source of M1 (drain loaded by R_D1):
    v_t, i_t, v_X_t = sp.symbols("v_t i_t v_X_t")
    eq_rs1 = [
        sp.Eq(i_t, g_m1 * v_t + (v_t - v_X_t) / r_O1),
        sp.Eq(v_X_t / R_D1, i_t),
    ]
    sol_rs1 = sp.solve(eq_rs1, [i_t, v_X_t])
    R_S1_exact = sp.simplify(v_t / sol_rs1[i_t])
    R_S1_expected = sp.simplify((r_O1 + R_D1) / (1 + g_m1 * r_O1))
    assert sp.simplify(R_S1_exact - R_S1_expected) == 0

    # Verify g_m1*r_O1 >> 1 approximation: R_S1 ≈ (1/g_m1)*(1 + R_D1/r_O1)
    R_S1_approx = sp.simplify((1 / g_m1) * (1 + R_D1 / r_O1))
    eps = sp.symbols("eps", positive=True)  # eps = 1/(g_m1 * r_O1)
    ratio_rs1 = sp.simplify((R_S1_exact / R_S1_approx).subs(g_m1, 1 / (eps * r_O1)))
    assert sp.limit(ratio_rs1, eps, 0) == 1
    rel_err_series = sp.series(ratio_rs1, eps, 0, n=3)

    # 2. Open-loop circuit KCL (with R_p at S1, lambda > 0 for M1 and M2, R_fb_out at v_out):
    eq_open = [
        sp.Eq(i_in, v_S1 / R_p + g_m1 * v_S1 + (v_S1 - v_X) / r_O1),
        sp.Eq(v_X / R_D1 - g_m1 * v_S1 - (v_S1 - v_X) / r_O1, 0),
        sp.Eq(v_out / r_O2 + v_out / R_fb_out + g_m2 * v_X, 0),
    ]
    sol_open = sp.solve(eq_open, [v_S1, v_X, v_out])
    v_X_kcl = sp.simplify(sol_open[v_X])
    R_0 = sp.simplify(sol_open[v_out] / i_in)

    # 3. Norton-to-Thevenin verification on input node:
    V_in_th = i_in * R_p
    v_S1_th, v_X_th = sp.symbols("v_S1_th v_X_th")
    eq_th = [
        sp.Eq((V_in_th - v_S1_th) / R_p, g_m1 * v_S1_th + (v_S1_th - v_X_th) / r_O1),
        sp.Eq(v_X_th / R_D1 - g_m1 * v_S1_th - (v_S1_th - v_X_th) / r_O1, 0),
    ]
    sol_th = sp.solve(eq_th, [v_S1_th, v_X_th])
    v_X_thev = sp.simplify(sol_th[v_X_th])
    diff_thev = sp.simplify(v_X_kcl / i_in - v_X_thev / i_in)
    assert diff_thev == 0, f"Norton-Thevenin mismatch: {diff_thev}"

    # 4. Open-loop input & output impedances
    eq_rin = [
        sp.Eq(i_t, v_t / R_p + g_m1 * v_t + (v_t - v_X_t) / r_O1),
        sp.Eq(v_X_t / R_D1 - g_m1 * v_t - (v_t - v_X_t) / r_O1, 0),
    ]
    sol_rin = sp.solve(eq_rin, [i_t, v_X_t])
    R_in_open = sp.simplify(v_t / sol_rin[i_t])

    sol_rout = sp.solve([sp.Eq(i_t, v_t / r_O2 + v_t / R_fb_out)], [i_t])
    R_out_open = sp.simplify(v_t / sol_rout[i_t])

    # 5. Feedback factor K
    V_1, V_Y, I_2 = sp.symbols("V_1 V_Y I_2")
    eq_k = [
        sp.Eq((V_Y - V_1) / R_1 + V_Y / R_2 + V_Y / R_F, 0),
        sp.Eq(I_2, (0 - V_Y) / R_F),
    ]
    sol_k = sp.solve(eq_k, [V_Y, I_2])
    K = sp.simplify(sol_k[I_2] / V_1)

    # 6. Loop gain and closed-loop quantities (exact lambda > 0)
    KR_0 = sp.simplify(K * R_0)
    denom = sp.simplify(1 + KR_0)
    R_closed = sp.simplify(R_0 / denom)
    R_in_closed = sp.simplify(R_in_open / denom)
    R_out_closed = sp.simplify(R_out_open / denom)

    # 7. Compact structural assertions with N = R_1*R_2 + R_1*R_F + R_2*R_F
    N = R_1 * R_2 + R_1 * R_F + R_2 * R_F
    assert sp.simplify(R_p - N / (R_1 + R_2)) == 0
    assert sp.simplify(R_fb_out - N / (R_2 + R_F)) == 0
    assert sp.simplify(K - (-R_2 / N)) == 0
    assert sp.simplify(R_in_open - par(R_p, R_S1_exact)) == 0
    assert sp.simplify(R_out_open - par(r_O2, R_fb_out)) == 0
    assert sp.simplify(v_X_kcl / i_in - (R_p * R_D1) / (R_p + R_S1_exact)) == 0
    assert sp.simplify(R_0 - (-g_m2 * R_out_open * R_p * R_D1 / (R_p + R_S1_exact))) == 0

    # Approximate forms with R_S1 -> R_S1_approx = (1/g_m1)*(1 + R_D1/r_O1)
    R_in_open_approx = sp.simplify(par(R_p, R_S1_approx))
    R_0_approx = sp.simplify(-g_m2 * R_out_open * R_p * R_D1 / (R_p + R_S1_approx))
    KR_0_approx = sp.simplify(K * R_0_approx)

    # 8. Exact unbroken closed-loop KCL for comparison
    v_S1_ex, v_X_ex, v_Y_ex, v_out_ex = sp.symbols("v_S1_ex v_X_ex v_Y_ex v_out_ex")
    eq_exact = [
        sp.Eq(i_in, (v_S1_ex - v_Y_ex) / R_F + g_m1 * v_S1_ex + (v_S1_ex - v_X_ex) / r_O1),
        sp.Eq(v_X_ex / R_D1 - g_m1 * v_S1_ex - (v_S1_ex - v_X_ex) / r_O1, 0),
        sp.Eq((v_Y_ex - v_out_ex) / R_1 + v_Y_ex / R_2 + (v_Y_ex - v_S1_ex) / R_F, 0),
        sp.Eq(v_out_ex / r_O2 + (v_out_ex - v_Y_ex) / R_1 + g_m2 * v_X_ex, 0),
    ]
    sol_exact = sp.solve(eq_exact, [v_S1_ex, v_X_ex, v_Y_ex, v_out_ex])
    R_closed_exact = sp.simplify(sol_exact[v_out_ex] / i_in)

    subs_num = {
        g_m1: 2e-3,
        g_m2: 2e-3,
        r_O1: 50e3,
        r_O2: 50e3,
        R_D1: 10e3,
        R_1: 5e3,
        R_2: 5e3,
        R_F: 10e3,
    }

    print("=== p11: P12.47 (Fig. 12.110, lambda > 0, divider feedback) ===")
    print("Let N = R_1*R_2 + R_1*R_F + R_2*R_F")
    print(f"R_p = R_F + R_1||R_2       = {R_p} = N / (R_1 + R_2)")
    print(f"R_fb_out = R_1 + R_2||R_F  = {R_fb_out} = N / (R_2 + R_F)")
    print(f"R_S1 (exact lambda > 0)    = {R_S1_exact}")
    print(f"R_S1 (gm1*rO1>>1 approx)   = {R_S1_approx}")
    print(f"R_S1_exact/R_S1_approx(eps)= {rel_err_series}  (eps = 1/(g_m1*r_O1))")
    print(f"V_X/i_in (direct KCL)      = {sp.simplify(v_X_kcl / i_in)}")
    print(f"V_X/i_in (Norton->Thevenin)= {sp.simplify(v_X_thev / i_in)}")
    print(f"diff(KCL - Thevenin)       = {diff_thev}")
    print(f"R_in_open (exact)          = {R_in_open} = R_p || R_S1_exact")
    print(f"R_in_open (approx R_S1)    = {R_in_open_approx}")
    print(f"R_out_open                 = {R_out_open} = r_O2 || R_fb_out")
    print(f"R_0 (exact)                = -g_m2 * R_out_open * R_p * R_D1 / (R_p + R_S1_exact)")
    print(f"R_0 (exact expanded)       = {R_0}")
    print(f"R_0 (approx R_S1)          = {R_0_approx}")
    print(f"K                          = {K} = -R_2 / N")
    print(f"KR_0 (exact)               = {KR_0}")
    print(f"KR_0 (approx R_S1)         = {KR_0_approx}")
    print(f"1 + KR_0                   = {sp.factor(denom)}")
    print("Closed-loop feedback equations (exact lambda > 0, verified via sympy.solve):")
    print("  R_closed     = R_0 / (1 + KR_0)")
    print("  R_in_closed  = R_in_open / (1 + KR_0)")
    print("  R_out_closed = R_out_open / (1 + KR_0)")
    print(f"R_closed (feedback exact)  = {R_closed}")
    print(f"R_in_closed (fb exact)     = {R_in_closed}")
    print(f"R_out_closed (fb exact)    = {R_out_closed}")
    print("Compact structural & N-factor assertions: ALL PASSED (diff == 0)")
    print("--- Exact unbroken KCL comparison ---")
    print(f"R_closed_exact             = {R_closed_exact}")
    print(
        f"Numeric check (gm1=gm2=2m,rO1=rO2=50k,RD1=10k,R1=R2=5k,RF=10k): "
        f"R_S1_ex={float(R_S1_exact.subs(subs_num)):.2f}, "
        f"R_S1_ap={float(R_S1_approx.subs(subs_num)):.2f}, "
        f"KR_0={float(KR_0.subs(subs_num)):.4f}, "
        f"R_closed_fb={float(R_closed.subs(subs_num)):.2f}, "
        f"R_closed_exact={float(R_closed_exact.subs(subs_num)):.2f}"
    )


if __name__ == "__main__":
    main()
