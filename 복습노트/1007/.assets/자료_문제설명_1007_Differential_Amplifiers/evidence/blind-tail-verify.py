"""Independent conditions-only verification; no existing solution is read."""
from pathlib import Path
import sympy as s

g, ro, rp, R, x, e = s.symbols('gm3 ro3 rpi3 R1 vx ve', positive=True)
g1, Rc, dR, vic = s.symbols('gm1 RC DeltaRC vic', positive=True)
# Q3 base is AC ground. Controlled current from collector to emitter = -g*e.
kcl_emitter = e/R + e/rp + (e-x)/ro + g*e
ve = s.solve(kcl_emitter, e)[0]
itest = s.factor((x-ve)/ro-g*ve)
Rout = s.factor(x/itest)
Re = R*rp/(R+rp)
Rout_expected = ro+(1+g*ro)*Re
assert s.simplify(Rout-Rout_expected)==0
assert s.simplify(kcl_emitter.subs(e,ve))==0
# Matched input BJTs: total emitter current = 2*gm1*(vic-vtail).
vt = s.symbols('vtail')
vtail = s.solve(vt/Rout-2*g1*(vic-vt),vt)[0]
ic = s.factor(g1*(vic-vtail))
vod = s.factor((-Rc*ic)-(-(Rc+dR)*ic))
Acm_diff = s.factor(vod/vic)
assert s.simplify(Acm_diff-g1*dR/(1+2*g1*Rout))==0
# vid/2 and -vid/2 => total current zero, vtail=0; exact differential gain.
Adm_exact = -g1*(Rc+dR/2)
CMRR_small_mismatch = s.factor(g1*Rc/Acm_diff)
assert s.simplify(CMRR_small_mismatch-Rc*(1+2*g1*Rout)/dR)==0
# Independently compare full pair KCL under arbitrary inputs.
a,b=s.symbols('vin1 vin2')
vt_general=s.solve(vt/Rout-g1*(a-vt)-g1*(b-vt),vt)[0]
vod_general=-Rc*g1*(a-vt_general)+(Rc+dR)*g1*(b-vt_general)
vid=s.symbols('vid')
assert s.simplify(vod_general.subs({a:vid/2,b:-vid/2})/vid-Adm_exact)==0
assert s.simplify(vod_general.subs({a:vic,b:vic})/vic-Acm_diff)==0

lines=[
'INDEPENDENT CONDITIONS-ONLY VERIFICATION: PASS',
'No workbook answer, previous derivation, or agent fragment was read.',
'Emitter KCL (sum of outgoing currents)= ve/R1 + ve/rpi3 + (ve-vx)/ro3 + gm3*ve = 0',
f've = {ve}',f'itest = {itest}',
'Let Re_star = R1 || rpi3.',
'EXACT Rout = ro3 + (1 + gm3*ro3)*Re_star.',
'EXACT Acm_to_diff = gm1*DeltaRC / (1 + 2*gm1*Rout). Sign is positive for RC at Q1 and RC+DeltaRC at Q2.',
'EXACT Adm = -gm1*(RC + DeltaRC/2).',
'Using requested small-mismatch |ADM| approx gm1*RC:',
'CMRR = RC*(1 + 2*gm1*Rout)/abs(DeltaRC).',
'With gm1*Rout >> 1: |Acm_to_diff| approx abs(DeltaRC)/(2*Rout), CMRR approx 2*gm1*Rout*RC/abs(DeltaRC).',
'With gm3*ro3 >> 1 and gm3*Re_star >> 1: Rout approx gm3*ro3*Re_star.',
'Thus |Acm_to_diff| approx abs(DeltaRC)/(2*gm3*ro3*Re_star).',
'CMRR approx 2*gm1*gm3*ro3*Re_star*RC/abs(DeltaRC).',
'gm3*ro3 multiplies (R1 || rpi3), not bare R1. No gm1*ro1 term exists: ro1=infinite.',
'Finite rpi3 limits Re_star. Replacing Re_star by R1 additionally requires rpi3 >> R1.',
]
vals={g:s.Rational(1,25),ro:100000,rp:2500,R:1000,g1:s.Rational(1,50),Rc:10000,dR:100}
rt=float(Rout.subs(vals)); re=float(Re.subs(vals)); rlead=float((g*ro*Re).subs(vals))
ac=float(Acm_diff.subs(vals)); cm=float(CMRR_small_mismatch.subs(vals))
lines += [f'Numeric test: gm3=.04 S, ro3=100000 ohm, rpi3=2500 ohm, R1=1000 ohm, gm1=.02 S, RC=10000 ohm, DeltaRC=100 ohm.',f'Re_star={re:.12g} ohm; Rout_exact={rt:.12g} ohm; Rout_leading={rlead:.12g} ohm.',f'gm3*Re_star={.04*re:.12g}; gm3*ro3=4000; gm1*Rout={.02*rt:.12g}.',f'Acm_to_diff_exact={ac:.12g}; CMRR_small_mismatch_exact={cm:.12g}.',f'Leading Acm={100/(2*rlead):.12g}; leading CMRR={2*.02*rlead*10000/100:.12g}.', 'All symbolic equality assertions and full-pair superposition checks passed.']
report='\n'.join(lines)+'\n'
Path(__file__).with_name('executed-evidence.txt').write_text(report,encoding='utf-8')
print(report)
