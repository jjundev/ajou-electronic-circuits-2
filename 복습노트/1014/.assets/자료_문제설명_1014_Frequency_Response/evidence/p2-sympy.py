import sympy as S
from math import log10,pi,sqrt

s,g,R,C,vi,vo=(S.Symbol('s',real=True),S.Symbol('g',positive=True),S.Symbol('R',positive=True),S.Symbol('C',positive=True),S.Symbol('vi',real=True),S.Symbol('vo',real=True))
H=S.factor(S.solve(S.Eq((1/R+s*C)*vo+g*vi,0),vo)[0]/vi)
print('CS output KCL H=',H);assert S.simplify(H+g*R/(1+s*R*C))==0

print('poles=',S.solve(S.denom(H),s),'low=',H.subs(s,0),'high=',S.limit(H,s,S.oo));print('cornerdB=',20*log10(1/sqrt(2)))
assert S.limit(H,s,S.oo)==0
