from sympy import symbols,simplify,solve
g,b,F,M,L,r,i,j,u,p=symbols('gm1 b RF RM RL ro2 i j u p')
# b=gm2 gm1 RD; u=input, p=sense node
Z=1/(g+1/(F+M)); P=F*M/(F+M); k=M/(F+M)
A=-b*r*Z/(r+L+P)
Ae=-(b*r+k)*Z/(r+L+P)
s=solve([g*u+(u-p)/F-i,p/M+(p-u)/F-j,j+b*u+(p+L*j)/r],[u,p,j])
assert simplify(s[j]/i-Ae/(1-k*Ae))==0
print('Textbook Aopen=',A,'K=',-k,'Zin0=',Z,'Zout0=',r+P,'gain=A/(1-k*A); Zin=Z/(1-k*A); stated textbook Zout=(r+P)(1-k*A). For unloaded port evaluate A with RL=0. Exact nodal replacement Ae=',Ae)
