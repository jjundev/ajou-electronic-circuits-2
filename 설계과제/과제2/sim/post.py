"""설계과제2 후처리: design.json + ngspice 결과(op/ac/meas/pz) + polemap.json → Bode 그림, 포화 표, 설계-SPICE 비교표."""
import json
import math
from pathlib import Path

import numpy as np

import handcalc
import polemap
import spice_io

SIM = Path(__file__).resolve().parent
REPORT = SIM.parent / "report"
FIG = REPORT / "figs"          # 보고서 그림은 이 한 폴더에만 둔다
VTH = 0.4
ORDER = ("M1", "M2", "M3")
NODES = ("X", "Y", "out")


def par(*rs):
    return 1 / sum(1 / r for r in rs)


def sat_rows(dev, order=ORDER):
    """포화 검증 행. vov = |VGS| − VTH, margin = |VDS| − vov (vdsat은 쓰지 않는다)."""
    rows = []
    for n in order:
        d = dev[n]
        vov = abs(d["vgs"]) - VTH
        margin = abs(d["vds"]) - vov
        rows.append(dict(name=n, id=abs(d["id"]), vgs=abs(d["vgs"]), vov=vov,
                         vds=abs(d["vds"]), margin=margin, ok=vov > 0 and margin > 0))
    return rows


def spice_node_R(dev, RL, RS=500.0):
    """SPICE gm·gds로 노드 저항을 손계산 식 그대로 계산한다."""
    ro = {k: 1 / dev[k]["gds"] for k in ORDER}
    gm2 = dev["M2"]["gm"]
    r13 = par(ro["M1"], ro["M3"])
    rin2 = (RL + ro["M2"]) / (1 + gm2 * ro["M2"])
    rcas = ro["M2"] + r13 + gm2 * ro["M2"] * r13
    return {"X": RS, "Y": par(r13, rin2), "out": par(RL, rcas)}


def spice_gain(dev, RL):
    """SPICE gm·gds를 손계산 이득식(Gm·Rout)에 넣은 값 (부호 포함)."""
    ro = {k: 1 / dev[k]["gds"] for k in ORDER}
    gm1, gm2 = dev["M1"]["gm"], dev["M2"]["gm"]
    r13 = par(ro["M1"], ro["M3"])
    rcas = ro["M2"] + r13 + gm2 * ro["M2"] * r13
    rin2_sc = ro["M2"] / (1 + gm2 * ro["M2"])                  # Gm은 출력 단락으로 정의
    return -gm1 * r13 / (r13 + rin2_sc) * par(RL, rcas)


def label_nodal(dd, c_probe=1.0):
    """handcalc.nodal 극점을 노드에 붙인다: 노드마다 c_probe(fF)를 더해 polemap.map_poles로 대응."""
    base = handcalc.nodal(dd)["f"]
    shifted = {k: handcalc.nodal(dd, extra={k: c_probe})["f"] for k in NODES}
    idx = polemap.map_poles(base, shifted)
    return {k: base[i] for k, i in idx.items()}


def spice_nodal_input(dev, RL):
    """SPICE 소자값(gm, gds, cgs, cgd, cbd, cbs) → handcalc.nodal 입력 dict."""
    return {
        "RL": RL,
        "gm": {k: dev[k]["gm"] for k in ORDER},
        "ro": {k: 1 / dev[k]["gds"] for k in ORDER},
        "caps": {k: {"CGS": dev[k]["cgs"] * 1e15, "CGD": dev[k]["cgd"] * 1e15,
                     "CDB": dev[k]["cbd"] * 1e15, "CSB": dev[k]["cbs"] * 1e15} for k in ORDER}}


def spice_nodal(dev, RL):
    """SPICE 소자값을 handcalc.nodal 3노드 회로에 넣어 푼다."""
    return handcalc.nodal(spice_nodal_input(dev, RL))


def node_caps(f, R):
    """C = 1/(2π f R) [fF]."""
    return {k: 1 / (2 * math.pi * f[k] * R[k]) * 1e15 for k in f}


def device_node_caps(dev, axy):
    """SPICE 소자 C(F)로 Miller 노드 C를 계산한다 [fF]."""
    m1, m2, m3 = dev["M1"], dev["M2"], dev["M3"]
    c = {"X": m1["cgs"] + (1 - axy) * m1["cgd"],
         "Y": (m1["cbd"] + (1 - 1 / axy) * m1["cgd"] + m2["cgs"] + m2["cbs"]
               + m3["cbd"] + m3["cgd"]),
         "out": m2["cbd"] + m2["cgd"]}
    return {k: v * 1e15 for k, v in c.items()}


def err_pct(spice, design):
    return (spice - design) / design * 100


def design_H(d, f):
    """설계 H(jf) = A0 / Π(1 + jf/f_k)."""
    h = np.full_like(f, d["A0"], dtype=complex)
    for k in NODES:
        h /= 1 + 1j * f / d["f"][k]
    return h


