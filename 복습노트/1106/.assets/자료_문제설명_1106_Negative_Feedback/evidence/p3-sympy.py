# verify-A p3: Razavi Ex 11.27, cascode MOS diff pair. Half circuit (tail = AC ground), lambda=0, body effect ignored except C_SB kept.
import sympy as sp
s,RS,RD,gm1,gm3,Vin,Vx,Vy,Vo=sp.symbols('s R_S R_D g_m1 g_m3 V_in V_x V_y V_o',positive=True)
CGS1,CGD1,CDB1,CGS3,CGD3,CSB3,CDB3=sp.symbols('C_GS1 C_GD1 C_DB1 C_GS3 C_GD3 C_SB3 C_DB3',positive=True)
A=-gm1/gm3
wX=1/(RS*(CGS1+(1-A)*CGD1)); wY=gm3/(CDB1+CGS3+CSB3+(1-1/A)*CGD1); wO=1/(RD*(CDB3+CGD3))
print("Half circuit: M1 (input) + M3 (cascode) + R_D; X=M1 gate, Y=M1 drain/M3 source; A_XY=-gm1/gm3 (=-1 if gm1=gm3)")
print("w_pX  =",wX," -> gm1=gm3: 1/[R_S(C_GS1+2C_GD1)]")
print("w_pY  =",wY," -> gm1=gm3: gm3/(C_DB1+C_GS3+C_SB3+2C_GD1)")
print("w_pout=",wO)
print("Same poles for M2/M4 side by symmetry; tail node not a pole for differential signal.")
eqs=[(Vx-Vin)/RS+s*CGS1*Vx+s*CGD1*(Vx-Vy),
     s*CGD1*(Vy-Vx)+gm1*Vx+s*(CDB1+CGS3+CSB3)*Vy+gm3*Vy,
     Vo/RD+s*(CDB3+CGD3)*Vo-gm3*Vy]
sol=sp.solve(eqs,[Vx,Vy,Vo],dict=True)[0]
den=sp.fraction(sp.together(sol[Vo]/Vin))[1]
vals={RS:10e3,RD:5e3,gm1:2e-3,gm3:2e-3,CGS1:100e-15,CGD1:20e-15,CDB1:30e-15,CGS3:100e-15,CSB3:30e-15,CDB3:30e-15,CGD3:20e-15}
print("sample:",vals)
print("exact |poles| =",sorted(abs(complex(x)) for x in sp.Poly(sp.expand(den.subs(vals)),s).nroots()))
print("Miller poles  =",sorted(float(w.subs(vals)) for w in (wX,wY,wO)))
