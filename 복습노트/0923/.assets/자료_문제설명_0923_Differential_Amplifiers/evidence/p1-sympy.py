import sympy as s
from sympy import Rational as Q
print('Independent derivation from blind conditions; author-early, not fragment author')
def check(name, expression):
    value=s.simplify(expression)
    print(name, value)
    assert value==0,(name,value)

vo,vs,R,r=s.symbols('vo vs R r',positive=True)
v=s.solve(s.Eq((vo-vs)/R+vo/r,0),vo)[0]
A=s.factor(v/vs);print('gain',A)
check('divider',A-r/(R+r));print('roInf',s.limit(A,r,s.oo),'ro0',s.limit(A,r,0))
