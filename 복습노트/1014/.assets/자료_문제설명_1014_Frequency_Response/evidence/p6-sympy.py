"""Independent blind P11.03: actual Fig11.64 connectivity, no author/reference read."""
import sympy as sp
s=sp.symbols('s')
g1,g2,beta,RB,C,ro1,ro2,vin=sp.symbols('gm1 gm2 beta2 RB CL ro1 ro2 vin',positive=True)
vo,vb=sp.symbols('vout vb2')
rpi=beta/g2
print('COMMON: output=common drain/collector-emitter junction relative to ground; CL output-ground; supplies and fixed Vb AC-ground. Other capacitances absent.')
print('BJT a,b VA=infinity -> ro1=ro2=infinity. Q1 collector current gm1*vin leaves output.')
print('(a) Q2 collector and base both at VCC; emitter=output. vbe2=-vout.')
i_a=(g2+1/rpi)*vo
Ha=sp.solve(sp.Eq(g1*vin+i_a+s*C*vo,0),vo)[0]/vin
Ra=sp.simplify(vo/i_a)
wa=sp.simplify(1/(Ra*C))
print('a exact internal Q2 emitter resistance:',Ra)
print('a H(s):',sp.factor(Ha))
print('a exact omega3dB:',wa)
print('a large-beta omega3dB:',sp.limit(wa,beta,sp.oo))
assert sp.simplify(wa/(g2/C)-(beta+1)/beta)==0
print('a exact/large-beta bandwidth ratio ->',sp.limit(wa/(g2/C),beta,sp.oo))
print('(b) Q2 collector=VCC, base connected to VCC through RB, emitter=output.')
base_kcl=sp.Eq(vb/RB+(vb-vo)/rpi,0)
ib=sp.solve(base_kcl,vb)[0]
i_b=sp.simplify((g2+1/rpi)*(vo-ib))
Rb=sp.factor(vo/i_b)
Hb=sp.simplify(sp.solve(sp.Eq(g1*vin+i_b+s*C*vo,0),vo)[0]/vin)
wb=sp.factor(1/(Rb*C))
Rbasic=1/g2+RB/beta
wbasic=sp.factor(1/(Rbasic*C))
print('b base KCL:',base_kcl)
print('b base voltage:',ib)
print('b exact internal resistance:',Rb)
print('b explicit-1/gm identity residual:',sp.simplify(Rb-beta/(beta+1)*Rbasic))
print('b H(s):',sp.factor(Hb))
print('b exact omega3dB:',wb)
print('b large-beta basic resistance:',Rbasic)
print('b large-beta omega3dB:',wbasic)
print('b exact/basic bandwidth ratio:',sp.simplify(wb/wbasic))
print('b exact/basic bandwidth ratio beta->infinity:',sp.limit(wb/wbasic,beta,sp.oo))
assert sp.simplify(Rb-beta/(beta+1)*Rbasic)==0
assert sp.limit(wb/wbasic,beta,sp.oo)==1
print('(c) M1 source=ground, gate=vin; M2 source=VDD and gate=Vb, both AC-ground, hence controlled gm2 source inactive, but MOS ro2 retained; lambda>0 retains ro1 too.')
Gc=1/ro1+1/ro2
Hc=sp.factor(sp.solve(sp.Eq(g1*vin+(Gc+s*C)*vo,0),vo)[0]/vin)
wc=sp.factor(Gc/C)
print('c KCL gm1*vin+(1/ro1+1/ro2+sCL)*vo=0')
print('c H(s):',Hc)
print('c omega3dB:',wc)
print('c resistance:',sp.factor(1/Gc))
print('(d) upper PMOS M1 source=VDD, gate=vin, drain=output. Lower NMOS M2 gate=drain=output, source=ground, so gm2*vo and vo/ro2 leave output; upper PMOS ro1 also connects output to AC ground.')
Gd=g2+1/ro1+1/ro2
Hd=sp.factor(sp.solve(sp.Eq(g1*vin+(Gd+s*C)*vo,0),vo)[0]/vin)
wd=sp.factor(Gd/C)
print('d H(s):',Hd)
print('d omega3dB:',wd)
print('d resistance:',sp.factor(1/Gd))
print('No cross-device gm1*ro2 assumption is used; all required MOS ro branches retained.')
print('GENERAL SINGLE-POLE CHECK: H(s)=H0*G/(G+sCL), G>0.')
G,w,H0=sp.symbols('G omega H0',positive=True)
normalized=G/(G+sp.I*w*C)
mag2=sp.simplify(normalized*sp.conjugate(normalized))
print('Normalized magnitude squared:',mag2)
print('At omega=G/CL:',sp.simplify(mag2.subs(w,G/C)))
assert sp.simplify(mag2.subs(w,G/C))==sp.Rational(1,2)
print('All four f3dB=omega3dB/(2*pi), in Hz; omega in rad/s. No finite transfer zero arises since only shunt CL is present.')
print('Limits: b RB->0 exact resistance:',sp.limit(Rb,RB,0),'a resistance:',Ra)
assert sp.simplify(sp.limit(Rb,RB,0)-Ra)==0
print('c ro1,ro2->infinity bandwidth ->0; d same ro limits bandwidth:',sp.limit(sp.limit(wd,ro1,sp.oo),ro2,sp.oo))
assert sp.limit(sp.limit(wd,ro1,sp.oo),ro2,sp.oo)==g2/C
print('BLIND SYMBOLIC PASS: ALL FOUR CIRCUITS')
