import sympy as S
from sympy import symbols, simplify, factor, Rational as Q
T=symbols('T',positive=True)
corners=[S.sqrt(mu)/lam for mu in (Q(9,10),Q(11,10)) for lam in (Q(4,5),Q(6,5))]
bounds=[]
for r in sorted(corners,key=float):
   threshold=simplify((abs(r-1)/Q(5,100)-1)/r)
   print('open-loop ratio',float(r),'T bound',threshold,float(threshold))
   bounds.append(threshold)
worst=max(bounds,key=float)
print('active bound',worst, float(worst))
print('small-signal approximation T >',(Q(1,2)*Q(1,10)+Q(1,5))/Q(1,20)-1)
