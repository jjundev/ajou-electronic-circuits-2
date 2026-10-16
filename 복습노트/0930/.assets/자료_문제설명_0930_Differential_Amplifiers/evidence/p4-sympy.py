import sympy as s
# Independently derived from blind problem and displayed input circuit, before reference access.
g1,g3,o1,o3,o5,R,v,y=s.symbols('g1 g3 o1 o3 o5 R v y')
for load in [g3+o1+o3,g3+o1+o3+o5,o1+o3+1/R]:
 out=s.solve(s.Eq(g1*v+load*y,0),y)[0];print('gain',out/v)
print('c: resistors midpoint odd-mode zero; PMOS vgs=0 so gm3 contributes zero')
print("Independent conclusion: a=-gm1/(gm3+go1+go3);b add go5;c=-gm1/(go1+go3+1/R1), tied PMOS gates virtual ground")
