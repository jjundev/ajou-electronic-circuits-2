# p8 (P12.22) independent verification: feedback polarity of Fig 12.89 (a)-(d)
# Method: Bode return ratio on each MOSFET's dependent source (input zeroed: Vin=0 -> R_S to ground,
# ideal current sources I1, I2 -> open). Loop broken at the controlled source: gm_k*v_ctrl -> gm_k*v_test.
# Returned control voltage v_ret; T = -v_ret/v_test. T>0 -> returned signal opposes test -> NEGATIVE feedback.
# Small-signal MOSFET (NMOS and PMOS identical form): current d->s = gm*(vg-vs) + (vd-vs)/ro.
import sympy as sp
gm1, gm2, ro1, ro2, RS, vt = sp.symbols('g_m1 g_m2 r_o1 r_o2 R_S v_t', positive=True)
vo, vn = sp.symbols('v_o v_n')
GND = 0

def solve_circuit(name, M1, M2, broken):
    # M = (d, g, s) as sympy expressions (0 = ac ground)
    nodes = [vo, vn]
    devs = {'M1': (M1, gm1, ro1), 'M2': (M2, gm2, ro2)}
    kcl = {vo: 0, vn: 0}
    for k, ((d, g, s), gm, ro) in devs.items():
        ctrl = vt if k == broken else (g - s)
        ids = gm*ctrl + (d - s)/ro
        if d in kcl: kcl[d] += ids      # leaving drain node into transistor
        if s in kcl: kcl[s] -= ids      # entering source node from transistor
    kcl[vn] += vn/RS                     # R_S to ground (Vin = 0)
    sol = sp.solve([kcl[vo], kcl[vn]], nodes, dict=True)[0]
    (d, g, s), _, _ = devs[broken]
    vret = sp.simplify((g - s).subs(sol))
    T = sp.simplify(-vret/vt)
    Tinf = sp.simplify(sp.limit(sp.limit(T, ro1, sp.oo), ro2, sp.oo))
    return T, Tinf

def sign_of(expr):
    n, dd = sp.fraction(sp.together(expr))
    n, dd = sp.expand(n), sp.expand(dd)
    def allpos(p):
        p = sp.Poly(p, gm1, gm2, ro1, ro2, RS)
        return all(c > 0 for c in p.coeffs())
    def allneg(p):
        p = sp.Poly(p, gm1, gm2, ro1, ro2, RS)
        return all(c < 0 for c in p.coeffs())
    if n == 0: return 0
    sn = 1 if allpos(n) else (-1 if allneg(n) else None)
    sd = 1 if allpos(dd) else (-1 if allneg(dd) else None)
    if sn is None or sd is None: return None
    return sn*sd

circuits = {
 # (d, g, s)
 '(a) M2 NMOS SF: gate=Vout, src=n1, drain=VDD':           ((vo, vn, GND), (GND, vo, vn)),
 '(b) M2 PMOS CS: gate=Vout, src=VDD, drain=n1':           ((vo, vn, GND), (vn, vo, GND)),
 '(c) M2 PMOS CG: gate=Vb, src=Vout, drain=n1':            ((vo, vn, GND), (vn, GND, vo)),
 '(d) M1 NMOS CG (gate=Vb, src=n1, drain=Vout); M2 PMOS CS (gate=Vout, src=VDD, drain=n1)':
                                                            ((vo, GND, vn), (vn, vo, GND)),
}
qual = {
 '(a)': 'Vin up -> n1 up -> M1 CS: Vout down -> M2 follower: n1(src) follows gate down -> opposes -> NEGATIVE',
 '(b)': 'Vin up -> n1 up -> Vout down -> M2 PMOS |Vsg| up -> more current pushed into n1 -> n1 up -> reinforces -> POSITIVE',
 '(c)': 'Vin up -> n1 up -> Vout down -> M2 PMOS CG src down -> |Vsg| down -> less current into n1 -> n1 down -> opposes -> NEGATIVE',
 '(d)': 'Vin up -> n1 up -> M1 CG Vgs down -> I_D1 down -> Vout up -> M2 PMOS |Vsg| down -> less current into n1 -> n1 down -> opposes -> NEGATIVE',
}
for name, (M1, M2) in circuits.items():
    print('='*70); print(name)
    print('  qualitative:', qual[name[:3]])
    for br in ('M2', 'M1'):
        T, Tinf = solve_circuit(name, M1, M2, br)
        s = sign_of(T)
        print(f'  return ratio on {br}: T = {T}')
        print(f'     r_o->oo : T = {Tinf}')
        print(f'     sign(T) over all positive params = {s}  ->',
              'NEGATIVE feedback' if s == 1 else ('POSITIVE feedback' if s == -1 else 'indeterminate/zero'))