def f3db(f, mag_db):
    a3 = mag_db[0] - 3
    k = int(np.argmax(mag_db < a3))
    return 10 ** np.interp(a3, [mag_db[k], mag_db[k - 1]], np.log10([f[k], f[k - 1]]))


def _table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(out) + "\n"


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    FIG.mkdir(parents=True, exist_ok=True)
    d = json.loads((SIM / "design.json").read_text())
    op = (SIM / "op.txt").read_text()
    dev = spice_io.parse_devices(op.split("=== DEVICES ===")[1])
    meas = spice_io.parse_scalars((SIM / "meas.txt").read_text())
    poles, zeros = spice_io.parse_pz((SIM / "pz.txt").read_text())
    pm = json.loads((SIM / "polemap.json").read_text())
    f_ac, db_ac, ph_ac = spice_io.load_ac(SIM / "ac.txt")

    # --- 02: 설계 Bode magnitude ---
    f = np.logspace(6, 11, 1001)
    hd = 20 * np.log10(abs(design_H(d, f)))
    f3_design = f3db(f, hd)
    asym = 20 * math.log10(abs(d["A0"])) - sum(
        20 * np.log10(np.maximum(f / d["f"][k], 1)) for k in NODES)
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.semilogx(f, hd, lw=1.6, label="|H(jf)| (3 Miller poles)")
    ax.semilogx(f, asym, ls="--", c="k", lw=.9, label="asymptote")
    for k, c in zip(NODES, ("tab:red", "tab:green", "tab:purple")):
        ax.axvline(d["f"][k], ls=":", c=c, lw=1.2, label=f"$f_{{{k}}}$ = {d['f'][k]/1e9:.2f} GHz")
    ax.axhline(hd[0] - 3, ls="-.", c="gray", lw=.8)
    ax.set_title(f"Design H(s): |A0| = {abs(d['A0']):.2f} ({hd[0]:.2f} dB), "
                 f"$f_{{-3dB}}$ = {f3_design/1e9:.2f} GHz", fontsize=11)
    ax.set_xlabel("frequency [Hz]")
    ax.set_ylabel("|H(jf)| [dB]")
    ax.set_ylim(min(hd) - 5, hd[0] + 5)
    ax.legend(loc="lower left", fontsize=9)
    ax.grid(alpha=.3, which="both")
    plt.tight_layout()
    plt.savefig(FIG / "02_bode_design.png", dpi=130)
    plt.close(fig)

    # --- 04: SPICE Bode magnitude + phase ---
    fig, ax = plt.subplots(2, 1, sharex=True, figsize=(7, 5.5))
    ax[0].semilogx(f_ac, db_ac, lw=1.6)
    ax[0].set_ylabel("|Vout/Vin| [dB]")
    ax[0].set_title(f"SPICE AC: A0 = {10**(meas['a0']/20):.2f} ({meas['a0']:.2f} dB), "
                    f"$f_{{-3dB}}$ = {meas['f3db']/1e9:.2f} GHz", fontsize=11)
    ax[1].semilogx(f_ac, ph_ac, lw=1.6)
    ax[1].set_ylabel("phase [deg]")
    ax[1].set_xlabel("frequency [Hz]")
    for i, a in enumerate(ax):
        a.axvline(meas["f3db"], ls="--", c="gray", lw=.8, label=f"$f_{{-3dB}}$ = {meas['f3db']/1e9:.2f} GHz")
        for k, c in zip(NODES, ("tab:red", "tab:green", "tab:purple")):
            a.axvline(pm[k]["f_hz"], ls=":", c=c, lw=1.2, label=f"pole {k} = {pm[k]['f_hz']/1e9:.2f} GHz")
        a.grid(alpha=.3, which="both")
    ax[0].legend(loc="lower left", fontsize=9)
    plt.tight_layout()
    plt.savefig(FIG / "04_ac_bode.png", dpi=130)
    plt.close(fig)

    # --- 포화 표 ---
    rows = sat_rows(dev)
    sat_md = _table(["MOSFET", r"$I_D$ [µA]", r"$\lvert V_{GS}\rvert$ [V]",
                     r"$\lvert V_{GS}\rvert - \lvert V_{TH}\rvert$ [V]", r"$\lvert V_{DS}\rvert$ [V]",
                     "margin [V]", "region"],
                    [[r["name"], f"{r['id']*1e6:.2f}", f"{r['vgs']:.4f}", f"{r['vov']:.4f}", f"{r['vds']:.4f}",
                      f"{r['margin']:.4f}", "saturation" if r["ok"] else "NOT saturation"] for r in rows])
    (REPORT / "sat_table.md").write_text(sat_md)

    # --- 비교표 ---
    a0_spice = 10 ** (meas["a0"] / 20)
    a0_formula = abs(spice_gain(dev, d["RL"]))
    sn = spice_nodal(dev, d["RL"])
    gain_md = _table(["항목", "설계", "SPICE", "오차 [%]"], [
        ["\\|A0\\| (AC, 1 MHz)", f"{abs(d['A0']):.3f}", f"{a0_spice:.3f}", f"{err_pct(a0_spice, abs(d['A0'])):+.2f}"],
        ["A0 [dB]", f"{20*math.log10(abs(d['A0'])):.2f}", f"{meas['a0']:.2f}", "-"],
        ["\\|A0\\| (SPICE gm·gds를 이득식에 대입)", f"{abs(d['A0']):.3f}", f"{a0_formula:.3f}",
         f"{err_pct(a0_formula, abs(d['A0'])):+.2f}"],
        ["\\|A0\\| (SPICE 소자값 3노드 정확해)", f"{abs(d['nodal']['A0']):.3f}", f"{abs(sn['A0']):.3f}",
         f"{err_pct(abs(sn['A0']), abs(d['A0'])):+.2f}"],
    ])
    R_sp = spice_node_R(dev, d["RL"])
    f_sp = {k: pm[k]["f_hz"] for k in NODES}
    fn = label_nodal(d)                                          # 1 fF 섭동으로 노드 대응
    fsn = label_nodal(spice_nodal_input(dev, d["RL"]))
    pole_rows = [[f"$f_{{{k}}}$ [GHz]", f"{d['f'][k]/1e9:.3f}", f"{fn[k]/1e9:.3f}", f"{fsn[k]/1e9:.3f}",
                  f"{f_sp[k]/1e9:.3f}",
                  f"{err_pct(f_sp[k], d['f'][k]):+.1f}", f"{err_pct(f_sp[k], fn[k]):+.1f}"] for k in NODES]
    pole_rows.append(["$f_{-3dB}$ [GHz]", f"{f3_design/1e9:.3f}", "-", "-", f"{meas['f3db']/1e9:.3f}",
                      f"{err_pct(meas['f3db'], f3_design):+.1f}", "-"])
    tau_d = sum(1 / (2 * math.pi * d["f"][k]) for k in NODES)
    tau_n = sum(1 / (2 * math.pi * x) for x in d["nodal"]["f"])
    tau_s = sum(1 / abs(p) for p in poles)
    tau_sn = sum(1 / (2 * math.pi * x) for x in sn["f"])
    pole_rows.append([r"$\sum 1/\omega_p$ [ps]", f"{tau_d*1e12:.2f}", f"{tau_n*1e12:.2f}", f"{tau_sn*1e12:.2f}",
                      f"{tau_s*1e12:.2f}",
                      f"{err_pct(tau_s, tau_d):+.1f}", f"{err_pct(tau_s, tau_n):+.1f}"])
    pole_md = _table(["항목", "설계 (Miller)", "설계 (표 C, 3노드 정확해)", "SPICE 소자값 3노드 정확해", "SPICE (pz)",
                      "오차 [%] (Miller 대비)", "오차 [%] (정확해 대비)"], pole_rows)

    axy_sp = -dev["M1"]["gm"] * R_sp["Y"]
    C_sp = node_caps(f_sp, R_sp)
    C_dev = device_node_caps(dev, axy_sp)
    cap_md = _table(["노드", r"$R$ 설계 [Ω]", r"$R$ SPICE [Ω]", "C 설계 [fF]",
                     r"C SPICE $=1/(2\pi f_p R)$ [fF]", "오차 [%]", "C SPICE 소자 C (Miller) [fF]"],
                    [[k, f"{d['R'][k]:.1f}", f"{R_sp[k]:.1f}", f"{d['C'][k]:.1f}", f"{C_sp[k]:.1f}",
                      f"{err_pct(C_sp[k], d['C'][k]):+.1f}", f"{C_dev[k]:.1f}"] for k in NODES])
    shift_md = _table(["+1 fF 노드", *[f"pole {i+1} ({abs(p)/2/math.pi/1e9:.2f} GHz)"
                                        for i, p in enumerate(sorted(poles, key=abs))], "대응"],
                      [[k, *[f"{x*100:.3f} %" for x in pm[k]["rel_shift"]], f"pole {pm[k]['index']+1}"]
                       for k in NODES])
    z = sorted(zeros, key=abs)
    zero_line = ", ".join(f"{zz.real/2/math.pi/1e9:+.1f} GHz" for zz in z)
    (REPORT / "compare.md").write_text(
        "## 이득\n\n" + gain_md +
        "\n## 극점\n\n" + pole_md +
        f"\nSPICE 영점: {zero_line} (양수 = RHP). 설계 RHP 영점 gm1/(2π CGD1) = "
        f"{d['gm']['M1']/(2*math.pi*d['caps']['M1']['CGD']*1e-15)/1e9:.1f} GHz.\n"
        "\n## 1 fF 섭동 상대 이동 |Δp|/|p|\n\n" + shift_md +
        f"\n## 노드 등가 C\n\nA_XY (SPICE) = {axy_sp:.3f}, A_XY (설계) = {d['AXY']:.3f}\n\n" + cap_md)

    print(sat_md)
    print((REPORT / "compare.md").read_text())


if __name__ == "__main__":
    main()
