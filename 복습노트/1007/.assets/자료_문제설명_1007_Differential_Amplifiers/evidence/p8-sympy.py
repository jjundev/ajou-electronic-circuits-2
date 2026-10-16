import sympy as s
s.init_printing()
gm,ro,rp,R,RC,RT=s.symbols('gm ro rp R RC RT', positive=True)
vi,vo,vx,it=s.symbols('vi vo vx it',real=True)
par=lambda a,b:s.simplify(a*b/(a+b))
def show(label,x): print(label, '=',([s.simplify(v) for v in x] if isinstance(x,list) else s.simplify(x)))
def ce(load):
 sol=s.solve(vo/load+gm*vi,vo)[0];show('Av from output KCL',sol/vi)
I=.0005;g=s.sqrt(2*100e-6*1000*I);ov=s.sqrt(2*I/(100e-6*1000));ov3=s.sqrt(2*.001/(100e-6*2000));r3=1/(.1*.001)
show('Vov1',ov);show('Vcm min',.4+ov+ov3);show('Vcm max matched load',1.8-I*1000+.4);show('Vcm max all branches',1.8-I*1020+.4);show('Acm',-1000/(1/g+2*r3));show('AcmDM',20/(1/g+2*r3));show('CMRR small mismatch',g*1000*(1/g+2*r3)/20);show('CMRR dB',20*s.log(g*1000*(1/g+2*r3)/20,10));print('ro1 ignored consistent dominant gmro assumption.')
