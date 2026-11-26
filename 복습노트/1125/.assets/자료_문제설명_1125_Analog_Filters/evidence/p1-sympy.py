from sympy import symbols, solve, simplify
g,h,D,M,L,v,i,u=symbols('gm1 gm2 RD RM RL vin i vtest', positive=True)
# h(gD(v-Mi)-(M+L)i)=i
G=g*D/(1/h+L+M)
T=M*G
current=solve(h*(g*D*(v-M*i)-(M+L)*i)-i,i)[0]
assert simplify(current/v-G/(1+T))==0
zin=simplify(v/(g*(v-M*current)))
# At vin=0, imposed downward current i yields top-minus-bottom laser voltage
# vport=gD(-Mi)-i/h-Mi
rn=M+1/h+g*D*M
print('T=',T,'Iout/Vin=',current/v,'Zin=',zin,'Zout across removed laser=',rn)
