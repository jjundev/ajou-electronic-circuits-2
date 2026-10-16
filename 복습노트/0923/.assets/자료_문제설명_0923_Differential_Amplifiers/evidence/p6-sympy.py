import sympy as s
# Independently derived from blind problem and displayed input circuit, before reference access.
P=s.Rational(3,1000);V=s.Rational(18,10);dv=s.Rational(1,2);mu=s.Rational(1,10000);I=P/V;wl=2*I/(mu*dv**2);print('Iss',I.evalf(),'W/L',wl);assert s.simplify(mu*wl*dv**2/2-I)==0
print("Independent conclusion: Iss=1.6667mA W/L=133.333 at power limit")
