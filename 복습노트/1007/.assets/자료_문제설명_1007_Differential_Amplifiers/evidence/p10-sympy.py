import sympy as s

N,gm3,RL,i=s.symbols('N gm3 RL i');gm4=gm3/N;vg=-i/gm3;io=-gm4*vg;vo=io*RL
assert s.simplify(vo/i-RL/N)==0
print('main: diode-node KCL vg=-i1/gm3; mirror gm4/gm3=1/N; vo/i1=',s.factor(vo/i),'ohms')
