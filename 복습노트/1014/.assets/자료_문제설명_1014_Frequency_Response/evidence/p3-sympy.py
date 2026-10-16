import sympy as S
from math import log10,pi,sqrt

s,g,R,C,vi,vo=(S.Symbol('s',real=True),S.Symbol('g',positive=True),S.Symbol('R',positive=True),S.Symbol('C',positive=True),S.Symbol('vi',real=True),S.Symbol('vo',real=True))
H=S.factor(S.solve(S.Eq((1/R+s*C)*vo+g*vi,0),vo)[0]/vi)
print('CS output KCL H=',H);assert S.simplify(H+g*R/(1+s*R*C))==0

w=S.Symbol('w',positive=True);w0=S.solve(S.Eq(1/(1+(w*R*C)**2),S.Rational(81,100)),w)[0]
num=float(w0.subs({R:1000,C:S.Rational(1,10**12)}));print('omega=',num,'f=',num/(2*pi),'MHz=',num/(2*pi*1e6),'checkratio=',1/sqrt(1+(num*1e-9)**2),'dB=',20*log10(.9))
assert abs(1/sqrt(1+(num*1e-9)**2)-.9)<1e-12
