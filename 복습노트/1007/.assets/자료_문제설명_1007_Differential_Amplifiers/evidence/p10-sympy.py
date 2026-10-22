import sympy as s
import json

Vp,Vn,Vt,A,I=s.symbols('Vp Vn Vt A Ic',positive=True)
g=I/Vt;rn=Vn/I;rp=Vp/I;gain=s.factor(g/(1/rn+1/rp));ans=s.solve(s.Eq(gain,A),Vp)[0]
print('gain=',gain,'Early P=',ans,'numeric VT=26mV=',ans.subs({Vn:5,Vt:s.Rational(26,1000),A:100}),'VT=25mV=',ans.subs({Vn:5,Vt:s.Rational(25,1000),A:100}))
