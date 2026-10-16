import sympy as s
from sympy import Rational as Q
print('Independent derivation from blind conditions; author-early, not fragment author')
def check(name, expression):
    value=s.simplify(expression)
    print(name, value)
    assert value==0,(name,value)

V,R,I,d=s.symbols('V R I d')
# Tail KCL and matched VBE enforce IC1=IC2=I/2 under betaInf.
x,y=s.symbols('x y');curr=s.solve([s.Eq(x+y,I),s.Eq(x,y)],[x,y])
VX=V-R*curr[x];VY=V-R*curr[y]
DX=s.expand(VX.subs(I,I+d)-VX);DY=s.expand(VY.subs(I,I+d)-VY)
print('DeltaVX=',DX,'DeltaVY=',DY);check('output common shift',DX+R*d/2);check('differential unchanged',DX-DY)
