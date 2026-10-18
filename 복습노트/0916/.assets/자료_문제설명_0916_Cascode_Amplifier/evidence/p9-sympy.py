# P9 (E9.10): E9.9 circuit with pnp cascode load (VA=4V, beta=50), Ic=1mA
import sympy as sp
VT = sp.Rational(26, 1000); I = sp.Rational(1, 1000)
gm = I/VT
par = lambda a, b: a*b/(a+b)
roN, rpiN = 5/I, 100/gm
roP, rpiP = 4/I, 50/gm
Ron = gm*roN*par(roN, rpiN); Rop = gm*roP*par(roP, rpiP)
Av = -gm*par(Ron, Rop)
print('Ron =', sp.N(Ron), ' Rop =', sp.N(Rop), ' Ron||Rop =', sp.N(par(Ron, Rop)))
print('Av (Eq. 9.61 approx) =', sp.N(Av, 6))
Ron2 = (1+gm*par(roN, rpiN))*roN + par(roN, rpiN); Rop2 = (1+gm*par(roP, rpiP))*roP + par(roP, rpiP)
print('Av with full Rout terms, Gm=gm1:', sp.N(-gm*par(Ron2, Rop2), 6))
vin, x, y, vo = sp.symbols('v_in v_x v_y v_o')
iQ1 = gm*vin + x/roN
iQ2 = gm*(0-x) + (vo-x)/roN; ib2 = -x/rpiN
iQ4 = (0-y)/roP                       # pnp Q4: e=VCC(0), b=0, c=y
iQ3 = gm*(y-0) + (y-vo)/roP; ib3 = y/rpiP   # pnp Q3: e=y, b=0, c=vo
s = sp.solve([sp.Eq(iQ2+ib2, iQ1), sp.Eq(iQ4, iQ3+ib3), sp.Eq(iQ3, iQ2)], [x, y, vo], dict=True)[0]
Av_ex = s[vo]/vin
print('exact nodal Av =', sp.N(Av_ex, 6), ' ratio exact/approx =', sp.N(Av_ex/Av, 6))
