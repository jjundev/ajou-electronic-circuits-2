# p5: CS stage, W->W/2, I_D->I_D/2. stdlib (no SymPy): numerical KCL check + scaling

import cmath, math, random
def exact_poles(Rs,Cx,CF,gm,Ro,Co):
    # KCL: X: (vx-vin)/Rs + s Cx vx + s CF (vx-vo)=0 ; O: gm vx + vo/Ro + s Co vo + s CF (vo-vx)=0
    # denominator a s^2 + b s + 1
    a=Rs*Ro*(Cx*CF+Cx*Co+CF*Co)
    b=Rs*(Cx+CF*(1+gm*Ro))+Ro*(CF+Co)
    d=cmath.sqrt(b*b-4*a)
    return sorted([abs((-b+d)/(2*a)),abs((-b-d)/(2*a))])
def gain_dc(gm,Ro): return -gm*Ro
def tf(s,Rs,Cx,CF,gm,Ro,Co):
    # solve 2x2 linear system for vo/vin
    a11=1/Rs+s*Cx+s*CF; a12=-s*CF; b1=1/Rs
    a21=gm-s*CF; a22=1/Ro+s*Co+s*CF
    det=a11*a22-a12*a21
    return (-a21*b1)/det
def check_den(Rs,Cx,CF,gm,Ro,Co):
    a=Rs*Ro*(Cx*CF+Cx*Co+CF*Co); b=Rs*(Cx+CF*(1+gm*Ro))+Ro*(CF+Co)
    m=0
    for _ in range(4):
        s=complex(random.uniform(-1,1),random.uniform(-1,1))*1e9
        H=tf(s,Rs,Cx,CF,gm,Ro,Co); Hf=gm*Ro*(s*CF/gm-1)/(a*s*s+b*s+1)
        m=max(m,abs(H-Hf)/abs(H))
    return m
def miller(Rs,Cx,CF,gm,Ro,Co):
    A=gm*Ro
    return 1/(Rs*(Cx+(1+A)*CF)), 1/(Ro*(Co+CF*(1+1/A)))

k=2e-4; W=20e-6; L=0.18e-6; I=0.5e-3; lam=0.1; Rs=1e3; RD=2e3
Cgs0,Cgd0,Cdb0=40e-15,10e-15,15e-15
def design(W,I,use_ro):
    Vov=math.sqrt(2*I/(k*W/L)); gm=2*I/Vov; ro=1/(lam*I)
    sc=W/20e-6
    Ro=(RD*ro/(RD+ro)) if use_ro else RD
    return Vov,gm,ro,Ro,Cgs0*sc,Cgd0*sc,Cdb0*sc
for use_ro in (False,True):
    o=design(W,I,use_ro); n=design(W/2,I/2,use_ro)
    print("use_ro=",use_ro)
    print(" Vov ratio",n[0]/o[0]," gm ratio",n[1]/o[1]," ro ratio",n[2]/o[2]," gain ratio",gain_dc(n[1],n[3])/gain_dc(o[1],o[3]))
    mo=miller(Rs,o[4],o[5],o[1],o[3],o[6]); mn=miller(Rs,n[4],n[5],n[1],n[3],n[6])
    # formula check (lambda=0): w_in'=1/[Rs(Cgs/2+(1+gm RD/2)Cgd/2)], w_out'=1/[RD(Cdb/2 + Cgd/2 (1+2/(gm RD)))]
    if not use_ro:
        fin=1/(Rs*(Cgs0/2+(1+o[1]*RD/2)*Cgd0/2)); fout=1/(RD*(Cdb0/2+Cgd0/2*(1+2/(o[1]*RD))))
        print(" formula residual in/out", abs(fin-mn[0])/fin, abs(fout-mn[1])/fout)
    print(" Miller w_in old/new",mo[0],mn[0]," ratio",mn[0]/mo[0])
    print(" Miller w_out old/new",mo[1],mn[1]," ratio",mn[1]/mo[1])
    print(" exact poles old",exact_poles(Rs,o[4],o[5],o[1],o[3],o[6])," new",exact_poles(Rs,n[4],n[5],n[1],n[3],n[6]))
    print(" KCL vs closed-form denominator residual", check_den(Rs,n[4],n[5],n[1],n[3],n[6]))
