# P7 (P9.22): |Av| = 500, beta=100, I1=1mA, VT=26mV -> min VA
import sympy as sp
VA = sp.symbols('V_A', positive=True)
VT = sp.Rational(26, 1000); I = sp.Rational(1, 1000)
gm = I/VT; ro = VA/I; rpi = 100/gm
par = lambda a, b: a*b/(a+b)
sol = sp.solve(sp.Eq(gm*gm*ro*par(ro, rpi), 500), VA)
print('approx |Av| = gm^2 rO (rO||rpi): VA =', sol, [sp.N(v) for v in sol])
Rout = (1+gm*par(ro, rpi))*ro + par(ro, rpi)
print('full Rout, Gm=gm1: VA =', sp.nsolve(gm*Rout - 500, VA, 0.6))
vin, x, vo = sp.symbols('v_in v_x v_o')
iQ1 = gm*vin + x/ro; iQ2c = gm*(0-x) + (vo-x)/ro; ib2 = -x/rpi
s = sp.solve([sp.Eq(iQ2c, 0), sp.Eq(iQ2c+ib2, iQ1)], [x, vo], dict=True)[0]
Av_ex = sp.simplify(s[vo]/vin)
print('exact nodal: VA =', sp.nsolve(-Av_ex - 500, VA, 0.6))
print('exact nodal |Av| at VA=0.650 V =', sp.N(-Av_ex.subs(VA, sp.Rational(13,20)), 6))
