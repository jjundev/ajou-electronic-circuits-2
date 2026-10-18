# p1 (E10.10, Fig 10.18(a)): BJT diff pair, ideal current-source loads, ideal tail.
# Full small-signal circuit, finite r_o and r_pi, KCL at P, out1, out2.
import sympy as sp
gm, ro, rpi, v1, v2 = sp.symbols('g_m r_O r_pi v_in1 v_in2', positive=True)
vP, o1, o2 = sp.symbols('v_P v_o1 v_o2')
ic = lambda b,c,e: gm*(b-e) + (c-e)/ro      # current into collector
ib = lambda b,e: (b-e)/rpi
eqs = [
    sp.Eq(ic(v1,o1,vP), 0),                 # node out1: ideal load -> no AC current
    sp.Eq(ic(v2,o2,vP), 0),                 # node out2
    sp.Eq(ic(v1,o1,vP)+ib(v1,vP)+ic(v2,o2,vP)+ib(v2,vP), 0),  # node P: ideal tail
]
s = sp.solve(eqs, [vP,o1,o2], dict=True)[0]
Ad = sp.simplify((s[o1]-s[o2])/(v1-v2))
print('A_d =', Ad)
target = -gm*ro
print('simplify(A_d - (-g_m r_O)) =', sp.simplify(Ad-target))
