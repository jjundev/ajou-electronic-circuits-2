"""Independent derivation from the sealed statement and figure."""
from sympy import Eq, I, Symbol, factor, limit, oo, pi, simplify, solve, symbols

s = Symbol("s")

g1, gb1, go1, go2, cgs, cgd = symbols("gm1 gmb1 go1 go2 Cgs1 Cgd1", positive=True)
vin, x = symbols("Vin Vx")
yout=gb1+go1+go2
eq=yout*x+(g1+s*cgs)*(x-vin)
ratio=factor(solve(eq,x)[0]/vin)
yin=factor((s*cgs*(vin-ratio*vin)+s*cgd*vin)/vin)
print("Source gain:", ratio)
print("Input admittance:", yin)
print("Low-frequency Cin:", simplify(limit(yin/s,s,0)))
print("M2 contributes go2 since its gate/source are both AC grounded; standard no-body-effect model sets gmb1=0.")
