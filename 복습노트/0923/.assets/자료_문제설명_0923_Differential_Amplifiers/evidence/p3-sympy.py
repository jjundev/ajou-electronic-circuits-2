import sympy as s
from sympy import Rational as Q
print('Independent derivation from blind conditions; author-early, not fragment author')
def check(name, expression):
    value=s.simplify(expression)
    print(name, value)
    assert value==0,(name,value)

I,K,VCM,VTH=s.symbols('I K VCM VTH',positive=True)
u=s.sqrt(I/K);P=VCM-VTH-u
for part,knew,inew,target in [('a',2*K,I,(1-1/s.sqrt(2))*u),('b',K,2*I,-(s.sqrt(2)-1)*u),('c',K/2,I,-(s.sqrt(2)-1)*u)]:
 new=VCM-VTH-s.sqrt(inew/knew);delta=s.simplify(new-P)
 print(part,'tail delta=',delta)
 check(part+' tail shift',delta-target)
 check(part+' branch current',knew*(VCM-VTH-new)**2/2-inew/2)
print('c assumes fixed VTH; if threshold changes add -DeltaVTH.')
