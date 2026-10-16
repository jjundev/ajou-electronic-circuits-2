import sympy as s
s.init_printing()
gm,ro,rp,R,RC,RT=s.symbols('gm ro rp R RC RT', positive=True)
vi,vo,vx,it=s.symbols('vi vo vx it',real=True)
par=lambda a,b:s.simplify(a*b/(a+b))
def show(label,x): print(label, '=',([s.simplify(v) for v in x] if isinstance(x,list) else s.simplify(x)))
def ce(load):
 sol=s.solve(vo/load+gm*vi,vo)[0];show('Av from output KCL',sol/vi)
I0,dI,RL=s.symbols('I0 dI RL',positive=True)
k=s.symbols('k',positive=True)
V=(k*(I0+dI)-(I0-dI))*RL;show('before',V.subs(dI,0));show('after',V);show('a before',V.subs({k:1,dI:0}));show('a after',V.subs(k,1));show('b before',V.subs({k:s.Rational(1,2),dI:0}));show('b after',V.subs(k,s.Rational(1,2)));print('k= (W/L)4/(W/L)3. Physical saturation/compliance must hold; negative ideal output not realizable with sink compliance.')
