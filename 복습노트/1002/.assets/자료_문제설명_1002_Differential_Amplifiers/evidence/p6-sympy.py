import sympy as S
from math import log10,pi,sqrt

gn,gp,rn,rp,vi,x,y,z=(S.Symbol('gn',positive=True),S.Symbol('gp',positive=True),S.Symbol('rn',positive=True),S.Symbol('rp',positive=True),S.Symbol('vi',real=True),S.Symbol('x',real=True),S.Symbol('y',real=True),S.Symbol('z',real=True))
# NMOS lower drain x, output y, PMOS stack intermediate z.
# PMOS upper fixed source contributes z/rp; lower common-gate source contributes gp*z+(z-y)/rp.
eqs=[x/rn+(x-y)/rn+gn*x+gn*vi,(y-x)/rn-gn*x+(y-z)/rp-gp*z,z/rp+(z-y)/rp+gp*z]
sol=S.solve(eqs,[x,y,z]);A=S.factor(-sol[y]/vi)
Rn=2*rn+gn*rn**2;Rp=2*rp+gp*rp**2;Gm=gn*(gn+1/rn)/(gn+2/rn)
assert S.simplify(A-Gm/(1/Rn+1/Rp))==0
print('Three-node exact |Av|=',A);print('Gm=',Gm,'Rn=',Rn,'Rp=',Rp)
t,an,ap=(S.Symbol('t',positive=True),S.Symbol('an',positive=True),S.Symbol('ap',positive=True));lead=gn/(1/(gn*rn**2)+1/(gp*rp**2))
ratio=S.factor((A/lead).subs({gn:t*an,gp:t*ap}));print('leading/exact shared gm scale ratio limit',S.limit(ratio,t,S.oo));assert S.simplify(S.limit(ratio,t,S.oo)-1)==0
q=S.Symbol('q',positive=True);subs={rn:20000,rp:10000,gn:S.sqrt(S.Rational(1,10**7)*q),gp:S.sqrt(S.Rational(1,2*10**7)*q)}
qa=S.nsolve(lead.subs(subs)-200,q,33);qe=S.nsolve(A.subs(subs)-200,q,30)
print('W/L leading=',qa,'exact=',qe,'exact gain at leading size=',S.N(A.subs(subs).subs(q,qa)))
assert abs(float(qa)-33.28427124746)<1e-8
