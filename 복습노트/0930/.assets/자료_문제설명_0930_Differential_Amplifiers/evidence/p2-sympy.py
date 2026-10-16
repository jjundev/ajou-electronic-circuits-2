import sympy as s
from sympy import Rational as Q
print('Independent derivation from blind conditions; author-early, not fragment author')
def check(name, expression):
    value=s.simplify(expression)
    print(name, value)
    assert value==0,(name,value)

P,V,CM,A,mu=s.symbols('P V CM A mu',positive=True)
I=P/V;R=2*(V-CM)/I;gm=A/R
W=s.factor(gm**2/(mu*I))
print('general WL=',W,'dWL/dV=',s.factor(s.diff(W,V)))
check('general expression',W-A*A*P/(4*mu*V*(V-CM)**2))
z={P:Q(2,1000),V:2,CM:Q(16,10),A:5,mu:Q(1,10000)}
print('numerical ISS RD gm WL',I.subs(z),R.subs(z),gm.subs(z),W.subs(z));check('WL390.625',W.subs(z)-Q(3125,8))
print('For V>CM, derivative numerator CM-3V<0 hence larger V lowers WL at fixedP/gain/outputCM.')
