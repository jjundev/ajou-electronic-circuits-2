import sympy as sp

# Problem 2 (E12.26): Common-gate amplifier with non-negligible divider loading (R1+R2 not >> R_D)
# Method: Razavi Sec. 12.7.1 two-port voltage-voltage breaking rules (Fig 12.53(a), 12.54(a))
# + Exact full small-signal KCL cross-check. Assumes lambda = 0.

g_m1, R_D, R_1, R_2 = sp.symbols('g_m1 R_D R_1 R_2', positive=True, finite=True)
v_in, v_out, v_g, i_in, v_x, i_x = sp.symbols('v_in v_out v_g i_in v_x i_x')
v_1, v_2, v_m, i_test, v_test = sp.symbols('v_1 v_2 v_m i_test v_test')

print("=== p2 (E12.26) SymPy Verification ===")

# Step 1 & 2: Feedback network two-port termination impedances (Fig 12.53(a))
# Port 1 (sensing replica at V_out, port 2 open)
eq_sense_m = sp.Eq((v_m - v_test) / R_1 + v_m / R_2, 0)
eq_sense_i = sp.Eq(i_test, (v_test - v_m) / R_1)
sol_sense = sp.solve([eq_sense_m, eq_sense_i], [v_m, i_test])
R_sense = sp.simplify(v_test / sol_sense[i_test])

# Port 2 (return replica at gate, port 1 shorted to ground)
eq_ret = sp.Eq(i_test, v_test / R_1 + v_test / R_2)
R_return = sp.simplify(v_test / sp.solve(eq_ret, i_test)[0])

# Step 3 & 4: Open-loop parameters (gate connected to ground through R_return, output loaded by R_sense)
# Note: MOSFET gate current i_g = 0, so v_g = 0 even with R_return != 0.
eq_gate_ol = sp.Eq(v_g / R_return, 0)
eq_out_ol = sp.Eq(v_out / R_D + v_out / R_sense + g_m1 * (v_g - v_in), 0)
eq_iin_ol = sp.Eq(i_in, -g_m1 * (v_g - v_in))
sol_ol = sp.solve([eq_gate_ol, eq_out_ol, eq_iin_ol], [v_g, v_out, i_in])

A_v_open = sp.simplify(sol_ol[v_out] / v_in)
R_in_open = sp.simplify(v_in / sol_ol[i_in])

# Open-loop output impedance: v_in = 0, test source v_x, i_x at V_out
eq_rout_ol_g = sp.Eq(v_g / R_return, 0)
eq_rout_ol_x = sp.Eq(i_x, v_x / R_D + v_x / R_sense + g_m1 * (v_g - 0))
sol_rout_ol = sp.solve([eq_rout_ol_g, eq_rout_ol_x], [v_g, i_x])
R_out_open = sp.simplify(v_x / sol_rout_ol[i_x])

# Step 5: Feedback factor K (Fig 12.54(a))
eq_K = sp.Eq((v_2 - v_1) / R_1 + v_2 / R_2, 0)
K = sp.simplify(sp.solve(eq_K, v_2)[0] / v_1)
T = sp.simplify(K * A_v_open)

# Step 6: Closed-loop parameters via feedback equations
eq_cl_fb = sp.Eq(v_out, A_v_open * (v_in - K * v_out))
A_v_closed_fb = sp.simplify(sp.solve(eq_cl_fb, v_out)[0] / v_in)
R_in_closed_fb = sp.simplify(R_in_open * (1 + T))
R_out_closed_fb = sp.simplify(R_out_open / (1 + T))

# Independent Exact Small-Signal KCL (no feedback decomposition)
eq_ex_g = sp.Eq((v_g - v_out) / R_1 + v_g / R_2, 0)
eq_ex_out = sp.Eq(v_out / R_D + (v_out - v_g) / R_1 + g_m1 * (v_g - v_in), 0)
eq_ex_iin = sp.Eq(i_in, -g_m1 * (v_g - v_in))
sol_ex = sp.solve([eq_ex_g, eq_ex_out, eq_ex_iin], [v_g, v_out, i_in])

A_v_closed_exact = sp.simplify(sol_ex[v_out] / v_in)
R_in_closed_exact = sp.simplify(v_in / sol_ex[i_in])

eq_ex_rout_g = sp.Eq((v_g - v_x) / R_1 + v_g / R_2, 0)
eq_ex_rout_x = sp.Eq(i_x, v_x / R_D + (v_x - v_g) / R_1 + g_m1 * (v_g - 0))
sol_ex_rout = sp.solve([eq_ex_rout_g, eq_ex_rout_x], [v_g, i_x])
R_out_closed_exact = sp.simplify(v_x / sol_ex_rout[i_x])

# Verify exact identity between two-port feedback method and exact KCL
assert sp.simplify(A_v_closed_fb - A_v_closed_exact) == 0
assert sp.simplify(R_in_closed_fb - R_in_closed_exact) == 0
assert sp.simplify(R_out_closed_fb - R_out_closed_exact) == 0

print("R_sense (open port 2) =", R_sense)
print("R_return (short port 1) =", R_return)
print("A_v_open     =", sp.factor(A_v_open))
print("R_in_open    =", R_in_open)
print("R_out_open   =", sp.factor(R_out_open))
print("K            =", K)
print("Loop gain T  =", sp.factor(T))
print("A_v_closed   =", sp.factor(A_v_closed_fb))
print("R_in_closed  =", sp.factor(R_in_closed_fb), "=", sp.apart(R_in_closed_fb, g_m1))
print("R_out_closed =", sp.factor(R_out_closed_fb))
print("Exact KCL vs Feedback Method difference == 0: ASSERT PASSED for all quantities")

# Numerical sanity check
vals = {g_m1: sp.Rational(1, 100), R_D: 2000, R_1: 3000, R_2: 1000}
print("\nNumerical check (g_m1=10mS, R_D=2k, R_1=3k, R_2=1k):")
for name, expr in [
    ("A_v_open", A_v_open), ("K", K), ("T", T),
    ("A_v_closed", A_v_closed_fb),
    ("R_in_open", R_in_open), ("R_in_closed", R_in_closed_fb),
    ("R_out_open", R_out_open), ("R_out_closed", R_out_closed_fb)
]:
    print(f"  {name:14s} = {sp.N(expr.subs(vals), 6)}")
