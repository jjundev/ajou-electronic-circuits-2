import sympy as sp
s, gm, RD, CL, RS, Cin = sp.symbols('s g_m R_D C_L R_S C_in', positive=True)
VX, Vout, Vin = sp.symbols('V_X V_out V_in')
# Gate AC ground, source node X. Drain->source current id = gm*VGS = -gm*VX (lambda = 0).
idd = -gm*VX
eqs = [sp.Eq((Vin-VX)/RS - s*Cin*VX + idd, 0),      # KCL at X: in from RS + id = into Cin
       sp.Eq(Vout/RD + s*CL*Vout + idd, 0)]           # KCL at output
sol = sp.solve(eqs, [VX, Vout]); H = sp.factor(sp.simplify(sol[Vout]/Vin)); print('H(s) =', H)
print('poles:', [sp.simplify(p) for p in sp.solve(sp.denom(sp.together(H)).subs(s, sp.Symbol('p')), sp.Symbol('p'))])
Rpar = RS*(1/gm)/(RS+1/gm)
print('win - 1/((RS||1/gm)Cin) =', sp.simplify(-sp.solve(1+gm*RS+sp.Symbol('p')*RS*Cin, sp.Symbol('p'))[0] - 1/(Rpar*Cin)))
print('H - target =', sp.simplify(H - (gm*RD/(1+gm*RS))/((1+s*Rpar*Cin)*(1+s*RD*CL))))
print('low-frequency gain =', sp.simplify(H.subs(s, 0)))
