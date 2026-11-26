import sympy as s
# Ideal tail, no body effect, all conductances positive. a,b are distinct port gains.
g,h,k,m,d,e,f,q=s.symbols('gm3 gm4 gm5 gm6 go3 go4 go5 go6', positive=True)
G,r,L,M=s.symbols('gm1 ro1 RL RM',positive=True)
# unknowns [X, diode-mirror Y, tail Z], nodal drain/drain/source equations.
N=s.Matrix([[f+d,k,-(d+g)],[0,m+q+e,-(e+h)],[-d,-e,g+h+d+e]])
rhs=s.Matrix([[-g,0],[0,-h],[g,h]])
X=(N.inv()*rhs)[0,:]
a,b=[s.factor(v) for v in (-X[0],X[1])]
# X=-a Vin + b VF. Downward j produces VF=M j.
A=G*r*a/(r+L+M)
T=G*r*b*M/(r+L+M)
rn=r+M+G*r*b*M
assert s.simplify(A/(1+T)-G*r*a/(rn+L))==0
n={g:.002,h:.002,k:.001,m:.001,d:1e-5,e:1e-5,f:1e-5,q:1e-5,G:.003,r:60000,L:500,M:200}
for name,z in [('a',a),('b',b),('Aopen',A),('T',T),('Acl',A/(1+T)),('Ro open',r+M),('Ro closed',rn)]:
 print(name,z,float(z.subs(n)))
print('Ri infinite. Matched high-intrinsic-gain model: a=b=gm3/(go3+go5).')
