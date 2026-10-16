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
N=s.symbols('N',positive=True);mu,W,I,lam=s.symbols('mu W I lam',positive=True)
gm=sqrt(2*mu*W*I);assert s.simplify(gm.subs(W,N*W)/gm-sqrt(N))==0
print('fixed L and I, ro invariant; gm ratio sqrt(N), dominant Rout ratio sqrt(N)')
print('exact ratio=',(r1+r2+sqrt(N)*g*r1*r2)/(r1+r2+g*r1*r2))
