import sympy as S
from sympy import symbols, simplify, factor, Rational as Q
V,I,R1,R2=symbols('Vout Iout R1 R2',positive=True)
print('a (Vout): returned voltage',factor(V*(1)), 'loop sign: -1')
print('b (Vout): returned voltage',factor(V*(1)), 'loop sign: +1')
print('c (Iout): returned voltage',factor(I*(R1)), 'loop sign: +1')
print('d (Iout): returned voltage',factor(I*(R1)), 'loop sign: -1')
print('e (Vout): returned voltage',factor(V*(R2/(R1+R2))), 'loop sign: -1')
print('f (Vout): returned voltage',factor(V*(1)), 'loop sign: +1')
