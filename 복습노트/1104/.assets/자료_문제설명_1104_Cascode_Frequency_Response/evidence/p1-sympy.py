import sympy as sp

s = sp.symbols("s")
ro1, ro2, C, gm = sp.symbols("ro1 ro2 Cgs3 gm3", positive=True)
gmb = sp.symbols("gmb3", nonnegative=True)
vx, vt, it = sp.symbols("vx vt it")
R = sp.symbols("R", positive=True)
parallel = 1 / (1 / ro1 + 1 / ro2)

# Gate-node KCL and current entering the output port.
gate_kcl = vx / R + s * C * (vx - vt)
output_kcl = (gm + s * C) * (vt - vx) + gmb * vt - it
solution = sp.solve([gate_kcl, output_kcl], [vx, vt])
z_general = sp.factor(solution[vt] / it)
z = sp.factor(z_general.subs(gmb, 0))
assert sp.simplify(z - (1 + s * R * C) / (gm + s * C)) == 0
assert sp.simplify(gate_kcl.subs(solution)) == 0
assert sp.simplify(output_kcl.subs(solution)) == 0
assert sp.limit(z, s, 0) == 1 / gm
assert sp.limit(z, s, sp.oo) == R
assert sp.limit(z, C, 0) == 1 / gm
print("R =", parallel)
print("vx/vt =", sp.solve(gate_kcl, vx)[0] / vt)
print("Zout =", z)
print("Zout with R expanded =", sp.factor(z.subs(R, parallel)))
print("Zout with grounded-body effect =", z_general)
print("DC limit =", sp.limit(z, s, 0))
print("High-frequency limit =", sp.limit(z, s, sp.oo))
print("Cgs3 -> 0 limit =", sp.limit(z, C, 0))
print("Both KCL residuals and closed-form agreement verified.")
