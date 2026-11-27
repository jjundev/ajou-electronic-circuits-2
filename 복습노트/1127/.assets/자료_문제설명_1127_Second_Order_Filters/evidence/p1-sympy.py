import sympy as sp

r1, r2, c1, c2, w = sp.symbols("R_1 R_2 C_1 C_2 omega", positive=True)
s = sp.symbols("s")
vin, vout = sp.symbols("V_in V_out")
y1, y2 = 1/r1 + s*c1, 1/r2 + s*c2
kcl = (vout - vin)*y1 + vout*y2
h = sp.factor(sp.solve(kcl, vout)[0]/vin)
wp = (1/r1 + 1/r2)/(c1 + c2)
wz = 1/(r1*c1)
gain_dc = r2/(r1+r2)
expected = gain_dc*(1+s/wz)/(1+s/wp)
gain_hf = c1/(c1+c2)
mag_sq = gain_dc**2*(1+(w/wz)**2)/(1+(w/wp)**2)
assert sp.factor(h - expected) == 0
assert sp.factor(sp.limit(h, s, sp.oo) - gain_hf) == 0
assert sp.factor(sp.expand_complex(h.subs(s, sp.I*w)*h.subs(s, -sp.I*w)) - mag_sq) == 0
assert sp.factor(sp.diff(mag_sq, w) - 2*w*gain_dc**2*(1/wz**2-1/wp**2)/(1+(w/wp)**2)**2) == 0
print("Output KCL:", kcl, "= 0")
print("H(s) =", h)
print("H(s) = K(1+s/omega_z)/(1+s/omega_p)")
print("K =", gain_dc, "; omega_z =", wz, "; omega_p =", wp)
print("Actual roots are negatives of the positive break frequencies, except when canceled.")
print("|H(j omega)| = K sqrt[(1+(omega/omega_z)^2)/(1+(omega/omega_p)^2)].")
print("Phase = atan(omega/omega_z) - atan(omega/omega_p).")
print("DC =", gain_dc, "; high-frequency =", gain_hf)
print("For omega>0, the squared-magnitude derivative has the sign of omega_p-omega_z.")
