import sympy as s
from sympy import Rational as Q
print('Independent derivation from blind conditions; author-early, not fragment author')
def check(name, expression):
    value=s.simplify(expression)
    print(name, value)
    assert value==0,(name,value)

I,R,V,d,VT,delta=s.symbols('I R V d VT delta',positive=True)
f=1/(1+s.exp(-d/VT));i1=I*f;i2=I*(1-f);x=V-R*i1;y=V-R*i2
print('original current curves',i1,i2,'output curves',x,y)
check('a currents halve',i1.subs(I,I/2)-i1/2)
check('a voltage drops halve',(V-x.subs(I,I/2))-(V-x)/2)
check('b currents unaffected',i1.subs(V,V+delta)-i1)
check('b voltage shift',x.subs(V,V+delta)-x-delta)
check('c drops halve',(V-x.subs(R,R/2))-(V-x)/2)
print('equilibrium IC1',i1.subs(d,0),'gain slope',s.simplify(s.diff(x-y,d).subs(d,0)))
print('positive steering endpoint IC1',s.limit(i1,d,s.oo),'all characteristic transformations proved symbolically.')
