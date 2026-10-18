# 2021-1 midterm Q4 independent check
from sympy import *
u = 1e-6
ID6 = 2e-3; ID1 = ID6/2; lam = 0.1
K1 = 100*u*100/0.2; K3 = 50*u*200/0.2; K5 = 100*u*200/0.2
gm1 = sqrt(2*K1*ID1); gm3 = sqrt(2*K3*ID1); gm5 = sqrt(2*K5*ID6)
rO1 = 1/(lam*ID1); rO3 = rO1; rO5 = 1/(lam*ID6); rO6 = rO5
print('gm1=%g gm3=%g gm5=gm6=%g  rO1=rO3=%g rO5=rO6=%g' % (gm1, gm3, gm5, rO1, rO5))
vt, vm, vin, vx, vs = symbols('v_t v_m v_in v_x v_s')
s = solve(Eq(gm5*(0-vm) + (vt-vm)/rO5, vm/rO6), vm, dict=True)[0]
Rt = N(vt/(vm/rO6).subs(s))
print('R_tail exact =', Rt, '  approx gm5 rO5 rO6 =', gm5*rO5*rO6)
def half(Rl, Rd):
    i1 = gm1*(vin-vs) + (vx-vs)/rO1
    s = solve([Eq(vx/Rl + i1, 0), Eq(i1, vs/Rd)], [vx, vs], dict=True)[0]
    g = N(s[vx]/vin)
    return g, -g/Rl
Acm, Gm = half(rO3, 2*Rt)
print('(1) A_CM exact (single-ended) =', Acm, '  approx -rO3/(2 gm5 rO5 rO6) =', -rO3/(2*gm5*rO5*rO6))
dR = 50
Acmdm = dR*Gm
print('(1) A_CM-DM exact = dR*Gm =', Acmdm, '  dR/(1/gm1+2gm5 rO5 rO6) =', dR/(1/gm1 + 2*gm5*rO5*rO6), '  dR/(2gm5 rO5 rO6) =', dR/(2*gm5*rO5*rO6))
Adm = N(solve(Eq(vx/rO3 + gm1*vin + vx/rO1, 0), vx)[0]/vin)
print('(2) A_DM =', Adm, '  (-gm1 (rO1||rO3) =', -gm1*rO1*rO3/(rO1+rO3), ')')
C = abs(Adm)/Acmdm
print('(2) CMRR exact =', C, ' (', N(20*log(C, 10)), 'dB);  with approx A_CM-DM=5e-5: ', 50/(dR/(2*gm5*rO5*rO6)))
