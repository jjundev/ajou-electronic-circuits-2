# Independent check E9.06 (Fig 9.11): R_P across D-S of M1
import sympy as sp
gm,ro1,ro2,RP,ix,vs,vx=sp.symbols('g_m1 r_O1 r_O2 R_P i_x v_s v_x',positive=True)
# KCL: current through M2 (r_O2): ix = vs/ro2 ; at output node: ix = gm*vgs1 + (vx-vs)/ro1 + (vx-vs)/RP, vgs1 = -vs
sol=sp.solve([sp.Eq(ix,vs/ro2),sp.Eq(ix,-gm*vs+(vx-vs)/ro1+(vx-vs)/RP)],[vs,vx],dict=True)[0]
Rout=sp.simplify(sol[vx]/ix)
Rp=ro1*RP/(ro1+RP); target=(1+gm*Rp)*ro2+Rp
print('Rout =',sp.factor(Rout)); print('simplify(Rout - [(1+gm(rO1||RP))rO2 + rO1||RP]) =',sp.simplify(Rout-target))
print('RP->oo limit:',sp.simplify(sp.limit(Rout,RP,sp.oo)))
x=sp.Symbol('x',positive=True)
print('ratio Rout/(gm rO2 (rO1||RP)) with gm=x/ro2, x->oo:',sp.limit(sp.simplify((Rout/(gm*ro2*Rp)).subs(gm,x/ro2)),x,sp.oo))
