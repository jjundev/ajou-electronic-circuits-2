# X9.07 independent check
import sympy as sp
k,W,L,I=sp.symbols('muCox W L I_D',positive=True)
g=lambda W,I: sp.sqrt(2*k*W/L*I)
r=sp.simplify(g(2*W,2*I)/g(W,I)); print("Gm_new/Gm_old =",r)
