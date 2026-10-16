import sympy as s
Ri=s.Integer(100000); gm=s.Rational(1,200)
fl=s.Integer(20); fh=s.Integer(20000)
Ci=s.simplify(1/(2*s.pi*Ri*fl))
CL=s.simplify(gm/(2*s.pi*fh))
z,Cin,Cout,V=s.symbols('s C_i C_L V_in')
vg,vo=s.symbols('v_g v_o')
eqg=vg/Ri+z*Cin*(vg-V)
eqo=gm*(vo-vg)+z*Cout*vo
H=s.factor(s.solve([eqg,eqo],[vg,vo])[vo]/V)
print('transfer:',H)
print('Ci min:',Ci,'F =',s.N(Ci*10**9,9),'nF')
print('CL max:',CL,'F =',s.N(CL*10**9,9),'nF')
assert s.simplify((1/(2*s.pi*Ri*Ci))-fl)==0
assert s.simplify((gm/(2*s.pi*CL))-fh)==0
