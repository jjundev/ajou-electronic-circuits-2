import sympy as s
s.init_printing()
gm,ro,rp,R,RC,RT=s.symbols('gm ro rp R RC RT', positive=True)
vi,vo,vx,it=s.symbols('vi vo vx it',real=True)
par=lambda a,b:s.simplify(a*b/(a+b))
def show(label,x): print(label, '=',([s.simplify(v) for v in x] if isinstance(x,list) else s.simplify(x)))
def ce(load):
 sol=s.solve(vo/load+gm*vi,vo)[0];show('Av from output KCL',sol/vi)
x,b=s.symbols('x beta',positive=True)
A=x*x*b/(b+x);show('A(x,beta)',A);roots=s.solve(A.subs(b,100)-4000,x);show('x roots',roots);show('VA VT26mV',roots[-1]*.026);print('Dominant cascode gain gm^2 ro (ro||rpi); finite beta retained.')

# Exact hybrid-pi model, upper base fixed, lower emitter grounded. Lower input base current does not change imposed vin.
y,z,u=s.symbols('y z u',real=True)
sol=s.solve([z/ro+z/rp+(z-y)/ro+gm*z+gm*u,(y-z)/ro-gm*z],[y,z]);A=s.simplify(-sol[y]/u)
show('exact magnitude from2KCL',A)
X,B=s.symbols('X B',positive=True)
Ae=s.simplify(A.subs({ro:X/gm,rp:B/gm}));show('exact in X beta',Ae);show('exact over main',s.simplify(Ae/(X**2*B/(X+B))));show('asymptotic ratio',s.limit(Ae/(X**2*B/(X+B)),X,s.oo))
