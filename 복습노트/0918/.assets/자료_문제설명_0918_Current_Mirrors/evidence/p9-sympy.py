import sympy as s
from sympy import Rational as Q
print('Independent derivation from blind conditions; author-early, not fragment author')
def check(name, expression):
    value=s.simplify(expression)
    print(name, value)
    assert value==0,(name,value)

# Part1 mirrors establish the CE current, then collector-node KCL determines gain.
Ic=Q(100,1000000)*2*Q(5,2);gm=Ic/Q(25,1000);ro=5/Ic
vo,vi=s.symbols('vo vi')
sol=s.solve(s.Eq(gm*vi+2*vo/ro,0),vo)[0]
print('1 IC=',Ic,'gm=',gm,'ro=',ro,'Av=',s.simplify(sol/vi));check('gain1',sol/vi+100)
# Part2 independent two-node hybrid-pi KCL. Input is lower Q2, upper Q1 base grounded.
g1,g2,o1,o2,o3,p1,vt,it,x=s.symbols('g1 g2 o1 o2 o3 p1 vt it x',positive=True)
D=o2+o3+p1
Rsolution=s.solve([s.Eq(it,o1*(vt-x)-g1*x),s.Eq(D*x,it)],[vt,x])
R=s.factor(Rsolution[vt]/it)
Gsolution=s.solve(s.Eq((g1+o1+D)*x+g2*vi,0),x)[0]
G=s.factor((-o1*Gsolution-g1*Gsolution)/vi)
Av=s.factor(-G*R)
print('2 exact Rout=',R,'exact Gm=',G,'exact gain=',Av)
vals={g1:Q(2,100),g2:Q(4,100),o1:Q(1,10000),o2:Q(1,5000),o3:Q(1,10000),p1:Q(1,10000)}
print('2 finite-beta exact numbers',R.subs(vals),G.subs(vals),Av.subs(vals))
check('Rout exact512500',R.subs(vals)-512500);check('Av exact-20100',Av.subs(vals)+20100)
Rlead=g1/(o1*D);Alead=-g2*Rlead
print('2 leading',Rlead.subs(vals),Alead.subs(vals),'omit AC base current',Rlead.subs(p1,0).subs(vals),Alead.subs(p1,0).subs(vals))
check('R leading limit',s.limit(R/Rlead,g1,s.oo)-1)
check('A leading limit',s.limit(Av/Alead,g1,s.oo)-1)
print('Condition interpretation: primary answer retains finite-beta AC input resistance; also report rpi->infinity alternative.')
