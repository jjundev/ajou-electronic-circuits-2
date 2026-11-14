# verifier-p2: P12.20 (Fig 12.87 a-d) sense/return identification, independent.
# Method: qualitative (topology) + symbolic small-signal checks.
#  - sense port: impedance the feedback element presents to node Vout (ideal V-sense: inf; I-sense: 0, in series)
#  - return port: where feedback element connects at the input (node n1, same node as I_in => parallel => current)
#  - Norton/Thevenin of return port (ideal I-return: Zout=inf; V-return: Zout=0)
#  - loop sign (break at an infinite-impedance gate) and closed-loop Vout/Iin
import sympy as sp

gm1, gm2, ro1, ro2, rI1, rI2 = sp.symbols('g_m1 g_m2 r_o1 r_o2 r_I1 r_I2', positive=True)
vout, vn1, vt = sp.symbols('v_out v_n1 v_t')
Iin = sp.symbols('I_in')
GM = {'M1': gm1, 'M2': gm2}; RO = {'M1': ro1, 'M2': ro2}

# netlists (small signal: VDD, Vb, gnd -> 0). (name, drain, gate, source); PMOS uses same id(d->s) form.
C = {
 'a': [('M2', '0', 'out', 'n1'), ('M1', 'out', 'n1', '0')],   # M2 NMOS follower: gate Vout, source n1
 'b': [('M2', 'n1', 'out', '0'), ('M1', 'out', 'n1', '0')],   # M2 PMOS CS: gate Vout, drain n1
 'c': [('M2', 'n1', '0', 'out'), ('M1', 'out', 'n1', '0')],   # M2 PMOS CG: source Vout, gate Vb, drain n1
 'd': [('M2', 'n1', 'out', '0'), ('M1', 'out', '0', 'n1')],   # M2 PMOS CS: gate Vout, drain n1; M1 CG (gate Vb, source n1)
}
# feedforward amp: (a)(b)(c) M1 CS gate n1; (d) M1 CG source n1.  I_in always into n1; I1 load at Vout; I2 at n1.

def idrain(name, d, g, s, V):
    return GM[name]*(V[g]-V[s]) + (V[d]-V[s])/RO[name]

def node_eqs(ckt, V, inj):
    # KCL: sum of currents leaving node = injected current
    eq = {'out': V['out']/rI1, 'n1': V['n1']/rI2}
    for (nm, d, g, s) in ckt:
        i = idrain(nm, d, g, s, V)
        if d in eq: eq[d] += i
        if s in eq: eq[s] -= i
    return [sp.Eq(eq['out'], inj.get('out', 0)), sp.Eq(eq['n1'], inj.get('n1', 0))]

out = []
P = lambda *a: out.append(' '.join(str(x) for x in a))

