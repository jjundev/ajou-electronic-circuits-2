"""설계과제2 손계산: 과제 주어진 값(µnCox=100µ, µpCox=50µ, λ 포함 square-law)으로 캐스코드 W/L·바이어스·Miller 극점 결정."""
import json
import math

import numpy as np
from pathlib import Path

kn, kp = 100e-6, 50e-6
ln, lp = 0.1, 0.2
VTH, VDD, L, RS = 0.4, 1.0, 0.18, 500.0   # L in µm
COX = 12.0                                 # fF/µm² (과제 표)
CGD_W, CJ_W, CGS_OV_W = 0.3, 0.4, 0.3      # fF/µm
F_MIN, SAT_MIN, P_MAX = 1.5e9, 0.1, 0.5e-3


def par(*rs):
    return 1 / sum(1 / r for r in rs)


def ro(lam, i, vds):                       # Level-1: gds = λ·ID/(1+λVDS)
    return (1 + lam * vds) / (lam * i)


def caps(W):
    """과제 표의 C 파라미터 (fF, W는 µm)."""
    return {"CGS": 2 / 3 * W * L * COX + CGS_OV_W * W, "CGD": CGD_W * W,
            "CDB": CJ_W * W, "CSB": CJ_W * W}


def _small_signal(I1, vov1, vov2, VY, RL):
    I2 = I1 / 2
    Vout = VDD - I2 * RL
    gm = {"M1": 2 * I1 / vov1, "M2": 2 * I2 / vov2}
    r = {"M1": ro(ln, I1, VY), "M2": ro(ln, I2, Vout - VY), "M3": ro(lp, I2, VDD - VY)}
    r13 = par(r["M1"], r["M3"])
    Rin2 = (RL + r["M2"]) / (1 + gm["M2"] * r["M2"])           # Y에서 본 M2 (부하 RL 포함)
    Rin2_sc = r["M2"] / (1 + gm["M2"] * r["M2"])                # 출력 단락 시 (Gm 정의)
    Gm = gm["M1"] * r13 / (r13 + Rin2_sc)
    Rcas = r["M2"] + r13 + gm["M2"] * r["M2"] * r13
    Rout = par(RL, Rcas)
    return dict(I2=I2, Vout=Vout, gm=gm, ro=r, Rin2=Rin2, Rin2_sc=Rin2_sc, RY=par(r13, Rin2),
                Gm=Gm, Rcas=Rcas, Rout=Rout, A0=-Gm * Rout)


def design(I1=400e-6, vov1=0.15, vov2=0.15, vov3=0.30, VY=0.30, av=10.0):
    RL = 1e3
    for _ in range(200):                   # Vout이 RL에 따라 바뀌므로 반복
        s = _small_signal(I1, vov1, vov2, VY, RL)
        new = RL * av / abs(s["A0"])
        done = abs(new - RL) / RL < 1e-12
        RL = new
        if done:
            break
    s = _small_signal(I1, vov1, vov2, VY, RL)
    I2, Vout = s["I2"], s["Vout"]
    gm, r = s["gm"], s["ro"]
    gm["M3"] = 2 * I2 / vov3
    vds = {"M1": VY, "M2": Vout - VY, "M3": VDD - VY}
    WL = {"M1": 2 * I1 / (kn * vov1**2 * (1 + ln * vds["M1"])),
          "M2": 2 * I2 / (kn * vov2**2 * (1 + ln * vds["M2"])),
          "M3": 2 * I2 / (kp * vov3**2 * (1 + lp * vds["M3"]))}
    W = {k: round(v * L, 2) for k, v in WL.items()}
    c = {k: caps(w) for k, w in W.items()}

    AXY = -gm["M1"] * s["RY"]
    C = {"X": c["M1"]["CGS"] + (1 - AXY) * c["M1"]["CGD"],
         "Y": (c["M1"]["CDB"] + (1 - 1 / AXY) * c["M1"]["CGD"] + c["M2"]["CGS"]
               + c["M2"]["CSB"] + c["M3"]["CDB"] + c["M3"]["CGD"]),
         "out": c["M2"]["CDB"] + c["M2"]["CGD"]}
    R = {"X": RS, "Y": s["RY"], "out": s["Rout"]}
    f = {k: 1 / (2 * math.pi * R[k] * C[k] * 1e-15) for k in C}
    sat = {"M1": vds["M1"] - vov1, "M2": vds["M2"] - vov2, "M3": vds["M3"] - vov3}
    d = dict(I1=I1, I2=I2, RL=RL, Vout=Vout, VY=VY, vov={"M1": vov1, "M2": vov2, "M3": vov3},
                Rin2=s["Rin2"], Rin2_sc=s["Rin2_sc"], RY=s["RY"], Gm=s["Gm"], Rcas=s["Rcas"], Rout=s["Rout"],
                A0=s["A0"], AXY=AXY, AXY_approx=-gm["M1"] / gm["M2"],
                Vin=VTH + vov1, Vb1=VY + VTH + vov2, Vb2=VDD - VTH - vov3, P=VDD * I1,
                vds=vds, WL=WL, W=W, gm=gm, ro=r, sat=sat, caps=c, R=R, C=C, f=f)
    d["nodal"] = nodal(d)
    return d


