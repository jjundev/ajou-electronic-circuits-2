"""P10.62: derive a MOS cascode gain from the differential node KCL."""
import sympy as sp

v_id, v_x, v_out = sp.symbols("v_id v_x v_out", real=True)
gm1, gm3, ro1, ro3 = sp.symbols("g_m1 g_m3 r_o1 r_o3", positive=True)
gmb3 = sp.symbols("g_mb3", nonnegative=True)
x = sp.symbols("x", positive=True)

# voltages and currents below mean left branch minus right branch.
# The M1/M2 source is shared, and the M3/M4 gates and bulks are at fixed bias.
i_1 = gm1 * v_id + v_x / ro1
i_3 = -(gm3 + gmb3) * v_x + (v_out - v_x) / ro3

# The two ideal loads have zero incremental current.
kcl = (i_1 - i_3, i_3)
solution = sp.solve(kcl, (v_x, v_out), dict=True)[0]
gain = sp.factor(solution[v_out] / v_id)
matched_magnitude = sp.simplify(
    -gain.subs({gmb3: 0, gm3: gm1, ro3: ro1}).subs(gm1, x / ro1)
)

beta = sp.Rational(100, 10**6) * 20 / sp.Rational(18, 100)
channel_modulation = sp.Rational(1, 10)
target_gain = 300
# For I_D = I_SS / 2, (g_m r_o)^2 = 4 beta / (lambda^2 I_SS).
x_exact = sp.solve(matched_magnitude - target_gain, x)[0]
x_approx = sp.sqrt(target_gain)
tail_current = 4 * beta / (channel_modulation**2 * x**2)
tail_exact = tail_current.subs(x, x_exact)
tail_approx = tail_current.subs(x, x_approx)

print("Differential node voltages =", solution)
print("Differential gain =", gain)
print("KCL residuals =", [sp.simplify(eq.subs(solution)) for eq in kcl])
print("Matched gain magnitude with no body effect =", matched_magnitude)
print("High-gain limit of |A_v|/(g_m r_o)^2 =", sp.limit(matched_magnitude / x**2, x, sp.oo))
print("beta (A/V^2) =", beta)
print("Positive exact x =", x_exact)
print("Exact-KCL tail current (mA) =", sp.N(1000 * tail_exact, 10))
print("High-gain approximate tail current (mA) =", sp.N(1000 * tail_approx, 10))
print("Exact magnitude at the approximate current =", sp.N(matched_magnitude.subs(x, x_approx), 10))
assert all(sp.simplify(eq.subs(solution)) == 0 for eq in kcl)
assert sp.simplify(matched_magnitude - (x**2 + x)) == 0
assert sp.simplify(matched_magnitude.subs(x, x_exact)) == target_gain
assert sp.simplify(x_approx**2) == target_gain
