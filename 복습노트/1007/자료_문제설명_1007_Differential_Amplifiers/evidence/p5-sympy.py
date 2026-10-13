# p5 (2021-1 midterm Q4): NMOS diff pair M1,M2, PMOS current-source loads M3,M4, cascode tail M5/M6.
import sympy as sp

# ---- bias / small-signal parameters ----
ID6 = sp.Rational(2, 1000); ID1 = ID6/2
un, up, lam = sp.Rational(100, 10**6), sp.Rational(50, 10**6), sp.Rational(1, 10)
gm = lambda k, W_L, I: sp.sqrt(2*k*W_L*I)
gm1v = gm(un, 500, ID1); ro1v = 1/(lam*ID1)
gm3v = gm(up, 1000, ID1); ro3v = 1/(lam*ID1)
gm5v = gm(un, 1000, ID6); ro5v = 1/(lam*ID6); ro6v = ro5v
print("gm1 =", gm1v, "S, ro1 =", ro1v, "ohm, gm1*ro1 =", gm1v*ro1v)
print("ro3 =", ro3v, "ohm (PMOS load, gm3 =", gm3v, ")")
print("gm5 =", gm5v, "S, ro5 = ro6 =", ro5v, "ohm")

# ---- full-circuit small-signal KCL (symbolic) ----
g1, r1, r3, dR, g5, r5, r6, vi1, vi2 = sp.symbols('g_m1 r_o1 r_o3 DeltaR g_m5 r_o5 r_o6 v_in1 v_in2', positive=True)
vX, vY, vP, vQ = sp.symbols('v_X v_Y v_P v_Q')
RL1, RL2 = r3, r3 + dR          # output-resistance mismatch DeltaR between the two loads
i1 = g1*(vi1 - vP) + (vX - vP)/r1   # drain current of M1 (into drain, X -> P)
i2 = g1*(vi2 - vP) + (vY - vP)/r1
i5 = g5*(0 - vQ) + (vP - vQ)/r5     # M5 gate at ac ground
eqs = [sp.Eq(-vX/RL1, i1),          # KCL at X: current from load = i1
       sp.Eq(-vY/RL2, i2),
       sp.Eq(i1 + i2, i5),          # KCL at P
       sp.Eq(i5, vQ/r6)]            # KCL at Q (M6 = r_o6)
sol = sp.solve(eqs, [vX, vY, vP, vQ], dict=True)[0]

# Tail resistance (looking into M5 drain)
Rss = r5 + r6 + g5*r5*r6
print("\nR_SS exact =", sp.N(Rss.subs({g5: gm5v, r5: ro5v, r6: ro6v})), "ohm;  gm5*ro5*ro6 =", gm5v*ro5v*ro6v)

vals = {g1: gm1v, r1: ro1v, r3: ro3v, g5: gm5v, r5: ro5v, r6: ro6v}
vc = sp.symbols('v_c')

# (1) A_CM (matched loads), single-ended
ACM = sp.simplify((sol[vX]/vi1).subs({vi2: vi1, dR: 0}))
ACM_target = -g1*r1*r3/(r3 + r1 + (1 + g1*r1)*2*Rss)
print("\n(1) A_CM exact symbolic check: simplify(A_CM - target) =", sp.simplify(ACM - ACM_target))
print("    A_CM exact numeric =", sp.N(ACM.subs(vals), 6))
# approximation gm*ro >> 1 : r_o1 -> oo then gm5 large
ACM_approx = -r3/(1/g1 + 2*Rss)
print("    limit r_o1->oo of A_CM equals -r_o3/(1/gm1+2R_SS):", sp.simplify(sp.limit(ACM, r1, sp.oo) - ACM_approx) == 0)
print("    -r_o3/(1/gm1 + 2 gm5 ro5 ro6) =", sp.N((-r3/(1/g1 + 2*g5*r5*r6)).subs(vals), 6), " ~ -r_o3/(2R_SS) =", sp.N((-r3/(2*g5*r5*r6)).subs(vals), 6))

# A_CM-DM with DeltaR = 50 ohm
ACMDM = sp.simplify(((sol[vX] - sol[vY])/vi1).subs({vi2: vi1}))
ACMDM_lin = sp.simplify(sp.diff(ACMDM, dR).subs(dR, 0))          # first order in DeltaR
print("\n    A_CM-DM exact (DeltaR=50) =", sp.N(ACMDM.subs(vals).subs(dR, 50), 6))
print("    limit r_o1->oo of dA/dDeltaR = 1/(1/gm1+2R_SS):", sp.simplify(sp.limit(ACMDM_lin, r1, sp.oo) - 1/(1/g1 + 2*Rss)) == 0)
print("    DeltaR/(1/gm1 + 2 gm5 ro5 ro6) =", sp.N((50/(1/g1 + 2*g5*r5*r6)).subs(vals), 6), " ~ DeltaR/(2R_SS) =", sp.N((50/(2*g5*r5*r6)).subs(vals), 6))

# (2) differential gain (matched), (vX - vY)/(vin1 - vin2)
vd = sp.symbols('v_d')
Ad = sp.simplify(((sol[vX] - sol[vY]).subs({vi1: vd/2, vi2: -vd/2, dR: 0}))/vd)
print("\n(2) A_d: simplify(A_d - (-gm1 (ro1||ro3))) =", sp.simplify(Ad - (-g1*r1*r3/(r1 + r3))))
Ad_num = sp.N(Ad.subs(vals), 6)
print("    A_d =", Ad_num)
CMRR_exact = sp.N(abs(Ad.subs(vals)) / ACMDM.subs(vals).subs(dR, 50), 6)
CMRR_approx = sp.N(abs(Ad.subs(vals)) / (50/(2*gm5v*ro5v*ro6v)), 6)
print("    CMRR exact =", CMRR_exact, "=", sp.N(20*sp.log(CMRR_exact, 10), 5), "dB")
print("    CMRR (gm ro>>1 approx) =", CMRR_approx, "=", sp.N(20*sp.log(CMRR_approx, 10), 5), "dB")
