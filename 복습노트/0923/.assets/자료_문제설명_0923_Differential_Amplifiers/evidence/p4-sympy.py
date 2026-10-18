# E10.15 independent: equilibrium, M1/M2 saturated: VDD - RD*Iss/2 >= VCM - VTH
import sympy as sp
RD=sp.symbols('R_D',positive=True)
VDD,VCM,VTH,Iss=sp.Rational(18,10),sp.Rational(16,10),sp.Rational(5,10),sp.Rational(5,10000)
RDmax=sp.solve(sp.Eq(VDD-RD*Iss/2,VCM-VTH),RD)[0]
print('R_D,max =',RDmax,'ohm =',float(RDmax)/1e3,'kohm')
print('check RDmax-2800 =',sp.simplify(RDmax-2800))
