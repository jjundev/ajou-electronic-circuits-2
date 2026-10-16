import sympy as S
from math import log10,pi,sqrt

g,ro,rpi,vi,x,y=(S.Symbol('g',positive=True),S.Symbol('ro',positive=True),S.Symbol('rpi',positive=True),S.Symbol('vi',real=True),S.Symbol('x',real=True),S.Symbol('y',real=True))
sol=S.solve([x/ro+x/rpi+(x-y)/ro+g*x+g*vi,(y-x)/ro-g*x],[x,y]);A=S.factor(-sol[y]/vi)
beta,z=(S.Symbol('beta',positive=True),S.Symbol('z',real=True));A=S.factor(A.subs({rpi:beta/g,ro:z/g}));lead=beta*z**2/(beta+z)
print('BJT exact=',A,'leading=',lead);assert S.simplify(A-beta*z*(1+z)/(beta+z))==0
print('Exact/leading large intrinsic-gain limit=',S.limit(A/lead,z,S.oo));assert S.simplify(S.limit(A/lead,z,S.oo)-1)==0
zs=20+S.sqrt(4400);print('approx min VA at VT26mV=',S.N(zs*S.Rational(26,1000)));print('target=',S.N(lead.subs({beta:100,z:zs})));print('monotonic derivative=',S.factor(S.diff(lead,z)))
assert S.simplify(lead.subs({beta:100,z:zs})-4000)==0
