import sympy as S
from math import log10,pi,sqrt

g,rt,re,vi,x,y,it,gin=(S.Symbol('g',positive=True),S.Symbol('rt',positive=True),S.Symbol('re',positive=True),S.Symbol('vi',real=True),S.Symbol('x',real=True),S.Symbol('y',real=True),S.Symbol('it',real=True),S.Symbol('gin',positive=True))
# re includes lower ro and upper rpi; rt upper ro||RP where present.
eqx=x/re+(x-y)/rt+g*x+gin*vi;eqy=(y-x)/rt-g*x
sol=S.solve([eqx,eqy],[x,y]);A=S.factor(sol[y]/vi)
out=S.solve([eqx.subs(vi,0),eqy-it],[x,y]);R=S.factor(out[y]/it)
assert S.simplify(R-(rt+re+g*rt*re))==0
assert S.simplify(A+gin*re*(1+g*rt))==0
for name,vals in [('a',{g:.02,rt:10000,re:2500,gin:.04}),('b',{g:.02,rt:5000,re:5000,gin:.02})]:print(name,'Rout_single exact=',R.subs(vals),'Avexact=',A.subs(vals),'leadingR=',(g*rt*re).subs(vals),'leadingA=',(-gin*g*rt*re).subs(vals))
print('b differential exact R=',2*R.subs({g:.02,rt:5000,re:5000}));t=S.Symbol('t',positive=True)
print('R exact/leading gm-scale limit',S.limit((R/(g*rt*re)).subs(g,t*g),t,S.oo));assert S.simplify(S.limit((R/(g*rt*re)).subs(g,t*g),t,S.oo)-1)==0
print('A exact/leading gm-scale limit',S.limit((A/(-gin*g*rt*re)).subs(g,t*g),t,S.oo));assert S.simplify(S.limit((A/(-gin*g*rt*re)).subs(g,t*g),t,S.oo)-1)==0
