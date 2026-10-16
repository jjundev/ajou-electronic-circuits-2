import sympy as s
W,I,mu,L=s.symbols('W I mu L',positive=True)
gm=s.sqrt(2*mu*(W/L)*I)
ratio=s.simplify(s.sqrt(2*mu*(W/2/L)*(I/2))/gm)
gmnew=s.Rational(1,200)*ratio
Ri=s.Integer(100000); fl=s.Integer(20); fh=s.Integer(20000)
Ci=1/(2*s.pi*Ri*fl); CL=gmnew/(2*s.pi*fh)
print('gm ratio, new gm:',ratio,gmnew)
print('Ci min:',Ci,'F =',s.N(Ci*10**9,9),'nF')
print('CL max:',CL,'F =',s.N(CL*10**9,9),'nF')
assert ratio==s.Rational(1,2)
