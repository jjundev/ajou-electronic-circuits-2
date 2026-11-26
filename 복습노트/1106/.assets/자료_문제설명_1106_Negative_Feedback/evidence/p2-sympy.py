import sympy as S
from sympy import symbols, simplify, factor, Rational as Q
gm=lambda k,wl,i:S.sqrt(2*k*wl*i)
g1=gm(Q(100,10**6),1000,Q(2,1000)); g2=gm(Q(100,10**6),500,Q(1,1000))
Cgs1,Cgd1,Cdb1,Cgs2,Csb2,Cgd3,Cdb3=symbols('Cgs1 Cgd1 Cdb1 Cgs2 Csb2 Cgd3 Cdb3',positive=True)
A=-g1/g2
print('gm1, gm2, Ayx:',g1,g2,A)
print('omega_X',1/(100*(Cgs1+(1-A)*Cgd1)))
print('omega_Y',g2/(Cdb1+Cgs2+Csb2+Cgd3+Cdb3+(1-1/A)*Cgd1))
assert A==-2
