import sympy as s
Rb,Rc,rpi,C,gm=s.symbols('R_B R_C r_pi C_F g_m',positive=True)
z=s.symbols('s')
Rin=s.simplify(1/(1/Rb+1/rpi))
A=-gm*Rc
Ci=s.simplify(C*(1-A)); Co=s.simplify(C*(1-1/A))
pi=s.simplify(-1/(Rin*Ci)); po=s.simplify(-1/(Rc*Co))
Y=s.Matrix([[1/Rb+1/rpi+z*C,-z*C],[gm-z*C,1/Rc+z*C]])
D=s.factor(Y.det()); pe=s.solve(D,z)[0]
print('A, Rin, Ci, Co:',A,Rin,Ci,Co)
print('estimated poles (rad/s):',pi,po)
print('KCL determinant:',D)
print('one exact pole:',pe)
ratio=s.factor(pe/pi)
u=s.symbols('u',positive=True)
print('exact/input estimated pole ratio:',ratio)
print('ratio under u=RC/[Rin(1+gmRC)]:',1/(1+u),'limit as u->0:',s.limit(1/(1+u),u,0,dir='+'))
assert s.simplify(ratio - 1/(1+Rc/(Rin*(1+gm*Rc))))==0
assert s.limit(1/(1+u),u,0,dir='+')==1
assert s.simplify(D.subs(z,pe))==0
