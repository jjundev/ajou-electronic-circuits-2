"""Independent derivation from the sealed statement and figure."""
from sympy import Eq, I, Symbol, factor, limit, oo, pi, simplify, solve, symbols

s = Symbol("s")

from sympy import Rational
i=Rational(5,10000)
v=Rational(1,5)
g=2*i/v
l=Rational(18,100)
mob=Rational(100,10**6)
width=2*i*l/(mob*v**2)
cgs=Rational(2,3)*width*l*12/10**15
cgd=width/(5*10**15)
gm1,gm2,rd=symbols("gm1 gm2 R_D",positive=True)
g1,x,y=symbols("Vg Vx Vout")
nodes=solve([gm1*g1+gm2*x,y/rd-gm2*x],(x,y))
local=simplify((nodes[x]/g1).subs(gm2,gm1))
c_in=cgs+cgd*(1-local)
rgmax=1/(2*pi*5*10**9*c_in)
rdmax=1/(2*pi*10**10*cgd)
gain=(nodes[y]/g1).subs({gm1:g,rd:rdmax})
for key,vv in [("W (um)",width),("gm (S)",g),("Cgs (F)",cgs),("Cgd (F)",cgd),("Rg max (ohm)",rgmax),("Rd max (ohm)",rdmax),("Av (V/V)",gain)]:
    print(key,"=",vv,"=",vv.evalf(10))
