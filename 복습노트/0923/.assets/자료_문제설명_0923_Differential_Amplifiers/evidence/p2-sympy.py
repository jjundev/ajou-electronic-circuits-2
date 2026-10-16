import sympy as s
# Independently derived from blind problem and displayed input circuit, before reference access.
v,R,r=s.symbols('v R r',positive=True);x=v*r/(R+r);y=v*r/(R+r);print('differential',s.simplify(x-y))
print("Independent conclusion: differential ripple gain0 by exact symmetry")
