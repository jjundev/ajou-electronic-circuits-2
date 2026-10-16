import sympy as S
from math import log10,pi,sqrt

s,g,RS,RD,Ci,CL,vi,vs,vo=(S.Symbol('s',real=True),S.Symbol('g',positive=True),S.Symbol('RS',positive=True),S.Symbol('RD',positive=True),S.Symbol('Ci',positive=True),S.Symbol('CL',positive=True),S.Symbol('vi',real=True),S.Symbol('vs',real=True),S.Symbol('vo',real=True))
sol=S.solve([(vs-vi)/RS+s*Ci*vs+g*vs,(1/RD+s*CL)*vo-g*vs],[vs,vo]);H=S.factor(sol[vo]/vi)
print('CG KCL H=',H,'poles=',S.solve(S.denom(H),s));assert S.simplify(H-g*RD/((1+g*RS+s*RS*Ci)*(1+s*RD*CL)))==0

win=(1/RS+g)/Ci;wout=1/(RD*CL);Rsolve=S.solve(S.Eq(wout,10*win),RD)[0]
print('RD=',Rsolve);assert S.simplify(Rsolve-Ci/(10*CL)/(1/RS+g))==0
print('substitution output/input=',S.simplify((wout/win).subs(RD,Rsolve)));assert S.simplify((wout/win).subs(RD,Rsolve))==10
