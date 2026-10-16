import sympy as S
from math import log10,pi,sqrt

f=S.Symbol('f',positive=True);ratio=S.sqrt(1+(f/10**9)**2)/S.sqrt((1+(f/10**8)**2)*(1+(f/10**10)**2))
for fv in [1e8,1e9,1e10]:print('exactcornerGHz',fv/1e9,'dB',20*log10(float(ratio.subs(f,fv))))
# Rational H has two denominator factors and one numerator, hence high-f amplitude order -1.
print('highfrequency amplitude coefficient=',S.limit(f*ratio,f,S.oo));assert S.simplify(S.limit(f*ratio,f,S.oo)-10**9)==0
asym=lambda ff:0 if ff<=1e8 else -20*log10(ff/1e8) if ff<=1e9 else -20 if ff<=1e10 else -20-20*log10(ff/1e10)
print('asymptotesdB',[asym(x) for x in [1e8,1e9,1e10,1e11]]);assert asym(1e11)==-40
