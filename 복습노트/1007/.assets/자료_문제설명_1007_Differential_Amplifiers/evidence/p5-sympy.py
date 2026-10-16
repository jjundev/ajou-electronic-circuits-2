import sympy as S
from math import log10,pi,sqrt

g,ri,RL,T,vi,vs,vo=(S.Symbol('g',positive=True),S.Symbol('ri',positive=True),S.Symbol('RL',positive=True),S.Symbol('T',positive=True),S.Symbol('vi',real=True),S.Symbol('vs',real=True),S.Symbol('vo',real=True))
# CM half source resistor2T, output loadRL, input output resistance ri.
id=g*(vi-vs)+(vo-vs)/ri
sol=S.solve([vo/RL+id,vs/(2*T)-id],[vo,vs]);A=S.factor(sol[vo]/vi)
Q=ri+2*T*(1+g*ri);Gm=g*ri/Q;Rout=1/(1/RL+1/Q)
assert S.simplify(A+Gm*Rout)==0
assert S.simplify(A+g*ri*RL/(RL+Q))==0
print('Exact CM KCL=',A,'Gm=',Gm,'Rout=',Rout)

# Cascode tail exact test: output upper device with ro5,source lowerro6.
g5,r5,r6,x,y,it=(S.Symbol('g5',positive=True),S.Symbol('r5',positive=True),S.Symbol('r6',positive=True),S.Symbol('x',real=True),S.Symbol('y',real=True),S.Symbol('it',real=True))
isrc=-g5*x+(y-x)/r5;test=S.solve([x/r6-isrc,isrc-it],[x,y]);Tex=S.factor(test[y]/it)
assert S.simplify(Tex-r5-r6-g5*r5*r6)==0
nums={g:.01,ri:10000,RL:10000,T:510000};print('CM finite-ro exact=',A.subs(nums))
print('DM gain KCL=',-.01/(1/10000+1/10000),'tail exact=',Tex.subs({g5:.02,r5:5000,r6:5000}))
print('textbook leading ACM=-.01,ACMDM=50/(2*500k)=',50/1e6,'CMRR=',50/(50/1e6))
# Current-transfer and output-impedance mismatch method: conversion=Gm*deltaR.
D=S.Symbol('D',positive=True);conv=Gm*D;lead=D/(2*T)
print('conversion exact/leading gm limit',S.limit(conv/lead,g,S.oo));assert S.simplify(S.limit(conv/lead,g,S.oo)-1)==0
print('CM exact/leading gm limit',S.limit(A/(-RL/(2*T)),g,S.oo));assert S.simplify(S.limit(A/(-RL/(2*T)),g,S.oo)-1)==0
print('tail exact/leading gm5 limit',S.limit(Tex/(g5*r5*r6),g5,S.oo));assert S.simplify(S.limit(Tex/(g5*r5*r6),g5,S.oo)-1)==0
