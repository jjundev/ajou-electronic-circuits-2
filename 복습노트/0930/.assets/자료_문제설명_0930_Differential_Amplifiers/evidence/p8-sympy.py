# p8 (P10.12) Fig 10.9, I_EE -> I_EE + dI, both bases at V_CM (symmetric split), alpha ~ 1
import sympy as sp
VCC, RC, IEE, dI, alpha = sp.symbols('V_CC R_C I_EE DeltaI alpha', positive=True)
VX = lambda i, a=1: VCC - RC*a*i/2
VY = lambda i, a=1: VCC - RC*a*i/2
dVX = sp.simplify(VX(IEE+dI) - VX(IEE)); dVY = sp.simplify(VY(IEE+dI) - VY(IEE))
print('dVX =', dVX, ' dVY =', dVY, ' d(VX - VY) =', sp.simplify(dVX - dVY))
print('with finite alpha: dVX =', sp.simplify(VX(IEE+dI, alpha) - VX(IEE, alpha)))
