import sympy as sp

q, wn = sp.symbols("Q omega_n", positive=True)
s = sp.symbols("s")
den = s**2 + wn*s/q + wn**2
discriminant = sp.factor(sp.discriminant(den, s))
q_equal, = sp.solve(discriminant, q)
double_den = sp.factor(den.subs(q, q_equal))
poles = sp.roots(double_den, s)
assert q_equal == sp.Rational(1, 2)
assert poles == {-wn: 2}
print("Discriminant =", discriminant)
print("For positive Q and omega_n, the only zero of the discriminant is Q =", q_equal)
print("Denominator at coincidence =", double_den)
print("Both pole locations are s = -omega_n; the common positive pole frequency is omega_n rad/s.")
print("This describes the denominator poles, which persist as transfer poles absent numerator cancellation.")
