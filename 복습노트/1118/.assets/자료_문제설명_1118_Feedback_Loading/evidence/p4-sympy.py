"""Fig. 12.38(a): output test with the independent input current source open."""
import sympy as sp

g1, g2, D1, D2, F = sp.symbols('g_m1 g_m2 R_D1 R_D2 R_F', positive=True)
s, x, o, it = sp.symbols('v_s v_x v_o i_test')
kcl = [g1*s + (s-o)/F, x/D1-g1*s, o/D2+g2*x+(o-s)/F-it]
sol = sp.solve(kcl, (s, x, o), dict=True)[0]
z = sp.factor(sol[o]/it)
z_expected = 1/(1/D2+(1+g2*D1)/(F+1/g1))
assert sp.simplify(z-z_expected) == 0
print("s, x, o KCL residuals:", [sp.simplify(eq.subs(sol)) for eq in kcl])
print("Exact Zout:", z)
print("Exact Yout = 1/R_D2 + (1+g_m2 R_D1)/(R_F+1/g_m1)")
print("v_s/v_o:", sp.factor(sol[s]/sol[o]))
print("v_x/v_o:", sp.factor(sol[x]/sol[o]))
print("At R_F >> 1/g_m1 and R_F >> R_D2, omit direct R_F loading:")
print("Zout ≈ R_D2/(1+g_m2 R_D1 R_D2/R_F)")
print("Infinite R_F limit:", sp.limit(z, F, sp.oo))
