import sympy as s
from sympy import Rational as Q
print('Independent derivation from blind conditions; author-early, not fragment author')
def check(name, expression):
    value=s.simplify(expression)
    print(name, value)
    assert value==0,(name,value)

RD=s.symbols('RD',positive=True);I=Q(5,10000);VDD=Q(18,10);VG=Q(16,10);VTH=Q(5,10)
vd=VDD-I*RD/2
boundary=s.solve(s.Eq(vd,VG-VTH),RD)[0]
print('max RD=',boundary,'drain boundary=',vd.subs(RD,boundary));check('target2800ohm',boundary-2800)
assert vd.subs(RD,boundary+1)<VG-VTH
