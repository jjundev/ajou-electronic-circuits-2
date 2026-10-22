import sympy as s
import json

g,R,T,I,V,lam=s.symbols('g R T I V lam', positive=True)
vx=s.solve(s.Eq(g*(1-s.Symbol('x')),s.Symbol('x')/(2*T)),s.Symbol('x'))[0]
a=s.factor(-g*(1-vx)*R)
print('half circuit Rs=2T; A=',a)
print('substituted=',s.factor(a.subs({g:I/V,T:1/(lam*I)})))
print('numeric=',a.subs({g:.001,R:10000,T:100000}))
