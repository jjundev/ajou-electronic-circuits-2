import sympy as s
from sympy import Rational as Q
print('Independent derivation from blind conditions; author-early, not fragment author')
def check(name, expression):
    value=s.simplify(expression)
    print(name, value)
    assert value==0,(name,value)

J=s.symbols('unit_current',positive=True)
u=s.solve(s.Eq(13*J,Q(130,1000000)),J)[0]
print('areas reference/output1/output2=13:5:23','unit current=',u)
check('50uA',5*u-Q(50,1000000));check('230uA',23*u-Q(230,1000000))
print('Shared VBE ensures IC=area*unit density; all NPN emitters grounded; active-region compliance required.')
