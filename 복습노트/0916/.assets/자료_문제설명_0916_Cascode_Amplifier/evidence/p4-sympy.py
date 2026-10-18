# P4 (E9.11): CMOS cascode Fig 9.20(b), numeric
import sympy as sp
ID = sp.Rational(1, 2000)
gn = sp.sqrt(2*sp.Rational(100, 10**6)*30*ID); gp = sp.sqrt(2*sp.Rational(50, 10**6)*40*ID)
ron = 1/(sp.Rational(1, 10)*ID); rop = 1/(sp.Rational(15, 100)*ID)
par = lambda a, b: a*b/(a+b)
print('gm1=gm2=', sp.N(gn), ' gm3=gm4=', sp.N(gp), ' rOn=', sp.N(ron), ' rOp=', sp.N(rop))
Av_apx = -gn*par(gn*ron*ron, gp*rop*rop)
print('Ron~', sp.N(gn*ron*ron), ' Rop~', sp.N(gp*rop*rop), ' par=', sp.N(par(gn*ron*ron, gp*rop*rop)))
print('Eq.(9.72) approx Av =', sp.N(Av_apx, 6))
vin, vx, vy, vo = sp.symbols('v_in v_x v_y v_o')
i1 = gn*vin + vx/ron                 # M1 drain current (x -> gnd)
i2 = gn*(0-vx) + (vo-vx)/ron         # M2 (o -> x)
I_sd4 = (0-vy)/rop                   # M4: s=VDD(0), g=0, d=y  (VDD -> y)
I_sd3 = gp*(vy-0) + (vy-vo)/rop      # M3: s=y, g=0, d=o (y -> o)
s = sp.solve([sp.Eq(i1, i2), sp.Eq(I_sd4, I_sd3), sp.Eq(I_sd3, i2)], [vx, vy, vo], dict=True)[0]
Av_ex = sp.simplify(s[vo]/vin)
print('exact nodal Av =', sp.N(Av_ex, 6), ' ratio exact/approx =', sp.N(Av_ex/Av_apx, 6))
