# p2 (E10.11, Fig 10.19(a)): BJT diff pair with PNP current-source loads Q3,Q4 (base at Vb = AC gnd).
import sympy as sp
gm1, ro1, rpi1, ro3, vd = sp.symbols('g_m1 r_O1 r_pi1 r_O3 v_d', positive=True)
vP, o1, o2 = sp.symbols('v_P v_o1 v_o2')
v1, v2 = vd/2, -vd/2
ic = lambda b,c,e: gm1*(b-e) + (c-e)/ro1
ib = lambda b,e: (b-e)/rpi1
eqs = [
    sp.Eq(-o1/ro3 - ic(v1,o1,vP), 0),       # node out1: current from r_O3 (to AC gnd) = Q1 collector current
    sp.Eq(-o2/ro3 - ic(v2,o2,vP), 0),
    sp.Eq(ic(v1,o1,vP)+ib(v1,vP)+ic(v2,o2,vP)+ib(v2,vP), 0),
]
s = sp.solve(eqs, [vP,o1,o2], dict=True)[0]
Ad = sp.simplify((s[o1]-s[o2])/vd)
print('v_P =', sp.simplify(s[vP]))
print('A_d =', Ad)
target = -gm1*(ro1*ro3/(ro1+ro3))
print('simplify(A_d + g_m1 (r_O1||r_O3)) =', sp.simplify(Ad-target))
