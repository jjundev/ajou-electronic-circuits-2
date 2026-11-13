# p10 (P12.15) independent solver-s3: amplifier models of Fig 12.19(a)-(d)
# small-signal MOSFET: i_d (drain->source) = gm*(vg-vs) + (vd-vs)/ro ; body effect ignored
import sympy as sp
gm1, gm2, RD, ro1, ro2, ro = sp.symbols('g_m1 g_m2 R_D r_O1 r_O2 r_O', positive=True)
vin, iin, it, vt = sp.symbols('v_in i_in i_t v_t')
oo = sp.oo
def idn(gm, vg, vd, vs, r=None):
    return gm*(vg-vs) + ((vd-vs)/r if r is not None else 0)

print("=== (a) CS M1 + follower M2, ideal I1 load ===")
# general with ro1, ro2; then limit ro->oo
n1, vo = sp.symbols('v_n1 v_o')
# open-circuit output: KCL n1: (0-n1)/RD = id1 ; KCL vo: id2 = 0 (ideal current source, small-signal open)
eqs = [sp.Eq(-n1/RD, idn(gm1, vin, n1, 0, ro1)), sp.Eq(idn(gm2, n1, 0, vo, ro2), 0)]
s = sp.solve(eqs, [n1, vo], dict=True)[0]
A0 = sp.simplify(s[vo]/vin)
print("A0 exact (ro1,ro2 finite) =", A0)
A0l = sp.limit(sp.limit(A0, ro1, oo), ro2, oo)
print("A0 (lambda=0) =", A0l)
# Rout: vin=0, apply vt at output, it into output node
eqs = [sp.Eq(-n1/RD, idn(gm1, 0, n1, 0, ro1)), sp.Eq(it + idn(gm2, n1, 0, vt, ro2), 0)]
s = sp.solve(eqs, [n1, it], dict=True)[0]
Rout = sp.simplify(vt/s[it]); print("Rout exact =", Rout, "; lambda=0 ->", sp.limit(Rout, ro2, oo))
print("Rin = oo (input is MOS gate, no gate current)")

print("=== (b) CG M1 (input current at source) + follower M2 ===")
ns, n1 = sp.symbols('v_s v_n1')
# KCL source node: i_in (into node, arrow up) + id1 (drain->source current enters source node) = 0
# KCL n1: current from n1 into RD toward VDD (ac gnd) = -id1 ... write: (0-n1)/RD = id1
eqs = [sp.Eq(iin + idn(gm1, 0, n1, ns, ro1), 0), sp.Eq(-n1/RD, idn(gm1, 0, n1, ns, ro1)),]
s = sp.solve(eqs, [ns, n1], dict=True)[0]
Rin = sp.simplify(s[ns]/iin); print("Rin exact =", Rin, "; lambda=0 ->", sp.limit(Rin, ro1, oo))
vn1 = sp.simplify(s[n1]/iin); print("v_n1/i_in =", vn1)
# follower gain 1 (open circuit) with ro2->oo => R0 = v_out/i_in
R0 = sp.limit(vn1, ro1, oo); print("R0 = v_out/i_in (lambda=0) =", R0)
print("Rout = 1/g_m2 (same follower as (a))")

print("=== (c) CS M1, output = drain current I_out (into drain) ===")
vd = sp.symbols('v_d')
Iout = idn(gm1, vin, vd, 0, ro)
print("Gm = I_out/v_in |vd=0 :", sp.simplify(Iout.subs(vd, 0)/vin))
print("Rout = vd/I_out |vin=0 :", sp.simplify(vd/Iout.subs(vin, 0)))
print("Rin = oo")

print("=== (d) CG M1, input current at source, output = drain current I_out (down into drain) ===")
ns, vd = sp.symbols('v_s v_d')
# output terminal shorted (vd=0) for current gain; KCL source: iin + id1 = 0
s = sp.solve(sp.Eq(iin + idn(gm1, 0, 0, ns, ro1), 0), ns)[0]
id1 = idn(gm1, 0, 0, s, ro1)
AI = sp.simplify(id1/iin)
print("I_out(down into drain)/i_in =", AI, "(literal arrow directions: I_in up into source, I_out down into drain)")
print("|A_I| = 1; with I_out taken as current leaving drain upward (same sense as I_in), A_I = +1")
print("Rin exact (vd=0) =", sp.simplify(s/iin), " lambda=0 ->", sp.limit(sp.simplify(s/iin), ro1, oo))
# Rout: input current source open (iin=0); apply vd, it into drain
s2 = sp.solve([sp.Eq(it, idn(gm1, 0, vd, ns, ro1)), sp.Eq(0 + it, it)], [ns], dict=True)
# source node: only connected to transistor (ideal current source open) => id1 must be 0 => it=0 for any vd
print("Rout: source node floats except through M1 (ideal Iin source open) -> i_t = 0 for any v_d -> Rout = oo")
print("Check with finite source-side resistance RS: Rout =", end=' ')
RS = sp.symbols('R_S', positive=True)
s3 = sp.solve([sp.Eq(it, idn(gm1, 0, vd, ns, ro1)), sp.Eq(it, ns/RS)], [ns, it], dict=True)[0]
Ro = sp.simplify(vd/s3[it]); print(Ro, "; RS->oo:", sp.limit(Ro, RS, oo))
