import sympy as S
from math import log10,pi,sqrt

g,Rt,R,D,vc,vs=(S.Symbol('g',positive=True),S.Symbol('Rt',positive=True),S.Symbol('R',positive=True),S.Symbol('D',positive=True),S.Symbol('vc',positive=True),S.Symbol('vs',real=True))
sol=S.solve(S.Eq(2*g*(vc-vs),vs/Rt),vs)[0];i=S.factor(g*(vc-sol));Ac=S.factor(-R*i/vc);Adc=S.factor(D*i/vc)
assert S.simplify(Ac+R/(1/g+2*Rt))==0
assert S.simplify(Adc-D/(1/g+2*Rt))==0
print('CM current/input',S.factor(i/vc),'ACM=',Ac,'ACM-DM=',Adc)

print('Parallel two2Rt',S.simplify(1/(1/(2*Rt)+1/(2*Rt))));assert S.simplify(1/(1/(2*Rt)+1/(2*Rt))-Rt)==0
assert S.simplify(Ac+(R/2)/(Rt+1/(2*g)))==0
print('Rt0=',S.limit(Ac,Rt,0),'Rtinf=',S.limit(Ac,Rt,S.oo));assert S.limit(Ac,Rt,S.oo)==0
