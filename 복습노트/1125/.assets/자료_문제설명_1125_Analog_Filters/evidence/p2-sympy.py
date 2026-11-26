from sympy import symbols,solve,simplify
g,n,p,gm5,d,vo,vi,id3,y,M,L,r,h=symbols('gm34 go34 go5 gm5 diode6 x vd id3 y RM RL ro1 gm1')
# ideal tail, matched NMOS: i4=-i3; d=gm6+go6
sol=solve([2*id3-g*vi-n*(vo-y),d*y-id3,p*vo+gm5*y+id3],[id3,y,vo])
H=-sol[vo]/vi
G=H*h*r/(r+L+M)
print('H=-vx/(vin-vf)=',H,'G=',G,'Zin=infinity, Zout=open=',r+M,'T=',M*G,'Iout/Vin=',G/(1+M*G),'Zout closed unloaded laser=',r+M+H*h*r*M)
