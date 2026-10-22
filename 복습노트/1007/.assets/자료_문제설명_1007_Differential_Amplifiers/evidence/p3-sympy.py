import sympy as s

I=s.Rational(1,1000);branch=I/2;kn=s.Rational(1,10000);kp=s.Rational(1,20000);l=s.Rational(1,10)
gmn=s.sqrt(2*kn*1000*branch);gmp=s.sqrt(2*kp*2000*branch);gmt=s.sqrt(2*kn*2000*I)
ron=1/(l*branch);rop=ron;rot=1/(l*I);tail=gmt*rot**2;rd=1/(1/ron+1/rop)
ADM=-gmn*rd;ACM=-rop/(2*tail)
assert ADM==-100;assert ACM==-s.Rational(1,200)
print('1 gm=',gmn,'roN=',ron,'roP=',rop,'DM=',ADM)
print('2 tail gm=',gmt,'Rtail=',tail,'2RSS=',2*tail,'SE/average CM=',ACM,'symmetric differential CM=0')
