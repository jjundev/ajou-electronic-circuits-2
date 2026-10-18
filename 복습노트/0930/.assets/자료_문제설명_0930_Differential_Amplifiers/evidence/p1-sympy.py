# p1 (E10.16) independent check: NMOS diff pair design, Av=5, P=2mW, VDD=1.8V, out CM >= 1.6V
import sympy as sp
P, VDD, VCMo, Av, k, ISS, RD, WL = sp.symbols('P V_DD V_CMout A_v muCox I_SS R_D WL', positive=True)
sol = sp.solve([sp.Eq(P, VDD*ISS),                     # power budget
                sp.Eq(VDD - RD*ISS/2, VCMo),           # output CM level at its boundary
                sp.Eq(sp.sqrt(2*k*WL*ISS/2)*RD, Av)],  # gm*RD = Av, gm = sqrt(2 muCox W/L I_D), I_D = ISS/2
               [ISS, RD, WL], dict=True)[0]
print('symbolic:', sol)
target_WL = Av**2*P/(4*k*VDD*(VDD-VCMo)**2)
print('simplify(WL - Av^2 P/(4 muCox VDD (VDD-VCMout)^2)) =', sp.simplify(sol[WL]-target_WL))
vals = {P: 2e-3, VDD: 1.8, VCMo: 1.6, Av: 5, k: 100e-6}
for s in (ISS, RD, WL):
    print(s, '=', sp.N(sol[s].subs(vals), 6))
gm = sp.N((Av/sol[RD]).subs(vals), 6)
print('g_m =', gm, 'S  (1/g_m =', sp.N(1/gm, 5), 'ohm)')
