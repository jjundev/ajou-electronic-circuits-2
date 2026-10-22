import sympy as s

k=s.Rational(1,10000);Vov=s.Rational(1,5);W=100;I=k*W*Vov**2/2;gm=s.sqrt(2*k*50*I/2);rt=1/(s.Rational(1,10)*I);RD=10000;delta=100
ADM=-gm*RD;ACM=-s.Rational(RD,2)/rt;leak=delta/(2*rt);CMRR=abs(ADM)/leak
I2=2*I;gm2=s.sqrt(2*k*50*I2/2);rt2=rt/2;c2=2*gm2*rt2*RD/delta
print('1 fixedVb tailW doubles I -> steering limit sqrt2 times; O')
print('I=',I,'gm=',gm,'RSS=',rt)
print('2 DM=',ADM,'3 CM=',ACM,'4 leak=',leak,'5 CMRR=',CMRR,'6 newCMRR=',s.N(c2,15))
assert CMRR==10000;assert s.simplify(c2-CMRR/s.sqrt(2))==0
print('Model: textbook rO_input omitted consistently in gain/CMtoDM; big-gmRSS leading terms. Full-model finite-rO differences are not hidden exactness.')
