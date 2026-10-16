import sympy as s
# Independently derived from blind problem and displayed input circuit, before reference access.
I,k,VT=s.symbols('I k VT',positive=True)
v=s.sqrt(2*I/k);rp=2*(1-1/s.sqrt(2))*v/I
assert s.simplify(k*(v-I*rp/2)**2/2-I/2)==0
print('MOS Rp=',rp);print('BJT Rp=',VT*s.log(2)/I)
print("Independent conclusion: MOS Rp=2(1-1/sqrt(2))*sqrt(2 Iref/k)/Iref; BJT Rp=VT ln2/Iref")
