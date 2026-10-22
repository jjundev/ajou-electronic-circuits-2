import sympy as s
import json

N,R,i=s.symbols('N RL i1',positive=True);g3=s.symbols('gm3',positive=True);g4=g3/N
vx=-i/g3;vo=-g4*vx*R
print('vo/i=',s.simplify(vo/i),'numeric N=2 RL=10k=',s.simplify(vo/i).subs({N:2,R:10000}))
