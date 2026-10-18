# P10.39 independent (large-signal square law, no small-signal model):
# Vin1=VCM+d, Vin2=VCM-d; KCL at P: ID1+ID2 = Iss + VP/RSS
import sympy as sp
k,VCM,VTH,Iss,RSS,d,VP=sp.symbols('k V_CM V_TH I_SS R_SS d V_P',positive=True)
ID1=k/2*(VCM+d-VP-VTH)**2; ID2=k/2*(VCM-d-VP-VTH)**2
F=ID1+ID2-Iss-VP/RSS
print('ID1+ID2 =',sp.expand(ID1+ID2),' -> only even powers of d (d^2 term)')
# implicit differentiation: dVP/dd = -(dF/dd)/(dF/dVP)
dVPdd=sp.simplify(-sp.diff(F,d)/sp.diff(F,VP))
print('dV_P/dd =',dVPdd,'; at d=0:',sp.simplify(dVPdd.subs(d,0)))
# symmetry: F(d) = F(-d) so V_P(d)=V_P(-d), even in d -> no first-order change
print('F(d)-F(-d) =',sp.simplify(F-F.subs(d,-d)))
