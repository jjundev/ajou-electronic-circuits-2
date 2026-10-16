import sympy as S
from math import log10,pi,sqrt

s,g,RS,RD,RP,Ci,CL,vi,vx,vs,vo=(S.Symbol('s',real=True),S.Symbol('g',positive=True),S.Symbol('RS',positive=True),S.Symbol('RD',positive=True),S.Symbol('RP',positive=True),S.Symbol('Ci',positive=True),S.Symbol('CL',positive=True),S.Symbol('vi',real=True),S.Symbol('vx',real=True),S.Symbol('vs',real=True),S.Symbol('vo',real=True))
sol=S.solve([(vx-vi)/RS+s*Ci*vx+(vx-vs)/RP,(vs-vx)/RP+g*vs,(1/RD+s*CL)*vo-g*vs],[vx,vs,vo]);H=S.factor(sol[vo]/vi)
print('three-node CG KCL H=',H,'poles=',S.solve(S.denom(H),s));win=(1/RS+1/(RP+1/g))/Ci
expected=g*RD/((1+s*RD*CL)*((1+g*RP)*(1+s*RS*Ci)+g*RS));assert S.simplify(H-expected)==0
print('input pole=',win,'RP0=',S.limit(win,RP,0),'RPinf=',S.limit(win,RP,S.oo));assert S.simplify(S.limit(win,RP,0)-(1/RS+g)/Ci)==0;assert S.simplify(S.limit(win,RP,S.oo)-1/(RS*Ci))==0
