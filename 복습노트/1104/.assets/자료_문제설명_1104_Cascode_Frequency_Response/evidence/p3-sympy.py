"""Independent derivation from the sealed statement and figure."""
from sympy import Eq, I, Symbol, factor, limit, oo, pi, simplify, solve, symbols

s = Symbol("s")

rb,rpi,gm,cp,cm=symbols("R_B r_pi gm C_pi C_mu", positive=True)
b,e,it=symbols("Vb Ve It")
yb=1/rb+s*cm
yp=1/rpi+s*cp
system=[yb*b+yp*(b-e),(gm+yp)*(e-b)-it]
z=factor(solve(system,(b,e))[e]/it)
candidate=(yb+yp)/(yb*(yp+gm))
assert simplify(z-candidate)==0
print("Zout:",candidate)
print("Pole corners:",1/(rb*cm),(gm+1/rpi)/cp)
print("Zero corner:",(1/rb+1/rpi)/(cp+cm))
print("Zout(0):",factor(z.subs(s,0)),"Zout(inf):",limit(z,s,oo))
print("HF coefficient s*Zout:",limit(s*z,s,oo))
print("Magnitude asymptotes start flat. Add 20 dB/dec at the zero and subtract 20 dB/dec at each pole in actual corner order; end at -20 dB/dec.")
