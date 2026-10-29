# p6: Fig 11.82 (a)(b)(c), Miller poles, lambda>0, body effect neglected. stdlib numeric check.

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

random.seed(1)
for case in "abc":
  for _ in range(3):
    gm1,gm2=random.uniform(1e-3,5e-3),random.uniform(1e-3,5e-3)
    ro1,ro2=random.uniform(1e4,5e4),random.uniform(1e4,5e4)
    Rs=random.uniform(100,2000)
    Cgs1,Cgd1,Cdb1,Cgs2,Cgd2,Cdb2,Csb2=[random.uniform(5e-15,50e-15) for _ in range(7)]
    par=lambda *r: 1/sum(1/x for x in r)
    if case in "ab":
        Ro=par(1/gm2,ro1,ro2); gm=gm1; Cx=Cgs1; CF=Cgd1
        Co=Cdb1+Cgs2+(Cdb2 if case=="a" else Csb2)
        win_f=1/(Rs*(Cgs1+(1+gm1*Ro)*Cgd1)); wout_f=1/(Ro*(Cgd1*(1+1/(gm1*Ro))+Co))
    else:
        Ro=par(ro1,ro2); gm=gm2; Cx=Cgs2; CF=Cgd2; Co=Cdb2+Cgd1+Cdb1
        win_f=1/(Rs*(Cgs2+(1+gm2*Ro)*Cgd2)); wout_f=1/(Ro*(Cgd2*(1+1/(gm2*Ro))+Co))
    m=miller(Rs,Cx,CF,gm,Ro,Co); ex=exact_poles(Rs,Cx,CF,gm,Ro,Co)
    print(case,"Av=",-gm*Ro," Miller(in,out)=",["%.4e"%v for v in m]," formula res",abs(m[0]-win_f)/win_f,abs(m[1]-wout_f)/wout_f," exact poles",["%.4e"%v for v in ex]," KCLres",check_den(Rs,Cx,CF,gm,Ro,Co))
