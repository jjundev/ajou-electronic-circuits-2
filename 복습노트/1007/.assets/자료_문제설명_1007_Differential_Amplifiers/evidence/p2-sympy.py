import sympy as S
from math import log10,pi,sqrt

g,ri,RL,T,vi,vs,vo=(S.Symbol('g',positive=True),S.Symbol('ri',positive=True),S.Symbol('RL',positive=True),S.Symbol('T',positive=True),S.Symbol('vi',real=True),S.Symbol('vs',real=True),S.Symbol('vo',real=True))
# CM half source resistor2T, output loadRL, input output resistance ri.
id=g*(vi-vs)+(vo-vs)/ri
sol=S.solve([vo/RL+id,vs/(2*T)-id],[vo,vs]);A=S.factor(sol[vo]/vi)
Q=ri+2*T*(1+g*ri);Gm=g*ri/Q;Rout=1/(1/RL+1/Q)
assert S.simplify(A+Gm*Rout)==0
assert S.simplify(A+g*ri*RL/(RL+Q))==0
print('Exact CM KCL=',A,'Gm=',Gm,'Rout=',Rout)

lead=-RL/(2*T);print('exact/leading gm limit',S.limit(A/lead,g,S.oo));assert S.simplify(S.limit(A/lead,g,S.oo)-1)==0
print('ideal tail limit',S.limit(A,T,S.oo));assert S.limit(A,T,S.oo)==0
print('zero-tail limit',S.limit(A,T,0));assert S.simplify(S.limit(A,T,0)+g/(1/ri+1/RL))==0
