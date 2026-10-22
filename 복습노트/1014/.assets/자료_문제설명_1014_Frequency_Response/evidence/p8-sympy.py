"""Blind independent P11.09 full two-node KCL, original cascade connectivity."""
import sympy as sp
s=sp.symbols('s')
g,R,C,vin,w=sp.symbols('gm RD CL vin omega',positive=True)
x,y=sp.symbols('VX Vout')
print('Actual Fig11.65: M1 gate vin, source ground, drain VX; RD1 VX-VDD, CL1 VX-ground; VX wire feeds M2 gate; M2 source ground drain Vout, RD2 Vout-VDD CL2 Vout-ground.')
print('Identical stages. VDD ACground; lambda0 -> ro omitted; MOS gates draw no current, all other caps absent -> M2 imposes no loading at VX and no feedback to first stage.')
k1=sp.Eq(x/R+s*C*x+g*vin,0)
k2=sp.Eq(y/R+s*C*y+g*x,0)
sol=sp.solve([k1,k2],[x,y])
H1=sp.factor(sol[x]/vin);H=sp.factor(sol[y]/vin)
print('Node VX KCL:',k1)
print('Node Vout KCL:',k2)
print('Stage1 transfer:',H1)
print('Full two-node transfer:',H)
assert sp.simplify(H-(g*R)**2/(1+s*R*C)**2)==0
assert sp.simplify(H-H1**2)==0
print('Two inversions -> positive DCgain:',H.subs(s,0))
print('Stage output-short current entering that stage=gm*its gate voltage; Gmstage=gm. Stage input-zero impedance RD || 1/(sCL). It is not a whole-cascade Gm claim.')
print('Double pole s=-1/(RDCL); fp=1/(2pi RDCL), wp=1/(RDCL).')
Hjw=H.subs(s,sp.I*w)
mag2=sp.simplify(Hjw*sp.conjugate(Hjw))
M=sp.simplify((g*R)**2/(1+(w*R*C)**2))
assert sp.simplify(mag2-M*M)==0
print('Magnitude:',M)
u=sp.symbols('u',positive=True)
N=1/(1+u*u)
D=20*sp.log(N,10)
slope=sp.simplify(20*u*sp.diff(sp.log(N),u))
print('u=f/fp; normalized magnitude1/(1+u^2), relative exactdB=-20log10(1+u^2).')
print('Bode asymptote: flat B0=40log10(gmRD) beforefp; beyondfp B0-40log10(f/fp), slope-40dB/dec.')
print('Exact normalized corner amplitude:',N.subs(u,1))
print('Exact corner relative dB:',sp.N(D.subs(u,1),16))
print('Exact low/high slope:',sp.limit(slope,u,0),sp.limit(slope,u,sp.oo))
assert N.subs(u,1)==sp.Rational(1,2)
assert sp.limit(slope,u,sp.oo)==-40
wb=sp.solve(sp.Eq(N,1/sp.sqrt(2)),u)[0]
print('True overall3dB normalized frequency:',sp.simplify(wb),sp.N(wb,16))
assert sp.simplify(wb-sp.sqrt(sp.sqrt(2)-1))==0
print('Single-stage corner fp is a double-pole frequency; not overall3dB point.')
print('BLIND TWO-NODE SYMBOLIC PASS')
