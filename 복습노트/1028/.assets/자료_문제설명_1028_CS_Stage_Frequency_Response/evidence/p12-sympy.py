import cmath, math, random
random.seed(1)
def kcl(s, R1, Cin, Cxy, Cout, gm, RL):
    # unknowns Vx, Vy with Vin=1 (stdlib, Cramer)
    # X: Vx(1/R1 + s Cin + s Cxy) - Vy s Cxy = 1/R1
    # Y: Vx(gm - s Cxy) + Vy(1/RL + s Cout + s Cxy) = 0
    a11=1/R1+s*Cin+s*Cxy; a12=-s*Cxy; a21=gm-s*Cxy; a22=(1/RL if RL!=math.inf else 0)+s*Cout+s*Cxy
    det=a11*a22-a12*a21
    return (a11*0 - a21*(1/R1))/det
def formula(s, R1, Cin, Cxy, Cout, gm, RL):
    a=R1*RL*(Cin*Cxy+Cout*Cxy+Cin*Cout); b=(1+gm*RL)*Cxy*R1+R1*Cin+RL*(Cxy+Cout)
    return (Cxy*s-gm)*RL/(a*s*s+b*s+1)
def quad(a,b):
    d=cmath.sqrt(b*b-4*a); return ((-b+d)/(2*a), (-b-d)/(2*a))

print("p12: stdlib numerical (SymPy absent); lambda=0")
RS=200; RD=1000; ID=1e-3; Cgs=50e-15; Cgd=10e-15; Cdb=15e-15; Vov=0.2
gm=2*ID/Vov; A=gm*RD; print("gm=",gm,"gmRD=",A)
Cin=Cgs+(1+A)*Cgd; Cout=Cdb+(1+1/A)*Cgd
wi=1/(RS*Cin); wo=1/(RD*Cout)
print("(a) Miller: Cin=",Cin,"Cout=",Cout,"w_in=",wi,"f=",wi/2/math.pi,"w_out=",wo,"f=",wo/2/math.pi)
a=RS*RD*(Cgs*Cgd+Cdb*Cgd+Cgs*Cdb); b=(1+A)*Cgd*RS+RS*Cgs+RD*(Cgd+Cdb)
p=quad(a,b); print("(b) Eq.11.73: a=",a,"b=",b,"poles=",p,"f(Hz)=",[abs(x)/2/math.pi for x in p])
print("    dominant-pole ref: 1/b=",1/b," b/a=",b/a)
print("ratio exact p1 / Miller lower (w_in)=",abs(p[0])/wi, " exact p2 / Miller w_out=",abs(p[1])/wo)
mx=max(abs(kcl(s,RS,Cgs,Cgd,Cdb,gm,RD)-formula(s,RS,Cgs,Cgd,Cdb,gm,RD))/abs(formula(s,RS,Cgs,Cgd,Cdb,gm,RD)) for s in [complex(random.uniform(-1e10,1e10),random.uniform(1e8,1e11)) for _ in range(6)])
print("KCL vs Eq.11.73 max rel residual",mx)
