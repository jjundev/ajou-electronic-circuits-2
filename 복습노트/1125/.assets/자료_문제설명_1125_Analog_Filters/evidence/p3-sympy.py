import sympy as s
g,h,D,r,L,M,F=s.symbols('gm1 gm2 RD ro2 RL RM RF', positive=True)
H=M/(M+F)
S=M*F/(M+F)
B=g+1/(M+F)
Z=r+L+S
v,p,I,j=s.symbols('vi vp Iin j')
sol=s.solve([I-g*v-(v-p)/F, p/M-j-(v-p)/F, j+h*D*g*v+(p+L*j)/r],[v,p,j])
for name,C in [('exact',r*h*D*g+H),('unilateral',r*h*D*g)]:
 A=-C/(B*Z)
 T=-A*H
 gain=A/(1+T)
 ri=1/(B*(1+T))
 rn=r+S+C*H/B
 if name=='exact':
  assert s.simplify(sol[j]/I-gain)==0 and s.simplify(sol[v]/I-ri)==0
 n={g:.002,h:.003,D:10000,r:60000,L:500,M:200,F:5000}
 for label,z in [('Aopen',A),('Ri_open',1/B),('Ro_open',r+S),('K',-H),('T',T),('gain',gain),('Ri',ri),('Ro laser removed',rn)]:
  print(name,label,z,float(z.subs(n)))
print('Exact Aopen refers to cutting only the reverse controlled feedback term. Unilateral model drops H compared with gm1 RD gm2 ro2.')
