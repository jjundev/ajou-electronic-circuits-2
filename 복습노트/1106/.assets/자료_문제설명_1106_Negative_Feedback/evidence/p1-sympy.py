# verify-A p1: Razavi 11.49 cascode with Q3 supplying 75% of IC1. VA=inf, Miller.
import sympy as sp
s,RB,RC,gm1,rpi1,rpi2,Cp1,Cm1,Cp2,Cm2,Ccs1,Ccs2,Cm3,Ccs3,Vin=sp.symbols('s R_B R_C g_m1 r_pi1 r_pi2 C_pi1 C_mu1 C_pi2 C_mu2 C_CS1 C_CS2 C_mu3 C_CS3 V_in',positive=True)
print("Assumptions: VA=inf (all ro=inf), IC2=IC1-0.75IC1=0.25IC1 -> gm2=gm1/4; Q3 base AC ground, ro3=inf;")
print("Q3 collector caps C_mu3, C_CS3 load node Y; impedance into Q2 emitter ~1/gm2 (beta>>1).")
gm2=gm1/4
Axy=-gm1/gm2
print("A_v,XY = -gm1/gm2 =",Axy)
CX=Cp1+(1-Axy)*Cm1
CY=Cp2+Ccs1+Cm3+Ccs3+(1-1/Axy)*Cm1
CO=Cm2+Ccs2
wX=1/((RB*rpi1/(RB+rpi1))*CX); wY=1/(CY/gm2); wO=1/(RC*CO)
print("|w_pX| = 1/[(R_B||r_pi1)(C_pi1+5C_mu1)] :",sp.simplify(wX))
print("|w_pY| = 1/[(1/gm2)(C_pi2+C_CS1+C_mu3+C_CS3+(5/4)C_mu1)], 1/gm2=4/gm1 :",sp.simplify(wY))
print("|w_pout| = 1/[R_C(C_mu2+C_CS2)] :",wO)
print("Standard cascode (gm1=gm2): Miller factor on C_mu1 at X = 2; here 5 -> Miller effect MORE significant.")
# exact node equations
Vx,Vy,Vo=sp.symbols('V_x V_y V_o')
CYt=Cp2+Ccs1+Cm3+Ccs3
eqs=[ (Vx-Vin)/RB+Vx*(1/rpi1+s*Cp1)+s*Cm1*(Vx-Vy),
      s*Cm1*(Vy-Vx)+gm1*Vx+s*CYt*Vy+gm2*Vy+Vy/rpi2,
      Vo/RC+s*CO*Vo-gm2*Vy]
sol=sp.solve(eqs,[Vx,Vy,Vo],dict=True)[0]
H=sp.factor(sp.simplify(sol[Vo]/Vin)); num,den=sp.fraction(H)
print("Exact H(s) =",H)
vals={RB:1e3,RC:2e3,gm1:0.04,rpi1:2500,rpi2:1e4,Cp1:10e-12,Cm1:1e-12,Cp2:3e-12,Cm2:1e-12,Ccs1:0.5e-12,Ccs2:0.5e-12,Cm3:0.5e-12,Ccs3:0.5e-12}
r=sp.Poly(den.subs(vals),s).nroots()
print("Numeric check (sample values):",vals)
print("exact poles |w| =",sorted([abs(complex(x)) for x in r]))
print("Miller  poles   =",sorted([float(w.subs(vals)) for w in (wX,wY,wO)]))
print("(X dominant; Miller X-pole vs exact agree when the other poles are far; Y pole uses rpi2->inf.)")
