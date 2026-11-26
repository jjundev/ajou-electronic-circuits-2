import sympy as S
from sympy import symbols, simplify, factor, Rational as Q
gm,r,C,s,K,B=symbols('gm ro CL s K B',nonzero=True)
A=-gm*r/(1+s*r*C)
H=factor(A/(1+K*A))
pole=S.solve(S.denom(H),s)[0]
ks=S.solve(S.Eq(-pole,B),K)[0]
print('signed A/(1+KA)',H,'pole',pole,'signed K (B rad/s)',ks)
assert simplify(pole.subs(K,ks)+B)==0
print('signed K (B Hz)',ks.subs(B,2*S.pi*B))
