import sympy as s
from sympy import Rational as Q
print('Independent derivation from blind conditions; author-early, not fragment author')
def check(name, expression):
    value=s.simplify(expression)
    print(name, value)
    assert value==0,(name,value)

I,B,J=s.symbols('I beta J',positive=True)
for label,n,m,total,target in [('a',1,5,6,-6/(B+6)),('b',5,1,6,-6/(5*B+6)),('c',2,3,10,-5/(B+5))]:
    density=s.solve(s.Eq(I,n*J+total*J/B),J)[0]
    out=s.factor(m*density);nom=Q(m,n)*I;error=s.factor(out/nom-1)
    print(label,'Icopy=',out,'normalized error=',error,'betaInf',s.limit(out/I,B,s.oo))
    check(label+' error',error-target)
    check(label+' KCL',I-n*density-total*density/B)
