import sympy as s
from sympy import Rational as Q
print('Independent derivation from blind conditions; author-early, not fragment author')
def check(name, expression):
    value=s.simplify(expression)
    print(name, value)
    assert value==0,(name,value)

R=s.symbols('R',positive=True);I=Q(1,1000);VCC=Q(5,2);VB=2
VC=VCC-I*R;bound=s.solve(s.Eq(VC,VB),R)[0]
print('maxRC=',bound,'collector voltage at boundary=',VC.subs(R,bound));check('500ohm',bound-500)
# Current-steering consistency: one volt difference vs26mV -> negligible other branch.
ratio=s.exp(-Q(1,1)/Q(26,1000));print('IC2/IC1 exp(-1/VT)=',s.N(ratio))
assert float(ratio)<1e-15
