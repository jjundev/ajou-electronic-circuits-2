# E10.21 independent: from (10.156) and (10.132), Av = -gm RD with gm at ID=Iss/2
import sympy as sp
k,Iss,RD,dV=sp.symbols('k I_SS R_D dV',positive=True)
dI=sp.sqrt(k*Iss)*dV
dVout=-RD*dI
Av=sp.simplify(dVout/dV)
gm=sp.sqrt(2*k*Iss/2)
print('Av =',Av,'; simplify(Av-(-gm RD)) =',sp.simplify(Av+gm*RD))
# also: small-dV limit of exact (10.147) derivative equals sqrt(k Iss)
exact=sp.Rational(1,2)*k*dV*sp.sqrt(4*Iss/k-dV**2)
print('d(exact)/d(dV) at 0 =',sp.simplify(sp.diff(exact,dV).subs(dV,0)),'; lim exact/dV dV->0 =',sp.simplify(sp.limit(exact/dV,dV,0)))
