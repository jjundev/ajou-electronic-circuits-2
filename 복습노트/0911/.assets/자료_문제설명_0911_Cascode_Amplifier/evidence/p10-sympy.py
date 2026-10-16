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
gm1,gm2,ro1,ro2=s.symbols('gm1 gm2 ro1 ro2',positive=True)
# Output open: upper controlled current plus ro current sums to zero.
sol=s.solve([s.Eq(gm2*(-vx)+(vo-vx)/ro2,0),s.Eq(gm1*vi+vx/ro1,0)],[vx,vo],dict=True)[0]
Ag=s.factor(sol[vo]/vi);print('MOS ideal-load exact gain=',Ag);assert s.simplify(Ag+gm1*ro1*(1+gm2*ro2))==0
x=s.symbols('x',positive=True);root=s.solve(s.Eq(x*(x+1),200),x)[0];I=s.Rational(1,1000);lam=s.Rational(1,10);mu=s.Rational(1,10000)
print('WL exact,dominant=',s.N(root**2*lam**2*I/(2*mu)),s.N(200*lam**2*I/(2*mu)));assert s.simplify(root*(root+1)-200)==0
