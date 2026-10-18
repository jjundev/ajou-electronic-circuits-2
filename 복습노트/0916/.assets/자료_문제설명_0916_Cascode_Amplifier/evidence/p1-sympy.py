# P1 (E9.6): MOS cascode, M1 top (gate Vb1) with parasitic R_P across D-S of M1, M2 bottom (gate Vb2) -> r_O2.
# Test: drive output with v_x, find i_x. Gates are AC ground.
import sympy as sp
gm1, ro1, ro2, RP, vx, vs, ix = sp.symbols('g_m1 r_O1 r_O2 R_P v_x v_s i_x', positive=True)
# node s (M1 source = M2 drain): ix flows down through M2 (r_O2, vgs2=0): vs = ix*ro2
# ix through M1 branch: gm1*vgs1 + (vx-vs)/ro1 + (vx-vs)/RP, vgs1 = -vs
eqs = [sp.Eq(vs, ix*ro2), sp.Eq(ix, gm1*(-vs) + (vx-vs)/ro1 + (vx-vs)/RP)]
sol = sp.solve(eqs, [vs, ix], dict=True)[0]
Rout = sp.simplify(vx/sol[ix])
print('Rout exact =', sp.factor(Rout))
rp = ro1*RP/(ro1+RP)
target = (1+gm1*ro2)*rp + ro2
print('simplify(Rout - [(1+gm1 rO2)(rO1||RP) + rO2]) =', sp.simplify(Rout-target))
approx = gm1*ro2*rp
print('ratio exact/approx(gm1 rO2 (rO1||RP)) as gm1->oo :', sp.limit(Rout/approx, gm1, sp.oo))
print('RP->oo limit (ordinary cascode):', sp.simplify(sp.limit(Rout, RP, sp.oo)))
