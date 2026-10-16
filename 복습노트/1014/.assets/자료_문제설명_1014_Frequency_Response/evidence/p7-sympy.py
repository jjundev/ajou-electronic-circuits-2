import sympy as s
s.init_printing()
gm,ro,rp,R,RC,RT=s.symbols('gm ro rp R RC RT', positive=True)
vi,vo,vx,it=s.symbols('vi vo vx it',real=True)
par=lambda a,b:s.simplify(a*b/(a+b))
def show(label,x): print(label, '=',([s.simplify(v) for v in x] if isinstance(x,list) else s.simplify(x)))
def ce(load):
 sol=s.solve(vo/load+gm*vi,vo)[0];show('Av from output KCL',sol/vi)
z,Ci,Cl,Rs=s.symbols('s Ci Cl Rs',positive=True);v=s.symbols('v');sol=s.solve([(v-vi)/Rs+z*Ci*v,vo/R+z*Cl*vo+gm*v],[v,vo]);show('H',sol[vo]/vi);print('poles=-1/(RsCi),-1/(RDCL); MOS gate draws no current, unilateral lambda0 model.')
