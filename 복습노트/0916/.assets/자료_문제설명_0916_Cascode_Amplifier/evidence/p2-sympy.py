# P2 (P9.28): Eq. (9.72) in device parameters
import sympy as sp
ID, un, up, WL1, WL2, WL3, ln, lp = sp.symbols('I_D muCn muCp WL1 WL2 WL3 lambda_n lambda_p', positive=True)
gm = lambda k, wl: sp.sqrt(2*k*wl*ID)
ron, rop = 1/(ln*ID), 1/(lp*ID)
Ron = gm(un, WL2)*ron*ron
Rop = gm(up, WL3)*rop*rop
par = lambda a, b: a*b/(a+b)
Av = sp.simplify(-gm(un, WL1)*par(Ron, Rop))
print('Av =', Av)
a = sp.sqrt(2*un*WL2)/ln**2; b = sp.sqrt(2*up*WL3)/lp**2
target = -sp.sqrt(2*un*WL1)*par(a, b)/ID
print('simplify(Av - target) =', sp.simplify(Av-target))
print('d(Av*I_D)/dI_D =', sp.simplify(sp.diff(Av*ID, ID)), ' -> |Av| proportional to 1/I_D (hyperbola)')
