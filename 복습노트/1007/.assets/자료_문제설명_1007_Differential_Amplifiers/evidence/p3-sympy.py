# P10.69 independent check: Fig 10.90 (a) cascode tail M5/M6, (b) cascode PMOS loads (M3 over M5), tail M7
from sympy import *
gm1,rO1,rO3,rO5,rO6,rO7,gm3,gm5,vin,vx,vs = symbols('g_m1 r_O1 r_O3 r_O5 r_O6 r_O7 g_m3 g_m5 v_in v_x v_s', positive=True)
vin, vx, vs = symbols('v_in v_x v_s')  # node voltages: no sign assumption
vt, vm = symbols('v_t v_m')
def cs_degen(Rload, Rdeg):
    i1 = gm1*(vin - vs) + (vx - vs)/rO1
    s = solve([Eq(vx/Rload + i1, 0), Eq(i1, vs/Rdeg)], [vx, vs], dict=True)[0]
    return simplify(s[vx]/vin)
# (a) tail resistance of cascode M5 over M6 by test source
s = solve(Eq(gm5*(0 - vm) + (vt - vm)/rO5, vm/rO6), vm, dict=True)[0]
Rt = simplify(vt/(vm/rO6).subs(s))
print('(a) R_tail =', Rt, ' minus (1+gm5 rO6) rO5 + rO6:', simplify(Rt - ((1+gm5*rO6)*rO5 + rO6)))
Aa = cs_degen(rO3, 2*Rt)
print('(a) exact A_CM =', Aa)
print('(a) ratio exact/(-rO3/(2 gm5 rO5 rO6)), gm1->oo, gm5->oo:', simplify(limit(limit(Aa/(-rO3/(2*gm5*rO5*rO6)), gm1, oo), gm5, oo)))
# (b) up resistance of PMOS cascode M3 (gate AC gnd) over M5 (rO5)
s = solve(Eq(gm3*(0 - vm) + (vt - vm)/rO3, vm/rO5), vm, dict=True)[0]
Rup = simplify(vt/(vm/rO5).subs(s))
print('(b) R_up =', Rup)
Ab = cs_degen(Rup, 2*rO7)
print('(b) exact A_CM =', simplify(Ab))
Rdown = (1 + gm1*2*rO7)*rO1 + 2*rO7
Gm = gm1*rO1/(rO1 + (1+gm1*rO1)*2*rO7)
print('(b) Ab - (-Gm*(Rup||Rdown)) =', simplify(Ab + Gm*Rup*Rdown/(Rup+Rdown)))
tb = -(gm3*rO3*rO5*2*gm1*rO1*rO7/(gm3*rO3*rO5 + 2*gm1*rO1*rO7))/(2*rO7)
g,k = symbols('g k', positive=True)
print('(b) ratio exact/[-(gm3 rO3 rO5 || 2 gm1 rO1 rO7)/(2 rO7)], gm1=g, gm3=k g, g->oo:', simplify(limit((Ab/tb).subs({gm1:g, gm3:k*g}), g, oo)))
nv = {gm1:1e-3,gm3:1e-3,gm5:1e-3,rO1:2e4,rO3:2e4,rO5:2e4,rO6:2e4,rO7:2e4}
print('numeric (gm=1mS, ro=20k): (a) exact', N(Aa.subs(nv)), ' approx', N((-rO3/(2*gm5*rO5*rO6)).subs(nv)))
print('                          (b) exact', N(Ab.subs(nv)), ' approx', N(tb.subs(nv)))
nv2 = {gm1:1e-3,gm3:1e-3,gm5:1e-3,rO1:1e5,rO3:1e5,rO5:1e5,rO6:1e5,rO7:1e5}
print('numeric (gm=1mS, ro=100k): (a) exact', N(Aa.subs(nv2)), ' approx', N((-rO3/(2*gm5*rO5*rO6)).subs(nv2)))
print('                           (b) exact', N(Ab.subs(nv2)), ' approx', N(tb.subs(nv2)), ' (Rup only:', N((-gm3*rO3*rO5/(2*rO7)).subs(nv2)), ')')
