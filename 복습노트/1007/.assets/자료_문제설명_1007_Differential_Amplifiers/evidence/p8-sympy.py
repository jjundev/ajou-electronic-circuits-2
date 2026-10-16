import sympy as S
from math import log10,pi,sqrt

g,ro,T,R,D,v1,v2,p,x,y=(S.Symbol('g',positive=True),S.Symbol('ro',positive=True),S.Symbol('T',positive=True),S.Symbol('R',positive=True),S.Symbol('D',positive=True),S.Symbol('v1',real=True),S.Symbol('v2',real=True),S.Symbol('p',real=True),S.Symbol('x',real=True),S.Symbol('y',real=True))
i1=g*(v1-p)+(x-p)/ro;i2=g*(v2-p)+(y-p)/ro
sol=S.solve([x/R+i1,y/(R+D)+i2,p/T-i1-i2],[x,y,p]);CM={v1:1,v2:1};DM={v1:S.Rational(1,2),v2:-S.Rational(1,2)}
Ac=S.factor(sol[x].subs(CM));conv=S.factor((sol[x]-sol[y]).subs(CM));Ad=S.factor((sol[x]-sol[y]).subs(DM));c=S.factor(-Ad/conv)
An=-R/(1/g+2*T);Cn=D/(1/g+2*T);Dn=-g*R;cn=-Dn/Cn
print('3node exact CMleft=',Ac,'conversion=',conv,'DM=',Ad,'CMRR=',c)
vals={g:.01,ro:20000,T:10000,R:1000,D:20}
print('numbers',*[S.N(k.subs(vals)) for k in [Ac,conv,Ad,c]])
print('CM ratio ro→inf',S.limit(Ac/An,ro,S.oo));assert S.simplify(S.limit(Ac/An,ro,S.oo)-1)==0
print('conversion ratio ro→inf',S.limit(conv/Cn,ro,S.oo));assert S.simplify(S.limit(conv/Cn,ro,S.oo)-1)==0
print('DM ratio remove ro then small mismatch',S.limit(S.limit(Ad/Dn,ro,S.oo),D,0));assert S.simplify(S.limit(S.limit(Ad/Dn,ro,S.oo),D,0)-1)==0
print('CMRR ratio remove ro then mismatch',S.limit(S.limit(c/cn,ro,S.oo),D,0));assert S.simplify(S.limit(S.limit(c/cn,ro,S.oo),D,0)-1)==0
print('VCMmin=.4+.1+.1=',.4+.1+.1,'max=1.8-.0005*1020+.4=',1.8-.0005*1020+.4)
assert abs((1.8-.0005*1020+.4)-1.69)<1e-12
