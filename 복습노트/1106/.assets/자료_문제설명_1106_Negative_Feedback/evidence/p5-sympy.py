import sympy as S
from sympy import symbols, simplify, factor, Rational as Q
A=500; beta=Q(1,8); X=Q(2,1000)
Y=A*X/(1+A*beta); Xf=beta*Y
assert Y==A*(X-Xf)
print('Vout, Vfb peak, mV:',1000*Y,1000*Xf,float(1000*Y),float(1000*Xf))
