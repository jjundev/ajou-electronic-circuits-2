from sympy import Eq, Symbol, symbols, solve, simplify, limit, oo

gm1, gm2, RD1, RD2, RF = symbols("gm1 gm2 RD1 RD2 RF", positive=True)
vs, vx, vo, iin = symbols("vs vx vo iin", real=True)
A = gm2 * RD1 * RD2

# The gate of M1 and both supplies are AC grounds. A positive incremental
# source voltage lowers M1 drain-to-source current, raising vx.
drive = solve([Eq(iin, gm1*vs), Eq(vx/RD1, gm1*vs),
               Eq(vo/RD2 + gm2*vx, 0)], [vs, vx, vo], dict=True)[0]
assert simplify(drive[vo]/iin + A) == 0
print("(a) iin up -> vs up -> vx up -> vo down. The output-to-input feedback current decreases, opposing iin.")
print("(b) unloaded open-loop vo/iin =", simplify(drive[vo]/iin), "ohms")
# Under the large-RF loading approximation, iRF is vo/RF (output to input).
impedance = solve(Eq(vo, -A*(iin + vo/RF)), vo)[0]/iin
assert simplify(impedance + A/(1 + A/RF)) == 0
print("(c) closed-loop vo/iin =", simplify(impedance), "ohms")
