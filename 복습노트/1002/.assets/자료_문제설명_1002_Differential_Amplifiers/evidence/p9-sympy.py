import sympy as sp

rc, va, vt, ic_tail, alpha, vce3 = sp.symbols(
    "R_C V_A V_T I_C_tail alpha V_CE3", positive=True
)
vc, ve, vo = sp.symbols("v_CM v_E v_o")
re = vt / (ic_tail / 2)
ro3 = va / ic_tail
ie_branch = (vc - ve) / re
nodes = sp.solve([2 * ie_branch - ve / ro3, vo / rc + alpha * ie_branch], [ve, vo])

acm_finite_beta = sp.simplify(nodes[vo] / vc)
acm = sp.factor(acm_finite_beta.subs(alpha, 1))
gain_magnitude = -acm
resistance_current_limit = sp.solve(
    (gain_magnitude - sp.Rational(1, 100)).subs(rc, sp.Symbol("R_C_I_C") / ic_tail),
    sp.Symbol("R_C_I_C"),
)[0]
acm_with_early_correction = sp.simplify(acm.subs(va, va + vce3))
assert sp.simplify(acm + rc * ic_tail / (2 * (va + vt))) == 0
assert sp.simplify(resistance_current_limit - (va + vt) / 50) == 0
assert sp.limit(acm, va, sp.oo) == 0

print(f"Tail KCL: {2 * ie_branch} = {ve / ro3}")
print(f"Single-ended A_CM, finite beta: {acm_finite_beta}")
print(f"Single-ended A_CM, alpha=1: {acm}")
print(f"|A_CM| < 1/100 iff R_C*I_C_tail < {sp.factor(resistance_current_limit)} (alpha=1)")
print(f"A_CM if r_o3=(V_A+V_CE3)/I_C_tail and alpha=1: {acm_with_early_correction}")
print(f"Limit V_A -> infinity: {sp.limit(acm, va, sp.oo)}")
