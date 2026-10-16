import sympy as s
from sympy import Rational as Q
print('Independent derivation from blind conditions; author-early, not fragment author')
def check(name, expression):
    value=s.simplify(expression)
    print(name, value)
    assert value==0,(name,value)

a=s.symbols('a',positive=True)
count=2+a+40/a
stationary=s.solve(s.diff(count,a),a)
print('continuous stationary=',stationary,'second derivative=',s.diff(count,a,2))
check('AMGM factorization',count-(2+2*s.sqrt(40))-(s.sqrt(a)-s.sqrt(40/a))**2)
pairs=[(k,40//k,2+k+40//k) for k in range(1,41) if 40%k==0]
print('all positive integer divisors and counts',pairs)
assert min(z[2] for z in pairs)==15
print('minimum15 at',[(x,y) for x,y,n in pairs if n==15])
check('current product25uA*8*5',Q(25,1000000)*8*5-Q(1,1000))
