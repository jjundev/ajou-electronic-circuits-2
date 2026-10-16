import sympy as s
from sympy import Rational as Q
print('Independent derivation from blind conditions; author-early, not fragment author')
def check(name, expression):
    value=s.simplify(expression)
    print(name, value)
    assert value==0,(name,value)

V,R,I,d=s.symbols('V R I d')
VX=V-R*I/2;VY=V-R*I/2
DX=s.expand(VX.subs(V,V+d)-VX);DY=s.expand(VY.subs(V,V+d)-VY)
print('DeltaVX=',DX,'DeltaVY=',DY,'DeltaDifferential=',s.simplify(DX-DY));check('differential rejection',DX-DY)
check('individual follow',DX-d)
