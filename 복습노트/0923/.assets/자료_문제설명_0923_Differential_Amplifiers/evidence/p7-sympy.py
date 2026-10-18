# P10.40 independent: M2 off -> M1 carries Iss; sat: V_X >= Vin1 - VTH
import sympy as sp
VDD,RD,Iss,VTH,k=sp.symbols('V_DD R_D I_SS V_TH k',positive=True)
Vin1,Vin2=sp.Rational(3,2),sp.Rational(3,10)
VX=VDD-RD*Iss
cond=sp.simplify(VX-(Vin1-VTH))   # must be >= 0
print('V_X =',VX,'; saturation requires',cond,'>= 0  i.e. R_D*I_SS <= V_DD - 1.5 + V_TH')
# consistency: M2 off assumption, V_P = Vin1 - VTH - sqrt(2Iss/k)
VP=Vin1-VTH-sp.sqrt(2*Iss/k)
print('V_P =',VP,'; M2 off needs Vin2 - V_P < V_TH ->',sp.simplify(Vin2-VP-VTH),'< 0 (i.e. sqrt(2Iss/k) < 1.2 V)')
