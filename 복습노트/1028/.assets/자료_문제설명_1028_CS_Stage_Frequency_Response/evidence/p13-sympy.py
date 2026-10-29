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

print("p13: stdlib numerical (SymPy absent). Model: Cin=CGS1, CXY=CGD1, Cout=CDB1+CDB2+CGD2 (M2 gate Vb=AC gnd; CGS2 shorted), RL=ro1||ro2")
mx=0
for t in range(6):
    RS=random.uniform(100,1e4); Cgs1,Cgd1,Cdb1,Cdb2,Cgd2,Cgs2=[random.uniform(1e-15,1e-13) for _ in range(6)]
    gm1=random.uniform(1e-4,1e-2); ro1,ro2=random.uniform(1e3,1e5),random.uniform(1e3,1e5)
    s=complex(random.uniform(-1e9,1e9),random.uniform(1e8,1e11))
    # full KCL: Y: s Cgd1(Vy-Vx)+gm1 Vx+Vy/ro1+Vy/ro2+s(Cdb1+Cdb2+Cgd2)Vy=0 (Cgs2: both ends AC gnd -> no current)
    H=kcl(s,RS,Cgs1,Cgd1,Cdb1+Cdb2+Cgd2,gm1,ro1*ro2/(ro1+ro2))
    RL=ro1*ro2/(ro1+ro2); Co=Cdb1+Cdb2+Cgd2
    a=RS*RL*(Cgs1*Cgd1+Co*Cgd1+Cgs1*Co); b=(1+gm1*RL)*Cgd1*RS+RS*Cgs1+RL*(Cgd1+Co)
    F=(Cgd1*s-gm1)*RL/(a*s*s+b*s+1); rel=abs(H-F)/abs(F); mx=max(mx,rel)
    pe=quad(a,b); print(" pt",t,"rel res",rel," exact |p|",[abs(x) for x in pe]," dominant 1/b,b/a",1/b,b/a)
print("max rel residual",mx)
print("wp1=1/[(1+gm1(ro1||ro2))CGD1 RS + RS CGS1 + (ro1||ro2)(CGD1+CDB1+CDB2+CGD2)]")
print("wp2=b/a, a=RS(ro1||ro2)[CGS1 CGD1 + (CGS1+CGD1)(CDB1+CDB2+CGD2)]")
