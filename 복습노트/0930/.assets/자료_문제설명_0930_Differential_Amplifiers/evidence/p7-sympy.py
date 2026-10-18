# p7 (P10.11) Fig 10.9, VCC -> VCC + dV, Early effect neglected
# collector currents set by I_EE and V_BE1 - V_BE2 only (no Early) -> independent of VCC
import sympy as sp
VCC, dV, RC, IEE, VT, vd = sp.symbols('V_CC DeltaV R_C I_EE V_T v_d', positive=True)
I1 = IEE/(1 + sp.exp(-vd/VT)); I2 = IEE - I1      # alpha ~ 1
VX = lambda vcc: vcc - RC*I1
VY = lambda vcc: vcc - RC*I2
dVX = sp.simplify(VX(VCC+dV) - VX(VCC)); dVY = sp.simplify(VY(VCC+dV) - VY(VCC))
print('dVX =', dVX, ' dVY =', dVY, ' d(VX - VY) =', sp.simplify(dVX - dVY))
print('at v_d = 0 (Fig 10.9, both bases at V_CM): VX = VY =', sp.simplify(VX(VCC).subs(vd, 0)))
