# P10.70: CMRR of Fig.10.91(a),(b) with load mismatch dR. lambda=0 for M1,M2; r_O3, r_O4 kept. Body effect neglected.
import sympy as sp
gm, gm3, RD, dR, ro3, ro4, vin1, vin2 = sp.symbols('g_m g_m3 R_D DeltaR_D r_O3 r_O4 v_in1 v_in2', positive=True)
vP, vo1, vo2, vX = sp.symbols('v_P v_out1 v_out2 v_X')

def solve_stage(Rtail_eqs, unknowns, vin1v, vin2v):
    i1 = gm*(vin1v - vP); i2 = gm*(vin2v - vP)          # M1,M2 drain currents (no r_o)
    eqs = [sp.Eq(vo1, -i1*RD), sp.Eq(vo2, -i2*(RD+dR))] + Rtail_eqs(i1+i2)
    s = sp.solve(eqs, [vo1, vo2, vP]+unknowns, dict=True)[0]
    return sp.simplify(s[vo1]-s[vo2])

# (a) tail = M3 with gate at ac ground: current into P node down through r_O3 only
tail_a = lambda itot: [sp.Eq(itot, vP/ro3)]
# (b) cascode tail M3 (gate ac gnd, source X), M4 (gate ac gnd): KCL at P and X
tail_b = lambda itot: [sp.Eq(itot, gm3*(0-vX) + (vP-vX)/ro3), sp.Eq(itot, vX/ro4)]

vc, vd = sp.symbols('v_c v_d')
Rss = {'a': ro3, 'b': ro3 + ro4 + gm3*ro3*ro4}
res = {}
for name, tail, unk in [('a', tail_a, []), ('b', tail_b, [vX])]:
    Acm = sp.simplify(solve_stage(tail, unk, vc, vc)/vc)
    Adm = sp.simplify(solve_stage(tail, unk, vd/2, -vd/2)/vd)
    cmrr = sp.simplify(sp.Abs(Adm)/sp.Abs(Acm))
    target_cm = gm*dR/(1+2*gm*Rss[name])
    target_cmrr = (RD+dR/2)*(1+2*gm*Rss[name])/dR
    print(f'({name}) R_SS =', Rss[name])
    print(f'({name}) A_CM (diff out) =', sp.factor(Acm), ' diff vs target:', sp.simplify(Acm-target_cm))
    print(f'({name}) A_DM (diff out) =', sp.factor(Adm), ' diff vs -g_m(R_D+dR/2):', sp.simplify(Adm+gm*(RD+dR/2)))
    print(f'({name}) CMRR =', sp.factor(cmrr), ' diff vs target:', sp.simplify(cmrr-target_cmrr))
    approx = sp.limit(cmrr*dR/(RD), dR, 0)*RD/dR
    print(f'({name}) CMRR, dR<<R_D  ->', sp.factor(approx))
    res[name] = cmrr
ratio = sp.simplify(res['b']/res['a'])
print('CMRR_b/CMRR_a =', sp.factor(ratio))
print('ratio as r_O ->oo with r_O3=r_O4=r :', sp.limit(ratio.subs({ro3:sp.Symbol('r'),ro4:sp.Symbol('r')}), sp.Symbol('r'), sp.oo))
print('CMRR_b - CMRR_a =', sp.factor(sp.simplify(res['b']-res['a'])), '(>0 for positive parameters)')
num = {gm: sp.Rational(1,100), gm3: sp.Rational(1,100), RD: 2000, dR: 20, ro3: 10000, ro4: 10000}
print('numeric example: CMRR_a =', sp.N(res['a'].subs(num)), ', CMRR_b =', sp.N(res['b'].subs(num)))
