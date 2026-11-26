"""Independent derivation from the sealed statement and figure."""
from sympy import Eq, I, Symbol, factor, limit, oo, pi, simplify, solve, symbols

s = Symbol("s")

rs,rp,rd,g1,g2,c1,cd1,c2,cd2=symbols("R_S R_P R_D gm1 gm2 Cgs1 Cgd1 Cgs2 Cgd2",positive=True)
vi,g,x,y=symbols("Vin Vg Vx Vout")
gz=g2+1/rp
low=solve([gz*x+g1*g,y/rd-g2*x],(x,y))
av=factor(low[x]/g)
ci=c1+cd1*(1-av)
cx=c2+cd1*(1-1/av)
h=factor(solve([(g-vi)/rs+s*ci*g,(gz+s*cx)*x+g1*g,(1/rd+s*cd2)*y-g2*x],(g,x,y))[y]/vi)
print("DC local gain across Cgd1:",av)
print("Miller split:",ci,cx)
print("Miller one-way H(s):",h)
print("Pole locations:",-1/(rs*ci),-gz/cx,-1/(rd*cd2))

# Junction-capacitance instantiation following the independent three-node derivation.
cdb1,csb2,cdb2=symbols("Cdb1 Csb2 Cdb2",positive=True)
full=h.subs({c2:cdb1+c2+csb2,cd2:cd2+cdb2},simultaneous=True)
expected=-g1*g2/((1+s*rs*ci)*(gz+s*(cx+cdb1+csb2))*(1/rd+s*(cd2+cdb2)))
assert simplify(full-expected)==0
print("With the node junction capacitances retained:",full)
