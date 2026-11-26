import sympy as S
from sympy import symbols, simplify, factor, Rational as Q
A,K,r1,r2,gm3,RD,gm1=symbols('A K R1 R2 gm3 RD gm1',positive=True)
b=r2/(r1+r2); follower=gm1*r2/(1+gm1*r2)
Y,X=symbols('Y X')
for name,forward,ret in [('a',A,K*b),('b',-A,-gm3*RD*b),('c',-A,-gm3*RD),('d',A*follower,1)]:
   T=simplify(forward*ret)
   h=S.solve(S.Eq(Y,forward*(X-ret*Y)),Y)[0]/X
   assert simplify(h-forward/(1+T))==0
   print(name,'loop return signed',-T,'closed-loop gain',factor(h))
