"""Independent derivation from the sealed statement and figure."""
from sympy import Eq, I, Symbol, factor, limit, oo, pi, simplify, solve, symbols

s = Symbol("s")

rs, g1, g2, go2, ci, cd1, cs2, cd2 = symbols("R_S gm1 gm2 go2 Ci1 Cd1 Cs2 Cd2", positive=True)
x, y, vin = symbols("Vx Vout Vin")
# Ci1 includes Cgs1 and any source junction capacitance retained.
# Cd1 includes Cgd1 and any drain junction capacitance retained.
loads = [
    ("a, M2 with gate/drain at AC ground; output at source",g2+go2, cs2),
    ("b, M2 with source/gate at AC ground; output at drain",go2, cd2),
    ("c, diode at output with source grounded",g2+go2, cs2),
]
for topology, conductance, capacitance in loads:
    equations=[(x-vin)/rs + (g1+s*ci)*x,(conductance+s*(cd1+capacitance))*y-g1*x]
    gain=factor(solve(equations,(x,y))[y]/vin)
    print(topology, "H =", gain, "; DC =", gain.subs(s,0))
print("Take go2=0 only if allowed and the output retains a DC conductance. For (a), add gmb2 if the bulk is at AC ground and body effect is included.")
