# P6 (E9.9): bipolar cascode Fig 9.16(b), Ic=1mA, VA=5V, beta=100, ideal current-source load
import sympy as sp
VT = sp.Rational(26, 1000); I = sp.Rational(1, 1000)
gm = I/VT; ro = 5/I; rpi = 100/gm
par = lambda a, b: a*b/(a+b)
apx = -gm*gm*ro*par(ro, rpi)
print('rO||rpi =', sp.N(par(ro, rpi)), ' Rout~gm rO (rO||rpi)=', sp.N(gm*ro*par(ro, rpi)))
print('Av approx -gm1 gm2 rO2 (rO1||rpi2) =', sp.N(apx, 6))
Rout = (1+gm*par(ro, rpi))*ro + par(ro, rpi)
print('Av with full Rout, Gm=gm1:', sp.N(-gm*Rout, 6))
vin, x, vo = sp.symbols('v_in v_x v_o')
iQ1 = gm*vin + x/ro
iQ2c = gm*(0-x) + (vo-x)/ro
ib2 = (0-x)/rpi
s = sp.solve([sp.Eq(iQ2c, 0), sp.Eq(iQ2c + ib2, iQ1)], [x, vo], dict=True)[0]
Av_ex = s[vo]/vin
print('exact nodal Av =', sp.N(Av_ex, 6), ' ratio exact/approx =', sp.N(Av_ex/apx, 6))
