"""Fresh independent P8 verification. Full KCL is INTERNAL ONLY.
M1 source+gate grounded; RE ABOVE drain => T=RE+ro1. Left-minus-right output.
DC square-law ignores lambda in operating point; AC retains input ro.
"""
import sympy as s
G,O,T,R,d,v,vL,vR,x,y,z = s.symbols('G O T R d v vL vR x y z', positive=True)
iL=G*(vL-z)+(x-z)/O
iR=G*(vR-z)+(y-z)/O
kcl=[x/R+iL,y/(R+d)+iR,z/T-iL-iR]
sol=s.solve(kcl,[x,y,z],dict=True)[0]
cm={vL:v,vR:v}
cmL=s.factor(sol[x].subs(cm)/v)
cmDiff=s.factor((sol[x]-sol[y]).subs(cm)/v)
leak=s.factor(s.diff(cmDiff,d).subs(d,0))
dm=s.factor((sol[x]-sol[y]).subs({vL:v/2,vR:-v/2,d:0})/v)
symcm=s.factor(cmL.subs(d,0))
assert s.simplify(dm+G*R*O/(R+O))==0
assert s.simplify(symcm+G*R*O/(R+O+2*T*(1+G*O)))==0
assert s.simplify(cmDiff.subs(d,0))==0
expected=G/((1+R/O)*(1+R/O+2*T*(G+1/O)))
assert s.simplify(leak-expected)==0
short_cm=-R/(2*T)
short_leak=d/(2*T*(1+R/O))
assert s.simplify(s.limit(symcm/short_cm,G,s.oo)-1)==0
assert s.simplify(s.limit(leak*d/short_leak,G,s.oo)-1)==0
cmrr=s.simplify((-dm)/short_leak)
assert s.simplify(cmrr-2*G*T*R/d)==0
assert s.simplify(s.limit(short_leak,O,s.oo)-d/(2*T))==0
print('INTERNAL exact KCL:',[str(e) for e in kcl])
print('Exact symmetric differential gain:',dm)
print('Exact symmetric single-ended CM:',symcm)
print('Exact unequal-load CM-DM:',cmDiff)
print('First derivative at deltaR=0:',leak)
print('Large G limit CM/shortCM:',s.limit(symcm/short_cm,G,s.oo))
print('Large G limit first-order leak/shortLeak:',s.limit(leak*d/short_leak,G,s.oo))
print('Reference ro-omission limit:',s.limit(short_leak,O,s.oo))
mu=s.Rational(1,10000);I=s.Rational(1,10000);Rval=10000
vovtail=s.sqrt(2*I/(mu*50));vov=s.sqrt(2*(I/2)/(mu*25))
gm=2*(I/2)/vov;ro=1/(s.Rational(1,10)*I/2);rotail=1/(s.Rational(1,10)*I);rss=rotail+10000
vlo=vovtail+I*10000+s.Rational(2,5)+vov
vhi=3-(I/2)*Rval+s.Rational(2,5)
cut=s.sqrt(2)*vov
vals={G:gm,O:ro,T:rss,R:Rval,d:10}
print('DC intermediate:',dict(VOV1=vovtail,VOV2=vov,gm=gm,ro_input=ro,ro_tail=rotail,RSS=rss))
print('(1) CM interval:',vlo,vhi,'V; explicit 10-ohm upper:',vhi-I/2*10)
print('(2) steering boundary: +/-',cut,'=',float(cut),'V; requires adequate CM headroom')
print('(3) ADM:',dm.subs(vals),'=',float(dm.subs(vals)))
print('(4) differential CM=0; SE short:',short_cm.subs(vals),'=',float(short_cm.subs(vals)))
print('(5) short CM-DM:',short_leak.subs(vals),'=',float(short_leak.subs(vals)))
print('(6) same-model CMRR:',cmrr.subs(vals),'dB:',float(20*s.log(cmrr.subs(vals),10)))
print('INTERNAL exact finite CMSE:',float(symcm.subs(vals)),'CM-DM:',float(cmDiff.subs(vals)))
print('INTERNAL exact first-order leakage:',float((d*leak).subs(vals)),'CMRR exact:',float((-dm/cmDiff).subs(vals)))
assert vlo==s.Rational(9,5) and vhi==s.Rational(29,10)
assert gm==s.Rational(1,2000) and ro==200000 and rss==110000
assert dm.subs(vals)==-s.Rational(100,21)
assert short_leak.subs(vals)==s.Rational(1,23100)
assert cmrr.subs(vals)==110000
print('PASS: all six parts; short route is large-product limit of full finite-ro KCL.')
# NEW independent Norton verification for the revised symmetric CM branch.
# Boundary 1: output shorted to AC ground, input v remains active.
Rs, vg, vs, isc, vt, it = s.symbols('Rs vg vs isc vt it', positive=True)
sc=s.solve([s.Eq(isc,G*(vg-vs)-vs/O),s.Eq(vs/Rs,isc)],(isc,vs),dict=True)[0]
Gsc=s.factor(sc[isc]/vg)
assert s.simplify(Gsc-G/(1+(G+1/O)*Rs))==0
# Boundary 2: input zero, test voltage at drain; RC restored as parallel load.
test=s.solve([s.Eq(it,-G*vs+(vt-vs)/O),s.Eq(vs/Rs,it)],(it,vs),dict=True)[0]
Rtrans=s.factor(vt/test[it])
assert s.simplify(Rtrans-(O+(1+G*O)*Rs))==0
Rloaded=s.factor(R*Rtrans/(R+Rtrans))
Aproduct=s.factor(-Gsc*Rloaded)
assert s.simplify(Aproduct.subs(Rs,2*T)-symcm)==0
assert s.simplify(s.limit(Gsc*Rs,G,s.oo)-1)==0
assert s.simplify(s.limit(Rtrans/(G*O*Rs),G,s.oo)-1)==0
assert s.simplify(s.limit(Rloaded,G,s.oo)-R)==0
assert s.simplify(s.limit(Aproduct/(-R/Rs),G,s.oo)-1)==0
n={G:gm,O:ro,Rs:2*rss,R:Rval}
print('NEW CM measurement boundaries: output short; independently input zero and drain test.')
print('INTERNAL short-current Gm exact:',Gsc,'=',float(Gsc.subs(n)),'S')
print('INTERNAL input-zero transistor resistance exact:',Rtrans,'=',float(Rtrans.subs(n)),'ohm')
print('INTERNAL loaded output resistance exact:',Rloaded,'=',float(Rloaded.subs(n)),'ohm')
print('INTERNAL product equals full symmetric CM KCL:',s.simplify(Aproduct.subs(Rs,2*T)-symcm))
print('Displayed Gm leading:',1/(2*rss),'S =',float(1/(2*rss)*10**6),'uS')
print('Displayed Rtrans leading:',gm*ro*(2*rss),'ohm =',float(gm*ro*(2*rss)/10**6),'Mohm')
print('Displayed loaded Rout ~ RC:',Rval,'ohm')
print('Displayed signed gain:',-s.Rational(Rval,2*rss),'=',float(-s.Rational(Rval,2*rss)))
print('Independent retry: RE=20kohm -> CMmin',vovtail+I*20000+s.Rational(2,5)+vov,'V; RSS=',rotail+20000,'ohm')
print('Independent retry: deltaRC=5ohm -> CMRR=',cmrr.subs(vals).subs(d,5) if False else cmrr.subs({**vals,d:5}),'dB=',float(20*s.log(cmrr.subs({**vals,d:5}),10)))
print('Independent retry: matched loads -> differential CM=',cmDiff.subs(d,0))
print('PASS: Gm -> loaded Rout -> signed gain uses one CM input/single-ended output port.')
