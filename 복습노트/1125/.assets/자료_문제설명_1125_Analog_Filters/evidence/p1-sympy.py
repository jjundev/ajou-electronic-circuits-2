import sympy as s
g,h,D,L,M=s.symbols('gm1 gm2 RD RL RM',positive=True)
u,x,j,i=s.symbols('Vin X j Iin')
A=g*D/(1/h+L+M)
T=A*M
ans=s.solve([i-g*(u-M*j), x-D*i,j-h*(x-(L+M)*j)], [i,x,j])
gain=A/(1+T)
ri=(1+T)/g
rn=1/h+M+g*D*M # differential laser voltage with input zero
assert s.simplify(ans[j]/u-gain)==0 and s.simplify(u/ans[i]-ri)==0
assert s.simplify(gain-g*D/(rn+L))==0
for expr in [T,gain,ri,rn]:
 print(expr, float(expr.subs({g:.002,h:.004,D:10000,L:500,M:200})))
