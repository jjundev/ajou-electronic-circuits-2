# p3 (E10.22) diff pair with diode-connected PMOS loads, lambda != 0; full-circuit small-signal KCL
import sympy as sp
gm1, gm3, ro1, ro3 = sp.symbols('g_m1 g_m3 r_o1 r_o3', positive=True)
vin, vx, vy, vp = sp.symbols('v_in v_x v_y v_p')
def i1(vg, vd):  # drain->source current of M1/M2
    return gm1*(vg - vp) + (vd - vp)/ro1
eqs = [sp.Eq(i1(vin/2, vx) + gm3*vx + vx/ro3, 0),      # node X (diode M3: gm3 + 1/ro3 to ac ground)
       sp.Eq(i1(-vin/2, vy) + gm3*vy + vy/ro3, 0),     # node Y
       sp.Eq(i1(vin/2, vx) + i1(-vin/2, vy), 0)]       # node P, ideal tail
s = sp.solve(eqs, [vx, vy, vp], dict=True)[0]
A = sp.simplify((s[vx]-s[vy])/vin)
par = lambda *z: 1/sum(1/zz for zz in z)
target = -gm1*par(1/gm3, ro1, ro3)
print('A_v = (v_x - v_y)/(v_in1 - v_in2) =', sp.factor(A))
print('simplify(A - (-g_m1 (1/g_m3 || r_o1 || r_o3))) =', sp.simplify(A-target))
print('lambda->0 limit:', sp.limit(sp.limit(A, ro1, sp.oo), ro3, sp.oo))
