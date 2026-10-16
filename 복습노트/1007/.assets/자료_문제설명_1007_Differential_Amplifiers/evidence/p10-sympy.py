import sympy as S
from math import log10,pi,sqrt

IC,VT,VA,VP,vo,vd=(S.Symbol('IC',positive=True),S.Symbol('VT',positive=True),S.Symbol('VA',positive=True),S.Symbol('VP',positive=True),S.Symbol('vo',real=True),S.Symbol('vd',real=True))
g=IC/VT;rn=VA/IC;rp=VP/IC
# Mirror doubles the half-input difference current; single output current=gm*vd.
A=S.factor(S.solve(S.Eq(vo/rn+vo/rp-g*vd,0),vo)[0]/vd)
print('active mirror KCL gain',A);assert S.simplify(1/A-VT/VA-VT/VP)==0
req=S.solve(S.Eq(A,100),VP)[0];print('required VAp=',req,'atVT26=',req.subs({VT:S.Rational(26,1000),VA:5}),'VT25=',req.subs({VT:S.Rational(25,1000),VA:5}))
assert S.simplify(A.subs(VP,req)-100)==0
print('VAp infinity gain=',S.limit(A,VP,S.oo))

# Full three-node finite-output-resistance mirror model (beta infinity).
gm,rn,rp,vd=S.symbols('gm rn rp vd',positive=True);x,y,e=S.symbols('x y e',real=True)
i1=gm*(vd/2-e)+(x-e)/rn;i2=gm*(-vd/2-e)+(y-e)/rn
full=S.solve([i1+gm*x+x/rp,i2+gm*x+y/rp,i1+i2],[x,y,e]);Ae=S.factor(full[y]/vd);lead=gm/(1/rn+1/rp)
print('Finite-ro full mirror gain',Ae,'leading=',lead);print('exact/leading intrinsic-gain limit',S.simplify(S.limit(Ae/lead,gm,S.oo)));assert S.simplify(S.limit(Ae/lead,gm,S.oo)-1)==0
