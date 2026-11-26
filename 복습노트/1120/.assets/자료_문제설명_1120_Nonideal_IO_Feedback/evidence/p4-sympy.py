import sympy as s
gm,g1,g2,RD,D1,D2,RM,F,R1,R2,RC,rp,ro,r1,r2,rn,rr=s.symbols('gm g1 g2 RD D1 D2 RM F R1 R2 RC rp ro ro1 ro2 roN roP',positive=True)
def par(*args): return 1/s.Add(*(1/x for x in args))
def show(**entries):
    for key,value in entries.items(): print(key,'=',value)
S=R1+R2
k=R2/S
b,c,e,t=s.symbols('vb vc ve it')
M=s.Matrix([[1/R1+1/R2+1/rp,-1/R1],[gm-1/R1,1/RC+1/R1]])
vb,vc=M.inv()*s.Matrix([e/rp,gm*e+t])
show(Av=s.factor(vc.diff(e)),Rin=s.factor(1/((gm+1/rp)*(1-vb.diff(e)))),Rout=s.factor(vc.diff(t)),rpi='beta/gm')
