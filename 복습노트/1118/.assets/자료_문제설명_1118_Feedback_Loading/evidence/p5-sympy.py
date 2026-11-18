"""Fig. 12.97: simultaneous independent input and output current injections."""
import sympy as sp

g1, g2, D, R1, R2 = sp.symbols('g_m1 g_m2 R_D R_1 R_2', positive=True)
s, f, o, ii, it = sp.symbols('v_in v_div v_o i_in i_test')
kcl = [g1*s+g2*f-ii, (f-o)/R1+f/R2, o/D+(o-f)/R1-g1*s-it]
sol = sp.solve(kcl, (s, f, o), dict=True)[0]
beta = R2/(R1+R2)
D_loaded = 1/(1/D+1/(R1+R2))
T = beta*g2*D_loaded
closed = [sp.diff(sol[o], ii), sp.diff(sol[s], ii), sp.diff(sol[o], it)]
expected = [D_loaded/(1+T), 1/(g1*(1+T)), D_loaded/(1+T)]
assert all(sp.simplify(a-b)==0 for a,b in zip(closed, expected))
print("KCL residuals:", [sp.simplify(eq.subs(sol)) for eq in kcl])
print("beta =", beta, "; loaded drain resistance =", D_loaded)
for label, form in zip(("v_o/i_in (i_test=0)", "v_in/i_in (i_test=0)", "v_o/i_test (i_in=0)"), closed):
    print(label, "=", sp.factor(form))
print("R1+R2 >> RD: T=beta*g_m2*R_D; Ztrans=R_D/(1+T); Zin=1/[g_m1(1+T)]; Zout=R_D/(1+T)")
print("Voltage ratio v_o/v_in, if requested:", sp.factor(closed[0]/closed[1]))
