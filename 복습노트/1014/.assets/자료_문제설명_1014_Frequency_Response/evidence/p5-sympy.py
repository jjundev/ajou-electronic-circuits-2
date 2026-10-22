"""Independent blind P11.02 maximum low-frequency gain from circuit/constraints."""
import sympy as sp
s=sp.symbols('s')
Ic,VT,R,C,VCC,P,fmin,vin=sp.symbols('IC VT R1 CL VCC Pmax fmin vin',positive=True)
vo=sp.symbols('vout')
gm=Ic/VT
print('Actual Fig11.63: NPN emitter ground, base Vin, collector Vout; R1 collector-to-VCC and CL collector-ground.')
print('Early ignored -> ro=infinity. Ideal input source drives vbe=vin. Other caps absent, supply AC-ground.')
kcl=sp.Eq(gm*vin+vo/R+s*C*vo,0)
H=sp.simplify(sp.solve(kcl,vo)[0]/vin)
print('Independent collector KCL:',kcl)
print('H(s):',H)
print('Output-short entering current=gm*vin so Gm=gm=IC/VT; input-zero output resistive load R1; H(0)=-gm R1.')
print('Single-pole frequency f3dB=1/(2pi R1 CL).')
Imax=P/VCC
Rmax=1/(2*sp.pi*fmin*C)
A=Ic*R/VT
print('Power constraint P_supply=VCC IC <=Pmax gives IC<=',Imax)
print('Bandwidth f3dB>=fmin gives R1<=',Rmax)
print('d|A|/dIC:',sp.diff(A,Ic),'positive')
print('d|A|/dR1:',sp.diff(A,R),'positive')
Amax=sp.simplify(A.subs({Ic:Imax,R:Rmax}))
print('Thus max uses both upper bounds; symbolic max magnitude:',Amax)
print('Signed low-frequency gain:',-Amax)
vals={P:sp.Rational(2,1000),VCC:sp.Rational(5,2),C:sp.Rational(2,10**12),fmin:10**9}
In=sp.simplify(Imax.subs(vals));Rn=sp.simplify(Rmax.subs(vals))
print('ICmax A exact/numeric:',In,sp.N(In,16))
print('R1max ohm exact/numeric:',Rn,sp.N(Rn,16))
print('R1max kohm:',sp.N(Rn/1000,16))
print('Gain remains conditional on VT because original does not specify temperature or VT.')
for vt in [sp.Rational(26,1000),sp.Rational(25,1000)]:
    av=sp.simplify(Amax.subs(vals).subs(VT,vt))
    print('VT(V)=',vt,'gm(S)=',sp.N(In/vt,16),'max magnitude=',sp.N(av,16),'signed=',sp.N(-av,16))
print('Recomputed actual power:',sp.simplify(In*vals[VCC]))
print('Recomputed bandwidth:',sp.simplify(1/(2*sp.pi*Rn*vals[C])))
Vc=sp.simplify(vals[VCC]-In*Rn)
print('Collector DC voltage VCC-ICR1 exact/numeric:',Vc,sp.N(Vc,16))
print('Active-region condition requires collector-base reverse bias VC>=VB for NPN (boundary equality); no VB value is supplied or invented.')
print('Therefore report above gain within intended active small-signal operating point, with headroom condition VB<=2.436338...V; no arbitrary0.7V needed.')
assert sp.simplify(In*vals[VCC]-vals[P])==0
assert sp.simplify(1/(2*sp.pi*Rn*vals[C])-vals[fmin])==0
print('SYMBOLIC CONSTRAINED MAXIMUM + EXACT-RATIONAL NUMERIC SUBSTITUTION PASS')
