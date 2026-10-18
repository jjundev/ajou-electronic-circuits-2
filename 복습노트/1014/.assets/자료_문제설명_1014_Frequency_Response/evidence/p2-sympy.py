import sympy as sp
s, gm, RD, CL, w = sp.symbols('s g_m R_D C_L omega', positive=True)
Vout, Vin = sp.symbols('V_out V_in')
# KCL at output (lambda=0): gm*Vin + Vout/RD + s*CL*Vout = 0
sol = sp.solve(sp.Eq(gm*Vin + Vout/RD + s*CL*Vout, 0), Vout)[0]
H = sp.simplify(sol/Vin); print('H(s) =', H)
target = -gm*RD/(1+s*RD*CL); print('H - target =', sp.simplify(H-target))
mag = sp.simplify(sp.Abs(H.subs(s, sp.I*w))); print('|H(jw)| =', mag)
print('|H| - gmRD/sqrt(1+w^2RD^2CL^2) =', sp.simplify(mag - gm*RD/sp.sqrt(1+w**2*RD**2*CL**2)))
print('pole s =', sp.solve(sp.denom(sp.together(H)).subs(s, sp.Symbol('p')), sp.Symbol('p')), ' -> omega_p = 1/(R_D C_L)')
print('|H(j wp)|/|H(0)| =', sp.simplify(mag.subs(w, 1/(RD*CL))/(gm*RD)), ' (-3 dB)')
print('limit w->oo of w*|H| =', sp.limit(w*mag, w, sp.oo), ' -> -20 dB/dec, |H|=1 near w = gm/CL')
