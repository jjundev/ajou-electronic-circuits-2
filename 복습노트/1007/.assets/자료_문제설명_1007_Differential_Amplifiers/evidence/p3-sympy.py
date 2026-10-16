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

t=S.Symbol('t',positive=True);a1,a3,a5,r3,r5,r6,r7=(S.Symbol('a1',positive=True),S.Symbol('a3',positive=True),S.Symbol('a5',positive=True),S.Symbol('r3',positive=True),S.Symbol('r5',positive=True),S.Symbol('r6',positive=True),S.Symbol('r7',positive=True))
Ta=r5+r6+t*a5*r5*r6;Lua=r3
Aa=A.subs({g:t*a1,T:Ta,RL:Lua});La=-r3/(2*t*a5*r5*r6)
print('a exact/leading scale limit',S.limit(Aa/La,t,S.oo));assert S.simplify(S.limit(Aa/La,t,S.oo)-1)==0
Lub=r3+r5+t*a3*r3*r5;Ab=A.subs({g:t*a1,T:r7,RL:Lub})
Lb=-(1/(1/(t*a3*r3*r5)+1/(2*t*a1*ri*r7)))/(2*r7)
print('b exact/parallel-leading scale limit',S.limit(Ab/Lb,t,S.oo));assert S.simplify(S.limit(Ab/Lb,t,S.oo)-1)==0
num={t:1,a1:.001,a3:.001,a5:.001,ri:100000,r3:100000,r5:100000,r6:100000,r7:100000}
print('equal gm.001 ro100k exact a,b',S.N(Aa.subs(num)),S.N(Ab.subs(num)));print('b wrong dropping lower=',-50,'correct leading=',S.N(Lb.subs(num)))
