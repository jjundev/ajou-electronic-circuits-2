import sympy as s
g,h,D,r,M,F=s.symbols('gm1 gm2 RD ro2 RM RF',positive=True)
u,v,I,t=s.symbols('vout vi Iin test_current')
# Positive t injected into output. RD-loaded common-gate first stage x=gm1 RD vi
K=[I-g*v-(v-u)/F,t-h*D*g*v-u/r-u/M-(u-v)/F]
sol=s.solve(K,[u,v])
B=g+1/F
Y=1/r+1/M+1/F
for kind,C in [('exact',h*D*g-1/F),('unilateral',h*D*g)]:
 A=-C/(B*Y)
 T=-A/F
 gain=A/(1+T)
 ri=1/(B*(1+T))
 ro=1/(Y*(1+T))
 if kind=='exact':
  for z in [sol[u].subs(t,0)/I-gain,sol[v].subs(t,0)/I-ri,sol[u].subs(I,0)/t-ro]:assert s.simplify(z)==0
 n={g:.002,h:.003,D:10000,r:60000,M:200,F:5000}
 for lab,z in [('Zopen',A),('Ri_open',1/B),('Ro_open',1/Y),('K',-1/F),('T',T),('Zcl',gain),('Ri',ri),('Ro',ro)]:
  print(kind,lab,z,float(z.subs(n)))
print('If channel-length modulation neglected use ro2 -> infinity. Unilateral approximation needs gm1 RD gm2 >> 1/RF.')
