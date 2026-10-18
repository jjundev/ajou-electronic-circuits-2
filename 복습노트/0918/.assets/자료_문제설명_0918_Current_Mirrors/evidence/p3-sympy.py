import sympy as sp
# NMOS mirror: M_REF diode-connected carries I_REF; M3 -> I1 (sink under M1), M4 -> I2 (sink under M2)
mun, Cox, VGS, VTH, WLr, WL3, WL4, lam = sp.symbols('mu_n C_ox V_GS V_TH WL_REF WL_3 WL_4 lambda', positive=True)
Id = lambda WL: sp.Rational(1,2)*mun*Cox*WL*(VGS-VTH)**2   # same V_GS for all (gates/sources shared), lambda=0
IREF, I1, I2 = sp.Rational(3,10), sp.Rational(2,10), sp.Rational(5,10)  # mA
r3 = sp.simplify(Id(WL3)/Id(WLr)); r4 = sp.simplify(Id(WL4)/Id(WLr))
print("I1/IREF =", r3, " I2/IREF =", r4)
s3 = sp.solve(sp.Eq(r3, I1/IREF), WL3)[0]; s4 = sp.solve(sp.Eq(r4, I2/IREF), WL4)[0]
print("(W/L)3 =", s3, "  (W/L)4 =", s4)
print("ratio (W/L)REF:(W/L)3:(W/L)4 =", "3:2:5 check ->", sp.simplify(s3/WLr*3), sp.simplify(s4/WLr*3))
# unit-device realization: unit carries 0.1 mA
u = sp.Rational(1,10)
print("units: REF =", IREF/u, " M3 =", I1/u, " M4 =", I2/u)
# CLM check: with lambda, exact only if V_DS equal to V_GS
VDS = sp.symbols('V_DS', positive=True)
ratio_clm = sp.simplify((WL3*(1+lam*VDS))/(WLr*(1+lam*VGS)))
print("with CLM I1/IREF =", ratio_clm, " limit lambda->0:", sp.limit(ratio_clm, lam, 0))
print("ANSWER p3:main: NMOS mirror from diode M_REF (I_REF=0.3 mA): (W/L)3=(2/3)(W/L)REF -> I1=0.2 mA, (W/L)4=(5/3)(W/L)REF -> I2=0.5 mA; i.e. (W/L)REF:(W/L)3:(W/L)4 = 3:2:5 (unit 0.1 mA device: 3,2,5 copies), lambda=0")
