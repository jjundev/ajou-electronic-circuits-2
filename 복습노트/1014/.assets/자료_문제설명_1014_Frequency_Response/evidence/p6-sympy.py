import sympy as s
s.init_printing()
gm,ro,rp,R,RC,RT=s.symbols('gm ro rp R RC RT', positive=True)
vi,vo,vx,it=s.symbols('vi vo vx it',real=True)
par=lambda a,b:s.simplify(a*b/(a+b))
def show(label,x): print(label, '=',([s.simplify(v) for v in x] if isinstance(x,list) else s.simplify(x)))
def ce(load):
 sol=s.solve(vo/load+gm*vi,vo)[0];show('Av from output KCL',sol/vi)
z,C=s.symbols('s C');x=s.symbols('x');sol=s.solve([x/R+z*C*x+gm*vi,vo/R+z*C*vo+gm*x],[x,vo]);show('H',sol[vo]/vi);show('double pole',-1/(R*C));print('DC magnitude(gmR)^2, initial0dB/dec then-40dB/dec at common pole; exact magnitude at pole is halfDC=-6.0206dB.')