for k, ckt in C.items():
    P('='*70); P('Fig 12.87(%s)' % k)
    fb = [t for t in ckt if t[0] == 'M2'][0]
    # terminals of feedback element M2 touching Vout / n1
    term_out = [t for t, n in zip(('D', 'G', 'S'), fb[1:]) if n == 'out']
    term_n1 = [t for t, n in zip(('D', 'G', 'S'), fb[1:]) if n == 'n1']
    P('M2 terminal on Vout:', term_out, '| M2 terminal on n1 (I_in node):', term_n1)

    # (1) sense port: current M2 draws from Vout with Vout=vt, n1 held at 0 (return port shorted)
    V = {'0': 0, 'out': vt, 'n1': 0}
    d, g, s = fb[1:]
    iM2 = idrain('M2', d, g, s, V)
    i_from_out = (iM2 if d == 'out' else 0) - (iM2 if s == 'out' else 0)   # current leaving Vout into M2
    Ysense = sp.simplify(i_from_out/vt)
    Zsense = sp.oo if Ysense == 0 else sp.simplify(1/Ysense)
    P('  sense port Z_in(FB) =', Zsense, '| limit ro2->oo:', sp.limit(Zsense, ro2, sp.oo) if Zsense != sp.oo else sp.oo)
    P('  M2 is a shunt branch from Vout (not in series with M1/I1 output current path) -> senses V_out (parallel)')

    # (2) return port: Norton at n1, with sense input Vout forced
    Vr = {'0': 0, 'out': vout, 'n1': vn1}
    iM2r = idrain('M2', d, g, s, Vr)
    # id flows drain->source: leaves n1 if drain on n1, enters n1 if source on n1
    i_into_n1 = (iM2r if s == 'n1' else 0) - (iM2r if d == 'n1' else 0)   # current delivered INTO n1 by M2
    i_into_n1 = sp.expand(i_into_n1)
    isc = sp.simplify(i_into_n1.subs(vn1, 0))
    Yout = sp.simplify(-sp.diff(i_into_n1, vn1))
    Zret = sp.oo if Yout == 0 else sp.simplify(1/Yout)
    P('  return: i_F into n1 (n1 shorted) =', isc, ' => K = i_F/v_out =', sp.simplify(isc/vout))
    P('  return port Z_out(FB) =', Zret, '| ro2->oo:', sp.limit(Zret, ro2, sp.oo))
    P('  M2 terminal tied to the same node n1 as I_in (parallel with input source) -> returns CURRENT (parallel)')

    # (3) loop sign: break at an infinite-impedance gate.
    if k in ('a', 'b', 'd'):
        # M2 gate is at Vout -> drive M2 gate with vt, measure v_out
        ck = [('M2', d, 'T', s) if t[0] == 'M2' else t for t in ckt]
        Vb = {'0': 0, 'T': vt, 'out': vout, 'n1': vn1}
        sol = sp.solve(node_eqs(ck, Vb, {}), [vout, vn1], dict=True)[0]
        LG = -sp.simplify(sol[vout]/vt); brk = 'M2 gate'
    else:
        # (c): M1 gate is at n1 -> drive M1 gate with vt, measure v_n1
        ck = [('M1', t[1], 'T', t[3]) if t[0] == 'M1' else t for t in ckt]
        Vb = {'0': 0, 'T': vt, 'out': vout, 'n1': vn1}
        sol = sp.solve(node_eqs(ck, Vb, {}), [vout, vn1], dict=True)[0]
        LG = -sp.simplify(sol[vn1]/vt); brk = 'M1 gate'
    LGi = sp.simplify(sp.limit(sp.limit(sp.limit(sp.limit(LG, rI1, sp.oo), rI2, sp.oo), ro1, sp.oo), ro2, sp.oo)) if k != 'b' else None
    P('  loop gain (break at %s), LG = -v_ret/v_t =' % brk, sp.factor(LG))
    sgn = sp.sign(LG.subs({gm1: 1, gm2: 1, ro1: 10, ro2: 10, rI1: 10, rI2: 10}))
    sgn2 = sp.sign(LG.subs({gm1: 3, gm2: 0.5, ro1: 7, ro2: 50, rI1: 4, rI2: 9}))
    P('  sign(LG) for positive params (two sets):', sgn, sgn2, '->', 'NEGATIVE feedback' if sgn > 0 else 'POSITIVE feedback')
    if LGi is not None: P('  LG ideal-limit (ro,rI->oo):', LGi)

    # (4) closed-loop transimpedance
    Vc = {'0': 0, 'out': vout, 'n1': vn1}
    solc = sp.solve(node_eqs(ckt, Vc, {'n1': Iin}), [vout, vn1], dict=True)[0]
    Rt = sp.factor(sp.simplify(solc[vout]/Iin))
    P('  Vout/Iin exact =', Rt)
    if k == 'a':
        P('  Vout/Iin (rI2->oo, ro2->oo) =', sp.simplify(sp.limit(sp.limit(Rt, rI2, sp.oo), ro2, sp.oo)))
    if k in ('c', 'd'):
        lim = sp.simplify(sp.limit(sp.limit(sp.limit(sp.limit(Rt, rI2, sp.oo), rI1, sp.oo), ro1, sp.oo), ro2, sp.oo))
        P('  Vout/Iin ideal (all ro, rI -> oo) =', lim)

P('='*70)
summary = {
 'a': 'sense V_out (M2 gate, Z=inf, parallel) / return current to n1 (M2 source, parallel with I_in) : voltage-current (shunt-shunt)',
 'b': 'sense V_out (M2 gate, Z=inf, parallel) / return current to n1 (M2 drain, Zout=ro2, parallel)   : voltage-current (shunt-shunt)',
 'c': 'sense V_out (M2 source shunt at Vout, Z~1/gm2, parallel) / return current to n1 (M2 drain, parallel): voltage-current (shunt-shunt)',
 'd': 'sense V_out (M2 gate, Z=inf, parallel) / return current to n1=M1 source (M2 drain, parallel)  : voltage-current (shunt-shunt)',
}
for k, v in summary.items(): P('VERDICT', k, ':', v)
print('\n'.join(out))
