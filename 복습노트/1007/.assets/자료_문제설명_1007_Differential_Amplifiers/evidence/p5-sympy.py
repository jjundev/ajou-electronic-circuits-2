import sympy as s
s.init_printing()
gm,ro,rp,R,RC,RT=s.symbols('gm ro rp R RC RT', positive=True)
vi,vo,vx,it=s.symbols('vi vo vx it',real=True)
par=lambda a,b:s.simplify(a*b/(a+b))
def show(label,x): print(label, '=',([s.simplify(v) for v in x] if isinstance(x,list) else s.simplify(x)))
def ce(load):
 sol=s.solve(vo/load+gm*vi,vo)[0];show('Av from output KCL',sol/vi)
I=.001;g=s.sqrt(2*100e-6*500*I);gn=s.sqrt(2*100e-6*1000*.002);r=10000;rt=5000;tail=gn*rt*rt;load=par(r,r)
show('gm1',g);show('tail Rout',tail);show('Acm dominant',-r/(2*tail));show('AcmDM deltaR50',50/(2*tail));show('DM gain',-g*load);show('CMRR',g*load/(50/(2*tail)));show('CMRRdB',20*s.log(g*load/(50/(2*tail)),10))
