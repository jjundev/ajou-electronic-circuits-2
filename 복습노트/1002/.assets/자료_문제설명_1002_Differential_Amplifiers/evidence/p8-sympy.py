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

vin=sp.Symbol('vin', positive=True);test=sp.Symbol('it')
Id=sp.Rational(1,1000);Itail=2*Id
kn=sp.Rational(100,1000000);kp=sp.Rational(50,1000000)
gm1=sp.sqrt(2*kn*sp.Integer(500)*Id)
gm3=sp.sqrt(2*kp*sp.Integer(1000)*Id)
gm5=gm3
ro=1/(sp.Rational(1,10)*Id)
ro7=1/(sp.Rational(1,10)*Itail)
dev=[('M','oL','inL','P',gm1,ro),('M','oR','inR','P',gm1,ro),
     ('M','oL','0','aL',gm3,ro),('M','oR','0','aR',gm3,ro),
     ('M','aL','0','0',gm5,ro),('M','aR','0','0',gm5,ro),
     ('M','P','0','0',sp.sqrt(2*kn*1000*Itail),ro7)]
nodes=['oL','oR','aL','aR','P']
vd,_=network(nodes,{'inL':vin/2,'inR':-vin/2},dev)
A_DM=sp.simplify((vd['oL']-vd['oR'])/vin)
vc,_=network(nodes,{'inL':vin,'inR':vin},dev)
A_CM=sp.simplify(vc['oL']/vin)
vtest,_=network(nodes,{'inL':sp.S.Zero,'inR':sp.S.Zero},dev,{'oL':test,'oR':-test})
Rdiff=sp.simplify((vtest['oL']-vtest['oR'])/test)
Rup_lead=gm3*ro*ro
Rhalf_lead=1/(1/ro+1/Rup_lead)
Gcm_lead=1/(2*ro7)
result('p8(1) exact nodal DM gain',A_DM)
result('p8(1) exact nodal differential Rout',Rdiff)
result('p8(1) leading DM gain',-gm1*Rhalf_lead)
result('p8(2) exact nodal CM gain',A_CM)
result('p8(2) basic tail Gm leading',Gcm_lead)
print('p8(1) exact/leading gain',sp.N(A_DM/(-gm1*Rhalf_lead),12))
g,r=sp.symbols('g r',positive=True)
upper_exact=2*r+g*r*r
upper_lead=g*r*r
print('p8(1) sympy.limit(upper branch exact/leading,g->infinity)',sp.limit(upper_exact/upper_lead,g,sp.oo))
print('p8(2) exact minus displayed leading',sp.simplify(A_CM+sp.Integer(50)))
