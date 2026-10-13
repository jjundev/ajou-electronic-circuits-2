# P10.75: active-load bipolar diff pair (Fig 10.96), |Av| = 100, V_A,n = 5 V -> V_A,p ?
import sympy as sp
gm1,gm2,gm3,gm4,ro1,ro2,ro3,ro4,vd = sp.symbols('g_m1 g_m2 g_m3 g_m4 r_o1 r_o2 r_o3 r_o4 v_d', positive=True)
vP,vX,vo = sp.symbols('v_P v_X v_out')
v1, v2 = vd/2, -vd/2
# currents flowing down (collector->emitter) in Q1,Q2 ; Q3,Q4 pnp: current from VCC into X / out (beta->inf, r_pi->inf)
i1 = gm1*(v1-vP) + (vX-vP)/ro1
i2 = gm2*(v2-vP) + (vo-vP)/ro2
i3 = gm3*(0-vX) + (0-vX)/ro3     # diode-connected pnp: v_EB = -vX
i4 = gm4*(0-vX) + (0-vo)/ro4
eqs = [sp.Eq(i3,i1), sp.Eq(i4,i2), sp.Eq(i1+i2,0)]  # ideal tail source
sol = sp.solve(eqs,[vP,vX,vo],dict=True)[0]
# symmetric pair: gm1=gm2=gm, gm3=gm4=gmp, ro1=ro2=ron, ro3=ro4=rop
gm,gmp,ron,rop = sp.symbols('g_m g_mp r_on r_op', positive=True)
Av = sp.simplify((sol[vo]/vd).subs({gm1:gm,gm2:gm,gm3:gmp,gm4:gmp,ro1:ron,ro2:ron,ro3:rop,ro4:rop}))
print('Exact Av =', Av)
target = gm*ron*rop/(ron+rop)
print('Av - gm(ron||rop) =', sp.simplify(Av-target))
print('lim gmp->inf (Av - gm(ron||rop)) =', sp.simplify(sp.limit(Av-target, gmp, sp.oo)))
# substitute bipolar params: gm = IC/VT, ron = VAn/IC, rop = VAp/IC
IC,VT,VAn,VAp = sp.symbols('I_C V_T V_An V_Ap', positive=True)
A_bjt = sp.simplify(target.subs({gm:IC/VT, ron:VAn/IC, rop:VAp/IC}))
print('Av (bipolar) =', A_bjt)
VApsol = sp.solve(sp.Eq(A_bjt.subs({VAn:5, VT:sp.Rational(26,1000)}),100), VAp)
print('V_A,p (VT=26mV) =', VApsol, '=', [sp.N(x,6) for x in VApsol], 'V')
VApsol25 = sp.solve(sp.Eq(A_bjt.subs({VAn:5, VT:sp.Rational(25,1000)}),100), VAp)
print('V_A,p (VT=25mV) =', VApsol25, '=', [sp.N(x,6) for x in VApsol25], 'V')
# exact-gain check with numbers (I_C arbitrary, e.g. 1 mA)
num = {gm:sp.Rational(1,26)/sp.Rational(1,1000)*sp.Rational(1,1000), ron:5/sp.Rational(1,1000), rop:VApsol[0]/sp.Rational(1,1000)}
num[gmp]=num[gm]
print('Exact Av with numbers (IC=1mA, VT=26mV) =', sp.N(Av.subs(num),8))
print('approx Av with numbers =', sp.N(target.subs(num),8))
