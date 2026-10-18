# Independent check X9.05: E9.05 cascode with W/L=32
import sympy as sp
gm,ro,ix,vs,vx=sp.symbols('g_m r_o i_x v_s v_x',positive=True)
sol=sp.solve([sp.Eq(ix,vs/ro),sp.Eq(ix,-gm*vs+(vx-vs)/ro)],[vs,vx],dict=True)[0]
Rout=sp.simplify(sol[vx]/ix); print('Rout =',sp.expand(Rout),' diff:',sp.simplify(Rout-((1+gm*ro)*ro+ro)))
k=sp.Rational(1,10**4); I=sp.Rational(5,10**4); lam=sp.Rational(1,10)
g=sp.sqrt(2*k*32*I); r=1/(lam*I)
print('gm =',g,'=',float(g),'S ; ro =',r,'; gm ro =',float(g*r))
print('Rout exact =',float(Rout.subs({gm:g,ro:r})),'ohm ; approx gm ro^2 =',float(g*r*r),'ohm')
