# Independent check P9.12 (Fig 9.49): max lambda for Rout >= 50k
import sympy as sp
lam,ro=sp.symbols('lambda r_o',positive=True)
k=sp.Rational(1,10**4); I=sp.Rational(5,10**4); WL=sp.Rational(20)/sp.Rational(18,100)
gm=sp.sqrt(2*k*WL*I); print('gm =',sp.nsimplify(gm),'=',float(gm),'S')
r=1/(lam*I)
la=sp.solve(sp.Eq(gm*r*r,50000),lam); print('approx gm ro^2 = 50k -> lambda_max =',la,'=',[float(v) for v in la],'1/V')
le=sp.solve(sp.Eq((1+gm*r)*r+r,50000),lam); print('exact (1+gm ro)ro+ro = 50k -> lambda_max =',[sp.nsimplify(v) for v in le],'=',[float(v) for v in le],'1/V')
print('gm ro at approx lambda =',float(gm*r.subs(lam,la[0])),' ratio lam_exact/lam_approx =',float(le[0]/la[0]))
