import sympy as s
# Independently derived from blind problem and displayed input circuit, before reference access.
vn,vo,gn,gp,go1,go3=s.symbols('vn vo gn gp go1 go3');q=s.solve(s.Eq(gn*vn+(gp+go1+go3)*vo,0),vo)[0];print(q/vn);assert s.simplify(s.limit(s.limit(q/vn,go1,0),go3,0)+gn/gp)==0
print("Independent conclusion: differential gain=-gmn/(gmp+gon+gop)")
