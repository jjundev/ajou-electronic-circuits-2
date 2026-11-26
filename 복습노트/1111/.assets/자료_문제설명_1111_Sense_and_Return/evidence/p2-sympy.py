import sympy as S
from sympy import symbols, simplify, factor, Rational as Q
A,K,test=symbols('A1 K test')
pathA=(-K*(A*test))/test
pathB=(K*(A*(-test)))/test
assert simplify(pathA-pathB)==0
print('signed returned/test:',pathA,'negative-feedback loop gain:',-pathA)
