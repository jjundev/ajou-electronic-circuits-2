# p9 (P10.66, Fig 10.87): CM gain with Q1,Q2 V_A=inf, tail Q3 output resistance r_O3 = V_A/I_C (I_C = I_EE).
import sympy as sp
gm, rpi, RC, ro3, vcm, IC, VA, VT = sp.symbols('g_m r_pi R_C r_O3 v_CM I_C V_A V_T', positive=True)
vP, o1 = sp.symbols('v_P v_o1')
# Q1=Q2 identical, both bases at v_CM, collectors to R_C, emitters at P; Q3 -> r_O3 from P to gnd
ie = (gm + 1/rpi)*(vcm - vP)                 # emitter current of each (r_O = inf)
s = sp.solve([sp.Eq(2*ie, vP/ro3), sp.Eq(o1, -RC*gm*(vcm-vP))],[vP,o1],dict=True)[0]
Acm = sp.simplify(s[o1]/vcm)
print('A_CM exact =', Acm)
std = -(RC/2)/(1/(2*gm)+ro3)
print('limit beta->oo (r_pi->oo) of A_CM - std:', sp.simplify(sp.limit(Acm,rpi,sp.oo)-std))
# with g_m = I_C/(2V_T) (each carries I_C/2), r_O3 = V_A/I_C:
A = sp.simplify(std.subs({gm: IC/(2*VT), ro3: VA/IC}))
print('|A_CM| =', sp.simplify(-A), '  -> check equals R_C I_C/(2(V_A+V_T)):', sp.simplify(-A - RC*IC/(2*(VA+VT))))
# |A_CM|<0.01  <=> R_C I_C < 0.02 (V_A+V_T)   (denominator positive, monotone)
print('solve |A_CM| = 1/100 for R_C*I_C:', sp.solve(sp.Eq(-A, sp.Rational(1,100)), RC)[0]*IC)
# exact (finite beta) gives |A_CM| = R_C I_C a /(...); show beta-correction is factor alpha:
print('exact/std ratio:', sp.simplify(Acm/std), ' (-> 1 as r_pi->oo)')
