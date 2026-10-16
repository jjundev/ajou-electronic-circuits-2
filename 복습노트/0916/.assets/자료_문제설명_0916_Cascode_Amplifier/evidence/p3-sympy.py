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
ee=s.solve([s.Eq(x/r1+(x-v)/rp+(x-y)/r2-g*(v-x),0),s.Eq((y-x)/r2+g*(v-x),0)],[x,y]);print('Av exact',s.factor(ee[y]/v));xs=s.solve(s.Eq(x/r1+(x-v)/rp+x/r2-g*(v-x),0),x)[0];G=s.factor((g*(v-xs)-xs/r2)/v);print('Gm exact',G,'gm large Gm',s.limit(G,g,s.oo));print('Av approx',-g*r2*rp/(r1+rp))

t=s.symbols("t",positive=True)
print("MOS exact/dominant gm scaled limit",s.limit(Rmos.subs(g,t*g)/(t*g*r1*r2),t,s.oo))
print("BJT R exact/dominant gm scaled limit",s.limit(Rbjt.subs(g,t*g)/(t*g*r2*r1*rp/(r1+rp)),t,s.oo))
print("BJT Av exact/dominant gm scaled limit",s.limit(Abjt.subs(g,t*g)/(-t**2*g**2*r2*r1*rp/(r1+rp)),t,s.oo))

# Verify explicitly both exact expressions and the independent lower-driven contrast.
G1,go,gpi=s.symbols('G1 go gpi',positive=True)
G_target=(g*G1-go*gpi)/(G1+go+gpi+g)
assert s.simplify(G-G_target.subs({G1:1/r1,go:1/r2,gpi:1/rp}))==0
print('short exact matches conductance KCL target=0')
A_target=(r1-g*r2*rp)/(r1+rp);assert s.simplify(ee[y]/v-A_target)==0
print('open exact equals independently derived voltage formula')
print('finite-beta large-gmro example upper driven gain',s.N(A_target.subs({g:s.Rational(1,26),r1:5000,r2:5000,rp:2600})))
