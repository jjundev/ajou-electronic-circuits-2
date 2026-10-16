import sympy as s
s.init_printing()
gm,ro,rp,R,RC,RT=s.symbols('gm ro rp R RC RT', positive=True)
vi,vo,vx,it=s.symbols('vi vo vx it',real=True)
par=lambda a,b:s.simplify(a*b/(a+b))
def show(label,x): print(label, '=',([s.simplify(v) for v in x] if isinstance(x,list) else s.simplify(x)))
def ce(load):
 sol=s.solve(vo/load+gm*vi,vo)[0];show('Av from output KCL',sol/vi)
Ci,Cl,Rs=s.symbols('Ci Cl Rs',positive=True);RD=s.solve(1/(R*Cl)-10*(1/Rs+gm)/Ci,R)[0];show('RD',RD);show('ratio check',s.simplify((1/(RD*Cl))/((1/Rs+gm)/Ci)))
