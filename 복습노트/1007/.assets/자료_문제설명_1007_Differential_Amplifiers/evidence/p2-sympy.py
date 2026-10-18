# P10.68 independent check: CM gain of NMOS pair with PMOS current-source loads M3,M4 and tail M5
from sympy import *
gm1, rO1, rO3, rO5, vin, vx, vs = symbols('g_m1 r_O1 r_O3 r_O5 v_in v_x v_s', positive=True)
vin, vx, vs = symbols('v_in v_x v_s')  # node voltages: no sign assumption
i1 = gm1*(vin - vs) + (vx - vs)/rO1      # M1 drain->source current
sol = solve([Eq(vx/rO3 + i1, 0), Eq(i1, vs/(2*rO5))], [vx, vs], dict=True)[0]
A = simplify(sol[vx]/vin)
print('A_CM exact (single-ended, CM half circuit) =', A)
Gm = gm1*rO1/(rO1 + (1 + gm1*rO1)*2*rO5)
Rdown = (1 + gm1*2*rO5)*rO1 + 2*rO5
Rout = rO3*Rdown/(rO3 + Rdown)
print('A - (-Gm*Rout) =', simplify(A + Gm*Rout))
print('limit gm1->oo :', simplify(limit(A, gm1, oo)))
print('ratio exact/(-rO3/(2 rO5)) for gm1->oo then rO1->oo:', limit(limit(A/(-rO3/(2*rO5)), gm1, oo), rO1, oo))
nv = {gm1: 1e-3, rO1: 2e4, rO3: 2e4, rO5: 2e4}
print('numeric example exact:', N(A.subs(nv)), ' approx -rO3/(2rO5):', N((-rO3/(2*rO5)).subs(nv)))
print('Note: differential output (vx - vy) of a perfectly symmetric circuit has CM gain 0.')
