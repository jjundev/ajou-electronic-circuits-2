import sympy as S
from sympy import symbols, simplify, factor, Rational as Q
gm1,gm2,gpi2,RB,rpi1,RC=symbols('gm1 gm2 gpi2 RB rpi1 RC', positive=True)
Cpi1,Cpi2,Cmu1,Cmu2,Cmu3=symbols('Cpi1 Cpi2 Cmu1 Cmu2 Cmu3',positive=True)
Gx=gm2+gpi2
A=-gm1/Gx
beta2=symbols('beta2', positive=True)
# Q2 emitter supplies one quarter of Q1 collector current; Gx=IE2/VT.
assert simplify(A.subs(gpi2,gm2/beta2).subs(gm2, gm1*beta2/(4*(beta2+1)))) == -4
print('Ax/base =',A,' = -4; ordinary value -1')
for R,C in [(1/(1/RB+1/rpi1),Cpi1+(1-A)*Cmu1),(1/Gx,Cpi2+Cmu3+(1-1/A)*Cmu1),(RC,Cmu2)]:
    print('pole [rad/s] =',factor(-1/(R*C)))
