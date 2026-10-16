import sympy as S
from math import log10,pi,sqrt

gm,vi,vo=(S.Symbol('gm',positive=True),S.Symbol('vi',real=True),S.Symbol('vo',real=True)); rn,rp,R=(S.Symbol('rn',positive=True),S.Symbol('rp',positive=True),S.Symbol('R',positive=True))
G=1/rn+1/rp+1/R
h=S.factor(S.solve(S.Eq(gm*vi+G*vo,0),vo)[0]/vi)
print('Output KCL gain=',h);assert S.simplify(h--gm/(1/rn+1/rp+1/R))==0
print('Zero drive check',S.simplify((h*vi).subs(vi,0)));print('unit S*ohm=1')

VT=S.Symbol('VT',positive=True);val=h.subs({rn:8000,rp:8000,R:10000,gm:S.Rational(1,2000)/VT})
print('IC=.5mA, ro=8k, R=10k; gain=',val,'at26mV=',val.subs(VT,S.Rational(26,1000)),'at25mV=',val.subs(VT,S.Rational(25,1000)))
assert S.simplify(val+S.Rational(10,7)/VT)==0
