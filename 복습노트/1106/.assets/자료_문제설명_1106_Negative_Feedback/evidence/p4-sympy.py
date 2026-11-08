# verify-A p4: 2023-1 final Q1. Miller theorem. Body effect (gmb) ignored; C_SB kept as caps to ground.
import sympy as sp
s,Vin,Vx,Vy,Vo=sp.symbols('s V_in V_x V_y V_o')
RG,RS,gm1,gm2,gm3,gm4,ro1,ro3,ro5=sp.symbols('R_G R_S g_m1 g_m2 g_m3 g_m4 r_o1 r_o3 r_o5',positive=True)
CGS1,CGD1,CDB1,CGS2,CGD2,CSB2,CDB2,CGS3,CSB3,CGS4,CDB4,CGD5,CDB5=sp.symbols(
 'C_GS1 C_GD1 C_DB1 C_GS2 C_GD2 C_SB2 C_DB2 C_GS3 C_SB3 C_GS4 C_DB4 C_GD5 C_DB5',positive=True)
print("=== (1) circuit (a), lambda=0")
print("M3: NMOS source follower (D=VDD, G=Vb2) -> looks like 1/gm3 into n1; M4 diode load -> 1/gm4 at out.")
print("R_n1 = 1/(gm2+gm3); A_v,(gate1->n1) = -gm1/(gm2+gm3). C_GD3 sits VDD-Vb2 (no effect); C_GD4 shorted by diode.")
A=-gm1/(gm2+gm3)
wX=1/(RG*(CGS1+(1-A)*CGD1))
Cn1=CDB1+CGS2+CSB2+CGS3+CSB3+(1-1/A)*CGD1
wn1=(gm2+gm3)/Cn1
CO=CGD2+CDB2+CGS4+CDB4
wO=gm4/CO
print("w_pX  = 1/{R_G[C_GS1+(1+gm1/(gm2+gm3))C_GD1]} :",wX)
print("w_pn1 = (gm2+gm3)/[C_DB1+C_GS2+C_SB2+C_GS3+C_SB3+(1+(gm2+gm3)/gm1)C_GD1] :",wn1)
print("w_pout= gm4/(C_GD2+C_DB2+C_GS4+C_DB4) :",wO)
eqs=[(Vx-Vin)/RG+s*CGS1*Vx+s*CGD1*(Vx-Vy),
     s*CGD1*(Vy-Vx)+gm1*Vx+s*(CDB1+CGS2+CSB2+CGS3+CSB3)*Vy+(gm2+gm3)*Vy,
     gm4*Vo+s*CO*Vo-gm2*Vy]
sol=sp.solve(eqs,[Vx,Vy,Vo],dict=True)[0]
H1=sp.factor(sol[Vo]/Vin); den=sp.fraction(sp.together(H1))[1]
vals={RG:10e3,gm1:4e-3,gm2:2e-3,gm3:2e-3,gm4:2e-3,CGS1:100e-15,CGD1:20e-15,CDB1:30e-15,CGS2:100e-15,CSB2:30e-15,CGS3:100e-15,CSB3:30e-15,CGD2:20e-15,CDB2:30e-15,CGS4:100e-15,CDB4:30e-15}
print("exact H_a(s) =",H1)
print("sample:",vals)
print("exact |poles| =",sorted(abs(complex(x)) for x in sp.Poly(sp.expand(den.subs(vals)),s).nroots()))
print("Miller poles  =",sorted(float(w.subs(vals)) for w in (wX,wn1,wO)))

print("\n=== (2) circuit (b), lambda!=0, differential half circuit (n3 = AC ground)")
print("out1 load: M3 NMOS (G=D=VDD, S=out1) -> 1/gm3||ro3 ; M5 PMOS current source -> ro5 ; M1 -> ro1")
Rout=1/(1/ro1+1/ro5+gm3+1/ro3)
print("R_out = ro1||ro5||(1/gm3)||ro3 =",Rout)
Av=-gm1*Rout
wX2=1/(RS*(CGS1+(1-Av)*CGD1))
Cout=CDB1+CDB5+CGD5+CGS3+CSB3+(1-1/Av)*CGD1
wO2=1/(Rout*Cout)
print("A_v = -gm1*R_out")
print("w_pX  = 1/{R_S[C_GS1+(1+gm1 R_out)C_GD1]} :",sp.simplify(wX2))
print("w_pout= 1/{R_out[C_DB1+C_DB5+C_GD5+C_GS3+C_SB3+(1+1/(gm1 R_out))C_GD1]} :",sp.simplify(wO2))
print("(C_GD3: both ends VDD; C_DB3: D=VDD, body=gnd -> not at out; C_GD5 to Vb1=AC gnd; C_DB5 to VDD=AC gnd)")
print("Vout/Vin(s) = (Vout1-Vout2)/(Vin1-Vin2) = -gm1 R_out / [(1+s/w_pX)(1+s/w_pout)]  (Miller: zero s=gm1/C_GD1 lost)")
eqs2=[(Vx-Vin)/RS+s*CGS1*Vx+s*CGD1*(Vx-Vo),
      s*CGD1*(Vo-Vx)+gm1*Vx+Vo/Rout+s*(CDB1+CDB5+CGD5+CGS3+CSB3)*Vo]
sol2=sp.solve(eqs2,[Vx,Vo],dict=True)[0]
H2=sp.factor(sp.simplify(sol2[Vo]/Vin))
print("exact half-circuit H(s) =",H2)
print("H(0) =",sp.simplify(H2.subs(s,0)))
v2={RS:10e3,gm1:4e-3,gm3:1e-3,ro1:50e3,ro3:50e3,ro5:50e3,CGS1:100e-15,CGD1:20e-15,CDB1:30e-15,CDB5:30e-15,CGD5:20e-15,CGS3:100e-15,CSB3:30e-15}
den2=sp.fraction(sp.together(H2))[1]
print("sample:",v2)
print("exact |poles| =",sorted(abs(complex(x)) for x in __import__('numpy').roots([float(c) for c in sp.Poly(sp.expand(den2.subs(v2)),s).all_coeffs()])))
print("Miller poles  =",sorted(float(w.subs(v2)) for w in (wX2,wO2)))
print("Gain check: H(0) = -gm1*R_out; Miller poles track exact when w_pX << w_pout.")
