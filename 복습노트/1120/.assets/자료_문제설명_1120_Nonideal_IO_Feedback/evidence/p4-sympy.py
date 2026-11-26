import sympy as s
rp, R1, R2, RC, beta = s.symbols('r_pi R_1 R_2 R_C beta', positive=True)
vin, vo, vb, it = s.symbols('v_in v_o v_b i_test')
K = R2/(R1+R2)
Rth = R1*R2/(R1+R2)
RL = 1/(1/RC+1/(R1+R2))
gm = beta/rp
# VE=vin, VA=infinity. KCL at base and collector with both divider legs.
ib = (vb-vin)/rp
sol = s.solve([(vb-vo)/R1+vb/R2+ib, vo/RC+(vo-vb)/R1+gm*rp*ib-it],
              (vb,vo), simplify=False)
i_in = -(beta+1)*ib.subs(vb,sol[vb])
closed = (sol[vo].diff(vin), vin/i_in.subs(it,0), sol[vo].diff(it))
# Short output for first-port feedback loading. Open first port for second-port loading.
a0 = beta*RL/(rp+Rth)
rin0 = (rp+Rth)/(beta+1)
exact_a0 = (beta+K)*RL/(rp+Rth)
T = K*a0
Texact = K*exact_a0
exact = (exact_a0/(1+Texact), rin0*(1+Texact), RL/(1+Texact))
replica = (a0/(1+T), rin0*(1+T), RL/(1+T))
for label, full, expected, usual in zip(('Acl', 'Rin', 'Rout'),closed,exact,replica):
    assert s.factor(full-expected) == 0
    assert s.factor(s.limit(s.factor(expected/usual),beta,s.oo)-1) == 0
for label, sign in [('A0 replica', 'beta*R_L/(r_pi+Rth)'),
                    ('effective A0 full KCL', '(beta+K)*R_L/(r_pi+Rth)'),
                    ('Rin0', '(r_pi+Rth)/(beta+1)'),
                    ('Rout0', 'R_L'),
                    ('Acl', 'A0/(1+K*A0)'),
                    ('Rin', 'Rin0*(1+K*A0)'),
                    ('Rout', 'Rout0/(1+K*A0)')]:
    print(label, '=', sign)
print('Rth=R1||R2; R_L=RC||(R1+R2); K=R2/(R1+R2)')
print('The finite beta exact forward term adds +K from the base-current path through R1.')
print('All exact/replica ratios tend to 1 for beta -> infinity.')
