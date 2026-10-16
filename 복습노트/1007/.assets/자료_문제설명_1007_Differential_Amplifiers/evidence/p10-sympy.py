import sympy as s
s.init_printing()
gm,ro,rp,R,RC,RT=s.symbols('gm ro rp R RC RT', positive=True)
vi,vo,vx,it=s.symbols('vi vo vx it',real=True)
par=lambda a,b:s.simplify(a*b/(a+b))
def show(label,x): print(label, '=',([s.simplify(v) for v in x] if isinstance(x,list) else s.simplify(x)))
def ce(load):
 sol=s.solve(vo/load+gm*vi,vo)[0];show('Av from output KCL',sol/vi)
VAn,VAp,VT,I=s.symbols('VAn VAp VT I',positive=True)
print('DM input gives left +gm vd/2 and right -gm vd/2. Ideal1:1 PNP mirror sums to +gm vd at right output, hence positive gain.')
A=(I/VT)*par(VAn/I,VAp/I);show('A',A);show('VAp needed',s.solve(A-100,VAp));show('at VAn5 VT26mV',s.solve(A-100,VAp)[0].subs({VAn:5,VT:.026}));print('Finite beta mirror transfer neglected in dominant model; output compliance assumed.')

# Full three node small signal model, beta infinity; matched npn and pnp gm, no tail current variation.
x,y,e,vd=s.symbols('x y e vd',real=True);gn,gp=s.symbols('gn gp',positive=True)
eq=[(gm+gp)*x+gn*(x-e)+gm*(vd/2-e),gp*y+gn*(y-e)+gm*(-vd/2-e)+gm*x,gn*(2*e-x-y)+2*gm*e]
sol=s.solve(eq,[x,y,e]);gain=s.factor(sol[y]/vd);target=gm*(2*gm+gp)/(2*(gm+gp)*(gn+gp));show('exact3node gain',gain);show('rootformula residual',s.simplify(gain-target));show('large intrinsic-gain correction',s.limit(gain/(gm/(gn+gp)),gm,s.oo))
