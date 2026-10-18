# P10.02 independent: two CE stages, vout = vX - vY, RC1=RC2, rO1=rO2, bases fixed
import sympy as sp
vcc,vX,vY,RC,rO,gm=sp.symbols('v_cc v_X v_Y R_C r_O g_m',positive=True)
s=sp.solve([sp.Eq((vcc-vX)/RC,vX/rO),sp.Eq((vcc-vY)/RC,vY/rO)],[vX,vY])
A=sp.simplify((s[vX]-s[vY])/vcc)
print('vX/vcc =',sp.simplify(s[vX]/vcc),' vY/vcc =',sp.simplify(s[vY]/vcc))
print('A = vout/vcc =',A,'; simplify(A-0)=',sp.simplify(A))
# mismatch sensitivity (for context)
RC2,rO2=sp.symbols('R_C2 r_O2',positive=True)
Am=sp.simplify(rO/(RC+rO)-rO2/(RC2+rO2))
print('general (mismatched) A =',Am)
