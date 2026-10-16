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
out=s.Rational(18,10)-s.Rational(1,1000)*500;ov=s.sqrt(2*s.Rational(1,1000)/(s.Rational(1,10000)*s.Rational(20,1)/s.Rational(18,100)));print('Vb1max',out+s.Rational(2,5),'VX',s.N(out-ov))

t=s.symbols("t",positive=True)
print("MOS exact/dominant gm scaled limit",s.limit(Rmos.subs(g,t*g)/(t*g*r1*r2),t,s.oo))
print("BJT R exact/dominant gm scaled limit",s.limit(Rbjt.subs(g,t*g)/(t*g*r2*r1*rp/(r1+rp)),t,s.oo))
print("BJT Av exact/dominant gm scaled limit",s.limit(Abjt.subs(g,t*g)/(-t**2*g**2*r2*r1*rp/(r1+rp)),t,s.oo))
