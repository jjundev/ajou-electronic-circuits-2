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
lam=s.symbols('lam',positive=True);I=s.Rational(1,2000);gm=s.Rational(1,300);ro=1/(lam*I)
sol=[x for x in s.solve(s.Eq(2*ro+gm*ro**2,50000),lam) if x.is_positive][0]
ap=sqrt(gm/(50000*I**2));print('lambda dominant, exact=',s.N(ap),s.N(sol));print('exact Rout at dominant lambda=',s.N((2*ro+gm*ro**2).subs(lam,ap)))
assert s.simplify((2*ro+gm*ro**2).subs(lam,sol)-50000)==0
