"""
SymPy independent verification script for Q5:
부하 저항 불일치 ΔRD 차동 증폭기의 Vin,CM 범위, ACM-DM, CMRR
"""

import sys
import math
from pathlib import Path
import sympy as sp

def verify_q5():
    lines = []
    lines.append("=== Q5 SymPy Verification Report ===")

    # -------------------------------------------------------------
    # (1) 직류 동작점 및 Vin,CM 허용 범위
    # -------------------------------------------------------------
    lines.append("\n--- (1) DC Operating Point & Vin,CM Range ---")

    VDD = sp.Rational(18, 10)               # 1.8 V
    mu_n_Cox = sp.Rational(100, 1_000_000)  # 100 uA/V^2
    WL = sp.Rational(200, 1) / sp.Rational(2, 10) # 1000
    kp = mu_n_Cox * WL                      # 100 mA/V^2 = 0.1 A/V^2
    VTH = sp.Rational(4, 10)                # 0.4 V
    ISS = sp.Rational(1, 1000)              # 1.0 mA
    RD1 = sp.Rational(2000, 1)              # 2.0 kOhm
    RD2 = sp.Rational(2100, 1)              # 2.1 kOhm
    delta_RD = sp.Rational(100, 1)          # 100 Ohm
    RSS = sp.Rational(1000, 1)              # 1.0 kOhm
    VCS = sp.Rational(3, 10)                # 0.3 V

    # Branch currents
    ID = ISS / 2  # 0.5 mA
    lines.append(f"ID1 = ID2: {float(ID)*1e3:.2f} mA")
    assert sp.simplify(ID - sp.Rational(5, 10000)) == 0, "ID must be 0.5 mA"

    # Overdrive and VGS
    Vov = sp.sqrt(2 * ID / kp)
    VGS = VTH + Vov
    lines.append(f"Vov: {float(Vov):.4f} V")
    lines.append(f"VGS: {float(VGS):.4f} V")
    assert sp.simplify(Vov - sp.Rational(1, 10)) == 0, "Vov must be 0.1 V"
    assert sp.simplify(VGS - sp.Rational(5, 10)) == 0, "VGS must be 0.5 V"

    # DC Drain voltages
    VD1 = VDD - ID * RD1
    VD2 = VDD - ID * RD2
    lines.append(f"VD1: {float(VD1):.4f} V")
    lines.append(f"VD2: {float(VD2):.4f} V")
    assert sp.simplify(VD1 - sp.Rational(8, 10)) == 0, "VD1 must be 0.8 V"
    assert sp.simplify(VD2 - sp.Rational(75, 100)) == 0, "VD2 must be 0.75 V"

    # Vin,CM,min (Tail CS active: VP >= VCS => Vin,CM - VGS >= VCS)
    Vin_CM_min = VCS + VGS
    # Vin,CM,max (M1, M2 in saturation: VDS >= VGS - VTH => Vin,CM <= VD2 + VTH)
    Vin_CM_max = VD2 + VTH

    lines.append(f"Vin,CM,min: {float(Vin_CM_min):.4f} V")
    lines.append(f"Vin,CM,max: {float(Vin_CM_max):.4f} V")
    assert sp.simplify(Vin_CM_min - sp.Rational(8, 10)) == 0, "Vin,CM,min must be 0.80 V"
    assert sp.simplify(Vin_CM_max - sp.Rational(115, 100)) == 0, "Vin,CM,max must be 1.15 V"

    # -------------------------------------------------------------
    # (2) 차동 이득 Ad 및 공통 모드 이득 ACM 유도 및 계산
    # -------------------------------------------------------------
    lines.append("\n--- (2) Differential Gain Ad and Common Mode Gain ACM ---")

    gm_val = 2 * ID / Vov
    lines.append(f"gm: {float(gm_val)*1e3:.2f} mS")
    assert sp.simplify(gm_val - sp.Rational(1, 100)) == 0, "gm must be 10 mS"

    # Full symbolic small-signal equations for general inputs
    gm_s, RD1_s, RD2_s, RSS_s = sp.symbols('g_m R_D1 R_D2 R_SS')
    vin1_s, vin2_s, vp_s = sp.symbols('v_in1 v_in2 v_p')

    # KCL at node P: vp / RSS = gm*(vin1 - vp) + gm*(vin2 - vp)
    eq_p = sp.Eq(vp_s / RSS_s, gm_s * (vin1_s - vp_s) + gm_s * (vin2_s - vp_s))
    sol_vp = sp.solve(eq_p, vp_s)[0]

    id1_s = gm_s * (vin1_s - sol_vp)
    id2_s = gm_s * (vin2_s - sol_vp)
    vout1_s = -id1_s * RD1_s
    vout2_s = -id2_s * RD2_s

    # 1. Pure differential input: vin1 = vd/2, vin2 = -vd/2
    vd_s = sp.Symbol('v_d')
    sol_diff_v1 = vout1_s.subs({vin1_s: vd_s/2, vin2_s: -vd_s/2})
    sol_diff_v2 = vout2_s.subs({vin1_s: vd_s/2, vin2_s: -vd_s/2})
    Ad_sym = sp.simplify((sol_diff_v1 - sol_diff_v2) / vd_s)
    lines.append(f"Derived Ad symbolic: {Ad_sym}")
    assert sp.simplify(Ad_sym - (-gm_s * (RD1_s + RD2_s) / 2)) == 0, "Ad symbolic mismatch"

    Ad_num = float(Ad_sym.subs({gm_s: gm_val, RD1_s: RD1, RD2_s: RD2}))
    lines.append(f"Ad numerical: {Ad_num:.4f}")
    assert abs(Ad_num - (-20.5)) < 1e-6, "Ad numerical mismatch"

    # 2. Pure common mode input: vin1 = vin2 = vin_cm
    vin_cm_s = sp.Symbol('v_in_cm')
    sol_cm_v1 = vout1_s.subs({vin1_s: vin_cm_s, vin2_s: vin_cm_s})
    sol_cm_v2 = vout2_s.subs({vin1_s: vin_cm_s, vin2_s: vin_cm_s})
    ACM_sym = sp.simplify(((sol_cm_v1 + sol_cm_v2) / 2) / vin_cm_s)
    lines.append(f"Derived ACM symbolic: {ACM_sym}")
    assert sp.simplify(ACM_sym - (-gm_s * (RD1_s + RD2_s) / (2 * (1 + 2 * gm_s * RSS_s)))) == 0, "ACM symbolic mismatch"

    ACM_num = float(ACM_sym.subs({gm_s: gm_val, RD1_s: RD1, RD2_s: RD2, RSS_s: RSS}))
    lines.append(f"ACM numerical: {ACM_num:.5f}")
    assert abs(ACM_num - (-20.5 / 21)) < 1e-6, "ACM numerical mismatch"
    assert abs(ACM_num - (-0.97619)) < 0.001, "ACM numerical mismatch"

    # -------------------------------------------------------------
    # (3) 공통 모드-차동 모드 변환 이득 ACM-DM
    # -------------------------------------------------------------
    lines.append("\n--- (3) Common-Mode to Differential-Mode Gain ACM-DM ---")

    ACM_DM_sym = sp.simplify((sol_cm_v1 - sol_cm_v2) / vin_cm_s)
    lines.append(f"Derived ACM-DM symbolic: {ACM_DM_sym}")
    # With RD2 = RD1 + delta_RD: (sol_cm_v1 - sol_cm_v2) = -id*RD1 - (-id*RD2) = id*(RD2 - RD1) = id*delta_RD
    assert sp.simplify(ACM_DM_sym - (gm_s * (RD2_s - RD1_s) / (1 + 2 * gm_s * RSS_s))) == 0, "ACM-DM symbolic mismatch"

    ACM_DM_num = float(ACM_DM_sym.subs({gm_s: gm_val, RD1_s: RD1, RD2_s: RD2, RSS_s: RSS}))
    lines.append(f"ACM-DM numerical: {ACM_DM_num:.5f} (1/21 = {1/21:.5f})")
    assert abs(ACM_DM_num - (1.0 / 21)) < 1e-6, "ACM-DM numerical mismatch"
    assert abs(ACM_DM_num - 0.04762) < 0.001, "ACM-DM numerical mismatch"

    # -------------------------------------------------------------
    # (4) 공통 모드 제거비 CMRR
    # -------------------------------------------------------------
    lines.append("\n--- (4) Common-Mode Rejection Ratio CMRR ---")

    CMRR_sym = sp.simplify(sp.Abs(Ad_sym / ACM_DM_sym))
    lines.append(f"Derived CMRR symbolic: {CMRR_sym}")

    CMRR_num = abs(Ad_num / ACM_DM_num)
    CMRR_dB = 20 * math.log10(CMRR_num)
    lines.append(f"CMRR exact numerical: {CMRR_num:.2f}")
    lines.append(f"CMRR exact dB: {CMRR_dB:.2f} dB")

    assert abs(CMRR_num - 430.5) < 1e-5, f"CMRR numerical mismatch: {CMRR_num}"
    assert abs(CMRR_dB - 52.68) < 0.02, f"CMRR dB mismatch: {CMRR_dB}"

    lines.append("\nALL Q5 ASSERTIONS PASSED.")

    # Save result file
    res_path = Path("중간고사대비/v1/.assets/evidence/Q5-result.txt")
    res_path.parent.mkdir(parents=True, exist_ok=True)
    res_path.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print("VERIFIED: PASS")

if __name__ == "__main__":
    verify_q5()
