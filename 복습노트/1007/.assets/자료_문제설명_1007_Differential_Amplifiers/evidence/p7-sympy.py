import sympy as S
from math import log10,pi,sqrt

g,Rt,R,D,vc,vs=(S.Symbol('g',positive=True),S.Symbol('Rt',positive=True),S.Symbol('R',positive=True),S.Symbol('D',positive=True),S.Symbol('vc',positive=True),S.Symbol('vs',real=True))
sol=S.solve(S.Eq(2*g*(vc-vs),vs/Rt),vs)[0];i=S.factor(g*(vc-sol));Ac=S.factor(-R*i/vc);Adc=S.factor(D*i/vc)
assert S.simplify(Ac+R/(1/g+2*Rt))==0
assert S.simplify(Adc-D/(1/g+2*Rt))==0
print('CM current/input',S.factor(i/vc),'ACM=',Ac,'ACM-DM=',Adc)

g3,r3,r4=(S.Symbol('g3',positive=True),S.Symbol('r3',positive=True),S.Symbol('r4',positive=True));Tcas=r3+r4+g3*r3*r4
Cnom=S.factor(g*R/Adc);Ca=Cnom.subs(Rt,r3);Cb=Cnom.subs(Rt,Tcas);CbLead=Cnom.subs(Rt,g3*r3*r4)
print('CMRR_a',Ca,'CMRR_b exact',Cb,'leading',CbLead)
print('cascode exact/leading limit=',S.limit(Cb/CbLead,g3,S.oo));assert S.simplify(S.limit(Cb/CbLead,g3,S.oo)-1)==0
print('r4zero returnsa',S.simplify(Cb.subs(r4,0)-Ca));assert S.simplify(Cb.subs(r4,0)-Ca)==0
print('strong CM improvement doublelimit=',S.limit(S.limit((Cb/Ca)/(g3*r4),g,S.oo),g3,S.oo));assert S.simplify(S.limit(S.limit((Cb/Ca)/(g3*r4),g,S.oo),g3,S.oo)-1)==0
