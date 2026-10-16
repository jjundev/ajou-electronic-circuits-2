import sympy as s
# Independently derived from blind problem and displayed input circuit, before reference access.
b=s.symbols('beta',positive=True)
for ar,ac,extra in [(1,5,0),(5,1,0),(2,3,5)]:
 z=s.symbols('z');sol=s.solve(s.Eq(1,ar*z+(ar+ac+extra)*z/b),z)[0];ratio=s.factor(ac*sol);print('copy/Iref',ratio,'fraction error',s.factor(ratio/(s.Rational(ac,ar))-1));assert s.limit(ratio,b,s.oo)==s.Rational(ac,ar)
print("Independent conclusion: copy ratios a5/(1+6/beta), b1/(5+6/beta), c3/(2+10/beta); signed errors negative")
