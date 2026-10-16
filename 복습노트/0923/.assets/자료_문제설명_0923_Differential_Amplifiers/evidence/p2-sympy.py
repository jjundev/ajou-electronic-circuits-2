import sympy as s
from sympy import Rational as Q
print('Independent derivation from blind conditions; author-early, not fragment author')
def check(name, expression):
    value=s.simplify(expression)
    print(name, value)
    assert value==0,(name,value)

x,y,vs,R1,R2,r1,r2=s.symbols('x y vs R1 R2 r1 r2',positive=True)
z=s.solve([s.Eq((x-vs)/R1+x/r1,0),s.Eq((y-vs)/R2+y/r2,0)],[x,y])
A=s.factor((z[x]-z[y])/vs);print('general differential ripple=',A)
check('symmetry cancellation',A.subs({R2:R1,r2:r1}));print('CM ripple',s.simplify((z[x]+z[y]).subs({R2:R1,r2:r1})/(2*vs)))
