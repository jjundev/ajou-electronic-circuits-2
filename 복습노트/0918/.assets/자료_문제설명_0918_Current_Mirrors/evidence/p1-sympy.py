import sympy as sp
I, k, Vth, R, VT, IS = sp.symbols('I_REF k V_TH R_P V_T I_S', positive=True)  # k = mu_n*Cox*W/L
# (a) square law, lambda=0, equal W/L
VGSref = Vth + sp.sqrt(2*I/k)
I1 = I/2
VGS1 = Vth + sp.sqrt(2*I1/k)
sol_a = sp.solve(sp.Eq(VGSref, VGS1 + I1*R), R)
Ra = sp.simplify(sol_a[0])
print("Rp(a) =", Ra, "| alt form:", sp.simplify(Ra - 2*(sp.sqrt(2)-1)/sp.sqrt(k*I)))
# check: plug back, solve for I1 given Ra
x = sp.symbols('x', positive=True)
chk = sp.solve(sp.Eq(VGSref, Vth + sp.sqrt(2*x/k) + x*Ra), x)
print("(a) check I1 =", [sp.simplify(c) for c in chk])
# (b) exponential, base currents neglected: emitter current of Q_REF = I_REF
VBEref = VT*sp.log(I/IS)
VBE1 = VT*sp.log(2*I/IS)
Rb = sp.simplify(sp.solve(sp.Eq(VBEref + I*R, VBE1), R)[0])
Rb = sp.simplify(sp.expand_log(Rb, force=True))
print("Rp(b) =", Rb)
print("(b) numeric VT=26mV, IREF=1mA: Rp =", sp.N(Rb.subs({VT:0.026, I:1e-3})), "ohm")
print("p1:1 answer: R_P = 2(sqrt2-1)/sqrt(muCox(W/L) I_REF) = (2-sqrt2)*V_ov,REF/I_REF")
print("p1:2 answer: R_P = V_T ln2 / I_REF")