def nodal(d):
    """X·Y·out 3노드 소신호 회로(과제 표 C)를 근사 없이 푼다: 저주파 이득과 극점(Hz, 오름차순)."""
    gm, r, c, fF = d["gm"], d["ro"], d["caps"], 1e-15
    G = np.zeros((3, 3))
    C = np.zeros((3, 3))
    G[0, 0] = 1 / RS                                             # X: (vx − vin)/RS
    G[1] = [gm["M1"], 1 / r["M1"] + 1 / r["M3"] + gm["M2"] + 1 / r["M2"], -1 / r["M2"]]
    G[2] = [0, -gm["M2"] - 1 / r["M2"], 1 / d["RL"] + 1 / r["M2"]]
    cgd1 = c["M1"]["CGD"] * fF
    C[0, 0] = c["M1"]["CGS"] * fF + cgd1
    C[0, 1] = C[1, 0] = -cgd1
    C[1, 1] = cgd1 + fF * (c["M1"]["CDB"] + c["M2"]["CGS"] + c["M2"]["CSB"]
                           + c["M3"]["CDB"] + c["M3"]["CGD"])
    C[2, 2] = fF * (c["M2"]["CDB"] + c["M2"]["CGD"])
    a0 = np.linalg.solve(G, [1 / RS, 0, 0])[2]
    p = np.linalg.eigvals(-np.linalg.solve(C, G))
    return {"A0": float(a0), "f": sorted(float(abs(x)) / (2 * math.pi) for x in p)}


def check(d):
    assert min(d["f"].values()) >= F_MIN, f"pole below {F_MIN:.2g} Hz: {d['f']}"
    assert min(d["sat"].values()) >= SAT_MIN, f"saturation margin < {SAT_MIN} V: {d['sat']}"
    assert d["P"] <= P_MAX, f"P = {d['P']:.3g} W > {P_MAX} W"
    assert abs(abs(d["A0"]) - 10) <= 1e-6, f"|A0| = {abs(d['A0'])}"


def write_outputs(d, sim_dir):
    sim_dir = Path(sim_dir)
    W = d["W"]
    (sim_dir / "params.inc").write_text(
        f".param W1={W['M1']}u W2={W['M2']}u W3={W['M3']}u RLV={d['RL']:.2f} "
        f"VIN={d['Vin']:.4f} VB1={d['Vb1']:.4f} VB2={d['Vb2']:.4f} XJ=0.49u\n")
    (sim_dir / "design.json").write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    d = design()
    check(d)
    write_outputs(d, Path(__file__).resolve().parent)
    print(f"I1 = {d['I1']*1e6:.0f} uA, I2 = |I3| = {d['I2']*1e6:.0f} uA, P = {d['P']*1e3:.3f} mW")
    print(f"RL = {d['RL']:.2f} ohm, Vout = {d['Vout']:.4f} V, VY = {d['VY']} V")
    print(f"Rin2 = {d['Rin2']:.2f}, Rin2(out short) = {d['Rin2_sc']:.2f}, RY = {d['RY']:.2f}, Gm = {d['Gm']*1e3:.4f} mS, "
          f"Rcas = {d['Rcas']:.4g}, Rout = {d['Rout']:.2f}, A0 = {d['A0']:.6f}")
    print(f"AXY = {d['AXY']:.4f} (approx -gm1/gm2 = {d['AXY_approx']:.2f})")
    for k in ("M1", "M2", "M3"):
        cc = d["caps"][k]
        print(f"{k}: W/L = {d['WL'][k]:7.2f}  W = {d['W'][k]:6.2f} um  gm = {d['gm'][k]*1e3:.3f} mS  "
              f"ro = {d['ro'][k]:.1f}  sat margin = {d['sat'][k]:.4f} V  "
              f"CGS/CGD/CDB/CSB = {cc['CGS']:.2f}/{cc['CGD']:.2f}/{cc['CDB']:.2f}/{cc['CSB']:.2f} fF")
    for k in ("X", "Y", "out"):
        print(f"node {k:3s}: R = {d['R'][k]:8.2f} ohm  C = {d['C'][k]:7.2f} fF  f = {d['f'][k]/1e9:.3f} GHz")
    print("nodal (table C, no Miller): A0 = {:.6f}, poles = {} GHz".format(
        d["nodal"]["A0"], ", ".join(f"{x/1e9:.3f}" for x in d["nodal"]["f"])))
    print(f"Vin,DC = {d['Vin']:.2f}  Vb1 = {d['Vb1']:.2f}  Vb2 = {d['Vb2']:.2f}")
