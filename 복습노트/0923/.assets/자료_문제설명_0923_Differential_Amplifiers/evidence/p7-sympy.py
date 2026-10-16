import sympy as s
from sympy import Rational as Q
print('Independent derivation from blind conditions; author-early, not fragment author')
def check(name, expression):
    value=s.simplify(expression)
    print(name, value)
    assert value==0,(name,value)

VD,VDD,I,R,VTH=s.symbols('VD VDD I R VTH',positive=True)
z=s.solve(s.Eq((VDD-VD)/R,I),VD)[0]
Rmax=s.solve(s.Eq(z,Q(3,2)-VTH),R)[0]
print('off M2 ->ID1=ISS; VD1=',z,'max RD=',Rmax)
check('saturation condition',Rmax*I-(VDD-Q(3,2)+VTH))
K=s.symbols('K',positive=True);Vp=Q(3,2)-VTH-s.sqrt(2*I/K)
print('M2 overdrive=',s.simplify(Q(3,10)-Vp-VTH),'must be <=0')
