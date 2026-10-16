import sympy as s
from sympy import Rational as Q
print('Independent derivation from blind conditions; author-early, not fragment author')
def check(name, expression):
    value=s.simplify(expression)
    print(name, value)
    assert value==0,(name,value)

la,Vg,Vt,Vd,K=s.symbols('lambda Vg Vt Vd K',positive=True)
Iref=K*(Vg-Vt)**2*(1+la*Vg)/2
Io=K*(Vg-Vt)**2*(1+la*Vd)/2
vd=s.solve(s.Eq(Io,Iref),Vd)[0]
err=s.factor((Io.subs(Vd,Vg-Vt)-Iref)/Iref)
print('a equal-current VDS=',vd,'b relative error=',err)
check('equal currents',Io.subs(Vd,vd)-Iref)
check('reference error comparison',err+la*Vt/(1+la*Vg))
print('zero lambda limit',s.limit(err,la,0),'first-order coefficient',s.limit(err/la,la,0))
