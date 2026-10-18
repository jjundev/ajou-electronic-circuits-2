import sympy as sp
gm, RD, CL, RS, Cin = sp.symbols('g_m R_D C_L R_S C_in', positive=True)
# From the CG stage (p8): win = (1+gm RS)/(RS Cin) = 1/((RS||1/gm)Cin), wout = 1/(RD CL)
win = (1+gm*RS)/(RS*Cin); wout = 1/(RD*CL)
RDs = sp.solve(sp.Eq(wout, 10*win), RD)[0]; print('R_D =', RDs)
Rpar = RS/(1+gm*RS)
print('R_D - (RS||1/gm)Cin/(10CL) =', sp.simplify(RDs - Rpar*Cin/(10*CL)))
print('check wout/win =', sp.simplify(wout.subs(RD, RDs)/win))
