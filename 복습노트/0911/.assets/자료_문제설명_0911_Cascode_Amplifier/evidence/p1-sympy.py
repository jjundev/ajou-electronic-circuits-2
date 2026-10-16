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
I=s.Rational(1,2000);mu=s.Rational(1,10000);ov1=sqrt(2*I/(mu*30/s.Rational(18,100)));ov2=sqrt(2*I/(mu*20/s.Rational(18,100)));gm=2*I/ov1;ro=1/(s.Rational(1,10)*I)
print('a Vb2,Vb1min=',s.N(ov2+s.Rational(2,5)),s.N(ov1+ov2+s.Rational(2,5)))
print('b exact,dominant=',s.N(2*ro+gm*ro**2),s.N(gm*ro**2));assert ov2==s.Rational(3,10)
