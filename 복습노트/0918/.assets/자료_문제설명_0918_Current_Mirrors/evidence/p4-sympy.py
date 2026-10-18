# P9.52 (Fig. 9.73): I_copy in (a) and (b), square-law, saturation, no CLM
import sympy as sp
IREF, mun, mup, Cox, Wn, Wp, VTHn, VTHp, VDD = sp.symbols('I_REF mu_n mu_p C_ox WLn WLp V_THn V_THp V_DD', positive=True)
VGSn, VSGp = sp.symbols('V_GSn V_SGp', positive=True)
In = lambda k, v: sp.Rational(1,2)*mun*Cox*k*Wn*(v-VTHn)**2
Ip = lambda k, v: sp.Rational(1,2)*mup*Cox*k*Wp*(v-VTHp)**2

def solve_vgs(expr_eq, var, vth):
    sols = [s for s in sp.solve(expr_eq, var) if sp.simplify(s - vth).is_positive is not False]
    return [s for s in sols if sp.simplify((s-vth)).could_extract_minus_sign() is False][0]

# (a) M_REF = 3(W/L)n diode; mirror NMOS 2(W/L)n; PMOS diode 5(W/L)p; PMOS out 3(W/L)p
vgs_a = solve_vgs(sp.Eq(In(3, VGSn), IREF), VGSn, VTHn)
I1a = sp.simplify(In(2, vgs_a))
vsg_a = solve_vgs(sp.Eq(Ip(5, VSGp), I1a), VSGp, VTHp)
Icopy_a = sp.simplify(Ip(3, vsg_a))
print("I1(a) =", I1a)
print("ANSWER p4:main (a): I_copy =", Icopy_a, "(sinks out of PMOS drain, i.e. flows downward)")

# (b) M_REF = (W/L)n diode; NMOS 5(W/L)n -> PMOS diode (W/L)p; PMOS 2(W/L)p sources into out node;
#     NMOS 3(W/L)n (gate tied to M_REF gate) sinks from out node; KCL at out node
vgs_b = solve_vgs(sp.Eq(In(1, VGSn), IREF), VGSn, VTHn)
I5 = sp.simplify(In(5, vgs_b))
vsg_b = solve_vgs(sp.Eq(Ip(1, VSGp), I5), VSGp, VTHp)
Ip2 = sp.simplify(Ip(2, vsg_b))
In3 = sp.simplify(In(3, vgs_b))
Icopy_b = sp.simplify(Ip2 - In3)   # KCL: I_P2 = I_N3 + I_copy
print("I(5Wn) =", I5, "; I(PMOS 2Wp) =", Ip2, "; I(NMOS 3Wn) =", In3)
print("ANSWER p4:main (b): I_copy =", Icopy_b, "(flows out of node to the right)")
assert sp.simplify(Icopy_a - sp.Rational(2,5)*IREF) == 0
assert sp.simplify(Icopy_b - 7*IREF) == 0
# ratio form, independent of mu, Cox, VTH
print("ratio check (a):", sp.nsimplify(Icopy_a/IREF), " (b):", sp.nsimplify(Icopy_b/IREF))
