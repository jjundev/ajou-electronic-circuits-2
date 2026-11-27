"""E10.11: solve the differential BJT pair with PNP loads."""
import sympy as sp

v_in, v_1, v_2, v_p = sp.symbols("v_in v_1 v_2 v_p", real=True)
gm, ro_in, ro_load, r_pi = sp.symbols("g_m1 r_o1 r_o3 r_pi1", positive=True)

# The PNP bases and emitters have fixed bias voltages. Their transconductance
# currents vanish, and each r_o connects its collector to AC ground.
v_be1, v_be2 = v_in / 2 - v_p, -v_in / 2 - v_p
i_c1 = gm * v_be1 + (v_1 - v_p) / ro_in
i_c2 = gm * v_be2 + (v_2 - v_p) / ro_in
i_b1, i_b2 = v_be1 / r_pi, v_be2 / r_pi

kcl = (
    i_c1 + v_1 / ro_load,
    i_c2 + v_2 / ro_load,
    -i_c1 - i_b1 - i_c2 - i_b2,
)
solution = sp.solve(kcl, (v_1, v_2, v_p), dict=True)[0]
gain = sp.factor((solution[v_1] - solution[v_2]) / v_in)

print("Node voltages =", solution)
print("Differential gain =", gain)
print("Ideal load limit (r_o3 -> infinity) =", sp.limit(gain, ro_load, sp.oo))
print("KCL residuals =", [sp.simplify(eq.subs(solution)) for eq in kcl])
assert solution[v_p] == 0
assert sp.simplify(gain + gm / (1 / ro_in + 1 / ro_load)) == 0
assert all(sp.simplify(eq.subs(solution)) == 0 for eq in kcl)
