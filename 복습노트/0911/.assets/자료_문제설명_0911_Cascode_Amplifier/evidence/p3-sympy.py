# X9.05 independent check
import sympy as sp
k=sp.Rational(100,10**6); I=sp.Rational(5,10**4); lam=sp.Rational(1,10); WL=32
ro=1/(lam*I); gm=sp.sqrt(2*k*WL*I)
print("gm =",sp.nsimplify(gm),"=",float(gm),"S; ro =",ro)
print("Rout approx gm ro^2 =",float(gm*ro**2),"ohm")
print("Rout exact (1+gm ro)ro+ro =",float((1+gm*ro)*ro+ro),"ohm")
