import sympy as s
from sympy import Rational as Q
print('Independent derivation from blind conditions; author-early, not fragment author')
def check(name, expression):
    value=s.simplify(expression)
    print(name, value)
    assert value==0,(name,value)

J=s.symbols('unit_current',positive=True)
unit=s.solve(s.Eq(3*J,Q(3,10000)),J)[0]
print('unit=',unit,'I1=',2*unit,'I2=',5*unit)
check('sink1 A',2*unit-Q(2,10000));check('sink2 A',5*unit-Q(5,10000))
print('Sources grounded; diode connection only at reference; each drain must retain VDS>=Vov.')
