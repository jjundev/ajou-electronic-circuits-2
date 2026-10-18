# P5 (P9.30): W -> N W, L and I_D fixed; Av = -gm1 rO1 gm2 rO2
import sympy as sp
N, k, WL1, WL2, ID, lam = sp.symbols('N k WL1 WL2 I_D lambda', positive=True)
Av = lambda w1, w2: -sp.sqrt(2*k*w1*ID)/(lam*ID)*sp.sqrt(2*k*w2*ID)/(lam*ID)
print('Av in device params =', sp.simplify(Av(WL1, WL2)))
print('Av(NW)/Av(W) =', sp.simplify(Av(N*WL1, N*WL2)/Av(WL1, WL2)))
print('gm scales by sqrt(N) each, rO unchanged -> |Av| x N')
