import sympy as s
# Independently derived from blind problem and displayed input circuit, before reference access.
Vdd=s.Rational(18,10);Vcm=s.Rational(16,10);Vth=s.Rational(5,10);I=s.Rational(5,10000);R=2*(Vdd-Vcm+Vth)/I;print(R);assert R==2800
print("Independent conclusion: RDmax=2.8kohm")
