import sympy as s
gm,g1,g2,RD,D1,D2,RM,F,R1,R2,RC,rp,ro,r1,r2,rn,rr=s.symbols('gm g1 g2 RD D1 D2 RM F R1 R2 RC rp ro ro1 ro2 roN roP',positive=True)
def par(*args): return 1/s.Add(*(1/x for x in args))
def show(**entries):
    for key,value in entries.items(): print(key,'=',value)
S=R1+R2
k=R2/S
Zi=par(rp,F); Zo=par(RC,ro,F); gc=gm; kf=1/F
a=1/Zi; d=1/Zo
A=-gc*Zi*Zo
D=1-kf*A
show(Zi=Zi,Zo=Zo,R0=A,K_signed_subtractive=-kf,K_return_current=kf,D=D,Rclosed_replica=A/D,Rin_replica=Zi/D,Rout_replica=Zo/D)
# Reciprocal passive network transmits -kf in both off-diagonal admittances.
M=s.Matrix([[a,-kf],[gc-kf,d]])
det=a*d+kf*(gc-kf)
assert s.simplify(M.det()-det)==0
show(Rclosed_exact=(kf-gc)/det,Rin_exact=d/det,Rout_exact=a/det)
