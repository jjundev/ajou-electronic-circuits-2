import sympy as s
from sympy import Rational as Q
print('Independent derivation from blind conditions; author-early, not fragment author')
def check(name, expression):
    value=s.simplify(expression)
    print(name, value)
    assert value==0,(name,value)

I,K,u,R=s.symbols('I K u R',positive=True)
# Derive gm by differentiating transistor square law at each branch current I/2.
v=s.symbols('v',positive=True);gm=s.diff(K*v*v/2,v).subs(v,s.sqrt(I/K))
A=-gm*R
u_eq=s.solve(s.Eq(K*u*u/2,I/2),u)[0]
print('gm=',gm,'u_eq=',u_eq,'Av=',A)
check('overdrive representation',A+I*R/u_eq)
