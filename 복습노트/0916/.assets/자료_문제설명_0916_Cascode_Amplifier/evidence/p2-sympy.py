import sympy as s
s.init_printing()
g,r1,r2,Rp,i,v,x,y,rp,b,VT,I,VA,kn,kp,N=s.symbols('g r1 r2 Rp i v x y rp b VT I VA kn kp N', positive=True)
i,v,x,y=s.symbols('i v x y', real=True)
# MOS cascode output test: bottom ro=r2, top gm=g,ro=r1; top gate grounded.
mos=s.solve([s.Eq(i,x/r2),s.Eq(i,(y-x)/r1-g*x)],[x,y]);Rmos=s.factor(mos[y]/i)
# BJT top base grounded: lower ro=r1, upper ro=r2,rpi=rp.
bjt=s.solve([s.Eq(i,x/r1+x/rp),s.Eq(i,(y-x)/r2-g*x)],[x,y]);Rbjt=s.factor(bjt[y]/i)
# Lower-driven BJT exact open output KCL.
amp=s.solve([s.Eq(x/r1+x/rp+(x-y)/r2+g*x+g*v,0),s.Eq((y-x)/r2-g*x,0)],[x,y]);Abjt=s.factor(amp[y]/v)
print('MOS output KCL:',Rmos,'; BJT output KCL:',Rbjt,'; BJT voltage gain:',Abjt)
an,ap,ln,lp=s.symbols('an ap ln lp',positive=True);gn=s.sqrt(2*an*I);gp=s.sqrt(2*ap*I);rn=gn/(ln*I)**2;rr=gp/(lp*I)**2;A=s.factor(-gn*rn*rr/(rn+rr));print('Av',A,'slope',s.simplify(s.diff(A,I)*I/A))

t=s.symbols("t",positive=True)
print("MOS exact/dominant gm scaled limit",s.limit(Rmos.subs(g,t*g)/(t*g*r1*r2),t,s.oo))
print("BJT R exact/dominant gm scaled limit",s.limit(Rbjt.subs(g,t*g)/(t*g*r2*r1*rp/(r1+rp)),t,s.oo))
print("BJT Av exact/dominant gm scaled limit",s.limit(Abjt.subs(g,t*g)/(-t**2*g**2*r2*r1*rp/(r1+rp)),t,s.oo))

an1,an2,ap3,lam=s.symbols('an1 an2 ap3 lam',positive=True)
g1=s.sqrt(2*an1*I);g2=s.sqrt(2*an2*I);g3=s.sqrt(2*ap3*I);rr=1/(lam*I)
A_general=s.factor(-g1*(g2*rr**2)*(g3*rr**2)/(g2*rr**2+g3*rr**2))
target=-s.sqrt(2*an1)/(lam**2*I)*s.sqrt(2*an2)*s.sqrt(2*ap3)/(s.sqrt(2*an2)+s.sqrt(2*ap3))
print('arbitrary device widths Av',A_general,'difference',s.simplify(A_general-target))
assert s.simplify(A_general-target)==0
