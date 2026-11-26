from sympy import *
g,h,D,E,F=symbols('gm1 gm2 RD1 RD2 RF',positive=True)
v,x,y,i,t=symbols('vs vx vo iin itest')
# vs is the CG input, vx the interstage node, vo the CS output.
kcl_in=g*v+(v-y)/F
kcl_x=x/D-g*v
kcl_out=y/E+h*x+(y-v)/F

s=solve([kcl_in-i,kcl_x,kcl_out],[v,x,y])
z=simplify(s[y]/i)
zin=simplify(s[v]/i)

sol_open=solve([g*v-i,kcl_x,y/E+h*x],[v,x,y])
A=h*D*E
assert simplify(sol_open[y]/i+A)==0
# At large RF the feedback current entering the CG source is vo/RF.
yb=solve(Eq(y,-A*(i+y/F)),y)[0]
assert simplify(yb/i+A/(1+A/F))==0
assert simplify(z+E*(g*h*D*F-1)/(g*F+g*E+1+g*A))==0
print('loop: incremental source current + -> vs + -> vx + -> vo - -> returned current -')
print('RF open',factor(sol_open[y]/i),'ohm')
print('large RF',factor(yb/i),'ohm; exact',factor(z),'ohm')
