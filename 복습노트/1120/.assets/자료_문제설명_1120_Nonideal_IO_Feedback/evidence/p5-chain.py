import sympy as sp
g,h,D,E,F,B=sp.symbols('gm1 gm2 RD1 RD2 R1 R2', positive=True)
v,x,s,y,i=sp.symbols('vin vx vs vout it')
S=F+B
K=B/S
P=F*B/S
L=E*S/(E+S)
A=g*D*h*L/(1+g*P)
# M1 drain, M1 source, M2 drain, with test current entering the output.
eq=[x/D+g*(v-s),s/B+(s-y)/F-g*(v-s),y/E+(y-s)/F+h*x-i]
sol=sp.solve(eq,[x,s,y])
G=sp.factor(sol[y].diff(v))
Z=sp.factor(sol[y].diff(i))
# The divider node responds to its own injected M1 source current.
# vs = K*y + P*j and output KCL becomes y/L = (h*D+K)*j + i.
H=g*(h*D+K)*L/(1+g*P)
assert sp.simplify(G-H/(1+K*H))==0
assert sp.simplify(Z-L/(1+K*H))==0
print('Unilateral forward gain',A)
print('Exact closed gain',G,'Exact output resistance',Z,sep='\n')
