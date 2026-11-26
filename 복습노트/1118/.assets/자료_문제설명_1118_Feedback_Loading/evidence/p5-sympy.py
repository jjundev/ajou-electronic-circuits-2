from sympy import *
R,R1,R2,g,h=symbols('RD R1 R2 gm1 gm2',positive=True)
D=1/(1/R+1/(R1+R2))
k=R2/(R1+R2)
T=h*k*D
v,y,i,t=symbols('vin vo iin itest')
k_in=g*v+h*k*y
k_out=y/D-g*v
a=solve([k_in-i,k_out],[y,v])
b=solve([k_in,k_out-t],[y,v])
for key,val,expected in [('Zt',a[y]/i,D/(1+T)),('Rin',a[v]/i,1/(g*(1+T))),('Rout',b[y]/t,D/(1+T))]:
    assert simplify(val-expected)==0
    print(key,factor(val),'ohm')
print('large R1+R2: replace loaded D by RD at fixed divider ratio')
