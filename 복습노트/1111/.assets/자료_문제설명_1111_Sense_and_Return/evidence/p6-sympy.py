import sympy as S
from sympy import symbols, simplify, factor, Rational as Q
A0=200
for K in [0,Q(1,10),Q(1,2)]:
   f=1+K*A0; h=Q(A0,1)/f
   print('K:',K,'DC:',h,float(20*S.log(h,10)),'dB; pole/omega0:',f)
   for x in [0,1,21,101,1000]:
      m=float(A0/S.sqrt(f**2+x**2)); phase=float(-S.atan(Q(x,f))*180/S.pi)
      print('omega/omega0',x,'magnitude',m,'phase degrees',phase)
