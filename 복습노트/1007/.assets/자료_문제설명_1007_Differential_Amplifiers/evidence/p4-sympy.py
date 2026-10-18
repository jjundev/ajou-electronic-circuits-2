# E10.27 independent check: A_CM-DM of bipolar pair with emitter-degenerated tail Q3 (R1), VA=oo for Q1,Q2
from sympy import *
gm1,rpi1,gm3,rpi3,rO3,R1,dRC,vcm,ve,vp,vt = symbols('g_m1 r_pi1 g_m3 r_pi3 r_O3 R_1 DeltaR_C v_cm v_e v_p v_t', positive=True)
Rp = R1*rpi3/(R1+rpi3)
# R_out3: test source vt at collector of Q3, base AC ground, emitter node ve to ground through R1||rpi3
s = solve(Eq(gm3*(0-ve) + (vt-ve)/rO3, ve/Rp), ve, dict=True)[0]
Rout3 = simplify(vt/(ve/Rp).subs(s))
print('R_out3 =', Rout3, '; minus [1+gm3(R1||rpi3)] rO3 + R1||rpi3 :', simplify(Rout3 - ((1+gm3*Rp)*rO3 + Rp)))
# CM: KCL at P, both halves identical, emitter current = ic + ib
vbe = vcm - vp
ic = gm1*vbe
s2 = solve(Eq(2*(ic + vbe/rpi1), vp/Rout3), vp, dict=True)[0]
A = simplify(dRC*ic.subs(s2)/vcm)    # |vout1 - vout2|/vcm = DeltaR_C * ic/vcm
target = dRC/(1/gm1 + 2*Rout3)
print('A_CM-DM exact (with r_pi1) =', A)
print('limit r_pi1->oo of A minus target =', simplify(limit(A, rpi1, oo) - target))
md = dRC/(1/gm1 + 2*(1+gm3*Rp)*rO3)
print('md form (drops R1||rpi3 term): ratio target/md as rO3->oo =', simplify(limit(target/md, rO3, oo)))
