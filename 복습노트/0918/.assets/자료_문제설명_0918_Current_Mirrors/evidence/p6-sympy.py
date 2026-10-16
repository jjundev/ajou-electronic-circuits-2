import sympy as s
# Independently derived from blind problem and displayed input circuit, before reference access.
b=s.symbols('beta',positive=True)
for ar,ac,pr,pc in [(1,1,1,1),(3,2,5,9)]:
 z,w=s.symbols('z w');eq=[s.Eq(1,ar*z+(ar+ac)*z/b),s.Eq(ac*z,pr*w+(pr+pc)*w/b)];sol=s.solve(eq,[z,w]);q=s.factor(pc*sol[w]);nom=s.Rational(ac*pc,ar*pr);print('ratio',q,'signed normalized error',s.factor(q/nom-1));assert s.limit(q,b,s.oo)==nom
print("Independent conclusion: a ratio=1/(1+2/beta)^2; b ratio=(6/5)/[(1+5/(3 beta))(1+14/(5 beta))]")
