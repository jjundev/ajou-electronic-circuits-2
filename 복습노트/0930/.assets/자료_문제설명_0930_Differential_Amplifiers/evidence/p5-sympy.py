import sympy as s
g,Rd,Rs,vi,i,vs,vo=s.symbols('g Rd Rs vi i vs vo')
x=s.solve([s.Eq(i,g*(vi-vs)),s.Eq(vs,i*Rs/2),s.Eq(vo,-i*Rd/2)],[i,vs,vo],dict=True)[0]
a=s.factor(x[vo]/vi)
print('DM half circuit KCL gain=',a)
assert s.simplify(a+Rd/(Rs+2/g))==0
print('Rs0=',s.simplify(a.subs(Rs,0)),'g infinity=',s.limit(a,g,s.oo))
