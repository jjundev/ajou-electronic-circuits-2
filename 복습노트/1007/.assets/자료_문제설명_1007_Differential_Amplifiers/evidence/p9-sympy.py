import sympy as S
from math import log10,pi,sqrt

m,I1,I2,R,V,I0,di=(S.Symbol('m',positive=True),S.Symbol('I1',positive=True),S.Symbol('I2',positive=True),S.Symbol('R',positive=True),S.Symbol('V',positive=True),S.Symbol('I0',positive=True),S.Symbol('di',positive=True))
# Actual output node: mirrored incoming=m*I1; I2 sink and resistor outward.
Vsol=S.solve(S.Eq(m*I1-I2-V/R,0),V)[0]
for name,k in [('a',1),('b',S.Rational(1,2))]:
 before=S.simplify(Vsol.subs({m:k,I1:I0,I2:I0}));after=S.simplify(Vsol.subs({m:k,I1:I0+di,I2:I0-di}));print(name,'before=',before,'after=',after)
 if k==1:assert before==0 and S.simplify(after-2*di*R)==0
 else:assert S.simplify(before+I0*R/2)==0 and S.simplify(after-R*(3*di-I0)/2)==0
print('These formal ideal-source values require compliance/saturation; negative b equilibrium is formal, not guaranteed by grounded practical sinks.')
