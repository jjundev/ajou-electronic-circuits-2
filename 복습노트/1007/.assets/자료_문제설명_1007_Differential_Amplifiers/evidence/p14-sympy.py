import sympy as s

VT=s.Rational(26,1000);VAn=s.Integer(5);A=100;VAp=s.simplify(1/(1/(A*VT)-1/VAn));VAp=s.Rational(65,12)
check=s.simplify(1/VT/(1/VAn+1/VAp));assert check==100
print('main: Gm=Ic/VT, Rout=(VAn/Ic)||(VAp/Ic). Target100 => VAp=',VAp,'V ≈',float(VAp),'V; substituted gain=',check)
print('Feasibility: limit VAp infinity gives VAn/VT=',s.N(VAn/VT),' >100; increasing VAp increasesgain.')
