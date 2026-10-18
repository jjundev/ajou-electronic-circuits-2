import sympy as sp
k, W, L, VGS, VTH, lam, VDS1 = sp.symbols('k W L V_GS V_TH lambda V_DS1', positive=True)
Id = lambda vds: sp.Rational(1,2)*k*W/L*(VGS-VTH)**2*(1+lam*vds)
IREF = Id(VGS)          # M_REF diode-connected: V_DS,REF = V_GS
Icopy = Id(VDS1)
# (a)
sol = sp.solve(sp.Eq(Icopy, IREF), VDS1)
print("(a) V_DS1 for Icopy=IREF:", sol)
# (b)
Icb = Icopy.subs(VDS1, VGS-VTH)
ratio = sp.simplify(Icb/IREF)
err_abs = sp.simplify(Icb-IREF)
rel = sp.simplify((Icb-IREF)/IREF)
print("(b) Icopy/IREF =", ratio)
print("(b) Icopy - IREF =", sp.factor(err_abs), " = ", sp.simplify(rel), "* I_REF")
print("(b) relative error =", rel)
print("(b) first-order in lambda:", sp.series(rel, lam, 0, 2).removeO())
print("(b) limit rel/lambda as lambda->0:", sp.limit(rel/lam, lam, 0))
# numeric spot check
vals = {VGS:1.0, VTH:0.4, lam:0.1}
print("(b) numeric check VGS=1,VTH=0.4,lam=0.1: rel err =", float(rel.subs(vals)), " approx -lam*VTH =", -0.04)
