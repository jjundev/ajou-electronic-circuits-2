import sympy as s
gm=s.Rational(1,150); Rd=s.Integer(2000); Cf=s.Integer(80)*s.Pow(10,-15)
A=-gm*Rd
Cin=s.simplify(Cf*(1-A))
print('A =',A,'; Cin =',Cin,'F =',s.N(Cin*10**12,10),'pF')
assert Cin==s.Rational(3440,10**15)/3
