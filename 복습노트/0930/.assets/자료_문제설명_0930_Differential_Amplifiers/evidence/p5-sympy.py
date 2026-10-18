# p5 (E10.24) Fig 10.38(a): ideal current-source loads and tails, R_DD between drains, R_SS between sources, lambda=0
import sympy as sp
gm, RDD, RSS = sp.symbols('g_m R_DD R_SS', positive=True)
vin, vx, vy, p1, p2 = sp.symbols('v_in v_x v_y v_p1 v_p2')
i1 = gm*(vin/2 - p1); i2 = gm*(-vin/2 - p2)   # drain->source currents
eqs = [sp.Eq(i1 + (vx - vy)/RDD, 0),   # node X: only R_DD supplies M1's signal current
       sp.Eq(i2 + (vy - vx)/RDD, 0),   # node Y
       sp.Eq(i1 - (p1 - p2)/RSS, 0),   # node P1: M1 source current goes through R_SS
       sp.Eq(i2 - (p2 - p1)/RSS, 0)]   # node P2
# with ideal current sources the output CM level is undefined (one KCL is redundant); pin it with v_x + v_y = 0
s = sp.solve(eqs + [sp.Eq(vx + vy, 0)], [vx, vy, p1, p2], dict=True)[0]
print('consistency check, all 4 KCLs satisfied:', [sp.simplify(e.lhs.subs(s)) for e in eqs])
A = sp.simplify((s[vx]-s[vy])/vin)
T = -(RDD/2)/(RSS/2 + 1/gm)
print('A_v =', sp.factor(A))
print('simplify(A - (-(R_DD/2)/(R_SS/2 + 1/g_m))) =', sp.simplify(A - T))
print('equivalently A + R_DD/(R_SS + 2/g_m) =', sp.simplify(A + RDD/(RSS + 2/gm)))
