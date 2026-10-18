# E9.05 independent check
import sympy as sp
k=sp.Rational(100,10**6); I=sp.Rational(5,10**4); lam=sp.Rational(1,10); R=500000
ro=1/(lam*I); gm,WL=sp.symbols('g_m WL',positive=True)
# exact cascode Rout = (1+gm ro)ro + ro (from KCL, see p1)
gma=sp.solve(sp.Eq(gm*ro**2,R),gm)[0]; gme=sp.solve(sp.Eq((1+gm*ro)*ro+ro,R),gm)[0]
WLa=sp.solve(sp.Eq(sp.sqrt(2*k*WL*I),gma),WL)[0]; WLe=sp.solve(sp.Eq(sp.sqrt(2*k*WL*I),gme),WL)[0]
print("ro =",ro)
print("approx (Rout=gm ro^2): gm =",float(gma),"S, W/L =",WLa,"=",float(WLa))
print("exact  (Rout=(1+gm ro)ro+ro): gm =",float(gme),"S, W/L =",WLe,"=",float(WLe))
print("gm*ro (approx) =",float(gma*ro))
