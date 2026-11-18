from sympy import Eq, Symbol, symbols, solve, simplify, limit, oo

gm1, gm2, RD1, RD2, RF = symbols("gm1 gm2 RD1 RD2 RF", positive=True)
vs, vx, vo, iin = symbols("vs vx vo iin", real=True)
A = gm2 * RD1 * RD2

# Test source is applied at M1 source with feedback connected.
network = [Eq(iin, gm1*vs + (vs-vo)/RF),
           Eq(vx/RD1, gm1*vs),
           Eq(vo/RD2 + gm2*vx + (vo-vs)/RF, 0)]
solution = solve(network, (vs, vx, vo), dict=True)[0]
exact = simplify(solution[vs]/iin)
assert simplify(exact - (RF+RD2)/(1+gm1*(RF+RD2+A))) == 0
print("with finite RF and both loading effects: Rin =", exact, "ohms")
# Disregard the small source-end voltage in iRF, and the load at the output.
model = solve([Eq(gm1*vs, iin+vo/RF), Eq(vo, -A*gm1*vs)],
              [vs, vo], dict=True)[0]
zin = simplify(model[vs]/iin)
assert simplify(zin - 1/(gm1*(1+A/RF))) == 0
print("under the stated large-RF approximation: Rin =", zin, "ohms")
print("open-loop 1/gm1 is reduced by 1 + A/RF")
