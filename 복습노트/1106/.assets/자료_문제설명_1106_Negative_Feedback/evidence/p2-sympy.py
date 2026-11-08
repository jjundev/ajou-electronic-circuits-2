# verify-A p2: 2021-1 final Q1, cascode + PMOS current source M3 at Y. lambda=0, body effect ignored.
import sympy as sp
un,up=100e-6,50e-6
ID1,ID3=2e-3,1e-3; ID2=ID1-ID3
gm=lambda u,WL,I: sp.sqrt(2*u*WL*I)
gm1=gm(un,1000,ID1); gm2=gm(un,500,ID2); gm3=gm(up,1000,ID3)
RS,RL=100,500
print("ID2 = ID1-ID3 =",ID2,"A ; gm1 =",float(gm1),"S, gm2 =",float(gm2),"S, gm3 =",float(gm3),"S (gm3 unused, ro3=inf)")
A=-gm1/gm2; print("A_v,XY = -gm1/gm2 =",float(A))
C=sp.symbols('C_GS1 C_GD1 C_DB1 C_GS2 C_GD2 C_SB2 C_DB2 C_GD3 C_DB3',positive=True)
CGS1,CGD1,CDB1,CGS2,CGD2,CSB2,CDB2,CGD3,CDB3=C
CX=CGS1+(1-A)*CGD1; CY=CGS2+CSB2+CDB1+CGD3+CDB3+(1-1/A)*CGD1; CO=CGD2+CDB2
wX=1/(RS*CX); wY=gm2/CY; wO=1/(RL*CO)
print("w_pX = 1/[R_S(C_GS1+3C_GD1)] =",sp.nsimplify(wX),"rad/s ; f_pX = w/(2pi)")
print("w_pY = gm2/[C_GS2+C_SB2+C_DB1+C_GD3+C_DB3+1.5C_GD1] =",sp.nsimplify(wY),"rad/s (1/gm2=100 ohm)")
print("(extra) w_pout = 1/[R_L(C_GD2+C_DB2)] =",sp.nsimplify(wO))
# exact node equations
s,Vin,Vx,Vy,Vo=sp.symbols('s V_in V_x V_y V_o')
CYt=CGS2+CSB2+CDB1+CGD3+CDB3
eqs=[(Vx-Vin)/RS+s*CGS1*Vx+s*CGD1*(Vx-Vy),
     s*CGD1*(Vy-Vx)+gm1*Vx+s*CYt*Vy+gm2*Vy,
     Vo/RL+s*CO*Vo-gm2*Vy]
sol=sp.solve(eqs,[Vx,Vy,Vo],dict=True)[0]
den=sp.fraction(sp.together(sol[Vo]/Vin))[1]
vals={CGS1:200e-15,CGD1:50e-15,CDB1:50e-15,CGS2:100e-15,CGD2:25e-15,CSB2:25e-15,CDB2:25e-15,CGD3:50e-15,CDB3:50e-15}
r=sp.Poly(sp.expand(den.subs(vals)),s).nroots()
print("sample caps:",vals)
print("exact |poles| =",sorted(abs(complex(x)) for x in r))
print("Miller poles  =",sorted(float(w.subs(vals)) for w in (wX,wY,wO)))
print("Note: with these sample caps X and Y poles are comparable, so Miller (pole-splitting ignored) deviates from exact; Miller form is what the problem asks.")
