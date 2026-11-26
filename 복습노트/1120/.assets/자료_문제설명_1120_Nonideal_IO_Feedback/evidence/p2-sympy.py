import sympy as s
gm,g1,g2,RD,D1,D2,RM,F,R1,R2,RC,rp,ro,r1,r2,rn,rr=s.symbols('gm g1 g2 RD D1 D2 RM F R1 R2 RC rp ro ro1 ro2 roN roP',positive=True)
def par(*args): return 1/s.Add(*(1/x for x in args))
def show(**entries):
    for key,value in entries.items(): print(key,'=',value)
S=R1+R2
k=R2/S
Z=par(RD,S)
A=gm*Z
D=1+k*A
show(K=k,Aopen=A,Rin_open=1/gm,Rout_open=Z,Aclosed=A/D,Rin_closed=D/gm,Rout_closed=Z/D)
v,e,i=s.symbols('vo vin itest')
assert s.simplify(s.solve(v/Z-gm*(e-k*v)-i,v)[0]-(A*e+Z*i)/D)==0
