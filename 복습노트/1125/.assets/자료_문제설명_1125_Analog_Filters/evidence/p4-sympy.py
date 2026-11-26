from sympy import symbols,solve,simplify
g,b,F,M,r,i,j,u,p,v=symbols('gm1 b RF RM ro2 i j u p v')
# v=top-minus-bottom of laser, j downward; b=gm2 gm1 RD
s=solve([g*u+(u-p)/F-i,p/M+(p-u)/F-j,j+b*u+(p+v)/r],[u,p,j])
N=s[j].subs(v,0); R=-1/s[j].diff(v)
assert simplify(s[j]-N+v/R)==0
print('Exact Norton Isc=',N,'Rn=',R,'current source points bottom to top internally. Textbook unilateral model omits forward passive feedthrough: A0=-b*ro2*Z/(ro2+P); Isc=A0*Iin/(1-k*A0); Rn=(ro2+P)*(1-k*A0).')
