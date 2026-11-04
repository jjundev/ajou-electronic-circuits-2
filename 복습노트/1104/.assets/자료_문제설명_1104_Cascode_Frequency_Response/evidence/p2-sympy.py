"""Solve Fig. 11.49(a) with a test current entering the output node."""
import sympy as sp

s = sp.symbols("s")
R, C, gm, go, gmb = sp.symbols("R C gm go gmb", positive=True)
vx, vy, it = sp.symbols("v_x v_y i_test")
G = go + gmb

gate_kcl = vx / R + s * C * (vx - vy)
source_kcl = G * vy + (gm + s * C) * (vy - vx) - it
solution = sp.solve([gate_kcl, source_kcl], [vx, vy])
zout = sp.factor(solution[vy] / it)
expected = (1 + s * R * C) / (gm + G + s * C * (1 + R * G))
checks = {
    "closed form": expected,
}
assert sp.simplify(zout - checks["closed form"]) == 0
assert sp.simplify(zout.subs(s, 0) - 1 / (gm + G)) == 0
assert sp.simplify(sp.limit(zout, s, sp.oo) - R / (1 + R * G)) == 0
assert sp.simplify(zout.subs({go: 0, gmb: 0}) - (1 + s * R * C) / (gm + s * C)) == 0
assert sp.simplify(zout.subs(gm, 1/R) - R/(1 + R * G)) == 0

print("R = ro1 || ro2, go = 1/ro3, C = Cgs3")
print("Gate KCL:", gate_kcl)
print("Source KCL:", source_kcl)
print("Zout:", zout)
print("Zout with no body effect:", zout.subs(gmb, 0))
print("DC:", sp.factor(zout.subs(s, 0)))
print("High frequency:", sp.limit(zout, s, sp.oo))
print("ro3 infinite, no body effect:", zout.subs({go: 0, gmb: 0}))
print("Pole:", sp.solve(sp.denom(expected), s)[0])
print("Zero:", sp.solve(sp.numer(expected), s)[0])
print("All five symbolic assertions passed.")
