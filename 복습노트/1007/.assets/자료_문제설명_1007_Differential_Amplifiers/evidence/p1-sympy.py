# P10.67 independent check: CM gain, M1,M2 lambda=0, M3 lambda!=0
from sympy import *
gm, RD, rO3, vin, vx, vs, ISS, Vov, lam = symbols('g_m R_D r_O3 v_in v_x v_s I_SS V_ov lambda', positive=True)
vin, vx, vs = symbols('v_in v_x v_s')  # node voltages: no sign assumption
# CM half circuit: M1 (lambda=0), load RD, source degeneration 2 r_O3
i1 = gm*(vin - vs)
sol = solve([Eq(vx/RD + i1, 0),        # KCL at X (RD to AC ground)
             Eq(i1, vs/(2*rO3))],      # KCL at P (half tail = 2 r_O3)
            [vx, vs], dict=True)[0]
A = simplify(sol[vx]/vin)
print('A_CM (half circuit) =', A)
print('A - (-RD/(1/gm+2rO3)) =', simplify(A + RD/(1/gm + 2*rO3)))
# gm = 2 I_D/Vov with I_D = ISS/2 ; rO3 = 1/(lambda ISS)
A2 = simplify(A.subs({gm: ISS/Vov, rO3: 1/(lam*ISS)}))
target = -RD*ISS/(2/lam + Vov)
print('A_CM in ISS, Vov, lambda =', A2)
print('simplify(A_CM - target) =', simplify(A2 - target))
print('limit lambda->0 (ideal tail):', limit(A2, lam, 0))
