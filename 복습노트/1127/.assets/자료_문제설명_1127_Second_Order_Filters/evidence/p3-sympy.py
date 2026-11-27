import sympy as sp

r1, r2, c1, c2 = sp.symbols("R_1 R_2 C_1 C_2", positive=True)
s = sp.symbols("s")
y1, y2 = 1/r1+s*c1, 1/r2+s*c2
wz = 1/(r1*c1)
wp_passive = (1/r1+1/r2)/(c1+c2)
wp_active = 1/(r2*c2)
condition = {c2: r1*c1/r2}
k_passive = r2/(r1+r2)
k_active = -r2/r1
passive_diff = (r1*c1-r2*c2)/(r1*r2*c1*(c1+c2))
active_diff = (r1*c1-r2*c2)/(r1*r2*c1*c2)
assert sp.factor(wp_passive - wz - passive_diff) == 0
assert sp.factor(wp_active - wz - active_diff) == 0
assert sp.factor((y1/(y1+y2)).subs(condition) - k_passive) == 0
assert sp.factor((-y1/y2).subs(condition) - k_active) == 0
assert sp.factor(k_passive.subs(condition) - (c1/(c1+c2)).subs(condition)) == 0
assert sp.factor(k_active.subs(condition) - (-c1/c2).subs(condition)) == 0
print("Passive omega_p - omega_z =", passive_diff)
print("Active omega_p - omega_z =", active_diff)
print("Both denominators are strictly positive, so coincidence is equivalent to R_1 C_1 = R_2 C_2.")
print("At that equality both admittances share the factor 1+s R_1 C_1.")
print("Passive: H(s) =", k_passive, "= C_1/(C_1+C_2), constant.")
print("Active: H(s) =", k_active, "= -C_1/C_2, constant and inverting.")
