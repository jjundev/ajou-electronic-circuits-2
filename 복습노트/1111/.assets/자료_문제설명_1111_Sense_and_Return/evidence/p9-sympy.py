# p9 (P12.10) independent check: Fig 12.82 CS stage M1 + ideal current-source load, C_L at Vout,
# feedback K from Vout to subtractor (Vin +, K*Vout -). Find K for closed-loop -3dB bandwidth B.
import sympy as sp
s = sp.symbols('s')
gm, rO, CL, B, K, Vin, Vout = sp.symbols('g_m r_O C_L B K V_in V_out', positive=True)
Kr = sp.symbols('K_r', real=True)   # sign-free K for literal analysis
# KCL at Vout: gm*Vgs + Vout/rO + s CL Vout = 0, Vgs = Vin - Kr*Vout
sol = sp.solve(sp.Eq(gm*(Vin - Kr*Vout) + Vout/rO + s*CL*Vout, 0), Vout)[0]
H = sp.simplify(sol/Vin)
print("literal Y/X =", H)
den = sp.denom(sp.together(H)); p = sp.solve(den, s)[0]
print("literal pole =", sp.simplify(p))
A1 = -gm*rO/(1+s*rO*CL)
print("open-loop A1 = -gm rO/(1+s rO CL); open-loop BW = 1/(rO CL)")
# Standard negative-feedback reading (book convention Y/X = A/(1+K A) with |A| = gm rO):
Hn = (gm*rO/(1+s*rO*CL))/(1 + K*gm*rO/(1+s*rO*CL))
pn = sp.solve(sp.denom(sp.together(sp.simplify(Hn))), s)[0]
print("neg-feedback pole =", sp.simplify(pn), " -> BW =", sp.simplify(-pn))
Ksol = sp.solve(sp.Eq(-pn, B), K)[0]
print("required K =", sp.simplify(Ksol), "=", sp.expand(Ksol))
print("check: BW(Ksol)-B =", sp.simplify((-pn).subs(K, Ksol) - B))
print("lim rO->oo of K:", sp.limit(Ksol, rO, sp.oo), "(lambda=0 case)")
print("requires B > 1/(rO CL) for K>0")
# literal sign: pole magnitude B with stable pole => (1 - Kr gm rO)/(rO CL) = B
Klit = sp.solve(sp.Eq(-sp.simplify(p), B), Kr)[0]
print("literal-sign K (stable) =", sp.simplify(Klit), " = -(required K above):", sp.simplify(Klit + Ksol))
# numeric sanity
vals = {gm:sp.Rational(1,1000), rO:10000, CL:sp.Rational(1,10**12), B:10**9}
print("numeric example K =", sp.N(Ksol.subs(vals),6))
