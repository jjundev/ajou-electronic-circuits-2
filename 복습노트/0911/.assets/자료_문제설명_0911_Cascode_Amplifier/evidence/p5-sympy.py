# P9.17 independent check (PMOS cascode, Rout=(1+gm1 ro1)ro2+ro1 by same KCL as NMOS)
import sympy as sp
k=sp.Rational(50,10**6); I=sp.Rational(5,10**4); lam=sp.Rational(2,10); R=40000
ro=1/(lam*I); gm,WL=sp.symbols('g_m WL',positive=True)
gma=sp.solve(sp.Eq(gm*ro**2,R),gm)[0]; gme=sp.solve(sp.Eq((1+gm*ro)*ro+ro,R),gm)[0]
f=lambda g: sp.solve(sp.Eq(2*k*WL*I,g**2),WL)[0]
print("ro =",ro,"ohm")
print("approx gm ro^2: gm =",float(gma),"S, gm*ro =",gma*ro,", W/L =",f(gma),"=",float(f(gma)))
print("exact (1+gm ro)ro+ro: gm =",float(gme),"S, gm*ro =",gme*ro,", W/L =",f(gme),"=",float(f(gme)))
print("note: gm*ro is only 2..4 here, so gm ro >> 1 is not satisfied; ratio approx/exact W/L =",f(gma)/f(gme))
