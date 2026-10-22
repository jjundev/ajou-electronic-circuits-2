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
Id=sp.Rational(1,2000);Itail=2*Id
kn=sp.Rational(100,1000000);kp=sp.Rational(50,1000000)
gm1=sp.sqrt(2*kn*sp.Integer(1000)*Id)
gm3=sp.sqrt(2*kp*sp.Integer(2000)*Id)
gm5=sp.sqrt(2*kn*sp.Integer(2000)*Itail)
ro1=1/(sp.Rational(1,10)*Id)
ro3=ro1
ro5=1/(sp.Rational(1,10)*Itail)
ro6=ro5
# MOS M1/M2 input; PMOS M3/M4 load; NMOS M5/M6 cascode tail.
dev=[('M','oL','inL','P',gm1,ro1),('M','oR','inR','P',gm1,ro1),
     ('M','oL','0','0',gm3,ro3),('M','oR','0','0',gm3,ro3),
     ('M','P','0','x',gm5,ro5),('M','x','0','0',gm5,ro6)]
nodes=['oL','oR','P','x']
vd,_=network(nodes,{'inL':vin/2,'inR':-vin/2},dev)
A_DM=sp.simplify((vd['oL']-vd['oR'])/vin)
vc,_=network(nodes,{'inL':vin,'inR':vin},dev)
A_CM=sp.simplify(vc['oL']/vin)
vtest,_=network(nodes,{'inL':sp.S.Zero,'inR':sp.S.Zero},dev,{'oL':test,'oR':-test})
Rdiff=sp.simplify((vtest['oL']-vtest['oR'])/test)
Rhalf=1/(1/ro1+1/ro3)
Rss_lead=gm5*ro5*ro6
result('p7(1) exact nodal DM gain',A_DM)
result('p7(1) exact nodal differential Rout',Rdiff)
result('p7(1) block DM gain',-gm1*Rhalf)
result('p7(2) exact nodal CM gain with cascode tail',A_CM)
result('p7(2) leading tail resistance',Rss_lead)
result('p7(2) leading CM gain',-ro3/(2*Rss_lead))
print('p7(1) exact minus block',sp.simplify(A_DM+gm1*Rhalf))
print('p7(2) exact/leading CM',sp.N(A_CM/(-ro3/(2*Rss_lead)),12))
g,rn,rp,rs=sp.symbols('g rn rp rs',positive=True)
cm_ratio=g/(g+1/rn+(1+rp/rn)/(2*rs))
print('p7(2) sympy.limit(CM exact/leading,rs->infinity,gm->infinity)',sp.limit(sp.limit(cm_ratio,rs,sp.oo),g,sp.oo))
