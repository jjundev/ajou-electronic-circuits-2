import sympy as sp

q = sp.Rational
s, rg, rd, gm, cgs, cgd = sp.symbols("s R_G R_D g_m C_GS C_GD", positive=True)
vin, vg, vx, vo = sp.symbols("v_in v_g v_x v_o")
dc = sp.solve([gm * vg + gm * vx, vo / rd - gm * vx], [vx, vo])
local_gain = sp.simplify(dc[vx] / vg)
midband_gain = sp.simplify(dc[vo] / vg)
ci = cgs + cgd * (1 - local_gain)
cx = cgs + cgd * (1 - 1 / local_gain)
co = cgd
miller = sp.solve(
    [(vg - vin) / rg + s * ci * vg,
     gm * vg + (gm + s * cx) * vx,
     (1 / rd + s * co) * vo - gm * vx],
    [vg, vx, vo],
)
transfer = sp.factor(miller[vo] / vin)
assert sp.simplify(transfer.subs(s, 0) - midband_gain) == 0

current = q("0.0005")
overdrive = q("0.2")
length_um = q("0.18")
mobility_cox = q("0.0001")
width_um = 2 * current * length_um / (mobility_cox * overdrive**2)
ff = q(1, 10**15)
params = {
    gm: 2 * current / overdrive,
    cgs: q(2, 3) * width_um * length_um * 12 * ff,
    cgd: q("0.2") * width_um * ff,
}
input_target = 5 * 10**9
output_target = 10 * 10**9
rg_max = 1 / (2 * sp.pi * input_target * ci.subs(params))
rd_max = 1 / (2 * sp.pi * output_target * co.subs(params))
design = params | {rg: rg_max, rd: rd_max}
fi = sp.simplify((1 / (2 * sp.pi * rg * ci)).subs(design))
fo = sp.simplify((1 / (2 * sp.pi * rd * co)).subs(design))
fx = sp.simplify((gm / (2 * sp.pi * cx)).subs(design))
assert (fi, fo) == (input_target, output_target)
print("local v_x/v_g =", local_gain)
print("midband v_o/v_in =", midband_gain)
print("Miller transfer =", transfer)
for label, result in [
    ("W [um]", width_um),
    ("g_m [mS]", 1000 * params[gm]),
    ("C_GS [fF]", params[cgs] / ff),
    ("C_GD [fF]", params[cgd] / ff),
    ("C_input [fF]", ci.subs(params) / ff),
    ("C_internal [fF]", cx.subs(params) / ff),
    ("C_output [fF]", co.subs(params) / ff),
    ("R_G max [ohm]", rg_max),
    ("R_D max [ohm]", rd_max),
    ("A_v [V/V]", midband_gain.subs(design)),
    ("f_input [GHz]", fi / 10**9),
    ("f_internal [GHz]", fx / 10**9),
    ("f_output [GHz]", fo / 10**9),
]:
    print(label, "=", result, "~", sp.N(result, 18))
