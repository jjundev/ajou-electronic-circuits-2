from sympy import Eq, Symbol, symbols, solve, simplify, limit, oo

gm1, gm2, RD1, RD2, RF = symbols("gm1 gm2 RD1 RD2 RF", positive=True)
vs, vx, vo, iin = symbols("vs vx vo iin", real=True)
A = gm2 * RD1 * RD2

# Retain both RF terminals to test the virtual-ground interpretation.
network = [Eq(iin, gm1*vs + (vs-vo)/RF),
           Eq(vx/RD1, gm1*vs),
           Eq(vo/RD2 + gm2*vx + (vo-vs)/RF, 0)]
solution = solve(network, (vs, vx, vo), dict=True)[0]
for name, expr, expected in [
    ("vo/iin [ohms]", solution[vo]/iin, -RF),
    ("vs/iin [ohms]", solution[vs]/iin, 0),
    ("current through RF from source to output / iin",
     (solution[vs] - solution[vo])/(RF*iin), 1),
]:
    end = limit(expr, RD1, oo)
    assert simplify(end - expected) == 0
    print(name, "as RD1 -> infinity =", end)
print("M1 source becomes a virtual AC ground. All input current flows from this node through RF to the output.")
