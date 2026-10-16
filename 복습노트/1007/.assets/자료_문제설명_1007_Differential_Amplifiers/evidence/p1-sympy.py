import sympy as S
from math import log10,pi,sqrt

g,Rt,R,D,vc,vs=(S.Symbol('g',positive=True),S.Symbol('Rt',positive=True),S.Symbol('R',positive=True),S.Symbol('D',positive=True),S.Symbol('vc',positive=True),S.Symbol('vs',real=True))
sol=S.solve(S.Eq(2*g*(vc-vs),vs/Rt),vs)[0];i=S.factor(g*(vc-sol));Ac=S.factor(-R*i/vc);Adc=S.factor(D*i/vc)
assert S.simplify(Ac+R/(1/g+2*Rt))==0
assert S.simplify(Adc-D/(1/g+2*Rt))==0
print('CM current/input',S.factor(i/vc),'ACM=',Ac,'ACM-DM=',Adc)

I,u,lam=(S.Symbol('I',positive=True),S.Symbol('u',positive=True),S.Symbol('lam',positive=True));target=S.factor(Ac.subs({g:I/u,Rt:1/(lam*I)}));assert S.simplify(target+R*I/(2/lam+u))==0
print('Overdrive form=',target,'lambda0=',S.limit(target,lam,0));assert S.limit(target,lam,0)==0

Vd=S.Symbol("Vd",positive=True);ac_exact=Ac.subs({g:I/u,Rt:(1+lam*Vd)/(lam*I)});print("CLM ro correction exact/firstorder limit",S.simplify(S.limit(ac_exact/target,lam,0)));assert S.simplify(S.limit(ac_exact/target,lam,0)-1)==0
