import sympy as s
from sympy import Rational as Q
print('Independent derivation from blind conditions; author-early, not fragment author')
def check(name, expression):
    value=s.simplify(expression)
    print(name, value)
    assert value==0,(name,value)

vi,vo=s.symbols('vi vo',real=True)
g1,g3,o1,o3,o5,R=s.symbols('g1 g3 o1 o3 o5 R',positive=True)
for panel,Y in [('a',g3+o3+o1),('b',g3+o3+o1+o5),('c',1/R+o3+o1)]:
 z=s.solve(s.Eq(g1*vi+Y*vo,0),vo)[0]
 print(panel,'gain=',s.factor(z/vi));check(panel+' outputKCL',g1*vi+Y*z)
# c resistor midpoint is an actual unknown, show it becomes zero for antisymmetric output.
x,y,m=s.symbols('x y m');mid=s.solve(s.Eq((m-x)/R+(m-y)/R,0),m)[0]
print('c midpoint under y=-x:',s.simplify(mid.subs(y,-x)))
check('c midpoint virtualground',mid.subs(y,-x))
print('In c PMOS gate is midpoint0, so gm3 gate-source drive is zero; do not use diode-connected gm3 load.')
