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

vin = sp.Symbol('vin', positive=True)
gm_a = sp.Rational(1,2)/25  # mA/mV = S: 0.5 mA / 25 mV
assert gm_a == sp.Rational(1,50)
R_C, R_E = sp.Integer(450), sp.Integer(100)
# (a) Q3/Q4 are diode-connected npn: base and collector at VCC, emitter above RC.
dev_a = [('Q','oL','inL','eL',gm_a,sp.oo,sp.oo),('Q','oR','inR','eR',gm_a,sp.oo,sp.oo),
         ('Q','0','0','uL',gm_a,sp.oo,sp.oo),('Q','0','0','uR',gm_a,sp.oo,sp.oo),
         ('R','uL','oL',R_C),('R','uR','oR',R_C),('R','eL','eR',R_E)]
nodes_a=['oL','oR','uL','uR','eL','eR']
va,_=network(nodes_a,{'inL':vin/2,'inR':-vin/2},dev_a)
A_a=sp.simplify((va['oL']-va['oR'])/vin)
result('p5(1) exact hybrid-pi differential gain with beta,ro infinite',A_a)
Gma=1/(1/gm_a+R_E/2)
Rla=R_C+1/gm_a
result('p5(1) block Gm',Gma);result('p5(1) block load',Rla)
print('p5(1) exact minus block',sp.simplify(A_a+Gma*Rla))

# (b) two pnp current-source loads, finite Early resistances, floating tail source.
gm_b = sp.Rational(1,4)/25 # 0.25mA/25mV
ro_b = sp.Integer(5)/sp.Rational(1,4000) # 5V/0.25mA = 20kOhm
dev_b=[('Q','oL','inL','P',gm_b,ro_b,sp.oo),('Q','oR','inR','P',gm_b,ro_b,sp.oo),
       ('Q','oL','0','0',gm_b,ro_b,sp.oo),('Q','oR','0','0',gm_b,ro_b,sp.oo),
       ('R','oL','oR',sp.Integer(20000))]
vb,_=network(['oL','oR','P'],{'inL':vin/2,'inR':-vin/2},dev_b)
A_b=sp.simplify((vb['oL']-vb['oR'])/vin)
result('p5(2) exact nodal differential gain',A_b)
R_b=1/(1/ro_b+1/ro_b+1/sp.Integer(10000))
print('p5(2) exact minus block',sp.simplify(A_b+gm_b*R_b))

# (c) Q2 common-base cascode above Q1, output biased by an ideal 0.5mA source.
beta=sp.Integer(200); I2=sp.Rational(1,2000) # A
I1c=I2*(1+1/beta)  # Q1 collector equals Q2 emitter DC current
gm1=I1c/sp.Rational(25,1000);gm2=I2/sp.Rational(25,1000)
ro1=sp.Integer(5)/I1c;ro2=sp.Integer(5)/I2;rpi2=beta/gm2
dev_c=[('Q','x','in','0',gm1,ro1,beta/gm1),('Q','o','0','x',gm2,ro2,rpi2)]
vc,_=network(['x','o'],{'in':vin},dev_c)
A_c=sp.simplify(vc['o']/vin)
result('p5(3) exact finite-beta, finite-ro voltage gain',A_c)
Rstar=1/(1/ro1+1/rpi2)
lead_c=-gm1*gm2*ro2*Rstar
result('p5(3) leading cascode gain',lead_c)
print('p5(3) exact/leading',sp.simplify(A_c/lead_c))
z=sp.Symbol('z',positive=True)
print('p5(3) sympy.limit(exact/leading, gm2*ro2->infinity)',sp.limit(1+1/z,z,sp.oo))
b=sp.Symbol('b',positive=True)
g0=I2/sp.Rational(25,1000);r0=sp.Integer(5)/I2
reference_lead=-g0*g0*r0/(1/r0+g0/b)
corrected_lead=-(1+1/b)*g0*g0*r0/( (1+1/b)/r0 + g0/b )
result('p5(3) equal-DC-current leading model at beta=200',reference_lead.subs(b,beta))
print('p5(3) finite-beta DC correction/reference at beta=200',sp.N((corrected_lead/reference_lead).subs(b,beta),12))
print('p5(3) sympy.limit(DC-correction/reference,beta->infinity)',sp.limit(corrected_lead/reference_lead,b,sp.oo))
