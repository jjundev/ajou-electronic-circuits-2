import sympy as s
# Independently derived from blind problem and displayed input circuit, before reference access.
I=s.symbols('I',positive=True);print('a',I*s.Rational(2,3)*s.Rational(3,5));print('b',I*5*2-I*3)
print("Independent conclusion: (a)2/5 Iref;(b)7 Iref net sourcing")
