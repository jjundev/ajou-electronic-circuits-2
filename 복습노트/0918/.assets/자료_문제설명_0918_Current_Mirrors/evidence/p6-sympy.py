import sympy as s
from sympy import Rational as Q
print('Independent derivation from blind conditions; author-early, not fragment author')
def check(name, expression):
    value=s.simplify(expression)
    print(name, value)
    assert value==0,(name,value)

I,B,Jn,Jp=s.symbols('I beta Jn Jp',positive=True)
for label,n,m,p,q,target in [('a',1,1,1,1,-(4*B+4)/(B+2)**2),('b',3,2,5,9,-(67*B+70)/((3*B+5)*(5*B+14)))]:
    z=s.solve([s.Eq(I,n*Jn+(n+m)*Jn/B),s.Eq(m*Jn,p*Jp+(p+q)*Jp/B)],[Jn,Jp])
    output=s.factor(q*z[Jp]);nom=Q(m,n)*Q(q,p)*I;error=s.factor(output/nom-1)
    print(label,'Icopy=',output,'relative error=',error,'largeBeta coefficient',s.limit(B*error,B,s.oo))
    check(label+' reference error',error-target)
    check(label+' infinite beta',s.limit(error,B,s.oo))
