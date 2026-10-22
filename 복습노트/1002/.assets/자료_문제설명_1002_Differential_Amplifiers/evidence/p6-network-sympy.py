# Independent nodal analysis from problem statements and circuit images only.
import sympy as sp

def network(nodes, fixed, devices, injections=None):
    injections = injections or {}
    v = {'0': sp.S.Zero, **fixed}
    v.update({name: sp.Symbol(name) for name in nodes if name not in v})
    kcl = {name: sp.S.Zero for name in nodes}
    def add(name, current):
        if name in kcl:
            kcl[name] += current
    for dev in devices:
        if dev[0] == 'R':
            _, a, b, resistance = dev
            i = (v[a]-v[b])/resistance
            add(a,i); add(b,-i)
        elif dev[0] in ('Q','M'):
            kind, d, g, s, gm, ro, *extra = dev
            i = gm*(v[g]-v[s]) + (v[d]-v[s])/ro
            add(d,i); add(s,-i)
            if kind == 'Q':
                rpi = extra[0]
                ib = (v[g]-v[s])/rpi
                add(g,ib); add(s,-ib)
    for name, current in injections.items():
        add(name,-current)
    unknown = [v[name] for name in nodes if name not in fixed]
    sol = sp.solve([kcl[name] for name in nodes if name not in fixed], unknown, dict=True)
    assert len(sol) == 1, sol
    return {name:sp.simplify(expr.subs(sol[0])) for name,expr in v.items()}, {name:sp.simplify(expr.subs(sol[0])) for name,expr in kcl.items()}

def result(label, value):
    print(label, '=', sp.simplify(value), '≈', sp.N(value, 16))

vin=sp.Symbol('vin', positive=True)
I=sp.Rational(1,2000) # A in each branch, standard symmetric bias
VT=sp.Rational(26,1000);gm=I/VT;ro=sp.Integer(10)/I
beta=sp.Integer(100);rpi=beta/gm;R=sp.Integer(10000)
# (1) pnp collector-to-base local feedback via separate R1/R2.
d1=[('Q','oL','inL','P',gm,ro,rpi),('Q','oR','inR','P',gm,ro,rpi),
    ('Q','oL','bL','0',gm,ro,rpi),('Q','oR','bR','0',gm,ro,rpi),
    ('R','oL','bL',R),('R','oR','bR',R)]
nodes1=['oL','oR','P','bL','bR']
v1,_=network(nodes1,{'inL':vin/2,'inR':-vin/2},d1)
A1=sp.simplify((v1['oL']-v1['oR'])/vin)
test=sp.Symbol('it')
vt1,_=network(nodes1,{'inL':sp.S.Zero,'inR':sp.S.Zero},d1,{'oL':test,'oR':-test})
Rdiff1=sp.simplify((vt1['oL']-vt1['oR'])/test)
Zp=1/(1/ro+(beta+1)/(R+rpi))
Rhalf1=1/(1/ro+1/Zp)
result('p6(1) nodal differential Rout',Rdiff1)
result('p6(1) nodal differential gain',A1)
print('p6(1) Rout minus 2*block',sp.simplify(Rdiff1-2*Rhalf1))
print('p6(1) gain plus gm*block',sp.simplify(A1+gm*Rhalf1))

# (2) two BJT cascode branches, upper emitter bridge R1, finite base resistances.
d2=[('Q','xL','inL','P',gm,ro,rpi),('Q','xR','inR','P',gm,ro,rpi),
    ('Q','oL','0','xL',gm,ro,rpi),('Q','oR','0','xR',gm,ro,rpi),
    ('Q','oL','0','aL',gm,ro,rpi),('Q','oR','0','aR',gm,ro,rpi),
    ('Q','aL','0','0',gm,ro,rpi),('Q','aR','0','0',gm,ro,rpi),
    ('R','aL','aR',R)]
nodes2=['oL','oR','xL','xR','aL','aR','P']
v2,_=network(nodes2,{'inL':vin/2,'inR':-vin/2},d2)
A2=sp.simplify((v2['oL']-v2['oR'])/vin)
vt2,_=network(nodes2,{'inL':sp.S.Zero,'inR':sp.S.Zero},d2,{'oL':test,'oR':-test})
Rdiff2=sp.simplify((vt2['oL']-vt2['oR'])/test)
Rlow=1/(1/ro+1/rpi)
Rupper=1/(1/ro+1/rpi+2/R)
Rdown_branch=gm*ro*Rlow
Rup_branch=gm*ro*Rupper
Rhalf_lead=1/(1/Rdown_branch+1/Rup_branch)
result('p6(2) exact nodal differential Rout',Rdiff2)
result('p6(2) exact nodal differential gain',A2)
result('p6(2) leading differential Rout with rpi and R/2',2*Rhalf_lead)
result('p6(2) leading gain with input gm',-gm*Rhalf_lead)
print('p6(2) exact/leading Rout',sp.N(Rdiff2/(2*Rhalf_lead),12))
print('p6(2) exact/leading gain',sp.N(A2/(-gm*Rhalf_lead),12))
g,r,e=sp.symbols('g r e',positive=True)
branch_exact=r+(1+g*r)*e
branch_lead=g*r*e
print('p6(2) branch exact/leading',sp.simplify(branch_exact/branch_lead))
print('p6(2) sympy.limit(branch exact/leading,g->infinity at fixed e)',sp.limit(branch_exact/branch_lead,g,sp.oo))
b=sp.symbols('b',positive=True)
print('p6(2) sympy.limit(BJT collector/emitter transfer,beta->infinity)',sp.limit(b/(b+1),b,sp.oo))
