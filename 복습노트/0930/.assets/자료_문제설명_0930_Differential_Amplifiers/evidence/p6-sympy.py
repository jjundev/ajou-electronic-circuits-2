# p6 (X10.24) Fig 10.38(a) with top current-source loads replaced by diode-connected PMOS (g_mP), lambda=0
import sympy as sp
gm, gmp, RDD, RSS = sp.symbols('g_mN g_mP R_DD R_SS', positive=True)
vin, vx, vy, p1, p2 = sp.symbols('v_in v_x v_y v_p1 v_p2')
i1 = gm*(vin/2 - p1); i2 = gm*(-vin/2 - p2)
eqs = [sp.Eq(i1 + (vx - vy)/RDD + gmp*vx, 0), sp.Eq(i2 + (vy - vx)/RDD + gmp*vy, 0),
       sp.Eq(i1 - (p1 - p2)/RSS, 0), sp.Eq(i2 - (p2 - p1)/RSS, 0)]
# source-side tails are ideal sources: one source-node KCL redundant; pin p1 + p2 = 0 (symmetry)
s = sp.solve(eqs[:3] + [sp.Eq(p1 + p2, 0)], [vx, vy, p1, p2], dict=True)[0]
print('all 4 KCLs satisfied:', [sp.simplify(e.lhs.subs(s)) for e in eqs])
A = sp.simplify((s[vx]-s[vy])/vin)
par = lambda a, b: a*b/(a+b)
T = -par(1/gmp, RDD/2)/(RSS/2 + 1/gm)
print('A_v =', sp.factor(A))
print('simplify(A - (-(1/g_mP || R_DD/2)/(R_SS/2 + 1/g_mN))) =', sp.simplify(A - T))
print('g_mP -> 0 recovers p5 result:', sp.simplify(sp.limit(A, gmp, 0) + RDD/(RSS + 2/gm)))
