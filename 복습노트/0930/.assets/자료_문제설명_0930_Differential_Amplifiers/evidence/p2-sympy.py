# p2 (P10.42) independent check: E10.16 redone with VDD=2V, and VDD vs W/L trade-off
import sympy as sp
P, VDD, VCMo, Av, k, ISS, RD, WL = sp.symbols('P V_DD V_CMout A_v muCox I_SS R_D WL', positive=True)
sol = sp.solve([sp.Eq(P, VDD*ISS), sp.Eq(VDD - RD*ISS/2, VCMo),
                sp.Eq(sp.sqrt(k*WL*ISS)*RD, Av)], [ISS, RD, WL], dict=True)[0]
target_WL = Av**2*P/(4*k*VDD*(VDD-VCMo)**2)
print('W/L(VDD) =', sp.factor(sol[WL]))
print('simplify(WL - Av^2 P/(4 muCox VDD (VDD-VCMout)^2)) =', sp.simplify(sol[WL]-target_WL))
print('R_D(VDD) =', sp.simplify(sol[RD]), ' I_SS =', sol[ISS])
for v in (2.0, 1.8):
    vals = {P: 2e-3, VDD: v, VCMo: 1.6, Av: 5, k: 100e-6}
    print('VDD=%.1f:' % v, {str(s): sp.N(sol[s].subs(vals), 6) for s in (ISS, RD, WL)})
d = sp.diff(target_WL, VDD).subs({P: 2e-3, VDD: 2, VCMo: 1.6, Av: 5, k: 1e-4})
print('d(W/L)/dVDD at VDD=2 =', sp.N(d, 6), '(negative: higher VDD -> smaller W/L)')
