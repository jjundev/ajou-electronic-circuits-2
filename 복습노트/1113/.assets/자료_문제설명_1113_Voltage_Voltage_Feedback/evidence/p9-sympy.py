# p9 (P12.24) independent polarity check: Figs 12.85-12.88, 16 circuits.
# Method (textbook 12.5): input zeroed (V source -> AC ground, I source -> open),
# loop broken at a high-impedance gate/base, test voltage Vt applied, V_ret computed.
# Small-signal: MOS i(d->s) = gm*(vg-vs) + (vd-vs)/ro  (same model for NMOS/PMOS).
#               BJT i_c = gm*vbe + vce/ro, i_b = vbe/rpi.
# Ideal DC current sources modeled by output resistance rI (-> AC ground); limit rI,ro->oo also checked.
# VDD, Vb, Vin(voltage) -> AC ground '0'. All gm, ro, R > 0.
import sympy as sp, random

P = dict(positive=True)
def S(n): return sp.Symbol(n, **P)

def solve(elems, fixed, out):
    nodes = set()
    for e in elems:
        for n in e[1:4] if e[0] in ('M','Q') else e[1:3]:
            if n not in fixed and n != '0': nodes.add(n)
    V = {n: sp.Symbol('v_'+n) for n in nodes}
    def v(n):
        if n == '0': return 0
        if n in fixed: return fixed[n]
        return V[n]
    kcl = {n: 0 for n in nodes}   # sum of currents leaving node
    def leave(n, i):
        if n in kcl: kcl[n] += i
    for e in elems:
        if e[0] == 'R':
            _, a, b, R = e; i = (v(a)-v(b))/R; leave(a, i); leave(b, -i)
        elif e[0] == 'M':
            _, d, g, s, gm, ro = e; i = gm*(v(g)-v(s)) + (v(d)-v(s))/ro
            leave(d, i); leave(s, -i)
        elif e[0] == 'Q':
            _, c, b, em, gm, rpi, ro = e; vbe = v(b)-v(em)
            ic = gm*vbe + (v(c)-v(em))/ro; ib = vbe/rpi
            leave(c, ic); leave(b, ib); leave(em, -(ic+ib))
    sol = sp.solve(list(kcl.values()), list(V.values()), dict=True)[0]
    return sp.simplify(v(out).subs(sol))

def sign_of(expr):
    e = sp.factor(sp.together(expr))
    if e.is_positive: return '+'
    if e.is_negative: return '-'
    num, den = sp.fraction(e)
    sn = sp.expand(num); sd = sp.expand(den)
    def allsign(p):
        cs = sp.Poly(p, *sorted(p.free_symbols, key=str)).coeffs()
        if all(c > 0 for c in cs): return 1
        if all(c < 0 for c in cs): return -1
        return 0
    s = allsign(sn)*allsign(sd)
    return {1:'+', -1:'-', 0:'?'}[s]

Vt = sp.Symbol('V_t')
gm1,gm2,gm3,gm4 = S('g_m1'),S('g_m2'),S('g_m3'),S('g_m4')
ro1,ro2,ro3,ro4 = S('r_o1'),S('r_o2'),S('r_o3'),S('r_o4')
rI1,rI2,rSS = S('r_I1'),S('r_I2'),S('r_SS')
R1,R2,RF,RC,rpi = S('R_1'),S('R_2'),S('R_F'),S('R_C'),S('r_pi')

dp = [('M','0','0','n1',gm1,ro1), ('M','n2','gt','n1',gm2,ro2), ('R','n1','0',rSS)]  # diff pair, M2 gate broken
C = {}
# Fig 12.85: break at M2 gate (gt); V_ret = node driving M2 gate
C['12.85(a)'] = (dp+[('R','n2','0',rI1),('M','0','n2','o',gm3,ro3),('R','o','0',rI2)], 'o',
  'Vin->0; M2 gate+ -> M2 i up -> n2 down (I1 load) -> M3 NMOS follower: Vout down -> back at M2 gate: opposes')
C['12.85(b)'] = (dp+[('R','n2','0',rI1),('M','o','n2','0',gm3,ro3),('R','o','0',R1)], 'o',
  'M2 gate+ -> n2 down -> M3 PMOS CS: |VGS3| up, i3 up -> Vout up -> reinforces')
C['12.85(c)'] = (dp+[('R','n2','0',rI1),('M','n3','n2','0',gm3,ro3),('R','n3','0',R1)], 'n3',
  'same topology as (b), output taken as I_out: n3 up -> reinforces')
C['12.85(d)'] = (dp+[('R','n2','0',rI1),('M','0','n2','n3',gm3,ro3),('R','n3','0',R1)], 'n3',
  'same as (a) with R1: follower non-inverting, M2 path inverting -> opposes')
C['12.85(e)'] = (dp+[('R','n2','0',rI1),('R','n2','n3',R1),('R','n3','0',R2)], 'n3',
  'Vout=n2; M2 gate+ -> Vout down -> divider R2/(R1+R2) -> M2 gate down -> opposes')
