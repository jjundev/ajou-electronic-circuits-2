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

print("p14: stdlib numerical (SymPy absent). R_Thev=RS||rpi, RL->inf (ideal current source, VA=inf)")
RS=1000; rpi=2600; R=RS*rpi/(RS+rpi); gm=1/26; Cpi=100e-15; Cmu=10e-15; Ccs=20e-15
print("sample values: RS=1k rpi=2.6k gm=1/26 Cpi=100f Cmu=10f Ccs=20f")
wp2=((1+gm*R)*Cmu+Ccs)/(R*(Cpi*Cmu+Cmu*Ccs+Cpi*Ccs))
for RL in [1e4,1e5,1e6,1e8,1e10]:
    A=gm*RL; wi=1/(R*(Cpi+(1+A)*Cmu)); wo=1/(RL*(Ccs+(1+1/A)*Cmu))
    a=R*RL*(Cpi*Cmu+Ccs*Cmu+Cpi*Ccs); b=(1+A)*Cmu*R+R*Cpi+RL*(Cmu+Ccs)
    p=quad(a,b)
    print(" RL=%.0e Miller w_in=%.4g w_out=%.4g | exact |p1|=%.4g |p2|=%.4g | dominant 1/b=%.4g b/a=%.4g"%(RL,wi,wo,abs(p[0]),abs(p[1]),1/b,b/a))
print("limit RL->inf: Miller both ->0 ; exact p1->0, |p2| -> [(1+gm R)Cmu+Ccs]/[R(CpiCmu+CmuCcs+CpiCcs)] =",wp2)
# KCL with RL=inf directly: H = (Cmu s - gm)/(s(a' s + b'))
mx=0
for t in range(5):
    s=complex(random.uniform(-1e9,1e9),random.uniform(1e8,1e11))
    H=kcl(s,R,Cpi,Cmu,Ccs,gm,math.inf)
    ap=R*(Cpi*Cmu+Ccs*Cmu+Cpi*Ccs); bp=gm*Cmu*R+Cmu+Ccs
    F=(Cmu*s-gm)/(s*(ap*s+bp)); mx=max(mx,abs(H-F)/abs(F))
print("RL=inf KCL vs (Cmu s-gm)/(s(a's+b')) max rel residual",mx)
