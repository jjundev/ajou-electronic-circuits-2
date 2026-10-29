# p7: E11.15 CE, VT=26 mV, VA=inf (r_o ignored)

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

VT=0.026; Ic=1e-3; beta=100; Rs=200; Cpi,Cmu,Ccs=100e-15,20e-15,30e-15; RL=2e3
gm=Ic/VT; rpi=beta/gm; Rth=Rs*rpi/(Rs+rpi)
m=miller(Rth,Cpi,Cmu,gm,RL,Ccs)
print("gm",gm,"rpi",rpi,"Rs||rpi",Rth,"gmRL",gm*RL)
print("Cin",(Cpi+(1+gm*RL)*Cmu)," Cout",(Ccs+Cmu*(1+1/(gm*RL))))
print("w_in",m[0],"rad/s  f_in",m[0]/2/math.pi)
print("w_out",m[1],"rad/s f_out",m[1]/2/math.pi)
print("w_in ignoring rpi (Rs only):",miller(Rs,Cpi,Cmu,gm,RL,Ccs)[0], "f",miller(Rs,Cpi,Cmu,gm,RL,Ccs)[0]/2/math.pi)
print("exact poles",exact_poles(Rth,Cpi,Cmu,gm,RL,Ccs)," KCLres",check_den(Rth,Cpi,Cmu,gm,RL,Ccs))
# (b) condition w_out<w_in  <=> RL(Ccs+Cmu-Rth gm Cmu) > Rth(Cpi+Cmu) - Cmu/gm
coef=Ccs+Cmu-Rth*gm*Cmu; rhs=Rth*(Cpi+Cmu)-Cmu/gm
print("(b) coef",coef," rhs",rhs," -> possible?", (coef>0) or (rhs<0))
for R in [10,100,500,1e3,2e3,1e4,1e5,1e6]:
    a,b=miller(Rth,Cpi,Cmu,gm,R,Ccs); print("  RL",R,"w_in",f"{a:.3e}","w_out",f"{b:.3e}","out limits?",b<a)
