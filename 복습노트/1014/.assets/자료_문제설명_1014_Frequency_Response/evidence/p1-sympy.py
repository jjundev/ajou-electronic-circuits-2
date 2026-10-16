import sympy as s
s.init_printing()
gm,ro,rp,R,RC,RT=s.symbols('gm ro rp R RC RT', positive=True)
vi,vo,vx,it=s.symbols('vi vo vx it',real=True)
par=lambda a,b:s.simplify(a*b/(a+b))
def show(label,x): print(label, '=',([s.simplify(v) for v in x] if isinstance(x,list) else s.simplify(x)))
def ce(load):
 sol=s.solve(vo/load+gm*vi,vo)[0];show('Av from output KCL',sol/vi)
w,wc=s.symbols('w wc',positive=True);H=1/s.sqrt(1+(w/wc)**2);show('high frequency limit',s.limit(H,w,s.oo));show('low frequency limit',s.limit(H,w,0));print('Video edges/rapid spatial detail contain high frequencies. Bandwidth too small attenuates them, slows transitions, creates blur/loss of fine detail; cannot claim all low-frequency image content vanishes.')
