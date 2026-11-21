"""Coordinator cross-check: adopted blind independent results (independent-blind.json,
written before any answer was shown) vs. author fragment final answers vs. md reference.
Each check prints simplify(fragment - blind); 0 (or limit 0 under the stated approximation) = agree."""
import sympy as sp
g, g1, g2, gN, RD, RD1, RD2, R1, R2, RF, RC, RM, rpi, rO, rO1, rO2, beta, RL0 = sp.symbols(
    'g g1 g2 gN R_D R_D1 R_D2 R1 R2 R_F R_C R_M r_pi r_O r_O1 r_O2 beta R_L0', positive=True)
par = lambda *x: 1/sum(1/v for v in x)
def chk(tag, a, b):
    d = sp.simplify(sp.together(a - b))
    print(f'{tag}: simplify(fragment - blind) = {d}')
K = R2/(R1+R2)
# p1 (E12.07) ideal: R1+R2 >> R_D
A1 = g*RD; T1 = K*A1
chk('p1:b A_closed', g*RD/(1+g*RD*R2/(R1+R2)), A1/(1+T1))
chk('p1:c Rin_closed', (1/g)*(1+g*RD*R2/(R1+R2)), (1+K*g*RD)/g)
chk('p1:c Rout_closed', RD/(1+g*RD*R2/(R1+R2)), RD/(1+g*K*RD))
# p2 (E12.26)
RLp = par(RD, R1+R2); A2 = g1*RLp; T2 = K*A2
chk('p2 A_closed', g1*RD*(R1+R2)/(RD+R1+R2+g1*RD*R2), A2/(1+T2))
chk('p2 Rin_closed', (1/g1)*(1+g1*RD*R2/(RD+R1+R2)), (1/g1)*(1+T2))
chk('p2 Rout_closed', RD*(R1+R2)/(RD+R1+R2+g1*RD*R2), RLp/(1+T2))
# p3 (P12.41) R_D -> ideal current source
A3 = g1*(R1+R2); T3 = K*A3
chk('p3 A_closed', g1*(R1+R2)/(1+g1*R2), A3/(1+T3))
chk('p3 Rin_closed', 1/g1+R2, (1/g1)*(1+T3))
chk('p3 Rout_closed', (R1+R2)/(1+g1*R2), (R1+R2)/(1+T3))
# p4 (P12.42) bipolar, r_pi = beta/g
RB = par(R1, R2); RL = par(RC, R1+R2); rp = beta/g
A4 = beta*RL/(rp+RB); T4 = K*A4
chk('p4 A_closed', RL/(1/g+RB/beta+K*RL), A4/(1+T4))
Rin4_blind = (rp+RB)/(beta+1)*(1+T4)
print('p4 Rin_closed: limit beta->oo of fragment/blind =', sp.limit(sp.simplify((1/g+RB/beta+K*RL)/Rin4_blind), beta, sp.oo), '(fragment uses ~ with beta>>1)')
chk('p4 Rout_closed', RL*(1/g+RB/beta)/(1/g+RB/beta+K*RL), RL/(1+T4))
# p5 (E12.28)
RL5 = par(RD2, R1+R2); A5 = g2*RD1*RL5/(1/g1+par(R1, R2))
chk('p5 A_open', g2*RD1*RL5/(1/g1+par(R1, R2)), A5)
chk('p5 Rout_closed', RL5/(1+K*A5), RL5/(1+K*A5))
# p6 (E12.27)
RL6 = par(rO1, rO2, R1+R2); A6 = gN*RL6
chk('p6 A_closed', gN*RL6/(1+gN*RL6*R2/(R1+R2)), A6/(1+K*A6))
# p7 (E12.29)
R07 = -g1*RF/(1+g1*RF)*RD1*g2*par(RD2, RF); R07b = -g1*g2*RD1*RF*par(RD2, RF)/(1+g1*RF)
chk('p7 R0', R07, R07b)
chk('p7 KR0', (-1/RF)*R07, g1*g2*RD1*par(RD2, RF)/(1+g1*RF))
chk('p7 closed', R07/(1+(-1/RF)*R07), -g1*g2*RD1*RF*par(RD2, RF)/(1+g1*RF+g1*g2*RD1*par(RD2, RF)))
# p8 (2023 Q2)
RL8 = par(RM, RF); R08 = -g1*RF/(1+g1*RF)*RD*g2*RL8
chk('p8:1 R0 vs blind', R08, -g1*g2*RD*RF*RL8/(1+g1*RF))
chk('p8:1 R0 vs md', R08, -g1*g2*RD*par(RF, 1/g1)*RL8)
chk('p8:2 closed', -g1*RF*RD*g2*RL8/(1+g1*RF+g1*RD*g2*RL8), R08/(1-R08/RF))
chk('p8:2 Rin_closed', RF/(1+g1*RF+g1*RD*g2*RL8), par(RF, 1/g1)/(1-R08/RF))
# p9 (2021 Q3)
RL9 = par(RM, RF); D = (1+g1*RF)*(1+g2*RL9)-g1*RD*g2*RL9
R09 = g1*RD*RF/(1+g1*RF)*g2*RL9/(1+g2*RL9)
chk('p9:1 closed vs blind', g1*RF*RD*g2*RL9/D, R09/(1+(-1/RF)*R09))
chk('p9:1 closed vs md', g1*RF*RD*g2*RL9/D, R09/(1-R09/RF))
chk('p9:2 Rin_closed', RF*(1+g1*RF*0+g2*RL9)/D, par(RF, 1/g1)/(1-R09/RF))
chk('p9:2 Rout_closed', RL9*(1+g1*RF)/D, par(RM, RF, 1/g2)/(1-R09/RF))
# p10 (P12.49)
Rin10 = par(RF, rp); Rout10 = par(RC, rO, RF); R010 = -g*Rin10*Rout10
chk('p10 KR0', (-1/RF)*R010, g*Rin10*Rout10/RF)
# p11 (P12.47)
RA = RF+par(R1, R2); RBB = R1+par(R2, RF)
Rm = (RD1+rO1)/(1+g1*rO1); RS1 = (1/g1)*(1+RD1/rO1)
print('p11 R_S1/R_m ->', sp.limit(sp.simplify(RS1/Rm), rO1, sp.oo), '(g_m1 r_O1 >> 1);',
      'ratio =', sp.simplify(RS1/Rm))
