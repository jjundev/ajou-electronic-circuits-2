"""Blind independent P11.06 normalized Bode construction from poles/zero only."""
import sympy as sp
x=sp.symbols('x',positive=True)
print('Given frequencies in Hz: poles fp1=100MHz=1e8Hz, fp2=10GHz=1e10Hz; zero fz=1GHz=1e9Hz.')
print('DC gain not supplied: let L0=20log10|A0| be unknown vertical offset. Do not infer0dB absolute gain.')
print('Let x=f/(100MHz). Real first-order pole/zero normalized magnitudes apply; a RHP vs LHP real zero has same magnitude.')
M2=(1+(x/10)**2)/((1+x*x)*(1+(x/100)**2))
print('Normalized exact squared magnitude:',sp.factor(M2))
print('Exact normalized dB=10log10(M2); total dB=L0+10log10(M2).')
print('A pole contributes -20dB/dec after corner, zero +20dB/dec after corner.')
print('f<100MHz: cumulative slope0dB/dec, levelL0.')
print('100MHz<f<1GHz: slope-20dB/dec, levelL0-20log10(f/100MHz).')
print('1GHz<f<10GHz: slope0dB/dec, levelL0-20dB.')
print('f>10GHz: slope-20dB/dec, levelL0-20-20log10(f/10GHz).')
print('Asymptote corner levels relative L0: at100MHz0dB, at1GHz-20dB, at10GHz-20dB.')
print('Poles/zero change slope; no vertical jumps at corners.')
low=sp.Integer(0);seg1=-20*sp.log(x,10);seg2=sp.Integer(-20);seg3=-20-20*sp.log(x/100,10)
assert sp.simplify(low-seg1.subs(x,1))==0
assert sp.simplify(seg1.subs(x,10)-seg2)==0
assert sp.simplify(seg2-seg3.subs(x,100))==0
print('Piecewise continuity residuals all0.')
exactdb=10*sp.log(M2,10)
slope=sp.simplify(10*x*sp.diff(sp.log(M2),x))
print('Exact dB/dec slope:',sp.factor(slope))
print('Exact low-frequency slope:',sp.limit(slope,x,0))
print('Exact high-frequency slope:',sp.limit(slope,x,sp.oo))
assert sp.limit(slope,x,0)==0
assert sp.limit(slope,x,sp.oo)==-20
print('M low-frequency limit:',sp.limit(sp.sqrt(M2),x,0))
print('High-frequency x*M limit:',sp.limit(x*sp.sqrt(M2),x,sp.oo))
for xx in [sp.Integer(1),sp.Integer(10),sp.Integer(100)]:
 print('Exact smooth relative corner dB at x=',xx,':',sp.N(exactdb.subs(x,xx),16))
print('Smooth response differs from straight-line asymptote near corners; plateau is a Bode asymptotic segment.')
print('If plotting angular frequency instead, all corners multiply by2pi:2pi*1e8,2pi*1e9,2pi*1e10 rad/s; same ratios/slopes/relative levels.')
print('BLIND SYMBOLIC BODE PASS')
