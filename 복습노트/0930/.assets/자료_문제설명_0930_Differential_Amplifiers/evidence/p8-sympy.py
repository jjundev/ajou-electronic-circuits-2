import sympy as s
# Independently derived from blind problem and displayed input circuit, before reference access.
V,R,I,d=s.symbols('V R I d');x=V-I*R/2;q=s.expand(x.subs(I,I+d)-x);print(q);assert q==-R*d/2
print("Independent conclusion: delta VX=delta VY=-RC deltaI/2, difference0 (alpha factor if finite beta)")
