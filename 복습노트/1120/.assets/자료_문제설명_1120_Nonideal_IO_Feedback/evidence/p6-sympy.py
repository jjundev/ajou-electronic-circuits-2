import sympy as s

n, p, gn, gp, GL, K = s.symbols('gm_n gm_p go_n go_p G_L K', positive=True)
x, vs, vo, it, v1, v2 = s.symbols('x vs vo i_test v1 v2')
id1 = n*(v1-vs)+gn*(x-vs)
id2 = n*(v2-vs)+gn*(vo-vs)
# Ideal tail source, matched diff pair and matched mirror.
kcl = [id1+id2, id1+(p+gp)*x, id2+p*x+(gp+GL)*vo-it]
sol = s.solve(kcl,(vs,x,vo),simplify=False)
G = n*(gp+2*p)/(gn+2*gp+2*p)
gout = 2*(gn+gp)*(gp+p)/(gn+2*gp+2*p)
loaded_ro = 1/(gout+GL)
assert s.factor(sol[vo]-(G*(v1-v2)+it)*loaded_ro) == 0
assert s.limit(s.factor(G/n),p,s.oo) == 1
assert s.limit(s.factor(gout/(gn+gp)),p,s.oo) == 1
assert s.factor(s.solve(vo-sol[vo].subs(v2,K*vo),vo)[0]-
                (G*v1+it)*loaded_ro/(1+K*G*loaded_ro)) == 0
print('Rsum=R1+R2; G_L=1/Rsum; K=R2/Rsum.')
print('Open: Gm_eff =', s.factor(G))
print('Open amplifier g_o_eff before external load =', s.factor(gout))
print('Rout0=1/(g_o_eff+1/Rsum); A0=Gm_eff*Rout0; Rin0=infinity.')
print('Closed (exact): A0/(1+K*A0); Rin=infinity; Rout0/(1+K*A0).')
print('For gm_p >> go_p,go_n, Gm_eff -> gm_n.')
print('In the same limit, g_o_eff -> go_n+go_p and Rout0 -> ro_n||ro_p||Rsum.')
