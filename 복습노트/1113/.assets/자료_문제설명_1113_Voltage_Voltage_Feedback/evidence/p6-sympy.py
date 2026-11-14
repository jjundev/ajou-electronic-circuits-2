# verifier-p6 (X12.13): feedback polarity when M2 becomes CG (source->A, gate->bias)
# Method: (a) input zeroed (v_in=0), (b) loop broken at M1's controlling voltage:
#   M1 current i1 = gm1*v_test (+ r_o1 term), (c) returned v_ret = v_gs1 = v_G1 - v_X = -v_X.
#   v_ret/v_test > 0  -> returned signal reinforces test -> POSITIVE feedback
#   v_ret/v_test < 0  -> opposes -> NEGATIVE feedback
# Sanity: the same procedure on the original Fig 12.29 (M2 = CS, gate at A) must give negative.
import sympy as sp

gm1, gm2, RD1, RD2, RF1, RF2, ro1, ro2, vt = sp.symbols('g_m1 g_m2 R_D1 R_D2 R_F1 R_F2 r_o1 r_o2 v_test', positive=True)
vA, vO, vX = sp.symbols('v_A v_out v_X')

def solve(cfg, with_ro):
    g1 = 1/ro1 if with_ro else 0
    g2 = 1/ro2 if with_ro else 0
    i1 = gm1*vt + g1*(vA - vX)              # drain A -> source X (control broken)
    if cfg == 'CG':                         # M2: drain vout, source A, gate AC ground
        i2 = gm2*(0 - vA) + g2*(vO - vA)    # drain vout -> source A
        eqs = [sp.Eq(vO/RD2 + i2 + (vO - vX)/RF1, 0),      # KCL vout (currents leaving)
               sp.Eq(vA/RD1 + i1 - i2, 0),                  # KCL A (i2 enters A)
               sp.Eq((vX - vO)/RF1 + vX/RF2 - i1, 0)]       # KCL X (i1 enters X)
    else:                                   # original: M2 CS, gate A, source ground
        i2 = gm2*vA + g2*vO                 # drain vout -> ground
        eqs = [sp.Eq(vO/RD2 + i2 + (vO - vX)/RF1, 0),
               sp.Eq(vA/RD1 + i1, 0),
               sp.Eq((vX - vO)/RF1 + vX/RF2 - i1, 0)]
    s = sp.solve(eqs, [vA, vO, vX], dict=True)[0]
    s = {k: sp.simplify(v) for k, v in s.items()}
    ratio = sp.factor(sp.simplify(-s[vX]/vt))   # v_ret/v_test, v_ret = 0 - v_X
    return s, ratio

def sign_info(expr):
    n, d = sp.fraction(sp.together(expr))
    n, d = sp.expand(n), sp.expand(d)
    def allpos(p):
        cs = sp.Poly(p, *sorted(p.free_symbols, key=str)).coeffs()
        return all(c > 0 for c in cs), all(c < 0 for c in cs)
    return n, d, allpos(n), allpos(d)

for cfg in ['CG', 'CS_original']:
    for with_ro in [False, True]:
        s, r = solve(cfg, with_ro)
        print('='*70)
        print(f'circuit={cfg}, r_o included={with_ro}')
        print('  v_A   =', s[vA]); print('  v_out =', s[vO]); print('  v_X   =', s[vX])
        print('  v_ret/v_test =', r)
        n, d, (np_, nn), (dp, dn) = sign_info(r)
        print(f'  numerator all-coeff positive={np_}, negative={nn}; denominator all positive={dp}, negative={dn}')
        sgn = (1 if np_ else -1 if nn else 0) * (1 if dp else -1 if dn else 0)
        verdict = {1: 'POSITIVE feedback (v_ret same sign as v_test)', -1: 'NEGATIVE feedback (v_ret opposes v_test)', 0: 'indeterminate'}[sgn]
        print('  [PART 1: gm1-control break = NET M1 return ratio incl. LOCAL source degeneration, not the global-loop polarity]')
        print('  sign(v_ret/v_test) =', sgn, '->', verdict)
        if with_ro:
            lim = sp.factor(sp.limit(sp.limit(r, ro1, sp.oo), ro2, sp.oo))
            print('  limit r_o1,r_o2->oo:', lim)

