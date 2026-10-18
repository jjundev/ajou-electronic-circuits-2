# p9 (E10.4) how close can VCM be to VCC: RC = 1k, IEE = 1 mA, no saturation (V_B <= V_C)
import sympy as sp
VCC, VCM, RC, IEE = sp.symbols('V_CC V_CM R_C I_EE', positive=True)
VX = VCC - RC*IEE/2            # both collectors at equilibrium (alpha ~ 1)
VCMmax = sp.solve(sp.Eq(VCM, VX), VCM)[0]
print('V_CM,max =', VCMmax)
print('V_CC - V_CM,max =', sp.N((VCC - VCMmax).subs({RC: 1000, IEE: sp.Rational(1, 1000)}), 4), 'V')
