# X9.01 independent check
import sympy as sp
VA=sp.symbols('V_A',positive=True)
VT=sp.Rational(26,1000); IC=sp.Rational(1,1000); beta=100
gm=IC/VT; rpi=beta/gm; ro=VA/IC; par=ro*rpi/(ro+rpi)
for name,expr in [("approx gm ro (ro||rpi)",gm*ro*par),("exact (1+gm(ro||rpi))ro+(ro||rpi)",(1+gm*par)*ro+par)]:
    s=[x for x in sp.solve(sp.Eq(expr,500000),VA) if x.is_real and x>0]
    print(name,": V_A =",[float(x) for x in s],"V")
