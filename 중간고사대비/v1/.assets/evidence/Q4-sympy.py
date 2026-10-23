"""
SymPy independent verification script for Q4:
소스 축퇴 차동쌍 반회로 해석 및 능동 전류 거울 부하 차동쌍
"""

import sys
from pathlib import Path
import sympy as sp

def verify_q4():
    lines = []
    lines.append("=== Q4 SymPy Verification Report ===")

    # -------------------------------------------------------------
    # (a) 소스 축퇴 차동쌍 반회로 해석 및 차동 이득 Ad
    # -------------------------------------------------------------
    lines.append("\n--- (a) Source-Degenerated Diff Pair Half-Circuit ---")

    # Parameters
    mu_n_Cox = sp.Rational(100, 1_000_000)   # 100 uA/V^2
    WL = sp.Rational(200, 1) / sp.Rational(2, 10)  # 1000
    k_prime = mu_n_Cox * WL                  # 100 mA/V^2 = 0.1 A/V^2
    ID = sp.Rational(5, 10000)               # 0.5 mA
    RSS = sp.Rational(400, 1)                # 400 Ohm
    RD = sp.Rational(4000, 1)                # 4 kOhm

    # gm1
    gm1_val = sp.sqrt(2 * k_prime * ID)
    lines.append(f"gm1 = gm2: {float(gm1_val)*1e3:.2f} mS")
    lines.append(f"1/gm1: {float(1/gm1_val):.2f} Ohm")
    assert sp.simplify(gm1_val - sp.Rational(1, 100)) == 0, "gm1 must be 10 mS"

    # Half circuit approach
    Rdeg_half = RSS / 2
    Av_half = -RD / (1 / gm1_val + Rdeg_half)
    lines.append(f"Av_half: {Av_half} = {float(Av_half):.4f}")
    assert sp.simplify(Av_half - sp.Rational(-40, 3)) == 0, "Av_half must be -40/3"

    # Full 2-transistor symbolic KCL proof of virtual ground
    gm_s, RSS_s, RD_s, vd = sp.symbols('g_m R_SS R_D v_d')
    vin1 = vd / 2
    vin2 = -vd / 2
    vs1, vs2 = sp.symbols('v_s1 v_s2')

    # KCL at S1: gm * (vin1 - vs1) = (vs1 - vs2) / RSS
    # KCL at S2: gm * (vin2 - vs2) = (vs2 - vs1) / RSS
    eq_s1 = sp.Eq(gm_s * (vin1 - vs1), (vs1 - vs2) / RSS_s)
    eq_s2 = sp.Eq(gm_s * (vin2 - vs2), (vs2 - vs1) / RSS_s)
    sol_vs = sp.solve([eq_s1, eq_s2], [vs1, vs2])

    v_mid = sp.simplify((sol_vs[vs1] + sol_vs[vs2]) / 2)
    lines.append(f"Virtual ground node v_mid = (vs1 + vs2)/2: {v_mid}")
    assert v_mid == 0, "v_mid must be strictly 0 (Virtual Ground proven)"

    # Solve differential gain from full network
    id1 = sp.simplify(gm_s * (vin1 - sol_vs[vs1]))
    id2 = sp.simplify(gm_s * (vin2 - sol_vs[vs2]))
    vout1 = -id1 * RD_s
    vout2 = -id2 * RD_s
    vout_d = sp.simplify(vout1 - vout2)
    Ad_full = sp.simplify(vout_d / vd)

    lines.append(f"Full network differential gain Ad: {Ad_full}")
    assert sp.simplify(Ad_full - (-RD_s / (1 / gm_s + RSS_s / 2))) == 0, "Ad full mismatch with half-circuit"

    Ad_num = float(Ad_full.subs({gm_s: gm1_val, RSS_s: RSS, RD_s: RD}))
    lines.append(f"Ad numerical: {Ad_num:.4f}")
    assert abs(Ad_num - (-13.3333)) < 0.001, "Ad numerical mismatch"

    # -------------------------------------------------------------
    # (b) 능동 전류 거울 부하 차동 증폭기
    # -------------------------------------------------------------
    lines.append("\n--- (b) Active Current-Mirror Load Diff Pair ---")

    mu_p_Cox = sp.Rational(50, 1_000_000)    # 50 uA/V^2
    WL_34 = sp.Rational(400, 1) / sp.Rational(2, 10)  # 2000
    kp_34 = mu_p_Cox * WL_34                 # 100 mA/V^2
    lambda_n = sp.Rational(1, 10)
    lambda_p = sp.Rational(1, 10)

    gm34_val = sp.sqrt(2 * kp_34 * ID)
    ro2_val = 1 / (lambda_n * ID)
    ro4_val = 1 / (lambda_p * ID)

    lines.append(f"gm3 = gm4: {float(gm34_val)*1e3:.2f} mS")
    lines.append(f"ro2: {float(ro2_val)/1e3:.2f} kOhm, ro4: {float(ro4_val)/1e3:.2f} kOhm")
    assert sp.simplify(gm34_val - sp.Rational(1, 100)) == 0, "gm3,4 must be 10 mS"
    assert sp.simplify(ro2_val - 20000) == 0, "ro2 must be 20 kOhm"
    assert sp.simplify(ro4_val - 20000) == 0, "ro4 must be 20 kOhm"

    # Gm -> Rout -> Av standard
    Gm_active = gm1_val
    Rout_active = (ro2_val * ro4_val) / (ro2_val + ro4_val)
    Av_active = Gm_active * Rout_active

    lines.append(f"Gm: {float(Gm_active)*1e3:.2f} mS")
    lines.append(f"Rout: {float(Rout_active)/1e3:.2f} kOhm")
    lines.append(f"Av: {float(Av_active):.2f}")

    assert sp.simplify(Gm_active - sp.Rational(1, 100)) == 0, "Gm must be 10 mS"
    assert sp.simplify(Rout_active - 10000) == 0, "Rout must be 10 kOhm"
    assert sp.simplify(Av_active - 100) == 0, "Av must be +100"

    # Full small-signal nodal KCL analysis for active mirror diff pair
    # Node D1 (connected to gate and drain of M3, and drain of M1)
    # Node D2 (output node, connected to drain of M4 and drain of M2)
    vd1, vout_s = sp.symbols('v_d1 v_out')
    gm1_s, gm3_s, gm4_s, ro1_s, ro2_s, ro3_s, ro4_s = sp.symbols('g_m1 g_m3 g_m4 r_o1 r_o2 r_o3 r_o4')

    # id1 = gm1 * (vd/2) + vd1/ro1
    # id3 (PMOS M3 to D1) = -gm3*vd1 - vd1/ro3
    # KCL at D1: id3 = id1 => -gm3*vd1 - vd1/ro3 = gm1*(vd/2) + vd1/ro1
    # => vd1 * (gm3 + 1/ro3 + 1/ro1) = -gm1 * (vd/2)
    eq_d1 = sp.Eq(vd1 * (gm3_s + 1/ro3_s + 1/ro1_s) + gm1_s * (vd / 2), 0)
    sol_vd1 = sp.solve(eq_d1, vd1)[0]

    # At output D2:
    # id4 (into D2) = -gm4*vd1 - vout/ro4
    # id2 (from D2) = -gm1*(vd/2) + vout/ro2
    # KCL at D2: id4 = id2 => -gm4*vd1 - vout/ro4 = -gm1*(vd/2) + vout/ro2
    # => vout * (1/ro2 + 1/ro4) = -gm4*vd1 + gm1*(vd/2)
    eq_d2 = sp.Eq(vout_s * (1/ro2_s + 1/ro4_s) - (-gm4_s * sol_vd1 + gm1_s * (vd / 2)), 0)
    sol_vout = sp.solve(eq_d2, vout_s)[0]

    Av_full_active = sp.simplify(sol_vout / vd)
    lines.append(f"Full small-signal Av expression: {Av_full_active}")

    # Substitute numerical values into exact full nodal equation
    subs_dict = {
        gm1_s: gm1_val, gm3_s: gm34_val, gm4_s: gm34_val,
        ro1_s: ro2_val, ro2_s: ro2_val, ro3_s: ro4_val, ro4_s: ro4_val
    }
    Av_full_num = float(Av_full_active.subs(subs_dict))
    lines.append(f"Av exact full nodal: {Av_full_num:.4f}")
    assert abs(Av_full_num - 99.5) < 1.0, f"Av exact nodal error: {Av_full_num}"

    lines.append("\nALL Q4 ASSERTIONS PASSED.")

    # Save result file
    res_path = Path("중간고사대비/v1/.assets/evidence/Q4-result.txt")
    res_path.parent.mkdir(parents=True, exist_ok=True)
    res_path.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print("VERIFIED: PASS")

if __name__ == "__main__":
    verify_q4()