C['12.85(f)'] = (dp+[('M','n2','n2','0',gm4,ro4),('M','o','n2','0',gm3,ro3),('R','o','0',R1)], 'o',
  'M2 gate+ -> i2 up through diode M4 -> n2 down -> M3 PMOS i3 up -> Vout up -> reinforces')
# Fig 12.86: CG M1 (source=Vin->0), break at M1 gate
cg = [('M','n1','gt','0',gm1,ro1), ('R','n1','0',rI1)]
C['12.86(a)'] = (cg+[('M','0','n1','o',gm2,ro2),('R','o','0',rSS)], 'o',
  'M1 gate+ -> i1 up -> n1 down -> NMOS follower M2: Vout down -> opposes')
C['12.86(b)'] = (cg+[('M','o','n1','0',gm2,ro2),('R','o','0',R1)], 'o',
  'n1 down -> PMOS M2 i up -> Vout up -> reinforces')
C['12.86(c)'] = (cg+[('M','n2','n1','0',gm2,ro2),('R','n2','0',R1)], 'n2',
  'same as (b), I_out output -> reinforces')
C['12.86(d)'] = ([('M','n1','gt','0',gm1,ro1),('M','n1','n1','0',gm3,ro3),('M','o','n1','0',gm2,ro2),('R','o','0',R1)], 'o',
  'diode M3 load: n1 down -> M2 mirror i up -> Vout up -> reinforces')
# Fig 12.87: I_in -> open; (a)-(c) break at M1 gate, V_ret = n1; (d) break at M2 gate, V_ret = Vout
cs1 = [('M','o','gt','0',gm1,ro1), ('R','o','0',rI1), ('R','n1','0',rI2)]
C['12.87(a)'] = (cs1+[('M','0','o','n1',gm2,ro2)], 'n1',
  'n1+ -> M1 CS: Vout down -> M2 NMOS follower: n1 down -> opposes')
C['12.87(b)'] = (cs1+[('M','n1','o','0',gm2,ro2)], 'n1',
  'n1+ -> Vout down -> PMOS CS M2 (source VDD): |VGS| up, more current into n1 -> n1 up -> reinforces')
C['12.87(c)'] = (cs1+[('M','n1','0','o',gm2,ro2)], 'n1',
  'n1+ -> Vout down -> PMOS CG M2 (gate Vb, source Vout): |VGS| down, less current into n1 -> n1 down -> opposes')
C['12.87(d)'] = ([('M','n1','gt','0',gm2,ro2),('R','n1','0',rI2),('M','o','0','n1',gm1,ro1),('R','o','0',rI1)], 'o',
  'M2 gate+ -> PMOS M2 current into n1 down -> n1 down -> CG M1 (gate Vb) i up -> Vout down -> opposes')
# Fig 12.88(a): break at Q1 base, n1 terminated by r_pi (replica of base loading)
C['12.88(a)'] = ([('Q','o','bt','0',gm1,rpi,ro1),('R','o','0',RC),('R','n1','o',RF),('R','n1','0',rpi)], 'n1',
  'base+ -> Vout down -> via R_F n1 down -> opposes')
# Fig 12.88(b): break at M1 gate; n1 sees only R_F (I_in open, gate removed) -> n1 = Vout
C['12.88(b)'] = ([('M','0','gt','n2',gm1,ro1),('M','n3','0','n2',gm2,ro2),('R','n2','0',rI2),('R','n3','0',rI1),
                  ('M','0','n3','o',gm3,ro3),('R','o','0',rSS),('R','n1','o',RF)], 'n1',
  'M1 gate+ -> i1 up, i2 down -> n3 up -> M3 NMOS follower Vout up -> R_F -> n1 up -> reinforces')

oo = sp.oo
res = {}
for k,(el,out,why) in C.items():
    L = sp.simplify(solve(el, {'gt':Vt, 'bt':Vt}, out)/Vt)
    sg = sign_of(L)
    # ideal limit: ro, rI -> oo (finite R kept)
    Li = L
    for s in [ro1,ro2,ro3,ro4,rI1,rI2,rSS]:
        if s in Li.free_symbols: Li = sp.limit(Li, s, oo)
    Li = sp.simplify(Li)
    # numeric spot check (secondary only)
    nums = []
    for _ in range(200):
        sub = {s: 10**random.uniform(-4,5) for s in L.free_symbols}
        nums.append(float(L.subs(sub)) > 0)
    nsg = '+' if all(nums) else ('-' if not any(nums) else 'mixed')
    pol = 'negative' if sg=='-' else ('positive' if sg=='+' else 'UNDETERMINED')
    res[k] = pol
    print(f'== Fig {k}')
    print('   reasoning :', why)
    print('   Vret/Vt   =', L)
    print('   ideal lim =', Li)
    print(f'   sign(Vret/Vt) symbolic={sg} (numeric sweep {nsg}) -> feedback = {pol}')
print()
print('SUMMARY (Vret/Vt>0 -> positive feedback, <0 -> negative feedback):')
for k,p in res.items(): print(f'  Fig {k}: {p}')
