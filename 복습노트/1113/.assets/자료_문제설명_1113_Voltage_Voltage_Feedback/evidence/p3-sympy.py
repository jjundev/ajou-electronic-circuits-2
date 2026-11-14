# verifier-p3 (E12.12) independent polarity check, Fig 12.28
# Method: (a) vin=0, (b) break loop at M2 gate, (c) apply Vtest at M2 gate,
# follow loop to X, find Vret/Vtest sign. All gm, ro, R > 0.
import sympy as sp

gm1, gm2, gm3, gm4, ro1, ro2, ro3, ro4, R1, R2, Rss = sp.symbols(
    'g_m1 g_m2 g_m3 g_m4 r_o1 r_o2 r_o3 r_o4 R_1 R_2 R_SS', positive=True)
vin, vt = sp.symbols('v_in V_test', real=True)
v1, vo, vp = sp.symbols('v_n1 v_out v_p')  # n1 (M3 drain/gate), vout, tail node n2

def solve_ckt(vg1, vg2, Rtail):
    """Small-signal nodal analysis. Currents = drain-to-source for NMOS (into drain),
    source-to-drain for PMOS (out of drain into node). Gates draw no current.
    Rtail: small-signal resistance of I_SS (sp.oo -> ideal)."""
    iM1 = gm1*(vg1 - vp) + (v1 - vp)/ro1        # into M1 drain (n1) -> to tail
    iM2 = gm2*(vg2 - vp) + (vo - vp)/ro2        # into M2 drain (vout) -> to tail
    iM3 = gm3*(0 - v1) + (0 - v1)/ro3           # M3 sd current into n1 (gate=drain=n1, VDD=0)
    iM4 = gm4*(0 - v1) + (0 - vo)/ro4           # M4 sd current into vout (gate=n1)
    itail = 0 if Rtail == sp.oo else vp/Rtail
    eqs = [
        sp.Eq(iM3, iM1),                         # KCL n1
        sp.Eq(iM4, iM2 + vo/(R1 + R2)),          # KCL vout (divider load; M2 gate is open circuit)
        sp.Eq(iM1 + iM2, itail),                 # KCL tail
    ]
    s = sp.solve(eqs, [v1, vo, vp], dict=True)[0]
    return sp.simplify(s[vo])

out = []
def P(*a):
    out.append(' '.join(str(x) for x in a)); print(*a)

P('== Structure (from SPICE + figure) ==')
P('M3 diode n1, M4 mirror -> vout; M1 gate=vin (+ input), M2 gate=X; X = R2/(R1+R2) * vout')

for label, Rt in [('ideal I_SS (R_SS -> oo)', sp.oo), ('finite R_SS', Rss)]:
    P('\n== Case:', label, '==')
    # Loop: vin=0, test at M2 gate
    vout_t = solve_ckt(0, vt, Rt)
    Vret = sp.simplify(vout_t*R2/(R1+R2))
    L = sp.simplify(Vret/vt)
    P('Vout/Vtest =', sp.simplify(vout_t/vt))
    P('Vret/Vtest =', L)
    # sign check: numerator & denominator polynomials in positive symbols
    n, d = sp.fraction(sp.together(L))
    n = sp.expand(n); d = sp.expand(d)
    P('numerator terms all negative?', all(t.as_coeff_Mul()[0] < 0 for t in sp.Add.make_args(n)))
    P('denominator terms all positive?', all(t.as_coeff_Mul()[0] > 0 for t in sp.Add.make_args(d)))
    P('sign(Vret/Vtest) for all positive params:', 'NEGATIVE' if (sp.ask(sp.Q.negative(L)) or
         (all(t.as_coeff_Mul()[0] < 0 for t in sp.Add.make_args(n)) and all(t.as_coeff_Mul()[0] > 0 for t in sp.Add.make_args(d)))) else 'UNDETERMINED')
    # forward path sign: vin -> vout (M2 gate grounded)
    A_plus = sp.simplify(solve_ckt(vin, 0, Rt)/vin)
    P('vout/vin with M2 gate grounded (forward, M1 = noninverting) =', A_plus)
    n2, d2 = sp.fraction(sp.together(A_plus))
    P('forward gain positive (all terms)?', all(t.as_coeff_Mul()[0] > 0 for t in sp.Add.make_args(sp.expand(n2))) and all(t.as_coeff_Mul()[0] > 0 for t in sp.Add.make_args(sp.expand(d2))))

# Symmetric limit check (gm1=gm2=gm, gm3=gm4, ideal tail, ro3=ro4 large)
gm, ro, gp, rop = sp.symbols('g_m r_o g_mp r_op', positive=True)
L0 = sp.simplify(solve_ckt(0, vt, sp.oo).subs({gm1: gm, gm2: gm, ro1: ro, ro2: ro, gm3: gp, gm4: gp, ro3: rop, ro4: rop})/vt*R2/(R1+R2))
P('\n== Symmetric, ideal tail ==')
P('Vret/Vtest =', L0)
P('limit r_op->oo (ro3=ro4->oo), still negative:', sp.simplify(sp.limit(L0, rop, sp.oo)))
P('unloaded divider: R1,R2 -> oo with k=R2/(R1+R2) fixed:')
k = sp.symbols('k', positive=True)
Lk = sp.simplify(sp.limit(L0.subs(R1, R2*(1-k)/k), R2, sp.oo))
P('  ->', Lk, ' (expected -k*g_m*(r_o||r_op))')
ratio = sp.simplify(Lk/(-k*gm*ro*rop/(ro+rop)))
P('  ratio to -k*gm*(ro||rop):', ratio, '; limit g_mp->oo:', sp.limit(ratio, gp, sp.oo), '(mirror 1/g_mp<<r_op approximation)')

P('\n== Qualitative chain (vin=0, loop broken at M2 gate) ==')
chain = [
 ('V_test (M2 gate) up', 'I_D2 up, tail fixed -> I_D1 down'),
 ('I_D1 down', 'M3 diode current down -> |V_GS3| down -> V_n1 up'),
 ('V_n1 up', 'M4 |V_GS| down -> I_D4 down'),
 ('vout node', 'I_D4 down (pull-up) and I_D2 up (pull-down) both -> vout DOWN'),
 ('X = R2/(R1+R2)*vout', 'V_ret DOWN -> opposes V_test -> NEGATIVE feedback'),
]
for a, b in chain: P(' ', a, '=>', b)
P('\nVERDICT: Fig 12.28 -> negative feedback (M2 gate is the inverting input; divider returns fraction of vout there).')
