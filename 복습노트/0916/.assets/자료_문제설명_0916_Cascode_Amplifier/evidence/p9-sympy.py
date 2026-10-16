import sympy as s
from sympy import sqrt
par=lambda a,b:s.cancel(a*b/(a+b))
g,r1,r2,rp=s.symbols('g r1 r2 rp', positive=True)
vx,vo,it,vi=s.symbols('vx vo it vi', real=True)
q=par(r1,rp)
# Upper device gate at AC ground: output test-current KCL and source continuity.
a=s.solve([s.Eq(it,(vo-vx)/q-g*vx),s.Eq(vx,it*r2)],[vo,vx],dict=True)[0]
R=s.factor(a[vo]/it)
assert s.simplify(R-(q+r2+g*q*r2))==0
print('Test-current KCL Rout=',R)
print('RP absent=',s.limit(R,rp,s.oo))
print('dominant-term ratio as gm->infinity=',s.limit(R/(g*q*r2),g,s.oo))
gm=s.Rational(1,26);rn=5000;rpn=2600;rp0=4000;rpp=1300
Rn=gm*rn*par(rn,rpn);Rp=gm*rp0*par(rp0,rpp);av=-gm*par(Rn,Rp);print('Rnpn,Rpnp,Av=',s.N(Rn),s.N(Rp),s.N(av));assert abs(float(av)+3979.46595566875)<.00001
