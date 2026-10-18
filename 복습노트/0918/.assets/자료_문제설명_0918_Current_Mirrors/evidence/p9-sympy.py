import sympy as sp
print("=== p9 (2023-1 midterm Q2) ===")
VT, VA, beta = sp.Rational(25,1000), 5, 200
IREF = sp.Rational(100,10**6)
# ---------- (1) circuit (a) ----------
ICM = IREF*sp.Rational(2,1)          # Q_M/Q_REF1 = 2A_E/A_E
IC1 = ICM*sp.Rational(5,2)           # Q2/Q_REF2 = 5A_E/2A_E
gm, ro1s, ro2s = sp.symbols('g_m1 r_o1 r_o2', positive=True)
vin, vout = sp.symbols('v_in v_out')
# KCL at vout: Q2 (pnp, gate/base at ac ground via X2 fixed) contributes only ro2
sol = sp.solve(sp.Eq(gm*vin + vout/ro1s + vout/ro2s, 0), vout)[0]
Av_a_sym = sp.simplify(sol/vin)
gm1 = IC1/VT; ro1 = VA/IC1; ro2 = VA/IC1
Av_a = Av_a_sym.subs({gm:gm1, ro1s:ro1, ro2s:ro2})
print("(1) I_C,M =", ICM*1e6, "uA ; I_C1 = I_C2 =", IC1*1e6, "uA")
print("(1) Av_a symbolic =", Av_a_sym)
print("(1) gm1 =", gm1, "S, ro1 = ro2 =", ro1, "ohm, Av_a =", Av_a, "=", sp.N(Av_a))
# ---------- (2) circuit (b) ----------
I1, Ic3, Ic2 = sp.Rational(1,2000), sp.Rational(1,2000), sp.Rational(1,1000)
g1, g2, r1, r2, r3, rp1 = sp.symbols('g1 g2 r1 r2 r3 rpi1', positive=True)
vx, vo, it, vi = sp.symbols('v_x v_o i_t v_i')
def solve_b(rpi):
    # node X (Q1 emitter): currents leaving X >=0 ; Q1 base at ac ground, vbe1=-vx
    eqX = sp.Eq(vx/r2 + vx/r3 + g2*vi + (vx/rpi if rpi is not None else 0) - (g1*(-vx) + (vo-vx)/r1), 0)
    # node out: test current it into out (I1 ideal -> open)
    eqO = sp.Eq(it, g1*(-vx) + (vo-vx)/r1)
    return eqX, eqO
vals = {g1: I1/VT, g2: Ic2/VT, r1: VA/I1, r2: VA/Ic2, r3: VA/Ic3}
for label, rpi in [("with rpi1 (Razavi model)", rp1), ("rpi1 -> inf (base current ignored)", None)]:
    eqX, eqO = solve_b(rpi)
    s = sp.solve([eqX.subs(vi,0), eqO.subs(vi,0)], [vx, vo], dict=True)[0]
    Rout = sp.simplify(s[vo]/it)
    s2 = sp.solve([eqX, eqO.subs(it,0)], [vx, vo], dict=True)[0]
    Av = sp.simplify(s2[vo]/vi)
    v = dict(vals); v[rp1] = beta/(I1/VT)
    print(f"(2) [{label}] Rout exact symbolic =", Rout)
    print(f"(2) [{label}] Av exact symbolic =", Av)
    Rn, An = Rout.subs(v), Av.subs(v)
    # approximation g1*r1 >> 1: leading term
    k = sp.symbols('k', positive=True)
    Rlead = sp.limit(Rout.subs(g1, k/r1)/k, k, sp.oo)
    Alead = sp.limit(Av.subs(g1, k/r1)/k, k, sp.oo)
    print(f"(2) [{label}] Rout approx (gm1 ro1>>1) = k*", sp.simplify(Rlead), " with k=gm1*ro1 ->", sp.N((Rlead*k).subs(k, vals[g1]*vals[r1]).subs(v)), "ohm")
    print(f"(2) [{label}] Av   approx (gm1 ro1>>1) =", sp.N((Alead*k).subs(k, vals[g1]*vals[r1]).subs(v)))
    print(f"(2) [{label}] Rout exact = {sp.N(Rn)} ohm, Av exact = {sp.N(An)}")
print("ANSWER (1): I_C1 = 500 uA, Av = -gm1(ro1||ro2) = -100")
print("ANSWER (2): Rout ~= gm1 ro1 (ro2||ro3||rpi1) = 500 kohm (exact 512.5k); Av = -gm2 Rout ~= -2.0e4 (exact -20100); if rpi1 ignored: 666.7k (exact 680k), Av ~ -2.67e4 (exact -26800)")
