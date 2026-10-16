import sympy as s
s.init_printing()
gm,ro,rp,R,RC,RT=s.symbols('gm ro rp R RC RT', positive=True)
vi,vo,vx,it=s.symbols('vi vo vx it',real=True)
par=lambda a,b:s.simplify(a*b/(a+b))
def show(label,x): print(label, '=',([s.simplify(v) for v in x] if isinstance(x,list) else s.simplify(x)))
def ce(load):
 sol=s.solve(vo/load+gm*vi,vo)[0];show('Av from output KCL',sol/vi)
z,C=s.symbols('s C');sol=s.solve(vo/R+z*C*vo+gm*vi,vo)[0];show('H',sol/vi);show('pole',s.solve(1+z*R*C,z));print('Magnitude gmR/sqrt(1+(wRC)^2); phase -180deg-atan(wRC) modulo360; high slope-20dB/dec.')
