import sympy as s
# Independently derived from blind problem and displayed input circuit, before reference access.
d,V,I,R,T=s.symbols('d V I R T',positive=True);i1=I/(1+s.exp(-d/T));i2=I-i1;x=V-R*i1;y=V-R*i2
print('a current factor',s.simplify(i1.subs(I,I/2)/i1),'output drop factor',s.simplify((V-x.subs(I,I/2))/(V-x)))
e=s.symbols('DeltaV');print('b output delta',s.simplify(x.subs(V,V+e)-x));print('c output drop factor',s.simplify((V-x.subs(R,R/2))/(V-x)));print('switching width VT unchanged')
print("Independent conclusion: Iss half halves current curves and output drops; VCC rise translates output curves;RC half halves voltage excursions only")
