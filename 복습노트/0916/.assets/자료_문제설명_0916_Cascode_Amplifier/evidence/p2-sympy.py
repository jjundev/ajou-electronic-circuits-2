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
a1,a2,a3,I,lam=s.symbols('a1 a2 a3 I lam',positive=True)
rn=a2/(lam**2*I**s.Rational(3,2));rpp=a3/(lam**2*I**s.Rational(3,2));av=s.factor(-a1*sqrt(I)*par(rn,rpp));print('Av=',av);assert s.simplify(I*s.diff(av,I)/av)==-1
print('normalized graph samples:',[(x,1/s.Rational(x)) for x in [1,2,4]])
