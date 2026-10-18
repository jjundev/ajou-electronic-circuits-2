# p11 (P10.17) Fig 10.12 characteristics under (a) IEE/2, (b) VCC + dV, (c) RC/2
import sympy as sp
v = sp.symbols('v', real=True)
VT, IEE, VCC, RC, dV = sp.symbols('V_T I_EE V_CC R_C DeltaV', positive=True)
def ch(I, Vcc, R):
    I1 = I/(1 + sp.exp(-v/VT)); I2 = I - I1
    VX, VY = Vcc - R*I1, Vcc - R*I2
    return dict(IC1_max=sp.limit(I1, v, sp.oo), I_cross=I1.subs(v, 0),
                VX_max=sp.limit(VX, v, -sp.oo), VX_min=sp.simplify(sp.limit(VX, v, sp.oo)),
                V_cross=sp.simplify(VX.subs(v, 0)),
                slope_VY_minus_VX_at0=sp.simplify(sp.diff(VY - VX, v).subs(v, 0)),
                v_for_90pct=sp.simplify(sp.solve(sp.Eq(I1/I, sp.Rational(9, 10)), v)[0]))
for name, args in [('nominal', (IEE, VCC, RC)), ('(a) IEE/2', (IEE/2, VCC, RC)),
                   ('(b) VCC+dV', (IEE, VCC + dV, RC)), ('(c) RC/2', (IEE, VCC, RC/2))]:
    print(name, ch(*args))
