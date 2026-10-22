import sympy as s
import json

kn=s.Rational(100,10**6);kp=s.Rational(50,10**6);It=s.Rational(1,1000);lam=s.Rational(1,10)
g1=s.sqrt(2*kn*1000*It/2);g5=s.sqrt(2*kn*2000*It);rn=1/(lam*It/2);rp=rn;rt=g5*(1/(lam*It))**2
print('gm1,gm5,ro1,ro3,Rtail=',g1,g5,rn,rp,rt)
print('Ad differential magnitude=',g1/(1/rn+1/rp))
print('Acm main approximation=',-rp/(2*rt),'numeric=',float(-rp/(2*rt)))
print('Acm finite exact=',-g1*rn*rp/(rn+rp+2*rt*(1+g1*rn)))
