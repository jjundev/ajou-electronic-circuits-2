import sympy as s
from sympy import Rational as Q
print('Independent derivation from blind conditions; author-early, not fragment author')
def check(name, expression):
    value=s.simplify(expression)
    print(name, value)
    assert value==0,(name,value)

I,K,d=s.symbols('I K d',positive=True)
# At complete steering ID2=0; the lower gate is at cutoff, so ID1=K*d^2/2.
root=s.solve(s.Eq(K*d*d/2,I),d)[0]
u=s.sqrt(I/K);print('positive cutoff differential=',root,'ratio to eq overdrive',s.simplify(root/u))
check('sqrt2 factor',root/u-s.sqrt(2))
full=K*d*s.sqrt(4*I/K-d*d)/2
check('full nonlinear formula boundary',full.subs(d,root)-I)
