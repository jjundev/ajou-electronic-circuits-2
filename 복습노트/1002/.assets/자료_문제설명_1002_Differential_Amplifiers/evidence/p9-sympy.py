import sympy as s
s.init_printing()
gm,ro,rp,R,RC,RT=s.symbols('gm ro rp R RC RT', positive=True)
vi,vo,vx,it=s.symbols('vi vo vx it',real=True)
par=lambda a,b:s.simplify(a*b/(a+b))
def show(label,x): print(label, '=',([s.simplify(v) for v in x] if isinstance(x,list) else s.simplify(x)))
def ce(load):
 sol=s.solve(vo/load+gm*vi,vo)[0];show('Av from output KCL',sol/vi)
Ic,VT,VA=s.symbols('Ic VT VA',positive=True)
g=Ic/(2*VT);tail=VA/Ic
sol=s.solve([vx/(2*tail)-g*(vi-vx),vo/RC+g*(vi-vx)],[vo,vx]);A=s.simplify(sol[vo]/vi);show('Acm',A);show('target difference',A+RC*Ic/(2*(VT+VA)));print('|Acm|<.01 iff RC Ic < .02(VA+VT). Ic is tail current, beta>>1.')
