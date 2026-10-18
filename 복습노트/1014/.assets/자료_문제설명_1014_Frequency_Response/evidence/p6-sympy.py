import sympy as sp
s, gm, RD, CL, w = sp.symbols('s g_m R_D C_L omega', positive=True)
VX, Vout, Vin = sp.symbols('V_X V_out V_in')
eqs = [sp.Eq(gm*Vin + VX/RD + s*CL*VX, 0), sp.Eq(gm*VX + Vout/RD + s*CL*Vout, 0)]
sol = sp.solve(eqs, [VX, Vout])
H = sp.simplify(sol[Vout]/Vin); print('H(s) =', sp.factor(H))
print('H - (gmRD)^2/(1+sRDCL)^2 =', sp.simplify(H - (gm*RD)**2/(1+s*RD*CL)**2))
mag = sp.simplify(sp.Abs(H.subs(s, sp.I*w)))
print('|H(j wp)|/|H0| at wp=1/(RDCL):', sp.simplify(mag.subs(w, 1/(RD*CL))/(gm*RD)**2), '(-6 dB)')
print('limit w->oo w^2|H| =', sp.limit(w**2*mag, w, sp.oo), ' -> -40 dB/dec beyond the double pole')
w3 = sp.solve(sp.Eq(mag/(gm*RD)**2, 1/sp.sqrt(2)), w)
print('-3dB freq:', [sp.simplify(x) for x in w3], ' sqrt(sqrt2-1) =', sp.N(sp.sqrt(sp.sqrt(2)-1)))
