# p12 (E12.09) independent solver-s3: why a unity-current-gain CG stage beats a wire
# Model a realistic current source: i_in in parallel with R_S; a realistic load R_L (to ac ground).
import sympy as sp
iin, RS, RL, gm, ro = sp.symbols('i_in R_S R_L g_m r_O', positive=True)
vs, vd = sp.symbols('v_s v_d')
oo = sp.oo
# (1) wire: i_in || R_S directly into R_L -> current divider
iL_wire = iin*RS/(RS+RL)
print("wire: i_L/i_in =", sp.simplify(iL_wire/iin))
# (2) CG stage: source node gets i_in||R_S, gate ac-grounded, drain to R_L (to ac gnd)
id_ = lambda vd, vs: gm*(0-vs) + (vd-vs)/ro      # drain->source current
# KCL source node: i_in (in) - vs/RS (out to RS) + id (in from channel) = 0
# KCL drain node: current into drain from load = id ; load current from ac gnd through RL into drain: (0-vd)/RL = id
s = sp.solve([sp.Eq(iin - vs/RS + id_(vd, vs), 0), sp.Eq(-vd/RL, id_(vd, vs))], [vs, vd], dict=True)[0]
iL_cg = sp.simplify(-s[vd]/RL)   # current in RL flowing from drain node down to gnd = vd/RL ; sign: magnitude ratio
ratio = sp.simplify(sp.Abs(iL_cg)/iin) if False else sp.simplify(s[vd]/RL/iin)
print("CG: i_L/i_in (current delivered to R_L) =", sp.factor(ratio))
print("CG, ro->oo:", sp.simplify(sp.limit(ratio, ro, oo)), "  (independent of R_L)")
print("wire, R_L->oo vs CG: wire ratio ->", sp.limit(iL_wire/iin, RL, oo))
# input / output impedances of CG
Rin_cg = sp.limit((RL+ro)/(1+gm*ro), ro, oo); print("CG Rin (ro->oo) =", Rin_cg)
Rout_cg = RS*gm*ro + RS + ro; print("CG Rout with source resistance R_S =", Rout_cg, "; with ideal i_in (R_S->oo):", sp.limit(Rout_cg, RS, oo))
# numerical illustration: R_S = 10k, R_L = 10k, g_m = 10 mS, r_O = 50k
vals = {RS: 10e3, RL: 10e3, gm: 10e-3, ro: 50e3}
print("numeric (R_S=10k, R_L=10k, gm=10mS, rO=50k): wire", float((iL_wire/iin).subs(vals)), " CG", float(ratio.subs(vals)))
# sign with literal arrows: i_in up into source -> drain current flows source->drain (upward), i.e. out of drain into load
print("sign: with RL from drain to ac gnd, v_d/i_in =", sp.simplify(s[vd]/iin), "> 0 => current leaves drain into load in same sense as i_in (|A_I|=1)")
# proof that ratio -> 1 when RS >> 1/gm and Rout >> RL
x = sp.symbols('x', positive=True)
print("CG ratio with gm->oo:", sp.limit(ratio, gm, oo))
