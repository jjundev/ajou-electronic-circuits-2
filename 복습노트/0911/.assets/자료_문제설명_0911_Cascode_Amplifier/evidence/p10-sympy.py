# P9.29 independent check: MOS cascode amp, ideal current-source load
import sympy as sp
gm1,gm2,ro1,ro2,vin,vx,vo=sp.symbols('g_m1 g_m2 r_o1 r_o2 v_in v_x v_o')
# KCL: output node (ideal load -> no current), node X
eqs=[sp.Eq(gm2*(0-vx)+(vo-vx)/ro2,0), sp.Eq(gm2*(0-vx)+(vo-vx)/ro2, gm1*vin+vx/ro1)]
s=sp.solve(eqs,[vo,vx],dict=True)[0]; Av=sp.simplify(s[vo]/vin)
print("Av =",sp.factor(Av))
print("Av + gm1 ro1(1+gm2 ro2) =",sp.simplify(Av+gm1*ro1*(1+gm2*ro2)))
print("(note: -gm1*Rout differs by gm1*ro2, i.e. Gm<gm1; ratio ->1 as gm ro->inf)")
k=sp.Rational(100,10**6); I=sp.Rational(1,1000); lam=sp.Rational(1,10); ro=1/(lam*I)
g,WL=sp.symbols('g WL',positive=True)
ga=sp.solve(sp.Eq(g**2*ro**2,200),g)[0]
ge=[x for x in sp.solve(sp.Eq(-Av.subs({gm1:g,gm2:g,ro1:ro,ro2:ro}),200),g) if x.is_positive][0]
f=lambda gg: sp.solve(sp.Eq(2*k*WL*I,gg**2),WL)[0]
print("ro =",ro)
print("approx (gm ro)^2=200: gm =",float(ga),", W/L =",f(ga),"=",float(f(ga)))
print("exact: gm =",float(ge),", gm ro =",float(ge*ro),", W/L =",float(f(ge)))
