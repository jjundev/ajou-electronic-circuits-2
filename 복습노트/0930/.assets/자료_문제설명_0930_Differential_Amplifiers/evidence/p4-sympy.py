# p4 (P10.52) Fig 10.78 (a)-(c), full-circuit KCL, lambda>0, body effect neglected
# (a) M3/M4 NMOS, drain and gate at VDD (ac ground), source at the output node
# (b) as (a) plus PMOS current sources M5/M6 (gate Vb) from VDD to the output nodes (r_o5)
# (c) PMOS M3/M4, sources at VDD, drains at outputs, gates tied to midpoint of R1 = R2 between drains
import sympy as sp
gm1, gm3, ro1, ro3, ro5, R1 = sp.symbols(
    'g_m1 g_m3 r_o1 r_o3 r_o5 R_1', positive=True)
vin, vx, vy, vp, vm = sp.symbols('v_in v_x v_y v_p v_m')
par = lambda *z: 1/sum(1/zz for zz in z)
def m1(vg, vd):
    return gm1*(vg - vp) + (vd - vp)/ro1
def solve(load_x, load_y, extra=(), unk=()):
    # load_x: small-signal current leaving node X through the load network
    eqs = [sp.Eq(m1(vin/2, vx) + load_x, 0), sp.Eq(m1(-vin/2, vy) + load_y, 0),
           sp.Eq(m1(vin/2, vx) + m1(-vin/2, vy), 0)] + list(extra)
    s = sp.solve(eqs, [vx, vy, vp] + list(unk), dict=True)[0]
    return sp.simplify((s[vx]-s[vy])/vin)
# (a) NMOS follower load, gate ac ground: current leaving X down through M3 = -(gm3*(0-vx) - vx/ro3)
Aa = solve(gm3*vx + vx/ro3, gm3*vy + vy/ro3)
Ab = solve(gm3*vx + vx/ro3 + vx/ro5, gm3*vy + vy/ro3 + vy/ro5)
# (c) PMOS: source->drain current = gm3*(v_s - v_g) = -gm3*vm flows INTO X; leaving X = gm3*vm + vx/ro3
Ac = solve(gm3*vm + vx/ro3 + (vx - vm)/R1, gm3*vm + vy/ro3 + (vy - vm)/R1,
           [sp.Eq((vx - vm)/R1 + (vy - vm)/R1, 0)], [vm])
for name, A, T in [('(a)', Aa, -gm1*par(1/gm3, ro1, ro3)),
                   ('(b)', Ab, -gm1*par(1/gm3, ro1, ro3, ro5)),
                   ('(c)', Ac, -gm1*par(ro1, ro3, R1))]:
    print(name, 'A_v =', sp.factor(A), ' | simplify(A - target) =', sp.simplify(A - T))
