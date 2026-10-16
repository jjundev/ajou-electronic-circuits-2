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
k,a,vdd,vt=s.symbols('k a vdd vt',positive=True);current=k*(a*vdd-vt)**2/2;der=s.diff(current,vt);rel=s.factor(der/current);print('absolute derivative=',der,'normalized=',rel);assert s.simplify(der+k*(a*vdd-vt))==0
print('fractional exact +/- .01V examples=',[(ov,(1-.01/ov)**2-1) for ov in [.5,.2]])
