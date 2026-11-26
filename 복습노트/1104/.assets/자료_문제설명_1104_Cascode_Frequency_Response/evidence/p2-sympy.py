"""Independent derivation from the sealed statement and figure."""
from sympy import Eq, I, Symbol, factor, limit, oo, pi, simplify, solve, symbols

s = Symbol("s")

r1, r2, r3, gm, c = symbols("ro1 ro2 ro3 gm3 Cgs3", positive=True)
x,y,it=symbols("Vx Vout It")
rg=r1*r2/(r1+r2)
system=[x/rg+s*c*(x-y),y/r3+(gm+s*c)*(y-x)-it]
z=factor(solve(system,(x,y))[y]/it)
candidate=(1+s*rg*c)/(gm+1/r3+s*c*(1+rg/r3))
assert simplify(z-candidate)==0
print("Retain ro3 from output to AC ground.")
print("Zout:",candidate,"; ro3→∞:",limit(candidate,r3,oo))
print("Zout(0):",candidate.subs(s,0),"; Zout(inf):",limit(candidate,s,oo))
