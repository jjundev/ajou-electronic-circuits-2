import sympy as S
from sympy import symbols, simplify, factor, Rational as Q
gm1,gm2,gm3,gm4,go1,go3,go5,Rs,RG=symbols('gm1 gm2 gm3 gm4 go1 go3 go5 Rs RG',positive=True)
Cgs1,Cgd1,Cdb1,Cgs2,Csb2,Cgs3,Csb3,Cgd2,Cdb2,Cgs4,Cdb4,Cgd5,Cdb5=symbols('Cgs1 Cgd1 Cdb1 Cgs2 Csb2 Cgs3 Csb3 Cgd2 Cdb2 Cgs4 Cdb4 Cgd5 Cdb5',positive=True)
Gx=gm2+gm3
A=-gm1/Gx
print('a omega_g,x,o:',1/(RG*(Cgs1+(1-A)*Cgd1)),Gx/(Cdb1+Cgs2+Csb2+Cgs3+Csb3+(1-1/A)*Cgd1),gm4/(Cgd2+Cdb2+Cgs4+Cdb4))
G=gm3+go3+go5+go1
C0=Cdb1+Cgs3+Csb3+Cgd5+Cdb5
A=-gm1/G
wg=1/(Rs*(Cgs1+(1-A)*Cgd1)); wo=G/(C0+(1-1/A)*Cgd1)
s=symbols('s')
M=S.Matrix([[1/Rs+s*(Cgs1+Cgd1),-s*Cgd1],[gm1-s*Cgd1,G+s*(C0+Cgd1)]])
exact=factor((M.inv()*S.Matrix([1/Rs,0]))[1])
print('b exact',exact); print('Miller omega_g and omega_o',wg,wo)
assert simplify(exact.subs(s,0)-A)==0 and simplify(exact.subs(s,gm1/Cgd1))==0
