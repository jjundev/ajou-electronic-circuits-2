import sympy as s
s.init_printing()
gm,ro,rp,R,RC,RT=s.symbols('gm ro rp R RC RT', positive=True)
vi,vo,vx,it=s.symbols('vi vo vx it',real=True)
par=lambda a,b:s.simplify(a*b/(a+b))
def show(label,x): print(label, '=',([s.simplify(v) for v in x] if isinstance(x,list) else s.simplify(x)))
def ce(load):
 sol=s.solve(vo/load+gm*vi,vo)[0];show('Av from output KCL',sol/vi)
z,Ci,Cl,Rs,RP=s.symbols('s Ci Cl Rs RP',positive=True);v,u=s.symbols('v u');sol=s.solve([(v-vi)/Rs+z*Ci*v+(v-u)/RP,(u-v)/RP+gm*u,vo/R+z*Cl*vo-gm*u],[v,u,vo]);show('H',sol[vo]/vi);show('input pole',-(1/Rs+1/(RP+1/gm))/Ci);show('output pole',-1/(R*Cl));print('RP=0 recovers common-gate input1/gm; RP->infty makes input pole1/RsCi.')
