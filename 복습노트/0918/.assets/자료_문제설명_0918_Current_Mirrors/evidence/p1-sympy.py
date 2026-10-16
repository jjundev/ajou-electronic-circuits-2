import sympy as s
from sympy import Rational as Q
print('Independent derivation from blind conditions; author-early, not fragment author')
def check(name, expression):
    value=s.simplify(expression)
    print(name, value)
    assert value==0,(name,value)

I,K,VT,R=s.symbols('I K VT R',positive=True)
# Independent KVLs from source/emitter resistor placement.
mos=s.solve(s.Eq(s.sqrt(2*I/K)-s.sqrt(I/K),I*R/2),R)[0]
bjt=s.solve(s.Eq(I*R,VT*s.log(2)),R)[0]
print('1 Rp=',mos,'2 Rp=',bjt)
check('MOS square-law current target residual',K*(s.sqrt(2*I/K)-I*mos/2)**2/2-I/2)
check('BJT exponential current ratio',s.exp(I*bjt/VT)-2)
