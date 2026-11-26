import sympy as S
from sympy import symbols, simplify, factor, Rational as Q
b=Q(1,4)
def h(A): return A/(1+b*A)
first,last=h(1000),h(500)
print('gain at A=1000,500:',first,last)
delta=(last-first)/first
assert delta==-Q(1,252)
print('relative % change:',100*delta,float(100*delta))
