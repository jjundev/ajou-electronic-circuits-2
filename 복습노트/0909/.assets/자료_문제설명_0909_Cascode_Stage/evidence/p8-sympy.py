# Independent check P9.15 (Fig 9.51): max Vb1 and V_X, lambda=0
import sympy as sp
V=sp.symbols('Vov1',positive=True)
k=sp.Rational(1,10**4); I=sp.Rational(1,1000); VTH=sp.Rational(2,5); VDD=sp.Rational(18,10); RD=500
W1=sp.Rational(20)/sp.Rational(18,100); W2=sp.Rational(40)/sp.Rational(18,100)
V1=VDD-I*RD; print('V1 = VDD - I RD =',V1)
Vb1max=V1+VTH; print('(a) M1 sat: V1 >= Vb1 - VTH -> Vb1,max =',Vb1max,'V')
o1=sp.solve(sp.Eq(I,k/2*W1*V**2),V)[0]; o2=sp.sqrt(2*I/(k*W2))
VX=Vb1max-VTH-o1
print('(b) Vov1 =',sp.nsimplify(o1),'=',float(o1),' V_X = Vb1 - VTH - Vov1 =',sp.nsimplify(VX),'=',float(VX),'V')
print('    check M2 sat: Vov2 =',float(o2),' V_X >= Vov2 ?',bool(VX>=o2))
