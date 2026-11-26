import sympy as S
from sympy import symbols, simplify, factor, Rational as Q
T,d=symbols('T d',positive=True)
r=symbols('r',positive=True)
rel=factor(r*(1+T)/(1+r*T)-1)
assert simplify(rel-(r-1)/(1+r*T))==0
for u in [Q(4,5),Q(6,5)]:
   threshold=(abs(u-1)/Q(1,100)-1)/u
   print('r',u,'strict nominal T >',threshold,float(threshold))
print('linearized strict threshold',Q(20,1)-1)
