import sympy as s
# Independently derived from blind problem and displayed input circuit, before reference access.
V,t,I,R=s.symbols('VDD VTH Iss RD',positive=True);drain=V-I*R;print(s.solve(s.Eq(drain,s.Rational(3,2)-t),R));print('M1 saturation needs Vd>=Vin1-VTH; M2 off needs VP>=Vin2-VTH')
print("Independent conclusion: RD <=(VDD-1.5+VTH)/Iss; assumed off additionally VP >=.3-VTH")
