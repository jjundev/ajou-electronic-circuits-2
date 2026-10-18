# E10.20 independent: Iss = P/VDD, W/L from dVin,max = sqrt(2 Iss/(k' W/L))
import sympy as sp
WL=sp.symbols('WL',positive=True)
P,VDD,kp,dV=sp.Rational(3,1000),sp.Rational(18,10),sp.Rational(100,10**6),sp.Rational(1,2)
Iss=P/VDD
wl=sp.solve(sp.Eq(dV,sp.sqrt(2*Iss/(kp*WL))),WL)[0]
print('I_SS =',Iss,'A =',float(Iss)*1e3,'mA')
print('W/L =',wl,'=',float(wl))
print('check W/L-400/3 =',sp.simplify(wl-sp.Rational(400,3)))
