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
gn=sqrt(2*s.Rational(1,10000)*30*s.Rational(1,2000));gp=sqrt(2*s.Rational(1,20000)*40*s.Rational(1,2000));rn=20000;rp0=s.Rational(40000,3)
av=-gn*par(gn*rn**2,gp*rp0**2);print('gain dominant=',s.N(av));assert abs(float(av)+319.5)<.1
