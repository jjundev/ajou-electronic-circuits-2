import sympy as S
from sympy import symbols, simplify, factor, Rational as Q
gm1,gm3,Rs,Rd=symbols('gm1 gm3 Rs Rd',positive=True)
Cgs1,Cgd1,Cdb1,Cgs3,Csb3,Cgd3,Cdb3=symbols('Cgs1 Cgd1 Cdb1 Cgs3 Csb3 Cgd3 Cdb3',positive=True)
Ax=-gm1/gm3
print('Miller estimates (rad/s):',1/(Rs*(Cgs1+(1-Ax)*Cgd1)),gm3/(Cdb1+Cgs3+Csb3+(1-1/Ax)*Cgd1),1/(Rd*(Cgd3+Cdb3)))
print('equal gm:',(1-Ax).subs(gm3,gm1),(1-1/Ax).subs(gm3,gm1))
