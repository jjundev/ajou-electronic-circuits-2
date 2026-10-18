# E9.07 independent check: CS stage, output shorted to AC ground, Gm=iout/vin
import sympy as sp
gm,ro,RD,vin,iout=sp.symbols('g_m1 r_o1 R_D v_in i_out',positive=True)
vout=0  # shorted
# current flowing from output node into ground short (out of drain node): KCL at drain
# drain current gm vin + vout/ro flows down through M1; supplied by RD (vout-0 across RD is 0) and the short
i=sp.solve(sp.Eq(iout, gm*vin+(vout-0)/ro - (0-vout)/RD),iout)[0]
Gm=sp.simplify(i/vin); print("Gm =",Gm, " diff vs g_m1:",sp.simplify(Gm-gm))
