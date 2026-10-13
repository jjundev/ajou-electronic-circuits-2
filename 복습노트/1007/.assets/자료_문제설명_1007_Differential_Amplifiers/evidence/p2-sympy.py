# P10.68 (Fig 10.89) common-mode gain, independent check. No body effect.
import sympy as sp
gm1, ro1, ro3, ro5, vin = sp.symbols('g_m1 r_O1 r_O3 r_O5 v_in', positive=True)
vP, vX, vY = sp.symbols('v_P v_X v_Y')
# Full circuit, both inputs = vin (CM). M3/M4 gates at fixed Vb1 -> just r_O3 to AC ground.
# X = drain M1, Y = drain M2, P = common source (tail M5 -> r_O5).
i1 = gm1*(vin - vP) + (vX - vP)/ro1   # current into drain of M1 from X toward P
i2 = gm1*(vin - vP) + (vY - vP)/ro1
eqs = [sp.Eq(-vX/ro3, i1),            # KCL at X: current from r_O3 = i1
       sp.Eq(-vY/ro3, i2),
       sp.Eq(i1 + i2, vP/ro5)]       # KCL at P
s = sp.solve(eqs, [vX, vY, vP], dict=True)[0]
Acm_se = sp.simplify(s[vX]/vin)
Acm_diff = sp.simplify((s[vX]-s[vY])/vin)
print("single-ended A_CM (exact) =", sp.factor(Acm_se))
print("differential-output A_CM (vX - vY)/vin =", Acm_diff)

# -Gm*Rout form with half circuit (tail -> 2 r_O5)
RS = 2*ro5
Gm = gm1*ro1/(ro1 + RS + gm1*ro1*RS)          # output shorted to ground
Rdeg = ro1 + RS + gm1*ro1*RS                  # degenerated M1 output resistance
Rout = ro3*Rdeg/(ro3 + Rdeg)
Av = -Gm*Rout
print("-Gm*Rout - exact single-ended =", sp.simplify(Av - Acm_se))
# approximation gm1 ro1 >> 1: take ro1 -> oo
approx = sp.limit(Acm_se, ro1, sp.oo)
print("limit ro1->oo (g_m r_O >> 1):", sp.simplify(approx))
print("check approx == -r_O3/(1/g_m1 + 2 r_O5):", sp.simplify(approx + ro3/(1/gm1 + 2*ro5)))
# further gm1*2ro5 >> 1
print("limit ro5 large ratio -> -r_O3/(2 r_O5):", sp.limit(approx*ro5, ro5, sp.oo), "/ r_O5")
# numerical example
vals = {gm1: sp.Rational(1,100), ro1: 20000, ro3: 20000, ro5: 20000}  # gm=10mS, rO=20k
print("numeric single-ended exact:", sp.N(Acm_se.subs(vals)), " approx -r_O3/(1/gm+2rO5):", sp.N((-ro3/(1/gm1+2*ro5)).subs(vals)))
