import sympy as sp

vi, vo, xn, xp = sp.symbols("v_i v_o x_n x_p")
gn, gp, nn, np = sp.symbols("g_mn g_mp g_on g_op", positive=True)
# Both output currents use the reference direction out of the output node.
inner_n_kcl = gn * vi + (gn + 2 * nn) * xn - nn * vo
inner_p_kcl = (gp + 2 * np) * xp - np * vo
inner = sp.solve([inner_n_kcl, inner_p_kcl], [xn, xp])
i_n = sp.factor((nn * vo - (nn + gn) * xn).subs(inner))
i_p = sp.factor((np * vo - (np + gp) * xp).subs(inner))
gm_eff = sp.factor(i_n.diff(vi))
r_n = sp.factor(1 / i_n.diff(vo))
r_p = sp.factor(1 / i_p.diff(vo))
gain = sp.factor(sp.solve(i_n + i_p, vo)[0] / vi)

s = sp.symbols("s", positive=True)  # s = sqrt(W/L)
ratio = sp.symbols("W_over_L", positive=True)
branch_current = sp.Rational(1, 2000)
gmn = s * sp.sqrt(2 * sp.Rational(100, 10**6) * branch_current)
gmp = s * sp.sqrt(2 * sp.Rational(50, 10**6) * branch_current)
small_signal = {
    gn: gmn,
    gp: gmp,
    nn: sp.Rational(1, 10) * branch_current,
    np: sp.Rational(1, 5) * branch_current,
}
exact_magnitude = -gain.subs(small_signal)
target_polynomial, denominator = sp.fraction(sp.together(exact_magnitude - 200))
positive_root = sp.nsolve(target_polynomial, s, 5.7)
assert abs(exact_magnitude.subs(s, positive_root).evalf() - 200) < sp.Rational(1, 10**8)
coefficient_signs = [sp.sign(c) for c in sp.Poly(target_polynomial, s).all_coeffs() if c != 0]
assert sum(a != b for a, b in zip(coefficient_signs, coefficient_signs[1:])) == 1

r_n_large_gain = gn / nn**2
r_p_large_gain = gp / np**2
standard_magnitude = sp.simplify(
    (gn / (1 / r_n_large_gain + 1 / r_p_large_gain)).subs(small_signal).subs(s, sp.sqrt(ratio))
)
leading_ratio = sp.solve(standard_magnitude - 200, ratio)[0]
print("G_m,eff =", gm_eff)
print("R_n =", r_n)
print("R_p =", r_p)
print("A_v, left minus right =", gain)
print("Exact gain target numerator =", sp.expand(target_polynomial))
print("Exact gain denominator =", sp.expand(denominator))
print("Exact W/L within the first-order small-signal and square-law model =", (positive_root**2).evalf(12))
print("Standard high-intrinsic-gain |A_v| =", sp.factor(standard_magnitude))
print("Standard W/L =", leading_ratio, "=", leading_ratio.evalf(12))
