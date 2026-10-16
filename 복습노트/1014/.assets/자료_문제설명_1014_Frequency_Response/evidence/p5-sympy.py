import sympy as s
s.init_printing()
gm,ro,rp,R,RC,RT=s.symbols('gm ro rp R RC RT', positive=True)
vi,vo,vx,it=s.symbols('vi vo vx it',real=True)
par=lambda a,b:s.simplify(a*b/(a+b))
def show(label,x): print(label, '=',([s.simplify(v) for v in x] if isinstance(x,list) else s.simplify(x)))
def ce(load):
 sol=s.solve(vo/load+gm*vi,vo)[0];show('Av from output KCL',sol/vi)
print('Ordered breakpoints100MHz pole,1GHz zero,10GHz pole; slopes0,-20,0,-20 dB/dec. Relative to DC:0dB to100MHz; -20dB at1GHz and10GHz; -40dB at100GHz. Unknown DC gain is an arbitrary vertical offset. All-pass/right-left zero phase cannot be inferred from magnitude.')
f=s.symbols('f',positive=True);H=s.sqrt(1+(f/1e9)**2)/s.sqrt((1+(f/1e8)**2)*(1+(f/1e10)**2));show('relativeDC',s.limit(H,f,0));show('high coefficient',s.limit(f*H,f,s.oo))
