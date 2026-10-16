import sympy as S
from math import log10,pi,sqrt

t,tau=(S.Symbol('t',positive=True),S.Symbol('tau',positive=True));y=1-S.exp(-t/tau)
assert S.simplify(tau*S.diff(y,t)+y-1)==0
tr=S.simplify(-tau*S.log(S.Rational(1,10))+tau*S.log(S.Rational(9,10)))
print('ODE step response=',y,'10–90 rise=',tr,'rise*BW=',S.N(tr/tau/(2*S.pi)),'5MHzrise=',float(tr.subs(tau,1/(2*pi*5e6))))
print('Bandwidth→infinity(tau→0)step=',S.limit(y,tau,0));assert S.simplify(S.limit(y,tau,0)-1)==0
