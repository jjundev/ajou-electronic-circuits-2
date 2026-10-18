# P10.72 independent check: PMOS mirror M3 (diode, I1) / M4 -> output node with I2 sink and RL to ground, lambda=0
from sympy import *
I0, dI, RL = symbols('I_0 DeltaI R_L', positive=True)
Vout = symbols('V_out')
def vout(I1, I2, ratio):          # ratio = (W/L)4/(W/L)3
    ID4 = ratio*I1
    return solve(Eq(ID4, I2 + Vout/RL), Vout)[0]   # KCL at output node
for name, ratio in (('(a) (W/L)3=(W/L)4', 1), ('(b) (W/L)3=2(W/L)4', Rational(1, 2))):
    b = simplify(vout(I0, I0, ratio)); a = expand(vout(I0+dI, I0-dI, ratio))
    print(name, ': before =', b, '  after =', a, '  change =', simplify(a-b))
