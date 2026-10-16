import sympy as s
from sympy import Rational as Q
print('Independent derivation from blind conditions; author-early, not fragment author')
def check(name, expression):
    value=s.simplify(expression)
    print(name, value)
    assert value==0,(name,value)

V=s.symbols('V');IC=Q(1,1000)/2;R=1000;VC=V-R*IC
# Strict active region: collector-base junction must not be forward biased.
VB=s.symbols('VB');bound=s.solve(s.Eq(VC,VB),VB)[0]
print('max input CM (strict active)=',bound,'distance fromVCC=',s.simplify(V-bound))
check('halfVolt headroom',V-bound-Q(1,2))
print('Allowing .4V forwardBC is a different approximate convention; not used in source example.')
