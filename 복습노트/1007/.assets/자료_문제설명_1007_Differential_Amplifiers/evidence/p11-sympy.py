import sympy as s

I,D,R,k=s.symbols('I D R k');before=R*(k*I-I);after=R*(k*(I+D)-(I-D))
for name,ratio in [('a',1),('b',s.Rational(1,2))]:print(name,'before=',before.subs(k,ratio),'after=',s.expand(after.subs(k,ratio)),'change=',s.expand((after-before).subs(k,ratio)))
assert s.simplify((after-before).subs(k,1)-2*D*R)==0
assert s.simplify((after-before).subs(k,s.Rational(1,2))-3*D*R/2)==0
print('Output KCL supply kI1 minus sinkI2, mirror remains saturation; no common-source symmetry assumption.')
