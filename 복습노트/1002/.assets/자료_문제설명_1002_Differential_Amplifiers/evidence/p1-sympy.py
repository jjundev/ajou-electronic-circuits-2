"""E10.10: solve the two collector nodes and the tail node."""
import sympy as sp

v_in, v_1, v_2, v_p = sp.symbols("v_in v_1 v_2 v_p", real=True)
gm, ro, r_pi = sp.symbols("g_m r_o r_pi", positive=True)

# Collector-to-emitter and base-to-emitter currents for the matched input pair.
v_be1, v_be2 = v_in / 2 - v_p, -v_in / 2 - v_p
i_c1 = gm * v_be1 + (v_1 - v_p) / ro
i_c2 = gm * v_be2 + (v_2 - v_p) / ro
i_b1, i_b2 = v_be1 / r_pi, v_be2 / r_pi

# Neither an ideal collector current source nor the ideal tail source has
# an incremental current. Currents sum to zero at all three unknown nodes.
kcl = (i_c1, i_c2, -i_c1 - i_b1 - i_c2 - i_b2)
solution = sp.solve(kcl, (v_1, v_2, v_p), dict=True)[0]
gain = sp.simplify((solution[v_1] - solution[v_2]) / v_in)

print("Node voltages =", solution)
print("Differential gain =", gain)
print("KCL residuals =", [sp.simplify(eq.subs(solution)) for eq in kcl])
assert solution[v_p] == 0
assert gain == -gm * ro
assert all(sp.simplify(eq.subs(solution)) == 0 for eq in kcl)
