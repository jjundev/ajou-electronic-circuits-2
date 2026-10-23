"""
SymPy independent verification script for Q3:
기생 저항 Rp 캐스코드 및 Folded Cascode 증폭기
"""

import sys
from pathlib import Path
import sympy as sp

def verify_q3():
    lines = []
    lines.append("=== Q3 SymPy Verification Report ===")

    # -------------------------------------------------------------
    # (a) 기생 저항 RP 결합 MOS 캐스코드 증폭기
    # -------------------------------------------------------------
    lines.append("\n--- (a) Cascode Amplifier with Parasitic RP ---")

    # Parameters
    mu_n_Cox = sp.Rational(100, 1_000_000)   # 100 uA/V^2
    mu_p_Cox = sp.Rational(50, 1_000_000)    # 50 uA/V^2
    lambda_n = sp.Rational(1, 10)            # 0.1 V^-1
    lambda_p = sp.Rational(1, 10)            # 0.1 V^-1
    ID_a = sp.Rational(1, 1000)              # 1 mA
    RP = sp.Rational(10000, 1)               # 10 kOhm

    WL_12 = sp.Rational(100, 1) / sp.Rational(2, 10)  # 500
    WL_34 = sp.Rational(50, 1) / sp.Rational(2, 10)   # 250

    # Small signal parameters
    gm1_val = sp.sqrt(2 * mu_n_Cox * WL_12 * ID_a)
    gm2_val = gm1_val
    ro1_val = 1 / (lambda_n * ID_a)
    ro2_val = 1 / (lambda_n * ID_a)

    gm3_val = sp.sqrt(2 * mu_p_Cox * WL_34 * ID_a)
    gm4_val = gm3_val
    ro3_val = 1 / (lambda_p * ID_a)
    ro4_val = 1 / (lambda_p * ID_a)

    lines.append(f"gm1 = gm2: {float(gm1_val)*1e3:.2f} mS")
    lines.append(f"ro1 = ro2: {float(ro1_val)/1e3:.2f} kOhm")
    lines.append(f"gm3 = gm4: {float(gm3_val)*1e3:.2f} mS")
    lines.append(f"ro3 = ro4: {float(ro3_val)/1e3:.2f} kOhm")

    assert sp.simplify(gm1_val - sp.Rational(1, 100)) == 0, "gm1 must be 10 mS"
    assert sp.simplify(ro1_val - 10000) == 0, "ro1 must be 10 kOhm"
    assert sp.simplify(gm3_val - sp.Rational(5, 1000)) == 0, "gm3 must be 5 mS"
    assert sp.simplify(ro3_val - 10000) == 0, "ro3 must be 10 kOhm"

    # RP in parallel with ro2
    ro2_prime = (ro2_val * RP) / (ro2_val + RP)
    lines.append(f"ro2' = ro2 || RP: {float(ro2_prime)/1e3:.2f} kOhm")
    assert sp.simplify(ro2_prime - 5000) == 0, "ro2' must be 5 kOhm"

    # Rout_n derivation via KCL
    # Test circuit at output node V_out looking into M2 with degeneration ro1
    gm2_s, ro1_s, ro2p_s, vt, it, vx = sp.symbols('g_m2 r_o1 r_o2_prime v_t i_t v_x')
    eq_n1 = sp.Eq(vx / ro1_s, it)
    eq_n2 = sp.Eq(it, gm2_s * (-vx) + (vt - vx) / ro2p_s)
    sol_casc_n = sp.solve([eq_n1, eq_n2], [vt, vx])
    Rout_n_sym = sp.simplify(sol_casc_n[vt] / it)
    lines.append(f"Derived Rout_n symbolic: {Rout_n_sym}")

    Rout_n_exact = float(Rout_n_sym.subs({gm2_s: gm1_val, ro1_s: ro1_val, ro2p_s: ro2_prime}))
    Rout_n_approx = float(gm1_val * ro1_val * ro2_prime)
    lines.append(f"Rout_n approx: {Rout_n_approx/1e3:.2f} kOhm, exact: {Rout_n_exact/1e3:.2f} kOhm")
    assert abs(Rout_n_approx/1e3 - 500.0) < 1e-4, "Rout_n approx mismatch"
    assert abs(Rout_n_exact/1e3 - 515.0) < 1e-4, "Rout_n exact mismatch"

    # PMOS load Rout_p
    Rout_p_approx = float(gm3_val * ro3_val * ro4_val)
    Rout_p_exact = float(ro4_val + ro3_val + gm3_val * ro3_val * ro4_val)
    lines.append(f"Rout_p approx: {Rout_p_approx/1e3:.2f} kOhm, exact: {Rout_p_exact/1e3:.2f} kOhm")
    assert abs(Rout_p_approx/1e3 - 500.0) < 1e-4, "Rout_p approx mismatch"
    assert abs(Rout_p_exact/1e3 - 520.0) < 1e-4, "Rout_p exact mismatch"

    # Total Rout and Av
    Rout_approx = (Rout_n_approx * Rout_p_approx) / (Rout_n_approx + Rout_p_approx)
    Rout_exact = (Rout_n_exact * Rout_p_exact) / (Rout_n_exact + Rout_p_exact)
    lines.append(f"Rout approx: {Rout_approx/1e3:.2f} kOhm, exact: {Rout_exact/1e3:.2f} kOhm")
    assert abs(Rout_approx/1e3 - 250.0) < 1e-4, "Rout approx mismatch"
    assert abs(Rout_exact/1e3 - 258.74) < 0.1, "Rout exact mismatch"

    # Short-circuit Gm: Gm approx = gm1 = 10 mS
    Gm_approx = float(gm1_val)
    Av_approx = -Gm_approx * Rout_approx
    Av_exact_Rout = -Gm_approx * Rout_exact
    lines.append(f"Av approx: {Av_approx:.2f}")
    lines.append(f"Av exact Rout: {Av_exact_Rout:.2f}")
    assert abs(Av_approx - (-2500.0)) < 1e-3, "Av approx mismatch"
    assert abs(Av_exact_Rout - (-2587.4)) < 1.0, "Av exact mismatch"

    # -------------------------------------------------------------
    # (b) PMOS 입력 Folded Cascode 증폭기
    # -------------------------------------------------------------
    lines.append("\n--- (b) PMOS-Input Folded Cascode Amplifier ---")

    ID5 = sp.Rational(5, 10000)   # 0.5 mA
    ID1 = sp.Rational(1, 1000)    # 1.0 mA
    ID2 = sp.Rational(5, 10000)   # 0.5 mA
    ID34 = sp.Rational(5, 10000)  # 0.5 mA

    WL_5 = sp.Rational(200, 1) / sp.Rational(2, 10)   # 1000
    WL_12_b = sp.Rational(100, 1) / sp.Rational(2, 10) # 500
    WL_34_b = sp.Rational(100, 1) / sp.Rational(2, 10) # 500

    # Small signal parameters
    gm5_val = sp.sqrt(2 * mu_p_Cox * WL_5 * ID5)
    ro5_val = 1 / (lambda_p * ID5)

    ro1_b_val = 1 / (lambda_n * ID1)

    gm2_b_val = sp.sqrt(2 * mu_n_Cox * WL_12_b * ID2)
    ro2_b_val = 1 / (lambda_n * ID2)

    gm3_b_val = sp.sqrt(2 * mu_p_Cox * WL_34_b * ID34)
    ro3_b_val = 1 / (lambda_p * ID34)
    ro4_b_val = ro3_b_val

    lines.append(f"gm5: {float(gm5_val)*1e3:.4f} mS, ro5: {float(ro5_val)/1e3:.2f} kOhm")
    lines.append(f"ro1: {float(ro1_b_val)/1e3:.2f} kOhm")
    lines.append(f"gm2: {float(gm2_b_val)*1e3:.4f} mS, ro2: {float(ro2_b_val)/1e3:.2f} kOhm")
    lines.append(f"gm3: {float(gm3_b_val)*1e3:.4f} mS, ro3 = ro4: {float(ro3_b_val)/1e3:.2f} kOhm")

    assert abs(float(gm5_val)*1e3 - 7.071) < 0.01, "gm5 mismatch"
    assert abs(float(ro5_val)/1e3 - 20.0) < 1e-4, "ro5 mismatch"
    assert abs(float(ro1_b_val)/1e3 - 10.0) < 1e-4, "ro1 mismatch"
    assert abs(float(gm2_b_val)*1e3 - 7.071) < 0.01, "gm2 mismatch"
    assert abs(float(ro2_b_val)/1e3 - 20.0) < 1e-4, "ro2 mismatch"
    assert abs(float(gm3_b_val)*1e3 - 5.0) < 1e-4, "gm3 mismatch"

    # Folding node source impedance
    RS_folding = (ro1_b_val * ro5_val) / (ro1_b_val + ro5_val)
    lines.append(f"Folding node RS' = ro1 || ro5: {float(RS_folding)/1e3:.4f} kOhm")
    assert abs(float(RS_folding)/1e3 - 6.6667) < 0.01, "RS_folding mismatch"

    # Gm -> Rout -> Av
    Gm_folded = float(gm5_val)

    Rout_n_folded = float(gm2_b_val * ro2_b_val * RS_folding)
    Rout_p_folded = float(gm3_b_val * ro3_b_val * ro4_b_val)
    Rout_folded = (Rout_n_folded * Rout_p_folded) / (Rout_n_folded + Rout_p_folded)
    Av_folded = -Gm_folded * Rout_folded

    lines.append(f"Gm: {Gm_folded*1e3:.4f} mS")
    lines.append(f"Rout,n: {Rout_n_folded/1e3:.2f} kOhm")
    lines.append(f"Rout,p: {Rout_p_folded/1e3:.2f} kOhm")
    lines.append(f"Rout: {Rout_folded/1e3:.2f} kOhm")
    lines.append(f"Av: {Av_folded:.2f}")

    assert abs(Rout_n_folded/1e3 - 942.8) < 0.2, "Rout_n_folded mismatch"
    assert abs(Rout_p_folded/1e3 - 2000.0) < 1e-3, "Rout_p_folded mismatch"
    assert abs(Rout_folded/1e3 - 640.7) < 0.2, "Rout_folded mismatch"
    assert abs(Av_folded - (-4530.0)) < 5.0, "Av_folded mismatch"

    lines.append("\nALL Q3 ASSERTIONS PASSED.")

    # Save result file
    res_path = Path("중간고사대비/v1/.assets/evidence/Q3-result.txt")
    res_path.parent.mkdir(parents=True, exist_ok=True)
    res_path.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print("VERIFIED: PASS")

if __name__ == "__main__":
    verify_q3()
