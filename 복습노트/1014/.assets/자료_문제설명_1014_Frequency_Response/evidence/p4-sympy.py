import sympy as s
s.init_printing()
gm,ro,rp,R,RC,RT=s.symbols('gm ro rp R RC RT', positive=True)
vi,vo,vx,it=s.symbols('vi vo vx it',real=True)
par=lambda a,b:s.simplify(a*b/(a+b))
def show(label,x): print(label, '=',([s.simplify(v) for v in x] if isinstance(x,list) else s.simplify(x)))
def ce(load):
 sol=s.solve(vo/load+gm*vi,vo)[0];show('Av from output KCL',sol/vi)
VT=s.symbols('VT',positive=True);f=1e9;C=2e-12;Ic=.002/2.5;Rc=1/(2*s.pi*f*C);A=Ic/VT*Rc;show('Imax',Ic);show('Rmax',Rc);show('Avmax magnitude',A);show('at VT26mV',A.subs(VT,.026));show('at VT25mV',A.subs(VT,.025))