# qualitative chain (structured) for the CG case
chain = [
 ('v_in up', 'M1 V_GS1 up -> i_D1 up'),
 ('i_D1 up', 'more current pulled through R_D1 -> v_A down'),
 ('v_A down (M2 source, gate fixed)', 'V_GS2 = V_b - v_A up -> i_D2 up'),
 ('i_D2 up', 'more drop on R_D2 -> v_out down'),
 ('v_out down', 'divider R_F1-R_F2 -> v_X down'),
 ('v_X down (M1 source)', 'V_GS1 = v_in - v_X up further -> i_D1 up further: reinforces => POSITIVE'),
]
print('='*70); print('qualitative chain (CG case):')
for a, b in chain: print('  ', a, '=>', b)
print('original CS: v_A down -> M2 (CS, gate A) i_D2 down -> v_out up -> v_X up -> V_GS1 down: opposes => NEGATIVE')

# ---------------------------------------------------------------------------
# PART 2: break the GLOBAL loop (the R_F1-R_F2 sense/return path) itself.
# The gm1-control break above also contains M1's LOCAL source degeneration
# (i1 injected straight into X), so it measures "net" M1 return ratio, not the
# polarity of the global loop asked about. Here: input zeroed (gate of M1 = 0),
# loop cut at the sensing point: V_test drives the top of R_F1 (feedback-network
# input); the amplifier output node O' is terminated by a replica of the network's
# input load (R_F1 + R_F2 to ground, loading only, sign-irrelevant).
# Returned signal = v_O' . v_ret/v_test > 0 -> POSITIVE, < 0 -> NEGATIVE.
print('='*70); print('PART 2: global-loop break at the sensing point (top of R_F1)')
vOp = sp.symbols('v_Op')
for cfg in ['CG', 'CS_original']:
    for with_ro in [False, True]:
        g1 = 1/ro1 if with_ro else 0
        g2 = 1/ro2 if with_ro else 0
        i1 = gm1*(0 - vX) + g1*(vA - vX)
        if cfg == 'CG':
            i2 = gm2*(0 - vA) + g2*(vOp - vA)
            eqs = [sp.Eq(vOp/RD2 + vOp/(RF1+RF2) + i2, 0),
                   sp.Eq(vA/RD1 + i1 - i2, 0),
                   sp.Eq((vX - vt)/RF1 + vX/RF2 - i1, 0)]
        else:
            i2 = gm2*vA + g2*vOp
            eqs = [sp.Eq(vOp/RD2 + vOp/(RF1+RF2) + i2, 0),
                   sp.Eq(vA/RD1 + i1, 0),
                   sp.Eq((vX - vt)/RF1 + vX/RF2 - i1, 0)]
        s = sp.solve(eqs, [vA, vOp, vX], dict=True)[0]
        r = sp.factor(sp.simplify(s[vOp]/vt))
        n, d, (np_, nn), (dp, dn) = sign_info(r)
        sgn = (1 if np_ else -1 if nn else 0) * (1 if dp else -1 if dn else 0)
        print(f'circuit={cfg}, r_o={with_ro}: v_ret/v_test = {r}')
        print(f'   sign = {sgn} ->', {1:'POSITIVE feedback',-1:'NEGATIVE feedback',0:'indeterminate'}[sgn])
        if with_ro:
            print('   limit r_o->oo:', sp.factor(sp.limit(sp.limit(r, ro1, sp.oo), ro2, sp.oo)))

# ---------------------------------------------------------------------------
# PART 3: why PART 1 (gm1-control break) is negative for CG: decomposition (lambda=0)
# i1 injects +i1 into X; M2 (CG) supplies fraction alpha=gm2 RD1/(1+gm2 RD1) of i1,
# drawn OUT of v_out. v_X = i1*Z_XX - alpha*i1*Z_XO.
print('='*70); print('PART 3: decomposition of PART-1 CG result (lambda=0)')
S = RD2 + RF1 + RF2
Zxx = RF2*(RF1 + RD2)/S
Zxo = RF2*RD2/S
alpha = gm2*RD1/(1 + gm2*RD1)
local = Zxx; glob = -alpha*Zxo
vx_dec = gm1*vt*(local + glob)
_, r1 = solve('CG', False)
print('  local (degeneration) term  Z_XX =', sp.simplify(local))
print('  global (via CG M2) term  -a*Z_XO =', sp.simplify(glob), ' (opposite sign: global loop is regenerative)')
print('  check simplify(-v_X_dec/v_test - PART1) =', sp.simplify(-vx_dec/vt - r1))
print('  Z_XX - a*Z_XO =', sp.factor(sp.simplify(local + glob)), ' > 0 always (a<1, R_F1+R_D2>R_D2):')
print('  -> local degeneration always outweighs the global positive loop; global loop polarity itself = POSITIVE')
