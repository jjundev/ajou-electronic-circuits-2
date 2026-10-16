import sympy as s
from sympy import Rational as Q
print('Independent derivation from blind conditions; author-early, not fragment author')
def check(name, expression):
    value=s.simplify(expression)
    print(name, value)
    assert value==0,(name,value)

vi,vo=s.symbols('vi vo',real=True)
gn,gp,on,op=s.symbols('gn gp on op',positive=True)
v=s.solve(s.Eq(gn*vi+(gp+on+op)*vo,0),vo)[0]
A=s.factor(v/vi)
print('DM half circuit, diode PMOS admittance gp+op; gain=',A)
check('parallel resistance form',A+gn/(gp+on+op))
print('lambdaZero',s.limit(s.limit(A,on,0),op,0))
