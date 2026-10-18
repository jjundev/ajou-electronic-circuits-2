import sympy as sp
R1, IC = sp.symbols('R_1 I_C', positive=True)
f3 = 10**9; CL = sp.Rational(2, 10**12); VCC = sp.Rational(5, 2); P = sp.Rational(2, 1000); VT = sp.Rational(26, 1000)
# KCL out: gm Vin + Vout/R1 + s CL Vout = 0 -> pole 1/(R1 CL); Av0 = gm R1
R1v = sp.solve(sp.Eq(1/(2*sp.pi*R1*CL), f3), R1)[0]
ICv = sp.solve(sp.Eq(IC*VCC, P), IC)[0]
gm = ICv/VT; A = gm*R1v
print('R1 =', R1v, '=', sp.N(R1v), 'ohm'); print('IC =', ICv, 'A'); print('gm =', sp.N(gm), 'S')
print('Av = gm R1 =', sp.N(A))
print('symbolic Av - P/(VCC VT 2 pi f CL) =', sp.simplify(A - P/(VCC*VT*2*sp.pi*f3*CL)))
print('headroom IC*R1 =', sp.N(ICv*R1v), 'V (<< VCC, Q1 stays active)')
