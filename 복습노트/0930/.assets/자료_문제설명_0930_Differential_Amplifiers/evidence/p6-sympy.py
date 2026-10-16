import sympy as s
from sympy import Rational as Q
print('Independent derivation from blind conditions; author-early, not fragment author')
def check(name, expression):
    value=s.simplify(expression)
    print(name, value)
    assert value==0,(name,value)

vi,vo,vs=s.symbols('vi vo vs',real=True)
gn,gp,RD,RS=s.symbols('gn gp RD RS',positive=True)
# Differential halves have resistances RDD/2, RSS/2; PMOS diode at output adds gp.
z=s.solve([s.Eq(2*vs/RS,gn*(vi-vs)),s.Eq((2/RD+gp)*vo+gn*(vi-vs),0)],[vo,vs])
A=s.factor(z[vo]/vi);target=-1/((2/RD+gp)*(RS/2+1/gn))
print('gain=',A);check('parallel loaded target',A-target)
print('gpZero limit',s.limit(A,gp,0),'RSzero limit',s.limit(A,RS,0))
