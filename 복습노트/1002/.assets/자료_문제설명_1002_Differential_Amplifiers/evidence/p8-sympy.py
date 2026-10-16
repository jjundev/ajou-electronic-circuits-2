import sympy as s
s.init_printing()
gm,ro,rp,R,RC,RT=s.symbols('gm ro rp R RC RT', positive=True)
vi,vo,vx,it=s.symbols('vi vo vx it',real=True)
par=lambda a,b:s.simplify(a*b/(a+b))
def show(label,x): print(label, '=',([s.simplify(v) for v in x] if isinstance(x,list) else s.simplify(x)))
def ce(load):
 sol=s.solve(vo/load+gm*vi,vo)[0];show('Av from output KCL',sol/vi)
g1,g2,r1,r2,r3,rpi,RP=s.symbols('g1 g2 r1 r2 r3 rpi RP',positive=True)
# Q1 upper common-base, Q2 input CE, Q3 middle PNP. rpi kept; DC base currents ignored.
y,z,u=s.symbols('y z u')
def derive(bridge,Rs,glo,gup,rup):
 eqx=z/Rs+(z-y)/rup+(z-y)*bridge+gup*z+glo*u
 eqy=(y-z)/rup+(y-z)*bridge-gup*z-it
 sol=s.solve([eqx,eqy],[y,z]);show('Av',s.diff(sol[y],u));show('Rout',s.diff(sol[y],it));return sol
print('(1)');a=derive(0,par(par(r2,r3),rpi),g2,g1,r1)
vals={g1:.02,g2:.04,r1:10000,r2:5000,r3:10000,rpi:10000};show('exact Av1',s.diff(a[y],u).subs(vals));show('exact Ro1',s.diff(a[y],it).subs(vals))
print('(2) bridge RP; each branch0.5mA');b=derive(1/RP,par(r1,rpi),g2,g1,r3)
vals={g1:.02,g2:.02,r1:10000,r3:10000,rpi:10000,RP:10000};show('exact Av2',s.diff(b[y],u).subs(vals));show('exact Ro2',s.diff(b[y],it).subs(vals))

print('Dominant: (1) Rout500k, Av-20000. (2) half Rout500k, differential Rout1M, gain-10000. Exact half510k -> differential1.020M; approximations agree reference.')
