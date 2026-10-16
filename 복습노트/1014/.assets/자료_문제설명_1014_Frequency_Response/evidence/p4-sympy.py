import sympy as S
from math import log10,pi,sqrt

s,g,R,C,vi,vo=(S.Symbol('s',real=True),S.Symbol('g',positive=True),S.Symbol('R',positive=True),S.Symbol('C',positive=True),S.Symbol('vi',real=True),S.Symbol('vo',real=True))
H=S.factor(S.solve(S.Eq((1/R+s*C)*vo+g*vi,0),vo)[0]/vi)
print('CS output KCL H=',H);assert S.simplify(H+g*R/(1+s*R*C))==0

P,Vcc,VT,BW=(S.Symbol('P',positive=True),S.Symbol('Vcc',positive=True),S.Symbol('VT',positive=True),S.Symbol('BW',positive=True));I=P/Vcc;G=I/VT;Rc=1/(2*S.pi*BW*C);A=G*Rc
print('maxgain symbolic',A)
v={P:S.Rational(2,1000),Vcc:S.Rational(25,10),VT:S.Rational(26,1000),BW:10**9,C:S.Rational(2,10**12)}
print('IC=',I.subs(v),'RC=',S.N(Rc.subs(v)),'gain=',S.N(A.subs(v)),'dB=',20*log10(float(A.subs(v))))
assert abs(float(A.subs(v))-2.44853758603)<1e-9
print('Positive derivatives dA/dgm=RC and dA/dRC=gm justify both upper bounds.')
