# P10.01 independent: CE stage, base bias fixed (v_be=0), small-signal vcc -> vout
import sympy as sp
vcc,vout,RC,rO,gm=sp.symbols('v_cc v_out R_C r_O g_m',positive=True)
vbe=0
# KCL at collector: (vcc-vout)/RC = gm*vbe + vout/rO
sol=sp.solve(sp.Eq((vcc-vout)/RC, gm*vbe+vout/rO),vout)[0]
A=sp.simplify(sol/vcc)
target=rO/(RC+rO)
print('A =',A)
print('simplify(A-target)=',sp.simplify(A-target))
print('limit rO->oo:',sp.limit(A,rO,sp.oo))
