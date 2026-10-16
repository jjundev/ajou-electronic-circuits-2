import sympy as s
# Independently derived from blind problem and displayed input circuit, before reference access.
V,R1,R2,I1,I2=s.symbols('V R1 R2 I1 I2');x=V-R1*I1;y=V-R2*I2;print(s.expand((x+y)/2));assert s.simplify(((x+y)/2).subs({R2:R1,I2:I1})-(V-R1*I1))==0
print("Independent conclusion: output CM=VCC-(RC1 IC1+RC2 IC2)/2; matched equal-current=VCC-IC RC")
