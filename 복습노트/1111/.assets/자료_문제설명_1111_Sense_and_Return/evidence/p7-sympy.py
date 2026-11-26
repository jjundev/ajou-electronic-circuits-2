import sympy as S
from sympy import symbols, simplify, factor, Rational as Q
for a in [Q(9,10), S.Pow(10,-Q(1,20))]:
   r=S.sqrt(1/a**2-1)
   assert simplify(1/S.sqrt(1+r**2)-a)==0
   print('amplitude fraction',a, 'bandwidth / pole',r, float(r))
