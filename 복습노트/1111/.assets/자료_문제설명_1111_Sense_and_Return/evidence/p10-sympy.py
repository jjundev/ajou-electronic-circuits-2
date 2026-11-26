import sympy as S
from sympy import symbols, simplify, factor, Rational as Q
g1,g2,RD,v,i=symbols('gm1 gm2 RD v i',positive=True)
# Unloaded small-signal models in figure: source-follower gain 1; KCL refers to currents into device.
vx,vy=symbols('vx vy')
print('a Vth/Vin',S.solve(S.Eq(vx/RD+g1*v,0),vx)[0]/v)
print('b Vth/Iin',S.solve(S.Eq(vx/RD-i,0),vx)[0]/i)
print('c drain-in Norton current / Vin',g1)
print('d drain-in Norton current / source-in Iin',S.solve(S.Eq(vy+i,0),vy)[0]/i)
