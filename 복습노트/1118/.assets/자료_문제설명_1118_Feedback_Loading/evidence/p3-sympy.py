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

A=h*D*E
assert simplify(zin-(F+E)/(1+g*(F+E+A)))==0
# large-RF model vo=-A*gm1*vs, iin=gm1*vs-vo/RF
zin_reduced=solve(Eq(i,g*v+A*g*v/F),v)[0]/i
print('exact',factor(zin),'ohm; reduced',factor(zin_reduced),'ohm')
