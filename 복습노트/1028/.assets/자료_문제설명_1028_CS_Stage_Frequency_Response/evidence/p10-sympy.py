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

print("p10: stdlib numerical KCL vs closed form at random points (SymPy absent)")
print("Model: X=gate node, Cin=CGS1+CGS2, CXY=CGD1+CGD2, Cout=CDB1+CDB2, gm=gm1+gm2, RL=ro1||ro2")
mx=0
for t in range(8):
    RS=random.uniform(100,1e4); Cg1,Cg2,Cd1,Cd2,Cb1,Cb2=[random.uniform(1e-15,1e-13) for _ in range(6)]
    gm1,gm2=random.uniform(1e-4,1e-2),random.uniform(1e-4,1e-2); ro1,ro2=random.uniform(1e3,1e5),random.uniform(1e3,1e5)
    s=complex(random.uniform(-1e9,1e9),random.uniform(1e8,1e11))
    # full node-by-node KCL with separate transistors (both gm*VX currents into ground from out)
    # X: (Vx-1)/RS + s(Cg1+Cg2)Vx + s(Cd1+Cd2)(Vx-Vy)=0 ; Y: s(Cd1+Cd2)(Vy-Vx)+gm1 Vx+gm2 Vx+Vy/ro1+Vy/ro2+s(Cb1+Cb2)Vy=0
    a11=1/RS+s*(Cg1+Cg2+Cd1+Cd2); a12=-s*(Cd1+Cd2); a21=gm1+gm2-s*(Cd1+Cd2); a22=1/ro1+1/ro2+s*(Cb1+Cb2+Cd1+Cd2)
    H=-a21/RS/(a11*a22-a12*a21)
    F=formula(s,RS,Cg1+Cg2,Cd1+Cd2,Cb1+Cb2,gm1+gm2,ro1*ro2/(ro1+ro2))
    rel=abs(H-F)/abs(F); mx=max(mx,rel); print(" pt",t,"rel residual",rel)
print("max rel residual",mx)
