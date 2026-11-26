"""Independent derivation from the sealed statement and figure."""
from sympy import Eq, I, Symbol, factor, limit, oo, pi, simplify, solve, symbols

s = Symbol("s")

r1, r2, gm, c = symbols("ro1 ro2 gm3 Cgs3", positive=True)
x, y, it = symbols("Vx Vout It")
rg=r1*r2/(r1+r2)
system=[x/rg+s*c*(x-y),(gm+s*c)*(y-x)-it]
z=factor(solve(system,(x,y))[y]/it)
candidate=(1+s*rg*c)/(gm+s*c)
assert simplify(z-candidate)==0
print("Input grounded; CS drain is shunted by ro1||ro2.")
print("Zout:",candidate)
print("Zout(0):",z.subs(s,0),"Zout(inf):",limit(z,s,oo))
