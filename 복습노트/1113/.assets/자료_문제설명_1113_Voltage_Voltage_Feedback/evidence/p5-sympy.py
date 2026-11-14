# p5 (E12.13) independent polarity check, Fig 12.29
# Two-stage CS (M1-RD1 -> node A -> M2 gate, M2-RD2 -> vout), divider RF1-RF2 from vout, mid node X -> M1 source.
import sympy as sp

gm1, gm2, ro1, ro2, RD1, RD2, RF1, RF2 = sp.symbols('g_m1 g_m2 r_o1 r_o2 R_D1 R_D2 R_F1 R_F2', positive=True)
A, Vo, X, Vt = sp.symbols('V_A V_out V_X V_test')

print("== Qualitative chain (vin up) ==")
chain = [
 ("vin up", "M1 Vgs up -> I_D1 up (M1 = CS with source at X)"),
 ("I_D1 up", "V_A = VDD - I_D1*R_D1 down (inversion 1)"),
 ("V_A down", "M2 Vgs down -> I_D2 down -> vout up (inversion 2)"),
 ("vout up", "V_X = vout*RF2/(RF1+RF2) up (divider, non-inverting)"),
 ("V_X up (M1 source)", "M1 Vgs = vin - V_X down -> I_D1 decreases: OPPOSES original I_D1 increase"),
]
for a,b in chain: print(f"  {a:22s} => {b}")
print("  conclusion: returned quantity opposes original effect -> NEGATIVE feedback")

print("\n== Symbolic loop-break test: vin=0, break at M2 gate (infinite gate impedance -> no loading) ==")
# M2 gate driven by V_test; returned signal = V_A (node that normally drives M2 gate)
id1 = gm1*(0 - X) + (A - X)/ro1       # drain->source current of M1 (gate at vin=0, source at X)
id2 = gm2*Vt + (Vo - 0)/ro2            # drain->source current of M2
eqs = [
  sp.Eq(-A/RD1, id1),                  # KCL at A: current in from RD1 (VDD ac gnd) = id1
  sp.Eq(-Vo/RD2, id2 + (Vo - X)/RF1),  # KCL at vout
  sp.Eq(id1 + (Vo - X)/RF1, X/RF2),    # KCL at X
]
sol = sp.solve(eqs, [A, Vo, X], dict=True)[0]
H = sp.simplify(sol[A]/Vt)
print("  V_ret/V_test (exact, with r_o) =", H)
num, den = sp.fraction(sp.together(H))
num = sp.expand(num); den = sp.expand(den)
print("  numerator   =", num)
print("  denominator =", den)
def all_pos(expr):
    return all(t.could_extract_minus_sign() is False for t in sp.Add.make_args(expr))
print("  numerator all terms same sign? ", all(t.could_extract_minus_sign() for t in sp.Add.make_args(num)) or all_pos(num))
print("  num terms negative:", [t.could_extract_minus_sign() for t in sp.Add.make_args(num)])
print("  den terms positive:", all_pos(den))
print("  -V_ret/V_test is_positive for all positive parameters:", sp.simplify(-H).is_positive)
Hinf = sp.simplify(sp.limit(sp.limit(H, ro1, sp.oo), ro2, sp.oo))
print("  ro1,ro2 -> oo :", Hinf)
print("  ro->oo, -H positive?", sp.simplify(-Hinf).is_positive)

print("\n== Cross-check: closed-loop vout/vin sign and Blackman-style consistency ==")
vin = sp.symbols('v_in')
id1c = gm1*(vin - X) + (A - X)/ro1
id2c = gm2*A + Vo/ro2
eqc = [sp.Eq(-A/RD1, id1c), sp.Eq(-Vo/RD2, id2c + (Vo - X)/RF1), sp.Eq(id1c + (Vo - X)/RF1, X/RF2)]
sc = sp.solve(eqc, [A, Vo, X], dict=True)[0]
Acl = sp.simplify(sp.limit(sp.limit(sc[Vo]/vin, ro1, sp.oo), ro2, sp.oo))
print("  vout/vin (ro->oo) =", sp.factor(Acl), " positive?", Acl.is_positive)
# closed-loop gain should approach 1+RF1/RF2 as loop gain -> oo (negative-feedback signature)
lim = sp.limit(Acl, gm1, sp.oo); lim = sp.limit(lim, gm2, sp.oo)
print("  limit gm1,gm2->oo of vout/vin =", sp.simplify(lim), " ; equals 1+RF1/RF2 ?", sp.simplify(lim-(1+RF1/RF2))==0)

print("\nVERDICT: V_ret/V_test < 0 for all positive g_m, r_o, R  => NEGATIVE feedback")
