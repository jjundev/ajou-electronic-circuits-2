import sympy as s
import json

g,r,R,rpi,d=s.symbols('gm3 ro3 R1 rpi3 DeltaRc',positive=True);x,t=s.symbols('x t')
# Test collector voltage t, emitter x, base ac grounded.
xe=s.solve(s.Eq(x/R+x/rpi+(x-t)/r+g*x,0),x)[0]
Rt=s.factor(t/((t-xe)/r-g*xe))
assert s.simplify(Rt-(r+(1+g*r)/(1/R+1/rpi)))==0
print('Rtail exact=',Rt,'dominant=',g*r/(1/R+1/rpi))
g1=s.symbols('gm1',positive=True);A=d/(1/g1+2*Rt)
print('CM-DM magnitude=',s.factor(A));print('numeric=',A.subs({g:.01,r:100000,R:1000,rpi:10000,d:100,g1:.005}))
