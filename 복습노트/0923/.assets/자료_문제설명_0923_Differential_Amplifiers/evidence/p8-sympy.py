import sympy as s
from sympy import Rational as Q
print('Independent derivation from blind conditions; author-early, not fragment author')
def check(name, expression):
    value=s.simplify(expression)
    print(name, value)
    assert value==0,(name,value)

I,K,d,R=s.symbols('I K d R',positive=True)
DeltaI=K*d*s.sqrt(4*I/K-d*d)/2
out=-R*DeltaI
A=s.simplify(s.diff(out,d).subs(d,0));gm=s.sqrt(K*I)
print('nonlinear DeltaI=',DeltaI,'equilibrium output slope=',A)
check('gmRD',A+gm*R)
print('zeroRD limit',s.limit(A,R,0))
