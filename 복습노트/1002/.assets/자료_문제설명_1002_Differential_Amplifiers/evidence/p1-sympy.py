import sympy as S
from math import log10,pi,sqrt

gm,vi,vo=(S.Symbol('gm',positive=True),S.Symbol('vi',real=True),S.Symbol('vo',real=True)); rn,rp,R=(S.Symbol('rn',positive=True),S.Symbol('rp',positive=True),S.Symbol('R',positive=True))
G=1/rn
h=S.factor(S.solve(S.Eq(gm*vi+G*vo,0),vo)[0]/vi)
print('Output KCL gain=',h);assert S.simplify(h--gm*rn)==0
print('Zero drive check',S.simplify((h*vi).subs(vi,0)));print('unit S*ohm=1')
