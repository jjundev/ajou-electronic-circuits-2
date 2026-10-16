import sympy as s

Rs,Rd,C,gm=s.symbols('R_S R_D C_F g_m', positive=True)
z=s.symbols('s')
Y=s.Matrix([[1/Rs+z*C,-z*C],[gm-z*C,1/Rd+z*C]])
D=s.factor(Y.det())
pole=s.solve(D,z)[0]
A=-gm*Rd
Cin=s.simplify(C*(1-A))
Cout=s.simplify(C*(1-1/A))
print('KCL determinant:',D)
print('exact pole:',pole)
print('A, Cin, Cout:',A,Cin,Cout)
print('Miller input/output estimates:',-1/(Rs*Cin),-1/(Rd*Cout))
assert s.simplify(D.subs(z,pole))==0
