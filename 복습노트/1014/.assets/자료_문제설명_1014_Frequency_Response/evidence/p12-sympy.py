import sympy as S
from pathlib import Path
import json
s,gm,Rs,Rd,Cin,CL=S.symbols('s gm Rs Rd Cin CL', positive=True)
vs,vd,vin,it=S.symbols('vs vd vin it')
# FIRST derivation, no reference read: Fig 11.12 only.
# Gate Vb and VDD are AC ground. Source=vs, drain=vd. vgs=-vs.
# Controlled drain-to-source current gm*vgs=-gm*vs.
# Current leaving source toward drain is +gm*vs. ro=infinity (lambda=0).
kcl_source=(vs-vin)/Rs+s*Cin*vs+gm*vs
kcl_drain=vd/Rd+s*CL*vd-gm*vs
sol=S.solve([kcl_source,kcl_drain],[vs,vd],dict=True)[0]
H=S.factor(sol[vd]/vin)
print('TOPOLOGY: input vin -- Rs -- source vs; Cin source-ground; gate AC ground; Rd drain-ground; CL drain-ground; output vd.')
print('KCL source =',kcl_source,'=0')
print('KCL drain =',kcl_drain,'=0')
print('vs/vin =',S.factor(sol[vs]/vin))
print('vd/vin =',H)
# Direct independent port test with capacitors omitted and lambda=0.
vs_test=S.solve(S.Eq(it,gm*vs),vs)[0]
rin=S.simplify(vs_test/it)
Rseen=S.simplify(1/(1/Rs+1/rin))
win=S.simplify(1/(Rseen*Cin))
wout=1/(Rd*CL)
rd_required=S.solve(S.Eq(wout,10*win),Rd)[0]
print('DC source test: it=gm*vs; Rin transistor=',rin)
print('Cin sees Rs parallel Rin=',Rseen)
print('omega_in [rad/s]=',win)
print('omega_out [rad/s]=',wout)
print('negative s poles=',[-win,-wout])
print('Rd for omega_out=10 omega_in [ohm]=',S.factor(rd_required))
print('ratio residual=',S.simplify((wout/win).subs(Rd,rd_required)-10))
assert S.simplify((wout/win).subs(Rd,rd_required)-10)==0
print('Units: Cin/CL dimensionless, Rs/(1+gm*Rs) ohm, hence Rd ohm; each RC seconds; 2*pi cancels for Hz ratio.')
print('Inequality: for positive values, omega_out>=10 omega_in iff 0<Rd<=Rd_required. Exactly 10 requires equality only.')
print('Rs->0, required Rd ->',S.limit(rd_required,Rs,0,dir='+'))
print('Rs->infinity, required Rd ->',S.limit(rd_required,Rs,S.oo))
print('gm->0, required Rd ->',S.limit(rd_required,gm,0,dir='+'))
num={gm:S.Rational(1,100),Rs:S.Integer(1000),Cin:S.Rational(1,10**12),CL:S.Rational(2,10**12)}
rdnum=S.simplify(rd_required.subs(num))
print('Illustrative exact SI gm=0.01S, Rs=1000ohm, Cin=1pF, CL=2pF: Rd=',rdnum,'ohm')
print('omega_in=',win.subs(num),'rad/s; omega_out=',wout.subs(num|{Rd:rdnum}),'rad/s')
print('numeric ratio=',S.simplify((wout/win).subs(num|{Rd:rdnum})))
initial={'p12:main':{'reviewer':'independent_checker_2 (not author)','method':'symbolic','circuit':'Fig11.12 PNG inspected before any comparison; CG source input, drain output, gate AC ground, lambda=0','derivation':'source KCL (vs-vin)/Rs+s*Cin*vs+gm*vs=0; drain KCL vd/Rd+s*CL*vd-gm*vs=0; transistor Rin=1/gm','conclusion':'omega_in=(1+gm*Rs)/(Rs*Cin), omega_out=1/(Rd*CL), Rd=Rs*Cin/[10*CL*(1+gm*Rs)]=(Rs parallel 1/gm)*Cin/(10*CL). Exact ten means equality; at least ten gives Rd<=this with Rd>0.','before_comparison':True}}
Path('C:/Users/Hyunjun/.codex/tmp/review-pack/1014-20261022-regen/problem-explain/final-v1/work/independent/p12-initial.json').write_text(json.dumps(initial,ensure_ascii=False,indent=2),encoding='utf-8')