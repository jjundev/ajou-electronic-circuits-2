import sympy as s
s.init_printing()
gm,ro,rp,R,RC,RT=s.symbols('gm ro rp R RC RT', positive=True)
vi,vo,vx,it=s.symbols('vi vo vx it',real=True)
par=lambda a,b:s.simplify(a*b/(a+b))
def show(label,x): print(label, '=',([s.simplify(v) for v in x] if isinstance(x,list) else s.simplify(x)))
def ce(load):
 sol=s.solve(vo/load+gm*vi,vo)[0];show('Av from output KCL',sol/vi)
dR,T=s.symbols('dR T',positive=True)
Adm=-gm*(RC+dR/2);Aconv=dR/(1/gm+2*T);show('CMRR exact load imbalance',s.Abs(Adm/Aconv));show('small mismatch',gm*RC*(1/gm+2*T)/dR);print('T is emitter-degenerated Q3 output resistance rO3+(1+gm3 rO3)(R1||rpi3).')
