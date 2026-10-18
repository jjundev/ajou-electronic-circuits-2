# P10 (P9.37): sensitivity of I1 to VTH
import sympy as sp
k, WL, R1, R2, VDD, VTH = sp.symbols('muCox WL R1 R2 V_DD V_TH', positive=True)
Vov = R2*VDD/(R1+R2) - VTH
I1 = k*WL/2*Vov**2
d = sp.diff(I1, VTH)
print('dI1/dVTH =', sp.factor(d))
print('simplify(d + muCox WL (R2VDD/(R1+R2)-VTH)) =', sp.simplify(d + k*WL*Vov))
print('simplify(d + 2 I1/Vov) =', sp.simplify(d + 2*I1/Vov))
print('relative (dI1/I1)/dVTH =', sp.simplify(d/I1), '  = -2/(V_GS - V_TH)')
for vdd in [3.0, 1.8, 1.2]:
    vals = {R1: 1, R2: 1, VDD: vdd, VTH: 0.4}
    print('VDD=%.1f: Vov=%.3f V, (dI1/I1)/dVTH = %.2f /V' % (vdd, float(Vov.subs(vals)), float((d/I1).subs(vals))))
