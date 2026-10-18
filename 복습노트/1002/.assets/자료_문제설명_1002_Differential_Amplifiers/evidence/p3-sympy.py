# p3 (E10.13, Fig 10.22(a)): BJT pair, PNP loads Q3,Q4 with bases at X, R1=R2 from each collector to X.
# Full circuit incl. r_pi of Q3/Q4 into node X. Symmetric: Q1=Q2 (g_m1,r_O1,r_pi1), Q3=Q4 (g_m3,r_O3,r_pi3), R1=R2.
import sympy as sp
gm1, ro1, rpi1, gm3, ro3, rpi3, R1, vd = sp.symbols('g_m1 r_O1 r_pi1 g_m3 r_O3 r_pi3 R_1 v_d', positive=True)
vP, o1, o2, X = sp.symbols('v_P v_o1 v_o2 v_X')
v1, v2 = vd/2, -vd/2
icN = lambda b,c,e: gm1*(b-e) + (c-e)/ro1
ibN = lambda b,e: (b-e)/rpi1
icP = lambda b,c,e: gm3*(b-e) + (c-e)/ro3   # same linear model for PNP; emitter = VCC = 0
ibP = lambda b,e: (b-e)/rpi3
eqs = [
    sp.Eq(icP(X,o1,0) + icN(v1,o1,vP) + (o1-X)/R1, 0),    # node out1: currents leaving node
    sp.Eq(icP(X,o2,0) + icN(v2,o2,vP) + (o2-X)/R1, 0),
    sp.Eq((X-o1)/R1 + (X-o2)/R1 + ibP(X,0)*2, 0),         # node X (both bases)
    sp.Eq(icN(v1,o1,vP)+ibN(v1,vP)+icN(v2,o2,vP)+ibN(v2,vP), 0),
]
s = sp.solve(eqs, [vP,o1,o2,X], dict=True)[0]
Ad = sp.simplify((s[o1]-s[o2])/vd)
print('v_X =', sp.simplify(s[X]), ' v_P =', sp.simplify(s[vP]))
print('A_d =', Ad)
par = 1/(1/ro1+1/ro3+1/R1)
print('simplify(A_d + g_m1 (r_O1||r_O3||R_1)) =', sp.simplify(Ad + gm1*par))
