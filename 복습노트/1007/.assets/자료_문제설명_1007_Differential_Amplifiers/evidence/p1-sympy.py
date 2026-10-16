import sympy as s
s.init_printing()
gm,ro,rp,R,RC,RT=s.symbols('gm ro rp R RC RT', positive=True)
vi,vo,vx,it=s.symbols('vi vo vx it',real=True)
par=lambda a,b:s.simplify(a*b/(a+b))
def show(label,x): print(label, '=',([s.simplify(v) for v in x] if isinstance(x,list) else s.simplify(x)))
def ce(load):
 sol=s.solve(vo/load+gm*vi,vo)[0];show('Av from output KCL',sol/vi)
Iss,Vov,lam=s.symbols('Iss Vov lam',positive=True)
g=Iss/Vov;tail=1/(lam*Iss)
sol=s.solve([vx/(2*tail)-g*(vi-vx),vo/R+g*(vi-vx)],[vo,vx]);A=s.simplify(sol[vo]/vi);show('Acm',A);show('claimed proof residual',A+R*Iss/(2/lam+Vov));show('lambda0',s.limit(A,lam,0))