K11 = -R2/(R1*R2+R1*RF+R2*RF)
# K by test: V1 at output, input port shorted, current through R_F
chk('p11 K', K11, -(par(R2, RF)/(R1+par(R2, RF)))/RF)
# Recheck (attempt bdc0c868): repaired fragments p1/p4/p8/p10/p11 keep the same final expressions (only = -> ~ notation).
# p10 retry 3 (repaired): loop gain vs R_F, R_o = R_C || r_O.
Ro = sp.Symbol('R_o', positive=True)
T = g*rpi*Ro*RF/((RF+rpi)*(RF+Ro))
print('p10 retry3 dT/dR_F roots:', sp.solve(sp.diff(T, RF), RF), '(single maximum -> non-monotonic overall)')
print('p10 retry3 lim R_F*T (R_F->oo) =', sp.limit(RF*T, RF, sp.oo), '= beta*R_o with g*r_pi=beta, so T ~ beta R_o/R_F')
print('p10 retry3 sign dT/dR_F for R_F > sqrt(r_pi R_o):', sp.simplify(sp.diff(T, RF).subs(RF, 2*sp.sqrt(rpi*Ro))) < 0)
num = {g: sp.Rational(40, 1000), rpi: 2500, Ro: 2000}
print('p10 retry3 T(100k,50k,25k) =', [round(float(T.subs(num).subs(RF, v)), 2) for v in (100000, 50000, 25000)], '|K| = 1/R_F increases as R_F decreases')
