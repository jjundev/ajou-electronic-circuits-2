# Independent check X9.06: R_P that halves Rout (Fig 9.11)
import sympy as sp
gm,ro,RP,x=sp.symbols('g_m r_O R_P x',positive=True)
Rp=ro*RP/(ro+RP)
Rexact=lambda R1: (1+gm*R1)*ro+R1
# approximate model Rout ~ gm rO2 (rO1||RP), rO1=rO2=rO
sa=sp.solve(sp.Eq(gm*ro*Rp, gm*ro*ro/2),RP); print('approx: RP =',sa)
se=sp.solve(sp.Eq(Rexact(Rp), Rexact(ro)/2),RP); print('exact: RP =',[sp.simplify(s) for s in se])
print('exact RP/rO with gm=x/rO, x->oo:',sp.limit(sp.simplify(se[0]/ro).subs(gm,x/ro),x,sp.oo))
