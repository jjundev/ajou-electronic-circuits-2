import sympy as s
s.init_printing()
gm,ro,rp,R,RC,RT=s.symbols('gm ro rp R RC RT', positive=True)
vi,vo,vx,it=s.symbols('vi vo vx it',real=True)
par=lambda a,b:s.simplify(a*b/(a+b))
def show(label,x): print(label, '=',([s.simplify(v) for v in x] if isinstance(x,list) else s.simplify(x)))
def ce(load):
 sol=s.solve(vo/load+gm*vi,vo)[0];show('Av from output KCL',sol/vi)
rn,rpp,tail=s.symbols('ron rop tail',positive=True)
# Full CM: output shunt rop, channel ron between source/output, gm(vin-vs).
sol=s.solve([vo/rpp+(vo-vx)/rn+gm*(vi-vx),vx/(2*tail)+(vx-vo)/rn-gm*(vi-vx)],[vo,vx]);A=s.factor(sol[vo]/vi);show('Acm exact',A);show('large tail coefficient',s.limit(A*tail,tail,s.oo));print('gmro>>1 plus tail dominant -> Acm~-rop/(2rtail).')
