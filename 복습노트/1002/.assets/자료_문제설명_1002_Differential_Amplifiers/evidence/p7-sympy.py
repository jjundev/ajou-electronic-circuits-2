import sympy as sp

gm1, gm5, ro1, ro3, ro5, ro6 = sp.symbols(
    "gm1 gm5 ro1 ro3 ro5 ro6", positive=True
)
vi1, vi2, vo1, vo2, vs, vx = sp.symbols("vi1 vi2 vo1 vo2 vs vx")
i1 = gm1 * (vi1 - vs) + (vo1 - vs) / ro1
i2 = gm1 * (vi2 - vs) + (vo2 - vs) / ro1
i_tail = (vs - vx) / ro5 - gm5 * vx
tail_inside = i_tail - vx / ro6
rt = sp.factor(vs / i_tail.subs(vx, sp.solve(tail_inside, vx)[0]))

nodes = sp.solve(
    [i1 + vo1 / ro3, i2 + vo2 / ro3, i_tail - i1 - i2, tail_inside],
    [vo1, vo2, vs, vx],
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
id_tail = r(1, 1000)
id_branch = id_tail / 2
mu_n_cox = r(100, 10**6)
lambda_n = lambda_p = r(1, 10)
values = {
    gm1: sp.sqrt(2 * mu_n_cox * (200 / r(1, 5)) * id_branch),
    gm5: sp.sqrt(2 * mu_n_cox * (400 / r(1, 5)) * id_tail),
    ro1: 1 / (lambda_n * id_branch),
    ro3: 1 / (lambda_p * id_branch),
    ro5: 1 / (lambda_n * id_tail),
    ro6: 1 / (lambda_n * id_tail),
}
assert sp.simplify(ad + gm1 * ro1 * ro3 / (ro1 + ro3)) == 0
assert sp.simplify(acm + gm1 * ro3 / (1 + ro3 / ro1 + 2 * rt * (gm1 + 1 / ro1))) == 0
assert cm_to_diff == 0

for label, expression in [
    ("R_tail (ohm)", rt),
    ("A_d", ad),
    ("A_CM (output mean)", acm),
    ("A_CM (large gm*ro, exact R_tail)", -ro3 / (2 * rt)),
    ("A_CM (leading R_tail)", -ro3 / (2 * gm5 * ro5 * ro6)),
    ("CM-to-differential gain", cm_to_diff),
]:
    evaluated = expression.subs(values)
    print(f"{label}: {expression} -> {evaluated} = {sp.N(evaluated, 12)}")
