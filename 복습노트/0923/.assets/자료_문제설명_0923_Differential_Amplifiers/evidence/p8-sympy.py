import sympy as s
# Independently derived from blind problem and displayed input circuit, before reference access.
d,k,I,R=s.symbols('d k I R',positive=True);q=k*d*s.sqrt(4*I/k-d*d)/2;gm=s.simplify(s.diff(q,d).subs(d,0));print('gm',gm,'gain',-gm*R);assert s.simplify(gm-s.sqrt(k*I))==0
print("Independent conclusion: from current difference derivative at0 gm=sqrt(k Iss); differential gain=-gm RD for VX-VY")
