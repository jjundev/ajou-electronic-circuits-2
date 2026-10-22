import sympy as s
import json

g,r,p,T=s.symbols('g r p T',positive=True);v,x=s.symbols('v x')
sol=s.solve([v/p+(v-x)/r+g*(1-x),x/(2*T)+(x-v)/r-g*(1-x)],(v,x))
a=s.factor(sol[v]);G=s.factor(g*r/(r+2*T*(1+g*r)));Ro=1/(1/p+1/(r+2*T*(1+g*r)))
assert s.simplify(a+G*Ro)==0
print('Gm=',G,'Rout=',s.factor(Ro),'A=',a)
print('large-tail limit relative rp/2T=',s.limit(a/(-p/(2*T)),T,s.oo))
print('numeric=',a.subs({g:.01,r:20000,p:20000,T:100000}))
