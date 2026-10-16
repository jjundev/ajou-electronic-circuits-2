import sympy as s
s.init_printing()
gm,ro,rp,R,RC,RT=s.symbols('gm ro rp R RC RT', positive=True)
vi,vo,vx,it=s.symbols('vi vo vx it',real=True)
par=lambda a,b:s.simplify(a*b/(a+b))
def show(label,x): print(label, '=',([s.simplify(v) for v in x] if isinstance(x,list) else s.simplify(x)))
def ce(load):
 sol=s.solve(vo/load+gm*vi,vo)[0];show('Av from output KCL',sol/vi)
w=s.symbols('w',positive=True);sol=s.solve(1/(1+(w*1000*1e-12)**2)-.9**2,w)[0];show('omega',sol);show('frequencyHz',sol/(2*s.pi));show('dropdB',20*s.log(.9,10))
