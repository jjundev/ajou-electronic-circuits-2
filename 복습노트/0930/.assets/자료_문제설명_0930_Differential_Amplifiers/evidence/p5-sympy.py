import sympy as s
# Independently derived from blind problem and displayed input circuit, before reference access.
gm,Rd,Rs,v,x,y=s.symbols('gm Rd Rs v x y');q=s.solve([s.Eq(gm*(v-x),x/(Rs/2)),s.Eq(y/(Rd/2)+gm*(v-x),0)],[x,y]);a=s.simplify(q[y]/v);print(a);assert s.simplify(a+Rd/(Rs+2/gm))==0;print('Rs zero',s.limit(a,Rs,0))
print("Independent conclusion: gain=-RDD/(RSS+2/gm)")
