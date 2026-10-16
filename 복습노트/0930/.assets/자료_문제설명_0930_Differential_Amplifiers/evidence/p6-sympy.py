import sympy as s
# Independently derived from blind problem and displayed input circuit, before reference access.
gn,gp,Rd,Rs,v,x,y=s.symbols('gn gp Rd Rs v x y');q=s.solve([s.Eq(gn*(v-x),x/(Rs/2)),s.Eq(y*(2/Rd+gp)+gn*(v-x),0)],[x,y]);a=s.factor(q[y]/v);print(a);print('gmp zero',s.limit(a,gp,0));assert s.simplify(s.limit(a,gp,0)+Rd/(Rs+2/gn))==0
print("Independent conclusion: gain=-gmn (RDD/2 ||1/gmp)/(1+gmn RSS/2)")
