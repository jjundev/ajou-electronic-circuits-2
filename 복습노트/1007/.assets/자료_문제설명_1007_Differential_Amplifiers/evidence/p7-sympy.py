# P10.70 independent check: CMRR of Fig 10.91 (a) tail M3, (b) cascode tail M3 over M4; lambda=0 for M1,M2
from sympy import *
gm1,gm3,rO3,rO4,RD,dRD,vcm,vp,vt,vm = symbols('g_m1 g_m3 r_O3 r_O4 R_D DeltaR_D v_cm v_p v_t v_m', positive=True)
def acmdm(Rt):
    ic = gm1*(vcm - vp)
    s = solve(Eq(2*ic, vp/Rt), vp, dict=True)[0]
    return simplify(dRD*ic.subs(s)/vcm)
s = solve(Eq(gm3*(0-vm) + (vt-vm)/rO3, vm/rO4), vm, dict=True)[0]
Rtb = simplify(vt/(vm/rO4).subs(s))
print('(b) R_tail =', Rtb, ' minus (1+gm3 rO4) rO3 + rO4:', simplify(Rtb - ((1+gm3*rO4)*rO3 + rO4)))
Adm = gm1*RD
Ca = simplify(Adm/acmdm(rO3)); Cb = simplify(Adm/acmdm(Rtb))
print('(a) CMRR =', Ca, ' minus (RD/dRD)(1+2gm1 rO3):', simplify(Ca - RD/dRD*(1+2*gm1*rO3)))
print('(b) CMRR =', Cb, ' minus (RD/dRD)(1+2gm1[(1+gm3 rO4)rO3+rO4]):', simplify(Cb - RD/dRD*(1+2*gm1*((1+gm3*rO4)*rO3+rO4))))
r = simplify(Cb/Ca)
print('CMRR_b/CMRR_a =', r)
print('(CMRR_b/CMRR_a)/(gm3 rO4) with gm1->oo, gm3->oo:', limit(limit(r/(gm3*rO4), gm1, oo), gm3, oo))
md_b = RD/dRD*(1+2*gm1*gm3*rO3*rO4)
print('(b) md approx: ratio exact/md with gm3->oo =', limit(Cb/md_b, gm3, oo))
