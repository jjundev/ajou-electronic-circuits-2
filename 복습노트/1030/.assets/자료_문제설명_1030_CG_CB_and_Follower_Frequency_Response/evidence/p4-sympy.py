"""Independent derivation from the sealed statement and figure."""
from sympy import Eq, I, Symbol, factor, limit, oo, pi, simplify, solve, symbols

s = Symbol("s")

g1, gb1, g2, go1, go2, cgs = symbols("gm1 gmb1 gm2 go1 go2 Cgs1", positive=True)
vin, x = symbols("Vin Vx")
yout=gb1+go1+g2+go2
eq=yout*x+(g1+s*cgs)*(x-vin)
ratio=factor(solve(eq,x)[0]/vin)
yin=factor(s*cgs*(1-ratio))
print("Source gain:", ratio)
print("Input admittance:", yin)
print("Low-frequency Cin:", simplify(limit(yin/s,s,0)))
print("Diode M2 has fixed source and bulk so no body transconductance term. The usual no-body-effect model sets gmb1=0.")
