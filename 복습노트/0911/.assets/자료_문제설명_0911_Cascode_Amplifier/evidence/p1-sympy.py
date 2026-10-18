# P9.14 independent check
import sympy as sp
k=sp.Rational(100,10**6); I=sp.Rational(5,10**4); Vth=sp.Rational(2,5)
WL1=sp.Rational(30,1)/sp.Rational(18,100); WL2=sp.Rational(20,1)/sp.Rational(18,100)
v=sp.symbols('v',positive=True)
Vov2=sp.solve(sp.Eq(I,k/2*WL2*v**2),v)[0]; Vov1=sp.solve(sp.Eq(I,k/2*WL1*v**2),v)[0]
Vb2=Vth+Vov2; Vb1min=Vov2+Vth+Vov1
print("(a) Vov2 =",Vov2," Vb2 =",Vb2,"=",float(Vb2),"V")
print("    Vov1 =",sp.nsimplify(Vov1),"=",float(Vov1)," Vb1,min = Vov2+VGS1 =",float(Vb1min),"V")
# (b) small-signal KCL: test voltage vx at drain of M1 (top), M2 bottom = ro2 to ground, gates AC ground
gm1,ro1,ro2,vx,vs,ix=sp.symbols('g_m1 r_o1 r_o2 v_x v_s i_x',positive=True)
sol=sp.solve([sp.Eq(ix, gm1*(0-vs)+(vx-vs)/ro1), sp.Eq(ix, vs/ro2)],[ix,vs],dict=True)[0]
Rout=sp.simplify(vx/sol[ix])
print("(b) Rout symbolic =",sp.expand(Rout))
print("    Rout - [(1+gm1 ro1)ro2+ro1] =",sp.simplify(Rout-((1+gm1*ro1)*ro2+ro1)))
lam=sp.Rational(1,10); ro=1/(lam*I); g1=sp.sqrt(2*k*WL1*I)
val=Rout.subs({gm1:g1,ro1:ro,ro2:ro}); approx=g1*ro*ro
print("    ro =",ro,"ohm, gm1 =",float(g1),"S")
print("    Rout exact =",float(val),"ohm ; approx gm1 ro1 ro2 =",float(approx),"ohm")
x=sp.symbols('x',positive=True)
print("    limit (exact/approx) as gm*ro->inf:",sp.limit(((1+x)*1+1)/x,x,sp.oo))
