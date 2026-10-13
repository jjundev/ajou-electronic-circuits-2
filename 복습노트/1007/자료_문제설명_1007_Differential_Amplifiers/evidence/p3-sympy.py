# P10.69 (Fig 10.90 a, b): common-mode gain, single-ended output (one side), lambda>0, no body effect.
# Full-circuit small-signal KCL (both halves), CM input v on both gates; bias gates ac ground.
import sympy as sp

v = sp.symbols('v')
gm1, r1, gm3, r3, gm5, r5, gm6, r6, gm7, r7 = sp.symbols('g_m1 r_O1 g_m3 r_O3 g_m5 r_O5 g_m6 r_O6 g_m7 r_O7', positive=True)

def nmos(vg, vd, vs, gm, ro):   # drain->source current
    return gm*(vg - vs) + (vd - vs)/ro
def pmos(vg, vd, vs, gm, ro):   # source->drain current
    return gm*(vs - vg) + (vs - vd)/ro

print("=== (a) PMOS loads M3,M4 (r_O3), tail = cascode M5 over M6 ===")
o1, o2, P, X = sp.symbols('o1 o2 P X')
eqs = [
    sp.Eq(pmos(0, o1, 0, gm3, r3), nmos(v, o1, P, gm1, r1)),                          # node o1
    sp.Eq(pmos(0, o2, 0, gm3, r3), nmos(v, o2, P, gm1, r1)),                          # node o2 (matched)
    sp.Eq(nmos(v, o1, P, gm1, r1) + nmos(v, o2, P, gm1, r1), nmos(0, P, X, gm5, r5)),  # node P
    sp.Eq(nmos(0, P, X, gm5, r5), nmos(0, X, 0, gm6, r6)),                            # node X
]
sa = sp.solve(eqs, [o1, o2, P, X], dict=True)[0]
Aa = sp.simplify(sa[o1]/v)
print("A_CM(a) exact =", Aa)
print("differential output CM gain (o1-o2)/v =", sp.simplify((sa[o1]-sa[o2])/v))
# Norton check: A = -Gm*Rout, Rtail = r5+r6+gm5 r5 r6
Rt = r5 + r6 + gm5*r5*r6
Gm_a = gm1*r1/(r1 + 2*Rt + 2*gm1*r1*Rt)
Rdn_a = r1 + 2*Rt + 2*gm1*r1*Rt
Rout_a = r3*Rdn_a/(r3 + Rdn_a)
print("simplify(A - (-Gm*Rout)) =", sp.simplify(Aa + Gm_a*Rout_a))
target_a = -r3/(2*gm5*r5*r6)
# approximation: g_m r_O >> 1  -> scale every gm by k, k->oo, compare ratio
k = sp.symbols('k', positive=True)
sub = {gm1: k*gm1, gm3: k*gm3, gm5: k*gm5, gm6: k*gm6, gm7: k*gm7}
print("limit k->oo of A(a)/target =", sp.limit(sp.simplify(Aa.subs(sub)/target_a.subs(sub)), k, sp.oo))
print("Approx: A_CM(a) ~ -r_O3/(2 g_m5 r_O5 r_O6)")

print("\n=== (b) cascode PMOS loads M3(top-of-M1)/M5, tail = M7 ===")
o1, o2, P, Y1, Y2 = sp.symbols('o1 o2 P Y1 Y2')
eqs = [
    sp.Eq(pmos(0, Y1, 0, gm5, r5), pmos(0, o1, Y1, gm3, r3)),   # node Y1 (M5 drain / M3 source)
    sp.Eq(pmos(0, Y2, 0, gm5, r5), pmos(0, o2, Y2, gm3, r3)),
    sp.Eq(pmos(0, o1, Y1, gm3, r3), nmos(v, o1, P, gm1, r1)),   # node o1
    sp.Eq(pmos(0, o2, Y2, gm3, r3), nmos(v, o2, P, gm1, r1)),
    sp.Eq(nmos(v, o1, P, gm1, r1) + nmos(v, o2, P, gm1, r1), nmos(0, P, 0, gm7, r7)),  # node P
]
sb = sp.solve(eqs, [o1, o2, P, Y1, Y2], dict=True)[0]
Ab = sp.simplify(sb[o1]/v)
print("A_CM(b) exact =", Ab)
print("differential output CM gain (o1-o2)/v =", sp.simplify((sb[o1]-sb[o2])/v))
Gm_b = gm1*r1/(r1 + 2*r7 + 2*gm1*r1*r7)
Rup = r3 + r5 + gm3*r3*r5
Rdn_b = r1 + 2*r7 + 2*gm1*r1*r7
Rout_b = Rup*Rdn_b/(Rup + Rdn_b)
print("simplify(A - (-Gm*Rout)) =", sp.simplify(Ab + Gm_b*Rout_b))
Rapp = (gm3*r3*r5)*(2*gm1*r1*r7)/(gm3*r3*r5 + 2*gm1*r1*r7)
target_b = -Rapp/(2*r7)
print("limit k->oo of A(b)/target =", sp.limit(sp.simplify(Ab.subs(sub)/target_b.subs(sub)), k, sp.oo))
print("Approx: A_CM(b) ~ -(g_m3 r_O3 r_O5 || 2 g_m1 r_O1 r_O7)/(2 r_O7)")
alt2 = -gm1*r1*gm3*r3*r5/(gm3*r3*r5 + 2*gm1*r1*r7)
print("same expression simplified: simplify(target_b - alt2) =", sp.simplify(target_b - alt2))

# numeric illustration: all gm=1mS? use gm=2mS, ro=10k for all
num = {gm1: 2e-3, gm3: 2e-3, gm5: 2e-3, gm6: 2e-3, gm7: 2e-3, r1: 1e4, r3: 1e4, r5: 1e4, r6: 1e4, r7: 1e4}
print("\nnumeric (gm=2mS, rO=10k all): A(a) exact =", float(Aa.subs(num)), " approx =", float(target_a.subs(num)))
print("numeric (gm=2mS, rO=10k all): A(b) exact =", float(Ab.subs(num)), " approx =", float(target_b.subs(num)))
