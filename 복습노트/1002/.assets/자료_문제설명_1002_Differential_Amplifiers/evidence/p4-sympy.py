import sympy as s
s.init_printing()
gm,ro,rp,R,RC,RT=s.symbols('gm ro rp R RC RT', positive=True)
vi,vo,vx,it=s.symbols('vi vo vx it',real=True)
par=lambda a,b:s.simplify(a*b/(a+b))
def show(label,x): print(label, '=',([s.simplify(v) for v in x] if isinstance(x,list) else s.simplify(x)))
def ce(load):
 sol=s.solve(vo/load+gm*vi,vo)[0];show('Av from output KCL',sol/vi)
VT=s.symbols('VT',positive=True)
I=s.Rational(1,2000);r=4/I;load=par(10000,par(r,r));A=-I/VT*load
show('Av(VT)',A);show('Av VT=26mV',A.subs(VT,.026));show('Av VT=25mV',A.subs(VT,.025))
