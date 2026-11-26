import sympy as S
from sympy import symbols, simplify, factor, Rational as Q
gm,ro,rs=symbols('gm ro Rs',positive=True)
print('Rin (ideal device):',1/gm,'Rout as ro tends to infinity:',S.limit(ro+rs+gm*ro*rs,ro,S.oo))
print('For a current-source input in the ideal device model: imposed i_in=gm vs; d(vs)/d(vout)=0')
