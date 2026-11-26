import sympy as s

gm, go, k, G = s.symbols('g_m g_o K G_L', positive=True)
vin, vout, i_test = s.symbols('v_in v_out i_test')
# G_L includes the output load and the resistance R1+R2.
# NMOS source-to-drain current with gate K*vout.
i_source = gm*(vin - k*vout) + go*(vin - vout)
closed = s.solve(G*vout - i_source - i_test, vout)[0]
a = s.factor(closed.diff(vin))
rin = s.factor(vin/i_source.subs(vout, closed.subs(i_test, 0)))
rout = s.factor(closed.diff(i_test))
a0, rin0, rout0 = [s.factor(x.subs(k, 0)) for x in (a, rin, rout)]
# To preserve loading, open the controlling gate signal, not the divider branch.
for label, exact in [('A0', a0), ('Rin0', rin0), ('Rout0', rout0),
                     ('Acl', a), ('Rincl', rin), ('Routcl', rout)]:
    print(label, 'exact =', exact, '; lambda=0 =', s.limit(exact, go, 0))

assert s.simplify(a.subs(go, 0) - a0.subs(go, 0)/(1+k*a0.subs(go, 0))) == 0
assert s.simplify(rin.subs(go, 0) - rin0.subs(go, 0)*(1+k*a0.subs(go, 0))) == 0
assert s.simplify(rout.subs(go, 0) - rout0.subs(go, 0)/(1+k*a0.subs(go, 0))) == 0
print('The ideal DC source is AC-open. G_L = 1/(R_1+R_2), K = R_2/(R_1+R_2).')
print('At lambda=0 the closed denominator simplifies to 1+g_m*R_2.')
