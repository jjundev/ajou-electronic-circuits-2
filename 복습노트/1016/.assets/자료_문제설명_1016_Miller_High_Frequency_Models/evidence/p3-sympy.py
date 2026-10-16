import sympy as s
Rb,Rc,Rf,rpi,gm=s.symbols('R_B R_C R_F r_pi g_m',positive=True)
A=-gm*Rc
Rfi=s.simplify(Rf/(1-A))
Rfo=s.simplify(Rf/(1-1/A))
Rin=s.simplify(1/(1/rpi+1/Rfi))
Av=s.factor(A*Rin/(Rb+Rin))
vi,vo,V=s.symbols('v_X v_out v_in')
eq1=(vi-V)/Rb+vi/rpi+(vi-vo)/Rf
eq2=vo/Rc+gm*vi+(vo-vi)/Rf
exact=s.factor(s.solve([eq1,eq2],[vi,vo])[vo]/V)
print('Miller Rfi, Rfo:',Rfi,Rfo)
print('input divider resistance:',Rin)
print('estimated gain:',Av)
print('exact KCL gain for comparison:',exact)
assert s.simplify(s.limit(exact,Rf,s.oo)-(-gm*Rc*rpi/(Rb+rpi)))==0
