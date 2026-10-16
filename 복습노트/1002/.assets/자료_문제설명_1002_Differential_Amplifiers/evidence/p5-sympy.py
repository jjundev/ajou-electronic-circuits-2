import sympy as S
from math import log10,pi,sqrt

g1,g3,r1,r3,vi,x,y,it=(S.Symbol('g1',positive=True),S.Symbol('g3',positive=True),S.Symbol('r1',positive=True),S.Symbol('r3',positive=True),S.Symbol('vi',real=True),S.Symbol('x',real=True),S.Symbol('y',real=True),S.Symbol('it',real=True))
# Input lower transistor current + upper source-entering current =0.
eqx=x/r1+(x-y)/r3+g3*x+g1*vi
eqy=(y-x)/r3-g3*x
sol=S.solve([eqx,eqy],[x,y]);A=S.factor(sol[y]/vi)
print('Cascode exact two-node gain',A)
assert S.simplify(A+g1*r1*(1+g3*r3))==0
out=S.solve([eqx.subs(vi,0),eqy-it],[x,y]);Rout=S.factor(out[y]/it)
print('Rout=',Rout);assert S.simplify(Rout-(r1+r3+g3*r1*r3))==0
z=S.Symbol('z',real=True);print('exact/leading limit=',S.limit(z*(1+z)/z**2,z,S.oo));assert S.simplify(S.limit(z*(1+z)/z**2,z,S.oo)-1)==0

K=S.Rational(1,10000)*S.Rational(20,1)/S.Rational(18,100);lam=S.Rational(1,10)
Iapprox=4*K/(lam**2*300);zx=(-1+S.sqrt(1201))/2;Iexact=4*K/(lam**2*zx**2)
print('ISS approximate A300=',S.N(Iapprox),'exact=',S.N(Iexact),'z exact=',S.N(zx));assert abs(float(Iapprox)-.0148148148148148)<1e-14
