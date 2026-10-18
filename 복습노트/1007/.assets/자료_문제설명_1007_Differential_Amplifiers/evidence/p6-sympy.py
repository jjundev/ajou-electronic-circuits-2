# E10.28 independent check: CMRR of Fig 10.48
from sympy import *
gm1,gm3,rpi3,rO3,R1,RC,dRC,vin,vx = symbols('g_m1 g_m3 r_pi3 r_O3 R_1 R_C DeltaR_C v_in v_x', positive=True)
vin, vx, vs = symbols('v_in v_x v_s')  # node voltages: no sign assumption
Rp = R1*rpi3/(R1+rpi3)
Rout3 = (1+gm3*Rp)*rO3 + Rp
Acmdm = dRC/(1/gm1 + 2*Rout3)
# differential half circuit (P = AC ground, VA=oo): KCL at collector
Adm = simplify(-solve(Eq(vx/RC + gm1*vin, 0), vx)[0]/vin)
CMRR = simplify(Adm/Acmdm)
print('|A_DM| =', Adm)
print('CMRR =', CMRR)
print('CMRR - gm1 RC (1/gm1+2Rout3)/dRC =', simplify(CMRR - gm1*RC*(1/gm1+2*Rout3)/dRC))
print('CMRR - (RC/dRC)(1+2gm1 Rout3) =', simplify(CMRR - RC/dRC*(1+2*gm1*Rout3)))
print('ratio with mismatch DM gain gm1(RC+dRC/2), dRC->0:', simplify(limit(gm1*(RC+dRC/2)/Acmdm/CMRR, dRC, 0)))
md = gm1*RC/dRC*(1/gm1 + 2*(1+gm3*Rp)*rO3)
print('md form (drops 2(R1||rpi3)): ratio CMRR/md as rO3->oo =', simplify(limit(CMRR/md, rO3, oo)))
