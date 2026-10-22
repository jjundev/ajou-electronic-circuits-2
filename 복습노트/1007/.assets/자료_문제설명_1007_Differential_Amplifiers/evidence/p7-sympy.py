import sympy as s
import json

k=s.Rational(100,10**6);w=50;wt=100;v=s.Rational(1,5);R=10000;lam=s.Rational(1,10);d=100
for factor in [1,2]:
 It=k*wt*factor*v**2/2;g=s.sqrt(k*w*It);rt=1/(lam*It);vin=s.sqrt(2*It/(k*w));Ad=g*R;Acm=-R/(2*rt);Acmdm=d/(2*rt);C=Ad/Acmdm
 print('width multiplier',factor,'It=',It,'gm=',g,'rt=',rt,'range halfwidth=',vin,'Ad=',Ad,'Acm=',Acm,'Acmdm=',Acmdm,'CMRR=',C,'numeric=',[float(z) for z in [It,g,rt,vin,Ad,Acm,Acmdm,C]])
print('Input-pair ro neglected first; CLM bias correction cannot be uniquely computed without VDD/Vin,CM.')
