import sympy as s
s.init_printing()
gm,ro,rp,R,RC,RT=s.symbols('gm ro rp R RC RT', positive=True)
vi,vo,vx,it=s.symbols('vi vo vx it',real=True)
par=lambda a,b:s.simplify(a*b/(a+b))
def show(label,x): print(label, '=',([s.simplify(v) for v in x] if isinstance(x,list) else s.simplify(x)))
def ce(load):
 sol=s.solve(vo/load+gm*vi,vo)[0];show('Av from output KCL',sol/vi)
dR,r3,r4,g3=s.symbols('dR r3 r4 g3',positive=True)
C=lambda T:gm*(R+dR/2)*(1/gm+2*T)/dR
show('a CMRR',C(r3));show('b CMRR',C(r3+r4+g3*r3*r4));show('improvement ratio',s.simplify(C(r3+r4+g3*r3*r4)/C(r3)));print('For small dR and gm ro>>1: a~2gm RD rO3/dR, b~2gm RD gm3 rO3rO4/dR.')
