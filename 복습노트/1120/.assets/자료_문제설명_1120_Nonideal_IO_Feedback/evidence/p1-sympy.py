import sympy as sp

# Problem 1 (E12.07): Common-gate amplifier with resistive voltage divider feedback
# Assumptions: lambda = 0 (r_O = inf), R1 + R2 >> R_D (divider loading neglected)

g_m, R_D, R_1, R_2 = sp.symbols('g_m R_D R_1 R_2', positive=True, finite=True)
v_in, v_out, v_g, i_in, v_x, i_x = sp.symbols('v_in v_out v_g i_in v_x i_x')
v_1, v_2 = sp.symbols('v_1 v_2')

print("=== p1 (E12.07) SymPy Verification ===")

# Part (a): Four components of feedback system (verified by small-signal equation structure)
# i_d = g_m * (v_g - v_in) = -g_m * (v_in - v_g)
# v_out = -i_d * R_D = g_m * R_D * (v_in - v_g)
print("Part (a) 4 components:")
print("  Feedforward system: CG stage (M1 + R_D), A_1 = g_m * R_D")
print("  Output sensing: Node V_out (parallel voltage sensing)")
print("  Feedback network: Resistive divider R_1, R_2 (K = R_2 / (R_1 + R_2))")
print("  Comparison (subtraction): M1 itself via V_in - V_F = V_S - V_G = -V_GS")

# Part (b): Open-loop and closed-loop voltage gain (under R1+R2 >> R_D, lambda=0)
# Open-loop: gate AC-grounded (v_g = 0), no divider loading on V_out
eq_ol_gain = sp.Eq(v_out / R_D + g_m * (0 - v_in), 0)
v_out_ol = sp.solve(eq_ol_gain, v_out)[0]
A_v_open = sp.simplify(v_out_ol / v_in)

# Feedback factor K: voltage divider with open output port
eq_K = sp.Eq((v_2 - v_1) / R_1 + v_2 / R_2, 0)
v_2_sol = sp.solve(eq_K, v_2)[0]
K = sp.simplify(v_2_sol / v_1)

T = sp.simplify(K * A_v_open)

# Closed-loop gain via feedback equation: v_out = A_v_open * (v_in - K * v_out)
eq_cl_fb = sp.Eq(v_out, A_v_open * (v_in - K * v_out))
A_v_closed_fb = sp.simplify(sp.solve(eq_cl_fb, v_out)[0] / v_in)

# Part (c): Open-loop and closed-loop I/O impedances (under R1+R2 >> R_D, lambda=0)
# Open-loop R_in: v_g = 0, i_in enters source of M1 -> i_in = -i_d = -g_m*(0 - v_in)
eq_rin_ol = sp.Eq(i_in, -g_m * (0 - v_in))
R_in_open = sp.simplify(v_in / sp.solve(eq_rin_ol, i_in)[0])

# Open-loop R_out: v_in = 0, v_g = 0, test voltage v_x at V_out, no divider loading
eq_rout_ol = sp.Eq(i_x, v_x / R_D + g_m * (0 - 0))
R_out_open = sp.simplify(v_x / sp.solve(eq_rout_ol, i_x)[0])

# Closed-loop R_in and R_out via feedback relations (series-shunt / voltage-voltage)
R_in_closed_fb = sp.simplify(R_in_open * (1 + T))
R_out_closed_fb = sp.simplify(R_out_open / (1 + T))

# Direct small-signal KCL in closed-loop (with R1+R2 >> R_D limit AND exact finite R1+R2 check)
# Exact closed-loop KCL (finite R1, R2):
eq_exact_gate = sp.Eq((v_g - v_out) / R_1 + v_g / R_2, 0)
eq_exact_out = sp.Eq(v_out / R_D + (v_out - v_g) / R_1 + g_m * (v_g - v_in), 0)
eq_exact_iin = sp.Eq(i_in, -g_m * (v_g - v_in))
sol_exact = sp.solve([eq_exact_gate, eq_exact_out, eq_exact_iin], [v_g, v_out, i_in])
A_v_closed_exact = sp.simplify(sol_exact[v_out] / v_in)
R_in_closed_exact = sp.simplify(v_in / sol_exact[i_in])

# Exact R_out_closed with v_in = 0:
eq_exact_rout_g = sp.Eq((v_g - v_x) / R_1 + v_g / R_2, 0)
eq_exact_rout_x = sp.Eq(i_x, v_x / R_D + (v_x - v_g) / R_1 + g_m * (v_g - 0))
sol_exact_rout = sp.solve([eq_exact_rout_g, eq_exact_rout_x], [v_g, i_x])
R_out_closed_exact = sp.simplify(v_x / sol_exact_rout[i_x])

# Take asymptotic limit R_sum = R1 + R2 -> oo while keeping K_ratio = R2/(R1+R2) fixed
R_sum, K_ratio = sp.symbols('R_sum K_ratio', positive=True)
subs_asymp = {R_1: (1 - K_ratio) * R_sum, R_2: K_ratio * R_sum}
A_v_asymp = sp.limit(A_v_closed_exact.subs(subs_asymp), R_sum, sp.oo)
R_in_asymp = sp.limit(R_in_closed_exact.subs(subs_asymp), R_sum, sp.oo)
R_out_asymp = sp.limit(R_out_closed_exact.subs(subs_asymp), R_sum, sp.oo)

diff_Av = sp.simplify(A_v_closed_fb.subs(R_2 / (R_1 + R_2), K_ratio) - A_v_asymp.subs(K_ratio, R_2 / (R_1 + R_2)))
# Substitute K_ratio = R_2/(R_1+R_2) cleanly for comparison:
K_expr = R_2 / (R_1 + R_2)
assert sp.simplify(A_v_closed_fb - A_v_asymp.subs(K_ratio, K_expr)) == 0
assert sp.simplify(R_in_closed_fb - R_in_asymp.subs(K_ratio, K_expr)) == 0
assert sp.simplify(R_out_closed_fb - R_out_asymp.subs(K_ratio, K_expr)) == 0

print("\n--- Results ---")
print("A_v_open         =", A_v_open)
print("K                =", K)
print("Loop gain T      =", T)
print("A_v_closed (fb)  =", sp.factor(A_v_closed_fb))
print("R_in_open        =", R_in_open)
print("R_out_open       =", R_out_open)
print("R_in_closed (fb) =", sp.simplify(R_in_closed_fb), "=", sp.expand(R_in_closed_fb))
print("R_out_closed(fb) =", sp.factor(R_out_closed_fb))
print("Exact KCL limit (R1+R2 -> oo) matches feedback formulas: ASSERT PASSED")
print("Exact finite-(R1+R2) A_v_closed   =", sp.factor(A_v_closed_exact))
print("Exact finite-(R1+R2) R_in_closed  =", sp.factor(R_in_closed_exact))
print("Exact finite-(R1+R2) R_out_closed =", sp.factor(R_out_closed_exact))
