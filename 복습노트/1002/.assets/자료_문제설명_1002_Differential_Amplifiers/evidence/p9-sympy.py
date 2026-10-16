import sympy as S
from math import log10,pi,sqrt

g,Rt,R,D,vc,vs=(S.Symbol('g',positive=True),S.Symbol('Rt',positive=True),S.Symbol('R',positive=True),S.Symbol('D',positive=True),S.Symbol('vc',positive=True),S.Symbol('vs',real=True))
sol=S.solve(S.Eq(2*g*(vc-vs),vs/Rt),vs)[0];i=S.factor(g*(vc-sol));Ac=S.factor(-R*i/vc);Adc=S.factor(D*i/vc)
assert S.simplify(Ac+R/(1/g+2*Rt))==0
assert S.simplify(Adc-D/(1/g+2*Rt))==0
print('CM current/input',S.factor(i/vc),'ACM=',Ac,'ACM-DM=',Adc)

I,VT,VA=(S.Symbol('I',positive=True),S.Symbol('VT',positive=True),S.Symbol('VA',positive=True));target=S.factor(Ac.subs({g:I/(2*VT),Rt:VA/I}));print('TailIC convention ACM',target);assert S.simplify(target+R*I/(2*(VA+VT)))==0
print('At RC IC=.02(VA+VT),gain=',S.simplify(target.subs(R,S.Rational(2,100)*(VA+VT)/I)));assert S.simplify(target.subs(R,S.Rational(2,100)*(VA+VT)/I))==-S.Rational(1,100)
print('VA infinite limit',S.limit(target,VA,S.oo));assert S.limit(target,VA,S.oo)==0
