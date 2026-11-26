"""Fig 12.61(a) 공통 정의 (P3·P4 대조용). M1 CG(게이트 AC 접지, r_o1=∞), M2 PMOS CS(r_O2 유한), R_F: N–P, R_M: P–접지."""
import sympy as sp
g1,g2,RD,RF,RM,RL,r2,Iin,It = sp.symbols('g_m1 g_m2 R_D R_F R_M R_L r_O2 I_in I_t', positive=True)
vN,vX,vD,vP = sp.symbols('v_N v_X v_D v_P')
par = lambda a,b: a*b/(a+b)

def kcl(Iin_val, laser=True, RLv=RL):
    i1 = g1*(0-vN)                      # M1 drain->source, arrives at N
    i2 = g2*(0-vX) + (0-vD)/r2          # M2 PMOS into D
    eqs = [sp.Eq(Iin_val + i1 - (vN-vP)/RF, 0), sp.Eq(-vX/RD, i1)]
    if laser:
        eqs += [sp.Eq(i2, (vD-vP)/RLv), sp.Eq(i2 + (vN-vP)/RF, vP/RM)]
    else:   # laser removed: test current It injected at D, extracted at P
        eqs += [sp.Eq(i2 + It, 0), sp.Eq(-It + (vN-vP)/RF, vP/RM)]
    s = sp.solve(eqs, [vN,vX,vD,vP], dict=True)[0]
    return s, i2.subs(s)

Ro = r2 + par(RF,RM)
A_open = (RF+RM)*RD/(RF+RM+1/g1) * (-g2*r2)/(r2+RL+par(RM,RF))
K = -RM/(RM+RF)
T = K*A_open
A0 = A_open.subs(RL, 0)
T0 = K*A0
