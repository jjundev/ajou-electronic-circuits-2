import sympy as s
from sympy import Rational as Q
print('Independent derivation from blind conditions; author-early, not fragment author')
def check(name, expression):
    value=s.simplify(expression)
    print(name, value)
    assert value==0,(name,value)

I,W=s.symbols('I W',positive=True)
P=Q(3,1000);V=Q(18,10);mu=Q(1,10000);d=Q(1,2)
z=s.solve([s.Eq(V*I,P),s.Eq(mu*W*d*d/2,I)],[I,W])
print('design',z);check('power residual',V*z[I]-P);check('cutoff residual',s.sqrt(2*z[I]/(mu*z[W]))-d)
check('WL133.333',z[W]-Q(400,3))
