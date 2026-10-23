"""
SymPy independent verification script for Q2:
축퇴 저항 전류 거울 복사비 설계 및 복합 바이어스 CE 단
"""

import sys
from pathlib import Path
import sympy as sp

def verify_q2():
    lines = []
    lines.append("=== Q2 SymPy Verification Report ===")

    # -------------------------------------------------------------
    # (a) 소스 축퇴 MOS 전류 거울의 복사비 설계 및 출력 저항
    # -------------------------------------------------------------
    lines.append("\n--- (a) Source-Degenerated Current Mirror ---")

    # Parameters
    mu_n_Cox = sp.Rational(100, 1_000_000)   # 100 uA/V^2 = 1e-4 A/V^2
    WL = sp.Rational(100, 1) / sp.Rational(2, 10)  # 500
    k_prime = mu_n_Cox * WL                  # 50 mA/V^2 = 0.05 A/V^2
    V_TH = sp.Rational(4, 10)                # 0.4 V
    I_REF = sp.Rational(1, 1000)             # 1 mA
    I_out = sp.Rational(5, 10000)            # 0.5 mA
    lambda_val = sp.Rational(1, 10)          # 0.1 V^-1

    # 1. Gate-source voltages
    # I_REF = 0.5 * k_prime * (V_GS1 - V_TH)^2
    V_GS1_sym = sp.Symbol('V_GS1', positive=True)
    eq_vgs1 = sp.Eq(I_REF, sp.Rational(1, 2) * k_prime * (V_GS1_sym - V_TH)**2)
    sol_vgs1 = [s for s in sp.solve(eq_vgs1, V_GS1_sym) if s > V_TH]
    V_GS1 = sol_vgs1[0]

    V_GS2_sym = sp.Symbol('V_GS2', positive=True)
    eq_vgs2 = sp.Eq(I_out, sp.Rational(1, 2) * k_prime * (V_GS2_sym - V_TH)**2)
    sol_vgs2 = [s for s in sp.solve(eq_vgs2, V_GS2_sym) if s > V_TH]
    V_GS2 = sol_vgs2[0]

    V_ov1 = V_GS1 - V_TH
    V_ov2 = V_GS2 - V_TH

    # 2. RS design
    # V_GS1 = V_GS2 + I_out * R_S
    R_S_exact = (V_GS1 - V_GS2) / I_out
    R_S_num = float(R_S_exact)

    lines.append(f"V_GS1 exact: {V_GS1} V, float: {float(V_GS1):.4f} V")
    lines.append(f"V_ov2 exact: {V_ov2} V, float: {float(V_ov2):.4f} V")
    lines.append(f"V_GS2 exact: {V_GS2} V, float: {float(V_GS2):.4f} V")
    lines.append(f"R_S exact: {R_S_exact} Ohm, float: {R_S_num:.4f} Ohm")

    assert sp.simplify(V_GS1 - sp.Rational(6, 10)) == 0, "V_GS1 must be 0.6 V"
    assert abs(float(V_ov2) - 0.141421356) < 1e-5, f"V_ov2 error: {float(V_ov2)}"
    assert abs(R_S_num - 117.157) < 0.1, f"R_S error: {R_S_num}"

    # 3. Small-signal parameters and Rout derivation via KCL
    gm2_sym, ro2_sym, RS_sym = sp.symbols('g_m2 r_o2 R_S', positive=True)
    vt, it, vs, vgs2 = sp.symbols('v_t i_t v_s v_gs2')

    # Circuit equations:
    # vs = it * RS
    # vgs2 = -vs = -it * RS
    # it = gm2 * vgs2 + (vt - vs) / ro2
    eq_kcl = sp.Eq(it, gm2_sym * (-vs) + (vt - vs) / ro2_sym)
    eq_vs = sp.Eq(vs, it * RS_sym)
    sol_kcl = sp.solve([eq_kcl, eq_vs], [vt, vs])

    Rout_expr = sp.simplify(sol_kcl[vt] / it)
    lines.append(f"Derived Rout symbolic: {Rout_expr}")
    # Verify standard form: Rout = ro2 * (1 + gm2 * RS) + RS
    Rout_standard = ro2_sym * (1 + gm2_sym * RS_sym) + RS_sym
    assert sp.simplify(Rout_expr - Rout_standard) == 0, "Rout symbolic mismatch"

    # Numerical evaluations
    gm2_val = 2 * I_out / V_ov2
    ro2_val = 1 / (lambda_val * I_out)

    Rout_num_exact = float(Rout_expr.subs({gm2_sym: gm2_val, ro2_sym: ro2_val, RS_sym: R_S_exact}))
    Rout_num_approx = float((ro2_sym * (1 + gm2_sym * RS_sym)).subs({gm2_sym: gm2_val, ro2_sym: ro2_val, RS_sym: R_S_exact}))

    lines.append(f"gm2: {float(gm2_val)*1e3:.4f} mS")
    lines.append(f"ro2: {float(ro2_val)/1e3:.4f} kOhm")
    lines.append(f"gm2 * R_S: {float(gm2_val * R_S_exact):.4f}")
    lines.append(f"Rout exact: {Rout_num_exact:.2f} Ohm ({Rout_num_exact/1e3:.3f} kOhm)")
    lines.append(f"Rout approx: {Rout_num_approx:.2f} Ohm ({Rout_num_approx/1e3:.3f} kOhm)")

    assert abs(float(gm2_val)*1e3 - 7.071) < 0.01, "gm2 mismatch"
    assert abs(float(ro2_val) - 20000.0) < 1e-3, "ro2 mismatch"
    assert abs(Rout_num_exact/1e3 - 36.69) < 0.1, "Rout exact mismatch with Q2.md"

    # -------------------------------------------------------------
    # (b) NPN/PNP 복합 바이어스 CE 증폭기 직류 동작점 및 Av
    # -------------------------------------------------------------
    lines.append("\n--- (b) Compound Current-Mirror Biased CE Amplifier ---")

    I_REF_b = sp.Rational(200, 1_000_000)  # 200 uA
    V_T = sp.Rational(26, 1000)            # 26 mV
    V_A = sp.Rational(40, 1)               # 40 V

    # Mirror ratios: Q_REF1: 1, Q_M: 2, Q_REF2: 2, Q_2: 3
    I_C_QM = 2 * I_REF_b                   # 400 uA
    I_C2 = sp.Rational(3, 2) * I_C_QM      # 600 uA = 0.6 mA
    I_C1 = I_C2                            # 0.6 mA

    gm1_val = I_C1 / V_T
    ro1_val = V_A / I_C1
    ro2_b_val = V_A / I_C2

    # Gm -> Rout -> Av
    Gm_val = gm1_val
    Rout_b_val = (ro1_val * ro2_b_val) / (ro1_val + ro2_b_val)
    Av_val = -Gm_val * Rout_b_val
    Av_early_formula = -V_A / (2 * V_T)

    lines.append(f"I_C1: {float(I_C1)*1e3:.3f} mA")
    lines.append(f"gm1: {float(gm1_val)*1e3:.4f} mS")
    lines.append(f"ro1: {float(ro1_val)/1e3:.4f} kOhm")
    lines.append(f"ro2: {float(ro2_b_val)/1e3:.4f} kOhm")
    lines.append(f"Rout: {float(Rout_b_val)/1e3:.4f} kOhm")
    lines.append(f"Av exact: {float(Av_val):.4f}")
    lines.append(f"Av formula (-V_A / 2V_T): {float(Av_early_formula):.4f}")

    assert sp.simplify(Av_val - Av_early_formula) == 0, "Av formula mismatch"
    assert abs(float(I_C1)*1e3 - 0.6) < 1e-6, "I_C1 mismatch"
    assert abs(float(gm1_val)*1e3 - 23.08) < 0.05, "gm1 mismatch"
    assert abs(float(ro1_val)/1e3 - 66.67) < 0.05, "ro1 mismatch"
    assert abs(float(Rout_b_val)/1e3 - 33.33) < 0.05, "Rout mismatch"
    assert abs(float(Av_val) - (-769.23)) < 0.1, "Av mismatch"

    lines.append("\nALL Q2 ASSERTIONS PASSED.")

    # Save result file
    res_path = Path("중간고사대비/v1/.assets/evidence/Q2-result.txt")
    res_path.parent.mkdir(parents=True, exist_ok=True)
    res_path.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print("VERIFIED: PASS")

if __name__ == "__main__":
    verify_q2()
