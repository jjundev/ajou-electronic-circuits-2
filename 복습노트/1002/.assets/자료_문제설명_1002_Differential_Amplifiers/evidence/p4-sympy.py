# p4 (X10.13): Fig 10.22(a) with V_A=4 V all, R1=R2=10k, I_EE=1 mA. Gain = -g_m1 (r_O1||r_O3||R_1), I_C=0.5 mA.
import sympy as sp
VT = sp.symbols('V_T', positive=True)
IC = sp.Rational(1,2)/1000; VA = 4; R1 = 10000
ro = VA/IC
gm = IC/VT
par = 1/(1/ro+1/ro+sp.Rational(1,R1))
A = sp.nsimplify(-gm*par)
print('r_O =', ro, 'ohm ; r_O1||r_O3||R1 =', sp.N(par), 'ohm')
print('A_d = ', A, ' = ', sp.N(A*VT), '/ V_T')
for vt in [sp.Rational(26,1000), sp.Rational(25,1000)]:
    print('  V_T =', vt, '->  A_d =', sp.N(A.subs(VT,vt),6))
