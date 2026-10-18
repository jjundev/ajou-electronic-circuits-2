# P10 (E10.3, Fig. 10.3(b)): two grounded-emitter CE stages driven by +vin / -vin.
# Output CM level = (V_X + V_Y)/2 at equilibrium (vin = 0, both bases at V_in,CM).
import sympy as sp
VCC, RC, IS, VT, Vcm, vin = sp.symbols('V_CC R_C I_S V_T V_inCM v_in', positive=True)
IC1 = IS*sp.exp((Vcm + vin)/VT)
IC2 = IS*sp.exp((Vcm - vin)/VT)
VX = VCC - RC*IC1
VY = VCC - RC*IC2
VCMout = sp.simplify(((VX + VY)/2).subs(vin, 0))
print("V_X(vin=0) =", sp.simplify(VX.subs(vin, 0)))
print("V_Y(vin=0) =", sp.simplify(VY.subs(vin, 0)))
# check: small-signal (linear) part of CM cancels -> first-order CM independent of vin
lin = sp.diff((VX + VY)/2, vin).subs(vin, 0)
print("d(V_CM,out)/d(vin) at vin=0 =", sp.simplify(lin))
print("main: V_CM,out = V_CC - R_C*I_C =", VCMout)
# sensitivity to input CM level (shows CM is set by V_BE, not by a tail source)
print("dV_CM,out/dV_inCM =", sp.simplify(sp.diff(VCMout, Vcm)), " = -R_C*I_C/V_T = -g_m*R_C")
