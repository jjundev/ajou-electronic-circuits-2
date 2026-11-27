# Razavi Ex 12.33, Fig 12.62(a): independent check (voltage-current / transimpedance feedback)
import sympy as sp

gm1, gm2, RD, RF, RM, rO2 = sp.symbols('g_m1 g_m2 R_D R_F R_M r_O2', positive=True)
Iin = sp.symbols('I_in')
par = lambda *r: 1/sum(1/x for x in r)

print("=== 1. Loaded open-loop (R_F to ground at both N and P) ===")
vN, vX, vP = sp.symbols('v_N v_X v_P')
# N: I_in = gm1*vN (into M1 source, CG) + vN/RF ; X: vX/RD = gm1*vN ; P: -gm2*vX = vP/RM + vP/rO2 + vP/RF
sol = sp.solve([sp.Eq(Iin, gm1*vN + vN/RF),
                sp.Eq(vX/RD, gm1*vN),
                sp.Eq(-gm2*vX, vP/RM + vP/rO2 + vP/RF)], [vN, vX, vP], dict=True)[0]
Rin_open = sp.simplify(sol[vN]/Iin)
A_open = sp.simplify(sol[vP]/Iin)
Rout_open = sp.simplify(par(rO2, RM, RF))
print("R_in,open  =", Rin_open, "   [= R_F || 1/g_m1 :", sp.simplify(Rin_open - par(RF, 1/gm1)) == 0, "]")
print("R_out,open =", Rout_open, "   [= r_O2 || R_M || R_F]")
print("A_open     =", sp.factor(A_open))
form = -par(RF, 1/gm1)*gm1*RD*gm2*par(rO2, RM, RF)
print("A_open == -(R_F||1/gm1)*gm1*R_D*gm2*(rO2||R_M||R_F) :", sp.simplify(A_open - form) == 0)
form2 = -(RF*RD/(RF + 1/gm1))*gm2*par(rO2, RM, RF)
print("A_open == -[R_F*R_D/(R_F+1/gm1)]*gm2*(rO2||R_M||R_F) :", sp.simplify(A_open - form2) == 0)

print("\n=== 2. Feedback factor and loop gain ===")
V1 = sp.symbols('V_1')
I2 = (0 - V1)/RF          # N shorted to ground, V1 at P, current reference N -> P
K = sp.simplify(I2/V1)
KA = sp.simplify(K*A_open)
print("K = I_2/V_1 =", K)
print("K*A_open    =", sp.factor(KA))
print("K*A_open > 0 (negative feedback):", KA.is_positive)

print("\n=== 3. Closed loop via 1 + K*A_open ===")
A_cl = sp.simplify(A_open/(1 + KA))
Rin_cl = sp.simplify(Rin_open/(1 + KA))
Rout_cl = sp.simplify(Rout_open/(1 + KA))
print("1 + K*A_open =", sp.factor(1 + KA))
print("A_closed     =", sp.factor(A_cl))
print("R_in,closed  =", sp.factor(Rin_cl))
print("R_out,closed =", sp.factor(Rout_cl))

print("\n=== 4. Exact nodal KCL (R_F between N and P, finite r_O2) ===")
ex = sp.solve([sp.Eq(Iin, gm1*vN + (vN - vP)/RF),
               sp.Eq(vX/RD, gm1*vN),
               sp.Eq(-gm2*vX, vP/RM + vP/rO2 + (vP - vN)/RF)], [vN, vX, vP], dict=True)[0]
A_ex = sp.simplify(ex[vP]/Iin)
Rin_ex = sp.simplify(ex[vN]/Iin)
print("A_exact = V_out/I_in =", sp.factor(A_ex))
print("R_in,exact = v_N/I_in =", sp.factor(Rin_ex))
It = sp.symbols('I_t')
exo = sp.solve([sp.Eq(0, gm1*vN + (vN - vP)/RF),
                sp.Eq(vX/RD, gm1*vN),
                sp.Eq(It - gm2*vX, vP/RM + vP/rO2 + (vP - vN)/RF)], [vN, vX, vP], dict=True)[0]
Rout_ex = sp.simplify(exo[vP]/It)
print("R_out,exact (I_in open) =", sp.factor(Rout_ex))
ratio = sp.simplify(A_ex/A_cl)
print("ratio A_exact/A_closed =", sp.factor(ratio))
print("  = 1 - 1/(g_m1*g_m2*R_D*R_F) ? :", sp.simplify(ratio - (1 - 1/(gm1*gm2*RD*RF))) == 0)
print("limit g_m2->oo of ratio           =", sp.limit(ratio, gm2, sp.oo))
print("limit g_m2->oo of A_exact         =", sp.limit(A_ex, gm2, sp.oo))
print("limit g_m2->oo of A_closed        =", sp.limit(A_cl, gm2, sp.oo), "  (= 1/K =", 1/K, ")")
print("exact numerator difference A_exact - A_closed =", sp.factor(sp.simplify(A_ex - A_cl)))
print("ratio R_in,exact/R_in,closed   =", sp.factor(sp.simplify(Rin_ex/Rin_cl)),
      " -> limit g_m2->oo:", sp.limit(sp.simplify(Rin_ex/Rin_cl), gm2, sp.oo))
print("ratio R_out,exact/R_out,closed =", sp.factor(sp.simplify(Rout_ex/Rout_cl)),
      " -> limit g_m2->oo:", sp.limit(sp.simplify(Rout_ex/Rout_cl), gm2, sp.oo))
vals = {gm1: 5e-3, gm2: 10e-3, RD: 5e3, RF: 10e3, RM: 2e3, rO2: 20e3}
print("numeric example", vals)
print("  A_open =", A_open.subs(vals), " K*A_open =", KA.subs(vals))
print("  A_closed =", A_cl.subs(vals), " A_exact =", A_ex.subs(vals))
print("  R_in closed/exact =", Rin_cl.subs(vals), Rin_ex.subs(vals))
print("  R_out closed/exact =", Rout_cl.subs(vals), Rout_ex.subs(vals))

print("\n=== 5. Sanity identity ===")
idn = sp.simplify(RF*RD/(RF + 1/gm1) - ((1/gm1)*RF/((1/gm1) + RF))*gm1*RD)
print("simplify(R_F*R_D/(R_F+1/g_m1) - ((1/g_m1)*R_F/((1/g_m1)+R_F))*g_m1*R_D) =", idn, "-> == 0:", idn == 0)
