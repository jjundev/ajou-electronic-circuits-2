# P9.13 independent check
import sympy as sp
k,WL,lam,ID,VA,VT,b,IC=sp.symbols('muCox WL lambda I_D V_A V_T beta I_C',positive=True)
Gm=sp.sqrt(2*k*WL*ID); ro=1/(lam*ID)
R=sp.simplify(Gm*ro*ro); print("(a) Rout =",R)
print("    target sqrt(2 muCox WL)/(lambda^2 I_D^(3/2)) diff:",sp.simplify(R-sp.sqrt(2*k*WL)/(lam**2*ID**sp.Rational(3,2))))
print("    d ln R / d ln I_D =",sp.simplify(sp.diff(sp.log(R),ID)*ID))
Rb=1/IC*VA/VT*b*VA*VT/(VA+b*VT)
print("(b) bipolar d ln R / d ln I_C =",sp.simplify(sp.diff(sp.log(Rb),IC)*IC))
print("    MOS exponent -3/2 vs bipolar -1 -> MOS is stronger function of bias current")
import math
for i in [0.1e-3,0.5e-3,1e-3,2e-3]:
    print("    I_D=%.1e  R/R(1mA)=%.3f"%(i,(1e-3/i)**1.5))
