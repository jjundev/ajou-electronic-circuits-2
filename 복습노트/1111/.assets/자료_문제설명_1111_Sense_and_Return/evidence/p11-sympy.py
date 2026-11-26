import sympy as S
from sympy import symbols, simplify, factor, Rational as Q
g1,g2,a,b,v,x,y,i=symbols('gm1 gm2 go1 go2 vin vx vout id')
# Drain-in port current at M2; node x KCL.
ix=S.solve(S.Eq(g1*v + a*x, -g2*x+b*(y-x)),x)[0]
idrain=factor((-g2*x+b*(y-x)).subs(x,ix))
G=factor(idrain.diff(v)); R=factor(1/idrain.diff(y))
print('vx:',ix,'id:',idrain,'Gm:',G,'Rout:',R)
assert simplify(R-1/a-1/b-g2/(a*b))==0
