# 2023-1 midterm Q4 independent check
from sympy import *
u = 1e-6
VDD = 1.8; ID3 = 1e-3; RD = 1e3; dRD = 20; VTH = 0.4; lam = 0.1
K1 = 100*u*200/0.2; K3 = 100*u*400/0.2
ID1 = ID3/2
Vov1 = sqrt(2*ID1/K1); Vov3 = sqrt(2*ID3/K3)
print('Vov1=%g Vov3=%g VGS1=%g' % (Vov1, Vov3, VTH+Vov1))
Vmin = VTH + Vov1 + Vov3
VmaxL = VDD - RD*ID1 + VTH; VmaxR = VDD - (RD+dRD)*ID1 + VTH
print('(1) V_CM,min = VGS1 + Vov3 =', Vmin, '; V_CM,max = VDD - RD ID1 + VTH =', VmaxL, ' (RD+dRD side:', VmaxR, ')')
gm1 = 2*ID1/Vov1; rO3 = 1/(lam*ID3); rO1 = 1/(lam*ID1)
print('gm1=%g rO3=%g rO1=%g' % (gm1, rO3, rO1))
vin, vx, vs = symbols('v_in v_x v_s')
def half(Rl, Rd, ro=None):
    i1 = gm1*(vin-vs) + ((vx-vs)/ro if ro else 0)
    s = solve([Eq(vx/Rl + i1, 0), Eq(i1, vs/Rd)], [vx, vs], dict=True)[0]
    g = N(s[vx]/vin)
    return g, -g/Rl
Acm, Gm = half(RD, 2*rO3)
print('(2) A_CM = -RD/(1/gm1+2rO3) =', Acm, '  (incl. rO1:', half(RD, 2*rO3, rO1)[0], ')')
Acmdm = dRD*Gm
print('(2) A_CM-DM = dRD/(1/gm1+2rO3) =', Acmdm, '  crude dRD/(2rO3) =', dRD/(2*rO3))
Adm = gm1*RD
print('(3) A_DM = gm1 RD =', Adm, '  CMRR =', Adm/Acmdm, ' (', N(20*log(Adm/Acmdm, 10)), 'dB)')
print('    incl. rO1: A_DM = gm1(RD||rO1) =', gm1*RD*rO1/(RD+rO1), '  CMRR =', N(gm1*RD*rO1/(RD+rO1)/(dRD*half(RD, 2*rO3, rO1)[1])))
# full two-sided KCL with finite rO1=rO2, rO3 tail, mismatch on side 2
v1,v2,vP,vo1,vo2 = symbols('v1 v2 vP vo1 vo2')
def full(a1,a2):
    eqs=[Eq(-vo1/RD, gm1*(a1-vP)+(vo1-vP)/rO1),          # current from RD into drain1 = M1 current
         Eq(-vo2/(RD+dRD), gm1*(a2-vP)+(vo2-vP)/rO1),
         Eq(vP/rO3, gm1*(a1-vP)+(vo1-vP)/rO1 + gm1*(a2-vP)+(vo2-vP)/rO1)]
    s=solve(eqs,[vo1,vo2,vP],dict=True)[0]; return s[vo1], s[vo2]
c1,c2=full(1,1); d1,d2=full(0.5,-0.5)
print('full KCL (rO1 incl.): A_CM out1 =',N(c1),' out2 =',N(c2),' A_CM-DM =',N(abs(c1-c2)),' A_DM =',N(d1-d2),' CMRR =',N(abs(d1-d2)/abs(c1-c2)))
print('vout2-side A_CM = -(RD+dRD)/(1/gm1+2rO3) =', -(RD+dRD)/(1/gm1+2*rO3))
