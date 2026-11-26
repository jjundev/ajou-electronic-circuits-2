"""Independent derivation from the sealed statement and figure."""
from sympy import Eq, I, Symbol, factor, limit, oo, pi, simplify, solve, symbols

s = Symbol("s")

rs, g1, g2, cgs1, cgd1, cgs2 = symbols("R_S gm1 gm2 Cgs1 Cgd1 Cgs2", positive=True)
x, y, vin = symbols("Vx Vout Vin")
equations = [
    (x-vin)/rs + (g1+s*cgs1)*x,
    (g2+s*(cgd1+cgs2))*y-g1*x,
]
nodes = solve(equations, (x,y))
gain = factor(nodes[y]/vin)
print("Common-gate input node Vx:", factor(nodes[x]/vin))
print("Transfer:", gain)
print("Poles:", solve(gain.as_numer_denom()[1], s))
print("Body effect extension: replace gm1 and gm2 by gm1+gmb1 and gm2+gmb2.")

# Junction-capacitance instantiation after the blind two-node derivation.
csb1,cdb1,cdb2=symbols("Csb1 Cdb1 Cdb2",positive=True)
full=gain.subs({cgs1:cgs1+csb1,cgd1:cgd1+cdb1+cdb2},simultaneous=True)
expected=g1*rs**-1/((rs**-1+g1+s*(cgs1+csb1))*(g2+s*(cgd1+cdb1+cgs2+cdb2)))
assert simplify(full-expected)==0
print("With the junction capacitances retained:",full)
