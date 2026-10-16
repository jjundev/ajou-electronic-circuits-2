import sympy as s
s.init_printing()
gm,ro,rp,R,RC,RT=s.symbols('gm ro rp R RC RT', positive=True)
vi,vo,vx,it=s.symbols('vi vo vx it',real=True)
par=lambda a,b:s.simplify(a*b/(a+b))
def show(label,x): print(label, '=',([s.simplify(v) for v in x] if isinstance(x,list) else s.simplify(x)))
def ce(load):
 sol=s.solve(vo/load+gm*vi,vo)[0];show('Av from output KCL',sol/vi)
rn,rpp,gn,gp,rt=s.symbols('rn rp gn gp rt',positive=True)
show('a tail cascode resistance',gn*rt**2);show('a dominant Acm',-rpp/(2*gn*rt**2));show('b upper cascode resistance',gp*rpp**2);show('b dominant Acm',-gp*rpp**2/(2*rt));print('General CM expression with effective upper load L, input ro rn, tail T: -gm rn L/(rn+L+2T(1+gm rn)); dominant result requires gm rn>>1 and 2Tgm rn>>rn+L.')

# Comparison exposed needed finite upper/lower parallel loading in(b); derive from general exact CM KCL.
g,L,r,T=s.symbols('g L r T',positive=True)
y,z,u=s.symbols('y z u',real=True)
sol=s.solve([y/L+(y-z)/r+g*(u-z),z/(2*T)+(z-y)/r-g*(u-z)],[y,z]);A=s.factor(sol[y]/u)
show('full CM KCL gain',A)
scale,a,b,c,d,e=s.symbols('scale a b c d e',positive=True)
# Take g large jointly for input and upper cascode, L~g r^2; T remains r-tail.
lim=s.limit(A.subs({g:scale*a,L:scale*b*c*d,r:e,T:T})/scale,scale,s.oo)
expected=-par(b*c*d,2*a*e*T)/(2*T)
show('b leading gain/scale',lim)
show('parallel formula residual',s.simplify(lim-expected))
print('Therefore(b) requires Rupper || Rlower, not Rupper alone. Rupper=gm3 rO3 rO5, Rlower=2gm1 rO1 rO7; source reference agrees.')
