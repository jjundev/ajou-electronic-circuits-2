import sympy as s
# Independently derived from blind problem and displayed input circuit, before reference access.
I,k,d=s.symbols('I k d',positive=True);q=k*d*s.sqrt(4*I/k-d*d)/2;dm=s.sqrt(2*I/k);print('difference at threshold',s.simplify(q.subs(d,dm)));assert s.simplify(q.subs(d,dm)-I)==0;print('ratio',s.simplify(dm/s.sqrt(I/k)))
print("Independent conclusion: full steering positive difference=sqrt(2 Iss/k)=sqrt2 equilibrium overdrive")
