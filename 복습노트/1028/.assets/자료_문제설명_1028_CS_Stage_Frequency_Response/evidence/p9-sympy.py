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

print("p9: SymPy not installed -> stdlib numerical. VT=26 mV, r_pi->inf, VA=inf")
VT=0.026; IC=1e-3; gm=IC/VT; Cpi=20e-15; Cmu=5e-15; Ccs=10e-15
fin=500e6; fout=2e9
# output pole (Miller): RC*(Ccs + (1+1/(gm RC))Cmu) = 1/(2 pi fout) -> RC(Ccs+Cmu) + Cmu/gm = tau
tau=1/(2*math.pi*fout)
RC=(tau-Cmu/gm)/(Ccs+Cmu)
# iteration check
r=tau/(Ccs+Cmu)
for k in range(6):
    r=tau/(Ccs+(1+1/(gm*r))*Cmu); print(" iter",k,"RC=",r)
A=gm*RC
RB=1/(2*math.pi*fin*(Cpi+(1+A)*Cmu))
print("gm=",gm,"RC(closed form)=",RC,"A=gm RC=",A,"RB=",RB)
RC0=tau/(Ccs+Cmu); A0=gm*RC0; RB0=1/(2*math.pi*fin*(Cpi+(1+A0)*Cmu))
print("approx (drop Cmu/(gm RC) term): RC=",RC0,"A=",A0,"RB=",RB0)
print("check fout=",1/(2*math.pi*RC*(Ccs+(1+1/A)*Cmu)),"fin=",1/(2*math.pi*RB*(Cpi+(1+A)*Cmu)))
# exact 2-pole poles with these values (internal only)
a=RB*RC*(Cpi*Cmu+Ccs*Cmu+Cpi*Ccs); b=(1+A)*Cmu*RB+RB*Cpi+RC*(Cmu+Ccs)
print("exact poles (Hz) for reference:",[abs(p)/(2*math.pi) for p in quad(a,b)])
