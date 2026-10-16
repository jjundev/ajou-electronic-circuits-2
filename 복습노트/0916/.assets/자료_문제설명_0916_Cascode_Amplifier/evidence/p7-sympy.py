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
gm1,gm2,ro1,ro2,rpi=s.symbols('gm1 gm2 ro1 ro2 rpi',positive=True)
sol=s.solve([s.Eq(gm1*vi+vx/ro1+vx/rpi,0),s.Eq(-gm2*vx+(vo-vx)/ro2,0)],[vx,vo],dict=True)[0]
Ag=s.factor(sol[vo]/vi);target=-gm1*(1+gm2*ro2)*par(ro1,rpi);assert s.simplify(Ag-target)==0
print('lower-input BJT exact open gain=',Ag);print('exact/dominant highgm2=',s.limit(Ag/(-gm1*gm2*ro2*par(ro1,rpi)),gm2,s.oo))
x=s.symbols('x',positive=True);ad=100*x**2/(x+100);ae=100*x*(x+1)/(x+100)
for label,expr in [('dominant',ad),('exact',ae)]:
 root=s.solve(s.Eq(expr,500),x)[0];print(label,'VA=',s.N(root*s.Rational(26,1000)));assert s.simplify(expr.subs(x,root)-500)==0
print('positive gain derivative=',s.factor(s.diff(ad,x)))
