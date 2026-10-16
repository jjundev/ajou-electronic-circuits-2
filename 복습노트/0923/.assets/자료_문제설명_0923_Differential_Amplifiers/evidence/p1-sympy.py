import sympy as s
# Independently derived from blind problem and displayed input circuit, before reference access.
v,o,R,r=s.symbols('v o R r');out=s.solve(s.Eq((o-v)/R+o/r,0),o)[0];print(out/v);assert s.limit(out/v,r,s.oo)==1
print("Independent conclusion: Vout/VCC=ro/(RC+ro)")
