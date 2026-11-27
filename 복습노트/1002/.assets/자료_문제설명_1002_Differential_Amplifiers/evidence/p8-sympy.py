import sympy as sp

gm1, gm3, ro1, ro3, ro5, ro7 = sp.symbols(
    "gm1 gm3 ro1 ro3 ro5 ro7", positive=True
)
vi1, vi2, vo1, vo2, vs, vx1, vx2 = sp.symbols(
    "vi1 vi2 vo1 vo2 vs vx1 vx2"
)
i1 = gm1 * (vi1 - vs) + (vo1 - vs) / ro1
i2 = gm1 * (vi2 - vs) + (vo2 - vs) / ro1
i_load1 = (vo1 - vx1) / ro3 - gm3 * vx1
i_load2 = (vo2 - vx2) / ro3 - gm3 * vx2
load_inside1 = i_load1 - vx1 / ro5
load_inside2 = i_load2 - vx2 / ro5
rp = sp.factor(vo1 / i_load1.subs(vx1, sp.solve(load_inside1, vx1)[0]))

nodes = sp.solve(
    [i1 + i_load1, i2 + i_load2, vs / ro7 - i1 - i2, load_inside1, load_inside2],
    [vo1, vo2, vs, vx1, vx2],
)
vd, vc = sp.symbols("vd vc")
ad = sp.factor(
    ((vo1 - vo2).subs(nodes, simultaneous=True) / vd)
    .subs({vi1: vd / 2, vi2: -vd / 2})
)
acm = sp.factor(
    (((vo1 + vo2) / 2).subs(nodes, simultaneous=True) / vc)
    .subs({vi1: vc, vi2: vc})
)
cm_to_diff = sp.simplify(
    (vo1 - vo2).subs(nodes, simultaneous=True).subs({vi1: vc, vi2: vc})
)

r = sp.Rational
id_tail = r(2, 1000)
id_branch = id_tail / 2
mu_n_cox = r(100, 10**6)
mu_p_cox = r(50, 10**6)
lambda_n = lambda_p = r(1, 10)
values = {
    gm1: sp.sqrt(2 * mu_n_cox * (100 / r(1, 5)) * id_branch),
    gm3: sp.sqrt(2 * mu_p_cox * (200 / r(1, 5)) * id_branch),
    ro1: 1 / (lambda_n * id_branch),
    ro3: 1 / (lambda_p * id_branch),
    ro5: 1 / (lambda_p * id_branch),
    ro7: 1 / (lambda_n * id_tail),
}
assert sp.simplify(ad + gm1 * ro1 * rp / (ro1 + rp)) == 0
assert sp.simplify(acm + gm1 * rp / (1 + rp / ro1 + 2 * ro7 * (gm1 + 1 / ro1))) == 0
assert cm_to_diff == 0

for label, expression in [
    ("R_P (ohm)", rp),
    ("A_d", ad),
    ("A_d (leading)", -gm1 * ro1),
    ("A_CM (output mean)", acm),
    ("A_CM (leading)", -gm1 * (gm3 * ro3 * ro5) / (gm3 * ro3 * ro5 / ro1 + 2 * ro7 * gm1)),
    ("A_CM denominator term R_P / r_o1", rp / ro1),
    ("A_CM denominator term 2*r_o7*(gm1 + 1/r_o1)", 2 * ro7 * (gm1 + 1 / ro1)),
    ("CM-to-differential gain", cm_to_diff),
]:
    evaluated = expression.subs(values)
    print(f"{label}: {expression} -> {evaluated} = {sp.N(evaluated, 12)}")
