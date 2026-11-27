import sympy as sp

a, wp, wz, w = sp.symbols("A omega_p omega_z omega", positive=True)
r1, r2, c1, c2 = sp.symbols("R_1 R_2 C_1 C_2", positive=True)
mag_sq = a**2*(1+(w/wz)**2)/(1+(w/wp)**2)
derivative = 2*w*a**2*(1/wz**2-1/wp**2)/(1+(w/wp)**2)**2
ratio = sp.sqrt(sp.limit(mag_sq, w, sp.oo)/mag_sq.subs(w, 0))
physical_ratio = (c1/c2)/(r2/r1)
assert sp.factor(sp.diff(mag_sq, w)-derivative) == 0
assert sp.factor(ratio - wp/wz) == 0
assert sp.factor(ratio.subs({wp: 1/(r2*c2), wz: 1/(r1*c1)}) - physical_ratio) == 0
assert ratio.subs(wp, 5*wz) == 5
print("The ratio of asymptotic magnitudes |H(infinity)|/|H(0)| = omega_p/omega_z =", ratio)
print("For omega>0, the derivative of |H|^2 has the sign of omega_p-omega_z.")
print("When omega_p=5 omega_z the high-frequency shelf is the passband, and its gain is 5 times the stopband gain.")
print("A ratio of 10 requires omega_p/omega_z=10 for a high-frequency passband, or 1/10 for a low-frequency passband.")
print("Therefore the proposed pole/zero ratio of 5 is impossible.")
