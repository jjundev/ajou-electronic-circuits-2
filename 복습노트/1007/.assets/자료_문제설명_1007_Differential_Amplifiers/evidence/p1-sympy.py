import sympy as s

gm,RD,rt,vin,vo,vs,I,lam,Vov=s.symbols('gm RD rt vin vo vs I lam Vov')
x=s.solve([vo/RD+gm*(vin-vs),vs/(2*rt)-gm*(vin-vs)],(vo,vs));A=s.factor(x[vo]/vin)
assert s.simplify(A+gm*RD/(1+2*gm*rt))==0
proof=s.simplify(A.subs({gm:I/Vov,rt:1/(lam*I)}));assert s.simplify(proof+RD*I/(2/lam+Vov))==0
print('main CM half-circuit KCL:',A,'original proof:',proof)
print('Large degeneration leading term:',s.limit(A*rt,rt,s.oo)/rt)
