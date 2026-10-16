import sympy as s
s.init_printing()
gm,ro,rp,R,RC,RT=s.symbols('gm ro rp R RC RT', positive=True)
vi,vo,vx,it=s.symbols('vi vo vx it',real=True)
par=lambda a,b:s.simplify(a*b/(a+b))
def show(label,x): print(label, '=',([s.simplify(v) for v in x] if isinstance(x,list) else s.simplify(x)))
def ce(load):
 sol=s.solve(vo/load+gm*vi,vo)[0];show('Av from output KCL',sol/vi)
I,k,lam=s.symbols('I k lam',positive=True)
g=s.sqrt(2*k*I);r=1/(lam*I);A=g*g*r*r
sol=s.solve(A-300,I)[0];show('branch current',sol);show('tail current',2*sol.subs({k:100e-6*20/.18,lam:.1}))
print('Dominant cascode model gmro>>1.')

x=s.symbols('x',positive=True)
root=s.solve(x*(x+1)-300,x)[0]
show('exact gmro',root)
show('exact Iss',4*(100e-6*20/.18)/(.1**2*root**2))
