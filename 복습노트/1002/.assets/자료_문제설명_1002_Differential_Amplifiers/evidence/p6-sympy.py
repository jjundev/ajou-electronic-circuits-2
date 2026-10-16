import sympy as s
s.init_printing()
gm,ro,rp,R,RC,RT=s.symbols('gm ro rp R RC RT', positive=True)
vi,vo,vx,it=s.symbols('vi vo vx it',real=True)
par=lambda a,b:s.simplify(a*b/(a+b))
def show(label,x): print(label, '=',([s.simplify(v) for v in x] if isinstance(x,list) else s.simplify(x)))
def ce(load):
 sol=s.solve(vo/load+gm*vi,vo)[0];show('Av from output KCL',sol/vi)
K=s.symbols('K',positive=True)
I=.0005;gn=s.sqrt(2*100e-6*K*I);gp=s.sqrt(2*50e-6*K*I);rn=1/(.1*I);rpp=1/(.2*I)
Rn=gn*rn**2;Rp=gp*rpp**2;A=gn*par(Rn,Rp)
show('gain(K)',A);show('K for gain200',s.solve(A-200,K));print('Both cascode branch resistances use dominant gmro^2 terms; same K does not mean same gm.')

K=s.symbols('K',positive=True)
I=s.Rational(1,2000);gn=s.sqrt(2*s.Rational(1,10000)*K*I);gp=gn/s.sqrt(2);rn=20000;rpp=10000;Lp=gp*rpp*rpp+2*rpp
u,y,z=s.symbols('u y z',real=True)
sol=s.solve([z/rn+(z-y)/rn+gn*z+gn*u,y/Lp+(y-z)/rn-gn*z],[z,y]);Ag=s.simplify(-sol[y]/u)
show('exact gain full KCL',Ag)
show('exact K',s.nsolve(Ag-200,K,30))
