import sympy as s
# Independently derived from blind problem and displayed input circuit, before reference access.
I,v,R=s.symbols('I v R',positive=True);gm=2*(I/2)/v;print(-gm*R);assert s.simplify(gm-I/v)==0
print("Independent conclusion: gain=-Iss RD/Vov_equil")
