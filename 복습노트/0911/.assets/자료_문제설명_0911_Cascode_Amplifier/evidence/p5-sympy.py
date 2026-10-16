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
I=s.Rational(1,2000);mu=s.Rational(1,20000);ro=10000;target=40000
gmd=s.Rational(target,ro**2);gme=s.Rational(target-2*ro,ro**2);wd=gmd**2/(2*mu*I);we=gme**2/(2*mu*I)
print('WL dominant,exact=',wd,we);print('exact resistance of dominant design=',2*ro+gmd*ro**2);assert wd==s.Rational(16,5);assert we==s.Rational(4,5)
T=s.symbols('T',positive=True);print('design ratio exact/dominant in large target/ro limit=',s.limit(((T-2)/T)**2,T,s.oo))
