import sympy as S
from math import log10,pi,sqrt

s,g,RS,RD,Ci,CL,vi,vg,vo=(S.Symbol('s',real=True),S.Symbol('g',positive=True),S.Symbol('RS',positive=True),S.Symbol('RD',positive=True),S.Symbol('Ci',positive=True),S.Symbol('CL',positive=True),S.Symbol('vi',real=True),S.Symbol('vg',real=True),S.Symbol('vo',real=True))
sol=S.solve([(vg-vi)/RS+s*Ci*vg,(1/RD+s*CL)*vo+g*vg],[vg,vo]);H=S.factor(sol[vo]/vi)
print('CS 2-node H=',H,'poles=',S.solve(S.denom(H),s));assert S.simplify(H+g*RD/((1+s*RS*Ci)*(1+s*RD*CL)))==0
