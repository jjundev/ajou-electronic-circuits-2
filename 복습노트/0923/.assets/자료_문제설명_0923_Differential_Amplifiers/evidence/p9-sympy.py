# X10.21 independent: gm = 2ID/Vov with ID=Iss/2 -> Av = -Iss RD / Vov_equil
import sympy as sp
Iss,RD,Vov,k=sp.symbols('I_SS R_D V_ov k',positive=True)
gm=2*(Iss/2)/Vov
Av=-gm*RD
print('Av =',Av,'; diff vs -Iss RD/Vov =',sp.simplify(Av+Iss*RD/Vov))
# cross-check against sqrt(k Iss) with Vov=sqrt(Iss/k)
print('consistency with -sqrt(k Iss)RD:',sp.simplify(Av.subs(Vov,sp.sqrt(Iss/k))+sp.sqrt(k*Iss)*RD))
