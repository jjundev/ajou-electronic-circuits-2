from sympy import symbols,solve,simplify
g,b,F,M,r,i,u,v=symbols('gm1 b RF RM ro2 i u v')
Z=1/(g+1/F); P=1/(1/M+1/r+1/F); A=-b*Z*P
Ae=(1/F-b)*Z*P
s=solve([g*u+(u-v)/F-i,v/M+v/r+(v-u)/F+b*u],[u,v])
assert simplify(s[v]/i-Ae/(1-Ae/F))==0
print('b=gm2 gm1 RD; A_V/I=',A,'K=',-1/F,'Zinopen=',Z,'Zoutopen=',P,'D=1-A/F; closed A/D, Zinopen/D, Zoutopen/D. Exact MNA uses Ae=',Ae,'in all three. Current sensing drives Zin down/Zout up, voltage sensing drives both down.')
