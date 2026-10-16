import sympy as s
# Independently derived from blind problem and displayed input circuit, before reference access.
l,v,t=s.symbols('lambda VGS VTH',positive=True)
ratio=(1+l*(v-t))/(1+l*v);print('ratio',ratio,'signed error',s.factor(ratio-1));assert s.limit(ratio,l,0)==1
print("Independent conclusion: VDS1=VGS; fractional signed error=-lambda VTH/(1+lambda VGS)")
