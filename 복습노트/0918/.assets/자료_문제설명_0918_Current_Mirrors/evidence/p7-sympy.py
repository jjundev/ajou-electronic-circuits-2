# P9.42: npn mirror generating 50 uA and 230 uA from I_REF = 130 uA, base currents neglected
import sympy as sp
IS_u, VT, IREF, n1, n2 = sp.symbols('I_Su V_T I_REF n1 n2', positive=True)
nR = sp.Symbol('n_REF', positive=True)  # reference area in units of A_E
# diode-connected Q_REF: IREF = nR*IS_u*exp(VBE/VT) -> VBE shared by Q1, Q2
VBE = VT*sp.log(IREF/(nR*IS_u))
I1 = sp.simplify(n1*IS_u*sp.exp(VBE/VT))
I2 = sp.simplify(n2*IS_u*sp.exp(VBE/VT))
print("I1 =", I1, "; I2 =", I2)
vals = {IREF: sp.Rational(130)}
s1 = sp.solve(sp.Eq(I1.subs(vals), 50), n1)[0]
s2 = sp.solve(sp.Eq(I2.subs(vals), 230), n2)[0]
print("A_E1/A_E,REF =", sp.simplify(s1/nR), "=", sp.N(s1/nR, 4))
print("A_E2/A_E,REF =", sp.simplify(s2/nR), "=", sp.N(s2/nR, 4))
# design choice: unit-transistor array, smallest integers: REF=13, Q1=5, Q2=23
d = {nR: 13, n1: 5, n2: 23, IREF: 130}
c1 = I1.subs(d); c2 = I2.subs(d)
print("check I1 =", c1, "uA ; I2 =", c2, "uA")
assert c1 == 50 and c2 == 230
print("ANSWER main: Q_REF:Q1:Q2 emitter areas = 13:5:23 (A_E1 = (5/13)A_E,REF ~ 0.385, A_E2 = (23/13)A_E,REF ~ 1.769); I1=50 uA, I2=230 uA verified")
