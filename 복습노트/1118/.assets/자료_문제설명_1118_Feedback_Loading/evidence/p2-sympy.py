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

assert limit(z,D,oo)==-F
assert limit(zin,D,oo)==0
print('vo/iin ->',limit(z,D,oo),'ohm')
print('vs/iin ->',limit(zin,D,oo),'ohm')
