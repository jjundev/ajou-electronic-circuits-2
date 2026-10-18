# Independent check E9.05: design NMOS cascode, Rout=500k, I=0.5mA, M1=M2
import sympy as sp
gm,ro,ix,vs,vx,WL=sp.symbols('g_m r_o i_x v_s v_x WL',positive=True)
sol=sp.solve([sp.Eq(ix,vs/ro),sp.Eq(ix,-gm*vs+(vx-vs)/ro)],[vs,vx],dict=True)[0]
Rout=sp.simplify(sol[vx]/ix); print('Rout =',sp.expand(Rout),' diff vs (1+gm ro)ro+ro:',sp.simplify(Rout-((1+gm*ro)*ro+ro)))
k=sp.Rational(1,10**4); I=sp.Rational(5,10**4); lam=sp.Rational(1,10); R=500000
r=1/(lam*I); print('ro =',r)
gma=sp.solve(sp.Eq(gm*r*r,R),gm)[0]; gme=sp.solve(sp.Eq(Rout.subs(ro,r),R),gm)[0]
f=lambda g: sp.solve(sp.Eq(g,sp.sqrt(2*k*WL*I)),WL)[0]
print('approx Rout~gm ro^2: gm =',gma,'=',float(gma),'S, W/L =',f(gma),'=',float(f(gma)))
print('exact: gm =',gme,'=',float(gme),'S, W/L =',f(gme),'=',float(f(gme)))
print('gm*ro (approx) =',float(gma*r),' ratio exact/approx W/L =',float(f(gme)/f(gma)))
x=sp.Symbol('x',positive=True); print('limit Rout/(gm ro^2) as gm ro=x->oo:',sp.limit(((1+x)*ro+ro)/(x*ro),x,sp.oo))
