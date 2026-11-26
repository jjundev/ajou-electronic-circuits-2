import sympy as S
from sympy import symbols, simplify, factor, Rational as Q
A,K,p=symbols('A0 K omega0',positive=True)
x=S.sqrt(A**2-(1+K*A)**2)
assert simplify(A**2/((1+K*A)**2+x**2))==1
print('exact omega_u:',p*x)
print('omega_u/(A omega0) = sqrt(1-(K+1/A)^2); large A limit:',S.limit(x/A,A,S.oo))
print('gain-bandwidth product:',simplify((A/(1+K*A))*p*(1+K*A)))
