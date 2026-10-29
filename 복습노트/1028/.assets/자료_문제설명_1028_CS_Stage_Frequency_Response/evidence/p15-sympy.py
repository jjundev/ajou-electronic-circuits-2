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

print("p15: stdlib numerical (SymPy absent). Dominant pole approx of P11.40 (RL->inf)")
RS=1000; rpi=2600; R=RS*rpi/(RS+rpi); gm=1/26; Cpi=100e-15; Cmu=10e-15; Ccs=20e-15
wp2=((1+gm*R)*Cmu+Ccs)/(R*(Cpi*Cmu+Cmu*Ccs+Cpi*Ccs))
for RL in [1e4,1e6,1e8,1e10,1e12]:
    A=gm*RL
    a=R*RL*(Cpi*Cmu+Ccs*Cmu+Cpi*Ccs); b=(1+A)*Cmu*R+R*Cpi+RL*(Cmu+Ccs)
    p=quad(a,b)
    print(" RL=%.0e dominant 1/b=%.4g (x RL=%.4g) b/a=%.4g | exact |p1|=%.4g |p2|=%.4g | ratio p2 exact/dom=%.8f"%(RL,1/b,RL/b,b/a,abs(p[0]),abs(p[1]),abs(p[1])/(b/a)))
print("limit: wp1=1/b ~ 1/{RL[(gm R +1)Cmu + Ccs]} -> 0 ; wp2=b/a ->",wp2,"= exact limit (identical to P11.40(b)); Miller wrongly gives both ->0")
