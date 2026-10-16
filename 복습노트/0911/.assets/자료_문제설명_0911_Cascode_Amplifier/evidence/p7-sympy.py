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
gm=s.Rational(1,26);ro=5000;rpi=2600;re=par(ro,rpi);rb=ro+(1+gm*ro)*re;rd=gm*ro*re
print('BJT Rout exact, dominant=',s.N(rb),s.N(rd))
rr=s.symbols('rr',positive=True);exact=rr+(1+gm*rr)*par(rr,rpi);dom=gm*rr*par(rr,rpi)
for label,expr in [('exact',exact),('dominant',dom)]:
 root=[x for x in s.solve(s.Eq(expr,500000),rr) if x.is_positive][0];print(label,'VA=',s.N(root/1000));assert s.simplify(expr.subs(rr,root)-500000)==0
