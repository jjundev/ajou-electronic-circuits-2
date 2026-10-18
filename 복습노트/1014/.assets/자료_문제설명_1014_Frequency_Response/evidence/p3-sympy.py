import sympy as sp
x = sp.symbols('x', positive=True)
RD = sp.Integer(1000); CL = sp.Rational(1, 10**12)
# H = -gm RD/(1+s RD CL); |H|/|H0| = 1/sqrt(1+(w RD CL)^2) = 0.9
xs = sp.solve(sp.Eq(1/sp.sqrt(1+x**2), sp.Rational(9, 10)), x)[0]
print('w RD CL =', xs, '=', sp.N(xs))
w = xs/(RD*CL); f = w/(2*sp.pi)
print('omega =', sp.N(w), 'rad/s ; f =', sp.N(f), 'Hz')
print('check |H|/H0 at w:', sp.N(1/sp.sqrt(1+(w*RD*CL)**2)))
print('dB drop:', sp.N(20*sp.log(sp.Rational(9, 10), 10)))
