import sympy as sp
s, gm, RD, CL, RS, Cin = sp.symbols('s g_m R_D C_L R_S C_in', positive=True)
VA, Vout, Vin = sp.symbols('V_A V_out V_in')
# VA = gate node; lambda = 0, gate draws no current
eqs = [sp.Eq((VA-Vin)/RS + s*Cin*VA, 0), sp.Eq(gm*VA + Vout/RD + s*CL*Vout, 0)]
sol = sp.solve(eqs, [VA, Vout]); H = sp.factor(sp.simplify(sol[Vout]/Vin)); print('H(s) =', H)
print('poles:', sp.solve(sp.denom(sp.together(H)).subs(s, sp.Symbol('p')), sp.Symbol('p')))
print('H - target =', sp.simplify(H - (-gm*RD)/((1+s*RS*Cin)*(1+s*RD*CL))))
