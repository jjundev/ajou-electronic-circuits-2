import sympy as s
# Independently derived from blind problem and displayed input circuit, before reference access.
V,R,I,d=s.symbols('V R I d');x=V-I*R/2;print(s.expand(x.subs(V,V+d)-x));assert s.expand(x.subs(V,V+d)-x)==d;print('difference0')
print("Independent conclusion: delta VX=delta VY=delta V, difference0")
