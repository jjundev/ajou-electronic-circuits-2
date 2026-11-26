from sympy import *
g,h,D,E,F=symbols('gm1 gm2 RD1 RD2 RF',positive=True)
v,x,y,i,t=symbols('vs vx vo iin itest')
# vs is the CG input, vx the interstage node, vo the CS output.
kcl_in=g*v+(v-y)/F
kcl_x=x/D-g*v
kcl_out=y/E+h*x+(y-v)/F

s=solve([kcl_in,kcl_x,kcl_out-t],[v,x,y])
rout=factor(s[y]/t)
A=h*D*E
assert simplify(rout-E*(1+g*F)/(1+g*(F+E+A)))==0
# RF very large: test voltage y supplies y/RF to M1, so x=D*y/RF.
rout_reduced=1/(1/E+h*D/F)
assert simplify(rout_reduced-E/(1+A/F))==0
print('exact',rout,'ohm; reduced',factor(rout_reduced),'ohm')
