# p10 (P10.14) Fig 10.11(a): VCC = 2.5 V, Vin1 = 2 V, Vin2 = 1 V, IEE = 1 mA; Q1 active -> V_X >= V_B1
import sympy as sp
RC = sp.symbols('R_C', positive=True)
VCC, Vin1, Vin2, IEE, VT = sp.Rational(5, 2), 2, 1, sp.Rational(1, 1000), sp.Rational(26, 1000)
frac = 1/(1 + sp.exp(-(Vin1 - Vin2)/VT))      # share of IEE in Q1
print('I_C1/I_EE at 1 V differential (V_T = 26 mV): 1 -', sp.N(1 - frac, 6))
RCmax = sp.solve(sp.Eq(VCC - RC*IEE, Vin1), RC)[0]
print('R_C,max (I_C1 = I_EE) =', RCmax, 'ohm')
print('R_C,max with exact share =', sp.N((VCC - Vin1)/(IEE*frac), 12), 'ohm')
