# p7 (P10.54, Fig 10.39(a)): bipolar cascode diff pair, ideal current-source loads I1,I2, beta=100.
# Half circuit: Q1 CE (emitter AC gnd), Q3 CB (base AC gnd), out at Q3 collector, ideal load.
import sympy as sp
gm, ro, rpi, vin = sp.symbols('g_m r_O r_pi v_in', positive=True)
vX, vo = sp.symbols('v_X v_o')
ic = lambda b,c,e: gm*(b-e) + (c-e)/ro
ib = lambda b,e: (b-e)/rpi
eqs = [sp.Eq(ic(0,vo,vX), 0),                                  # out node: ideal load
       sp.Eq(ic(vin,vX,0) - ic(0,vo,vX) - ib(0,vX), 0)]        # node X: i_c1 leaves X; i_e3 = i_c3+i_b3 enters X
s = sp.solve(eqs,[vX,vo],dict=True)[0]
A = sp.simplify(-s[vo]/vin)
R = ro*rpi/(ro+rpi)
A_std = gm*(gm*ro*R)
A_mid = gm*R*(1+gm*ro)   # exact closed form
print('exact |A| =', sp.factor(A))
print('simplify(exact - g_m (r_O||r_pi)(1+g_m r_O)) :', sp.simplify(A - A_mid))
print('limit exact/std (g_m r_O -> oo, fixed beta): ', sp.limit((A/A_std).subs({gm:sp.Symbol("u")/ro, rpi:100*ro/sp.Symbol("u")}), sp.Symbol('u'), sp.oo))
u, VT = sp.symbols('u V_T', positive=True)       # u = V_A/V_T = g_m r_O, beta = g_m r_pi
beta = 100
sub = {gm: 1, ro: u, rpi: beta}                   # gain is dimensionless in g_m*(.) form
Au_std = sp.simplify(A_std.subs(sub)); Au_ex = sp.simplify(A.subs(sub))
print('A_std(u) =', Au_std, ' ; A_exact(u) =', sp.simplify(Au_ex))
us = [r for r in sp.solve(sp.Eq(Au_std,4000),u) if r.is_positive][0]
ue = [r for r in sp.solve(sp.Eq(Au_ex,4000),u) if r.is_positive][0]
print('std:   V_A/V_T =', us, '=', sp.N(us,6), ' -> V_A =', sp.N(us*sp.Rational(26,1000),5),'V (V_T=26mV),', sp.N(us*sp.Rational(25,1000),5),'V (25mV)')
print('exact: V_A/V_T =', sp.N(ue,6), ' -> V_A =', sp.N(ue*sp.Rational(26,1000),5),'V (V_T=26mV),', sp.N(ue*sp.Rational(25,1000),5),'V (25mV)')
print('ratio A_exact/A_std as u->oo:', sp.limit(Au_ex/Au_std, u, sp.oo))
print('ratio at u_std:', sp.N((Au_ex/Au_std).subs(u,us),5))
