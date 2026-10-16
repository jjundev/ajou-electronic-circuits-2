import sympy as s
s.init_printing()
gm,ro,rp,R,RC,RT=s.symbols('gm ro rp R RC RT', positive=True)
vi,vo,vx,it=s.symbols('vi vo vx it',real=True)
par=lambda a,b:s.simplify(a*b/(a+b))
def show(label,x): print(label, '=',([s.simplify(v) for v in x] if isinstance(x,list) else s.simplify(x)))
def ce(load):
 sol=s.solve(vo/load+gm*vi,vo)[0];show('Av from output KCL',sol/vi)
sol=s.solve([vx/(2*RT)-gm*(vi-vx),vo/RC+gm*(vi-vx)],[vo,vx]);A=s.simplify(sol[vo]/vi);show('Acm',A);show('REE parallel equivalence',par(2*RT,2*RT)-RT);show('ideal tail limit',s.limit(A,RT,s.oo));print('Each common-mode half circuit has2REE, yielding -gmRC/(1+2gmREE); beta>>1.')
