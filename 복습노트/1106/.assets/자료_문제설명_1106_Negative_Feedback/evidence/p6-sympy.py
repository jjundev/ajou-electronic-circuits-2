import sympy as S
from sympy import symbols, simplify, factor, Rational as Q
A,r1,r2=symbols('A R1 R2',positive=True)
b=r2/(r1+r2)
h=A/(1+A*b)
assert simplify(S.limit(h,A,S.oo)-(1+r1/r2))==0
print('H',h,'relative gain deficit vs ideal',factor(1-h*b),'limit',S.limit(h,A,S.oo))
