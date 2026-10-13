# P10.72 (Fig 10.93): PMOS mirror M3 (diode) -> M4, I1 sinks from M3 drain,
# I2 sinks from Vout node, R_L to ground. lambda = 0 (no CLM).
import sympy as sp
I0, dI, RL, k, VTH, VDD = sp.symbols('I_0 DeltaI R_L k V_TH V_DD', positive=True)
Vsg, ID4, Vout, I1, I2, r = sp.symbols('V_SG I_D4 V_out I_1 I_2 r', real=True)

def solve_vout(I1v, I2v, ratio):
    # (W/L)_4 = (W/L)_3 / ratio ; square law, lambda = 0
    k3 = k; k4 = k/ratio
    # M3 diode: I1 = k3/2 (Vsg-VTH)^2  -> (Vsg-VTH)^2 = 2 I1/k3
    ov2 = 2*I1v/k3
    id4 = sp.Rational(1, 2)*k4*ov2          # M4 shares V_SG, sat, no CLM
    # KCL at Vout: I_D4 = I2 + Vout/RL
    sol = sp.solve(sp.Eq(id4, I2v + Vout/RL), Vout)[0]
    return sp.simplify(sol)

for name, ratio in (('a', 1), ('b', 2)):
    before = solve_vout(I0, I0, ratio)
    after = solve_vout(I0 + dI, I0 - dI, ratio)
    print(f"({name}) (W/L)3 = {ratio}(W/L)4")
    print("   V_out before =", before)
    print("   V_out after  =", sp.factor(after))
    print("   Delta V_out  =", sp.simplify(after - before))
    if name == 'a':
        tb, ta = sp.Integer(0), 2*dI*RL
    else:
        tb, ta = -I0*RL/2, (3*dI - I0)*RL/2
    print("   check before - target :", sp.simplify(before - tb))
    print("   check after  - target :", sp.simplify(after - ta))
