# Independent check P9.14 (Fig 9.50): cascode current source design
import sympy as sp
Vov1,Vov2,vx,vs,ix,gm,ro1,ro2 = sp.symbols('Vov1 Vov2 v_x v_s i_x g_m r_o1 r_o2', positive=True)
k=sp.Rational(100,10**6); I=sp.Rational(5,10000); VTH=sp.Rational(2,5)
W1=sp.Rational(30)/sp.Rational(18,100); W2=sp.Rational(20)/sp.Rational(18,100)
# (a) square law, lambda=0
s2=sp.solve(sp.Eq(I, k/2*W2*Vov2**2),Vov2)[0]; s1=sp.solve(sp.Eq(I, k/2*W1*Vov1**2),Vov1)[0]
Vb2=VTH+s2; Vb1min=s2+VTH+s1   # V_X >= Vov2 and V_X = Vb1 - VTH - Vov1
print('(a) Vov2 =',s2,'Vb2 =',Vb2,'=',float(Vb2),'V')
print('    Vov1 =',s1,'=',float(s1),' Vb1,min = Vov2+VTH+Vov1 =',sp.nsimplify(Vb1min),'=',float(Vb1min),'V')
# (b) small-signal: test voltage v_x at drain of M1, source node v_s, gate of M1 AC ground, M2 -> r_o2
eqs=[sp.Eq(ix, vs/ro2), sp.Eq(ix, gm*(0-vs)+(vx-vs)/ro1)]
sol=sp.solve(eqs,[vs,vx],dict=True)[0]; Rout=sp.simplify(sol[vx]/ix)
target=(1+gm*ro1)*ro2+ro1
print('(b) Rout symbolic =',sp.factor(Rout),' simplify(Rout-target) =',sp.simplify(Rout-target))
print('    limit Rout/(gm ro1 ro2), ro->oo:',sp.limit((Rout/(gm*ro1*ro2)).subs({ro1:sp.Symbol('r'),ro2:sp.Symbol('r')}),sp.Symbol('r'),sp.oo))
lam=sp.Rational(1,10); ro=1/(lam*I); gm1=2*I/s1
val=Rout.subs({gm:gm1,ro1:ro,ro2:ro})
print('    gm1 =',float(gm1),'S, ro =',float(ro),'ohm, gm1*ro =',float(gm1*ro))
print('    Rout exact =',float(val),'ohm ; approx gm1 ro1 ro2 =',float(gm1*ro*ro),'ohm')
