import sympy as S
from math import log10,pi,sqrt

g3,ro3,R1,rpi,x,y,it=(S.Symbol('g3',positive=True),S.Symbol('ro3',positive=True),S.Symbol('R1',positive=True),S.Symbol('rpi',positive=True),S.Symbol('x',real=True),S.Symbol('y',real=True),S.Symbol('it',real=True))
# Tail transistor base ground, source/emitter resistance R1||rpi.
Re=1/(1/R1+1/rpi);isrc=-g3*x+(y-x)/ro3
sol=S.solve([x/Re-isrc,isrc-it],[x,y]);Rt_exact=S.factor(sol[y]/it)
assert S.simplify(Rt_exact-(ro3+(1+g3*ro3)*Re))==0
Rt_book=(1+g3*Re)*ro3
print('tail exact=',Rt_exact,'book droppingRe=',Rt_book,'ratio ro3infty=',S.limit(Rt_exact/Rt_book,ro3,S.oo));assert S.simplify(S.limit(Rt_exact/Rt_book,ro3,S.oo)-1)==0

g,Rt,R,D,vc,vs=(S.Symbol('g',positive=True),S.Symbol('Rt',positive=True),S.Symbol('R',positive=True),S.Symbol('D',positive=True),S.Symbol('vc',positive=True),S.Symbol('vs',real=True))
sol=S.solve(S.Eq(2*g*(vc-vs),vs/Rt),vs)[0];i=S.factor(g*(vc-sol));Ac=S.factor(-R*i/vc);Adc=S.factor(D*i/vc)
assert S.simplify(Ac+R/(1/g+2*Rt))==0
assert S.simplify(Adc-D/(1/g+2*Rt))==0
print('CM current/input',S.factor(i/vc),'ACM=',Ac,'ACM-DM=',Adc)

exact=S.factor(Adc.subs(Rt,Rt_exact));book=S.factor(Adc.subs(Rt,Rt_book));print('ACMDM exact/book limit=',S.limit(exact/book,ro3,S.oo));assert S.simplify(S.limit(exact/book,ro3,S.oo)-1)==0
print('mismatch0=',S.simplify(exact.subs(D,0)));assert S.simplify(exact.subs(D,0))==0
