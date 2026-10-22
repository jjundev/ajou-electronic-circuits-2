"""Blind independent P11.01 derivation from original circuit and given values."""
import sympy as sp
s=sp.symbols('s')
gm,RD,CL,vin,w=sp.symbols('gm RD CL vin omega',positive=True)
vo=sp.symbols('vout')
print('Actual circuit: grounded-source NMOS gate Vin, drain Vout; RD Vout-to-VDD; CL Vout-ground.')
print('Supplies AC-ground; lambda=0 removes ro; only CL retained; gm*Vin leaves drain toward grounded source.')
kcl=sp.Eq(gm*vin+vo/RD+s*CL*vo,0)
H=sp.simplify(sp.solve(kcl,vo)[0]/vin)
print('KCL:',kcl)
print('H(s):',H)
print('Output-short entering current=gm Vin, so Gm=gm; input-zero output load=RD parallel 1/(sCL).')
Hjw=H.subs(s,sp.I*w)
mag2=sp.simplify(Hjw*sp.conjugate(Hjw))
norm2=sp.simplify(mag2/(gm*RD)**2)
print('Normalized magnitude squared:',norm2)
wp=sp.solve(sp.Eq(norm2,sp.Rational(9,10)**2),w)[0]
print('90 percent amplitude condition yields angular frequency:',wp)
assert sp.simplify(wp-sp.sqrt(19)/(9*RD*CL))==0
assert sp.simplify(norm2.subs(w,wp)-sp.Rational(81,100))==0
vals={RD:sp.Integer(1000),CL:sp.Rational(1,10**12)}
tau=sp.simplify((RD*CL).subs(vals))
wval=sp.simplify(wp.subs(vals));fval=sp.simplify(wval/(2*sp.pi))
print('RD=1000ohm, CL=10^-12F -> tau(s):',tau)
print('omega exact (rad/s):',wval)
print('omega numeric(rad/s):',sp.N(wval,16))
print('f exact(Hz):',fval)
print('f numeric(Hz):',sp.N(fval,16))
print('f MHz:',sp.N(fval/10**6,16))
db=20*sp.log(sp.Rational(9,10),10)
print('Actual10percent voltage-gain-loss dB:',sp.N(db,16))
print('Parenthetical approximately1dB is rounded description, not exact second target.')
one_db_ratio2=10**(-sp.Rational(1,10))
w1=sp.solve(sp.Eq(norm2,one_db_ratio2),w)[0]
print('If exact1dB instead, omega(rad/s):',sp.N(w1.subs(vals),16))
print('If exact1dB instead, f(MHz):',sp.N((w1/(2*sp.pi)).subs(vals)/10**6,16))
print('Target omega /3dB omega:',sp.simplify(wp*RD*CL))
assert sp.sqrt(19)/9<1
print('DC normalized squared magnitude:',sp.limit(norm2,w,0))
print('High-frequency normalized squared magnitude:',sp.limit(norm2,w,sp.oo))
print('SYMBOLIC+EXACT-RATIONAL SUBSTITUTION PASS')
