import sympy as s
import json

I,D,R,N=s.symbols('I0 DeltaI RL N',positive=True)
b=(I/N-I)*R;a=((I+D)/N-(I-D))*R
print('general before,after,change=',b,s.expand(a),s.simplify(a-b))
for n in [1,2]:print('N=',n,'before=',s.expand(b.subs(N,n)),'after=',s.expand(a.subs(N,n)),'numeric=',a.subs({N:n,I:.001,D:.0001,R:10000}))
