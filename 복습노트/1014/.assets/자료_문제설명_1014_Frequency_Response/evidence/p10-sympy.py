import sympy as sp
s, gm, RD, CL, RS, Cin, RP = sp.symbols('s g_m R_D C_L R_S C_in R_P', positive=True)
VX, VS, Vout, Vin = sp.symbols('V_X V_S V_out V_in')
# X: node at Cin/RS; S: source of M1; gate AC ground; id (drain->source) = gm*(0-VS)
idd = -gm*VS
eqs = [sp.Eq((Vin-VX)/RS - s*Cin*VX - (VX-VS)/RP, 0),
       sp.Eq((VX-VS)/RP + idd, 0),
       sp.Eq(Vout/RD + s*CL*Vout + idd, 0)]
sol = sp.solve(eqs, [VX, VS, Vout]); H = sp.factor(sp.simplify(sol[Vout]/Vin)); print('H(s) =', H)
poles = [sp.simplify(p) for p in sp.solve(sp.denom(sp.together(H)).subs(s, sp.Symbol('p')), sp.Symbol('p'))]; print('poles:', poles)
Rin = RP + 1/gm; Rpar = RS*Rin/(RS+Rin)
print('target win = 1/([RS||(RP+1/gm)]Cin), wout = 1/(RD CL)')
print('-pole - win:', [sp.simplify(-p - 1/(Rpar*Cin)) for p in poles])
print('-pole - wout:', [sp.simplify(-p - 1/(RD*CL)) for p in poles])
print('limit RP->0 of win:', sp.simplify(sp.limit(1/(Rpar*Cin), RP, 0)), ' (recovers p8)')
print('low-frequency gain:', sp.simplify(H.subs(s, 0)))
