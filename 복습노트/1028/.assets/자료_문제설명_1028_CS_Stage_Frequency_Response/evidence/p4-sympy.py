# p4: Vov -> Vov/2, L const. fT = gm/(2pi Cgs), Cgs=(2/3)WLCox (C_GD neglected)
k,W,L,V=2e-4,10e-6,0.18e-6,0.4
I=0.5*k*W/L*V**2
fT=lambda W,I,V: (2*I/V)/(2/3*W*L)
f0=fT(W,I,V)
# (a) I const, W increased: I=0.5k W/L V^2 -> W x4
Wa=W*4; Ia=I; print("(a) W ratio",Wa/W," I check",0.5*k*Wa/L*(V/2)**2/I," gm ratio",(2*Ia/(V/2))/(2*I/V)," fT ratio",fT(Wa,Ia,V/2)/f0)
# (b) W const, I decreased -> I x1/4
Ib=0.5*k*W/L*(V/2)**2; print("(b) I ratio",Ib/I," gm ratio",(2*Ib/(V/2))/(2*I/V)," fT ratio",fT(W,Ib,V/2)/f0)
print("closed form fT=3 mu Vov/(4 pi L^2) -> ratio 0.5 both cases")
