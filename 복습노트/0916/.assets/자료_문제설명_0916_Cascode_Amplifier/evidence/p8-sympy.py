# P8 (P9.26): Eq. (9.61) in beta, VA ; dependence on I
import sympy as sp
I, VT, bN, bP, VAN, VAP = sp.symbols('I V_T beta_N beta_P V_AN V_AP', positive=True)
par = lambda a, b: a*b/(a+b)
gm = I/VT
Ron = gm*(VAN/I)*par(VAN/I, bN*VT/I)
Rop = gm*(VAP/I)*par(VAP/I, bP*VT/I)
Av = sp.simplify(-gm*par(Ron, Rop))
print('Av =', sp.factor(Av))
a = bN*VAN**2/(VAN+bN*VT); b = bP*VAP**2/(VAP+bP*VT)
print('simplify(Av + (1/VT)[a||b]) =', sp.simplify(Av + par(a, b)/VT))
print('dAv/dI =', sp.simplify(sp.diff(Av, I)), ' -> independent of bias current')
