import sympy as s
g,h,D,r,M,F=s.symbols('gm1 gm2 RD ro2 RM RF',positive=True)
u,p,v,j,I=s.symbols('vLaser vp vi j Iin')
# At laser port voltage source u, positive j into laser.
K=[I-g*v-(v-p)/F,p/M-j-(v-p)/F,j+h*D*g*v+(u+p)/r]
res=s.solve(K,[p,v,j])[j]
for kind,C in [('exact',r*h*D*g+M/(M+F)),('unilateral',r*h*D*g)]:
 H=M/(M+F)
 B=g+1/(M+F)
 rn=r+M*F/(M+F)+C*H/B
 jn=-C*I/(B*rn)
 if kind=='exact': assert s.simplify(res-jn+u/rn)==0
 n={g:.002,h:.003,D:10000,r:60000,M:200,F:5000,I:1e-6}
 print(kind,'j_N downward through short',jn, float(jn.subs(n)), 'RN',rn,float(rn.subs(n)))
