import sympy as s
gm,g1,g2,RD,D1,D2,RM,F,R1,R2,RC,rp,ro,r1,r2,rn,rr=s.symbols('gm g1 g2 RD D1 D2 RM F R1 R2 RC rp ro ro1 ro2 roN roP',positive=True)
def par(*args): return 1/s.Add(*(1/x for x in args))
def show(**entries):
    for key,value in entries.items(): print(key,'=',value)
S=R1+R2
k=R2/S
Z=par(D2,S); P=par(R1,R2)
A=g1*D1*g2*Z/(1+g1*P); D=1+k*A
show(K=k,Aopen=A,Rin_open=s.oo,Rout_open=Z,Av_replica=A/D,Rin_closed=s.oo,Rout_replica=Z/D)
v,t=s.symbols('vin it'); h=1/R1
M=s.Matrix([[g1+1/R2+h,-h],[g1*g2*D1-h,1/D2+h]])
vs,vo=M.inv()*s.Matrix([g1*v,g1*g2*D1*v+t])
show(Av_exact=s.factor(vo.diff(v)),Rout_exact=s.factor(vo.diff(t)))
