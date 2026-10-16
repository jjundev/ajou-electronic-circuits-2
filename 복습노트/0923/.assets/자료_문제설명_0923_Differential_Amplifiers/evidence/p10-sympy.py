import sympy as s
from sympy import Rational as Q
print('Independent derivation from blind conditions; author-early, not fragment author')
def check(name, expression):
    value=s.simplify(expression)
    print(name, value)
    assert value==0,(name,value)

K,u,R,d,x=s.symbols('K u R d x',positive=True)
# Original nonlinear square laws minus the DC KCL. No small-signal equivalent model.
F=s.expand(K*((u-x+d/2)**2+(u-x-d/2)**2)/2-K*u*u-x/R)
print('nonlinear residual F=',F)
check('exchange symmetry',F.subs(d,-d)-F)
first=s.simplify(-s.diff(F,d)/s.diff(F,x)).subs({d:0,x:0})
second=s.simplify((-s.diff(F,d,2)/s.diff(F,x)).subs({d:0,x:0})/2)
print('first derivative',first,'quadratic coefficient',second)
check('virtual ground first order',first)
check('quadratic coefficient',second-K/(4*(2*K*u+1/R)))
print('Rinf coefficient',s.limit(second,R,s.oo),'Rzero coefficient',s.limit(second,R,0))
