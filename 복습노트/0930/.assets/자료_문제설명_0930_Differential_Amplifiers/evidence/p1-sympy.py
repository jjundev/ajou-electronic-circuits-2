import sympy as s
from sympy import Rational as Q
print('Independent derivation from blind conditions; author-early, not fragment author')
def check(name, expression):
    value=s.simplify(expression)
    print(name, value)
    assert value==0,(name,value)

I,R,W,gm=s.symbols('I R W gm',positive=True)
P=Q(2,1000);V=Q(18,10);CM=Q(16,10);mu=Q(1,10000);A=5
z=s.solve([s.Eq(V*I,P),s.Eq(V-I*R/2,CM),s.Eq(gm*R,A),s.Eq(gm**2,mu*W*I)],[I,R,W,gm],dict=True)[0]
print('design at power and maxRD boundaries',z)
check('power',V*z[I]-P);check('CM',V-z[I]*z[R]/2-CM);check('gain',z[gm]*z[R]-A)
print('Vov=',s.simplify(z[I]/z[gm]))
