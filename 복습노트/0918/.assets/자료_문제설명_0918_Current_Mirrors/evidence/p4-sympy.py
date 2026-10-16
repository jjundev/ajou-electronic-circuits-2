import sympy as s
from sympy import Rational as Q
print('Independent derivation from blind conditions; author-early, not fragment author')
def check(name, expression):
    value=s.simplify(expression)
    print(name, value)
    assert value==0,(name,value)

I,In,Ip,Jn,Jp,Io=s.symbols('I In Ip Jn Jp Io',positive=True)
a=s.solve([s.Eq(3*Jn,I),s.Eq(5*Jp,2*Jn),s.Eq(Io,3*Jp)],[Jn,Jp,Io])
b=s.solve([s.Eq(Jn,I),s.Eq(Jp,5*Jn),s.Eq(2*Jp,3*Jn+Io)],[Jn,Jp,Io])
print('a',a,'b',b)
check('a ratio',a[Io]/I-Q(2,5));check('b ratio',b[Io]/I-7)
