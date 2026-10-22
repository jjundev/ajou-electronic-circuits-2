import sympy as s
import json

g,T,R,d=s.symbols('gm1 Rtail Rc DeltaRc',positive=True)
Ad=g*R;Acm=d/(1/g+2*T);C=s.factor(Ad/Acm)
print('CMRR nominal matched-load convention=',C,'dominant=',2*g*T*R/d)
print('numeric=',C.subs({g:.005,T:1000000,R:10000,d:100}))
