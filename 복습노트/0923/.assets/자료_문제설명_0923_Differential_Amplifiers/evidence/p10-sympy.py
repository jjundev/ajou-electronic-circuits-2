import sympy as s
# Independently derived from blind problem and displayed input circuit, before reference access.
d,u,a,k,R=s.symbols('d u a k R',positive=True)
f=s.expand(k*((a+d/2-u)**2+(a-d/2-u)**2)/2-k*a*a-u/R);print('nonlinear KCL',f);c1,c2=s.symbols('c1 c2');series=s.series(f.subs(u,c1*d+c2*d*d),d,0,3).removeO();c1v=s.solve(s.Eq(series.coeff(d,1),0),c1)[0];c2v=s.solve(s.Eq(series.coeff(d,2).subs(c1,c1v),0),c2)[0];print('linear',c1v,'quadratic',c2v);assert c1v==0;print('quadratic Rss infinity',s.limit(c2v,R,s.oo),'Rss zero',s.limit(c2v,R,0))
print("Independent conclusion: tail first-order displacement zero; second order coefficient k/[4(2k a+1/Rss)]")
