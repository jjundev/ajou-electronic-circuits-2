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
I=s.Rational(1,1000);mu=s.Rational(1,10000);vth=s.Rational(2,5);vd=s.Rational(18,10)-I*500;ov1=sqrt(2*I/(mu*20/s.Rational(18,100)));ov2=sqrt(2*I/(mu*40/s.Rational(18,100)));vg=vd+vth;x=vg-vth-ov1
print('Vb1max,VX=',s.N(vg),s.N(x));print('upper VDS-Vov=',s.simplify(vd-x-ov1),'lower margin=',s.N(x-ov2));assert s.simplify(vd-x-ov1)==0
