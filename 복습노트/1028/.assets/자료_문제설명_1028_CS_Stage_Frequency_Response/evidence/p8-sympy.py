# p8: CE Q1 with PNP current-source load Q2 (base Vb ac ground). Ccs = collector-substrate.

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

Rs=10e3; I=0.5e-3; VT=0.025; beta=200; VA=5
gm=I/VT; rpi=beta/gm; ro=VA/I; Ro=ro*ro/(2*ro); Rth=Rs*rpi/(Rs+rpi)
print("gm",gm,"rpi",rpi,"ro1=ro2",ro,"Rout",Ro,"Rs||rpi",Rth,"Av",-gm*Ro)
random.seed(2)
for _ in range(3):
    Cpi1,Cmu1,Ccs1,Cmu2,Ccs2=[random.uniform(5e-15,200e-15) for _ in range(5)]
    Co=Ccs1+Cmu2+Ccs2
    m=miller(Rth,Cpi1,Cmu1,gm,Ro,Co)
    fin=1/(2*math.pi*5e3*(Cpi1+101*Cmu1)); fout=1/(2*math.pi*5e3*(1.01*Cmu1+Ccs1+Cmu2+Ccs2))
    print(" f_in",m[0]/2/math.pi," formula",fin," res",abs(m[0]/2/math.pi-fin)/fin," f_out",m[1]/2/math.pi," formula",fout," res",abs(m[1]/2/math.pi-fout)/fout," exact",[p/2/math.pi for p in exact_poles(Rth,Cpi1,Cmu1,gm,Ro,Co)]," KCLres",check_den(Rth,Cpi1,Cmu1,gm,Ro,Co))
