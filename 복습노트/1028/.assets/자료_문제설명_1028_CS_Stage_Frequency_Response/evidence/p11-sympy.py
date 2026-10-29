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

print("p11: stdlib numerical (SymPy absent)")
RS=200; Cgs=250e-15; Cgd=80e-15; Cdb=100e-15; gm=1/150; RL=2000
A=gm*RL; print("DC gain=-gm RL=",-A, "dB",20*math.log10(A))
Cin=Cgs+(1+A)*Cgd; Cout=Cdb+(1+1/A)*Cgd
wi=1/(RS*Cin); wo=1/(RL*Cout)
print("(a) Miller: Cin=",Cin,"Cout=",Cout,"w_in=",wi,"f_in=",wi/2/math.pi,"w_out=",wo,"f_out=",wo/2/math.pi)
a=RS*RL*(Cgs*Cgd+Cdb*Cgd+Cgs*Cdb); b=(1+A)*Cgd*RS+RS*Cgs+RL*(Cgd+Cdb)
p=quad(a,b); print("(b) exact: a=",a,"b=",b,"poles(rad/s)=",p,"f(Hz)=",[abs(x)/2/math.pi for x in p])
print("    zero (RHP) z=gm/CGD=",gm/Cgd,"rad/s, f=",gm/Cgd/2/math.pi)
print("(c) dominant: wp1=1/b=",1/b,"f=",1/b/2/math.pi," wp2=b/a=",b/a,"f=",b/a/2/math.pi)
# check formula against KCL at random s
mx=max(abs(kcl(s,RS,Cgs,Cgd,Cdb,gm,RL)-formula(s,RS,Cgs,Cgd,Cdb,gm,RL))/abs(formula(s,RS,Cgs,Cgd,Cdb,gm,RL)) for s in [complex(random.uniform(-1e10,1e10),random.uniform(1e8,1e11)) for _ in range(6)])
print("KCL vs Eq.11.73 max rel residual",mx)
for f in [1e7,1e8,4e8,1e9,5e9,1e10,1.33e10]:
    s=2j*math.pi*f
    Hm=-A/((1+s/wi)*(1+s/wo)); He=formula(s,RS,Cgs,Cgd,Cdb,gm,RL); Hd=-A*(1-s*Cgd/gm)/((1+s*b)*(1+s*a/b))
    print(" f=%.3g Hz |H| dB: Miller %.2f exact %.2f dominant %.2f"%(f,20*math.log10(abs(Hm)),20*math.log10(abs(He)),20*math.log10(abs(Hd))))
