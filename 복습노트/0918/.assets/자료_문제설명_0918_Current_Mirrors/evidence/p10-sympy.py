import sympy as s
Vcc,R1,R2,I1,I2,Vx,Vy,I,R,d=s.symbols('Vcc R1 R2 I1 I2 Vx Vy I R d')
x=s.solve([s.Eq((Vcc-Vx)/R1,I1),s.Eq((Vcc-Vy)/R2,I2)],[Vx,Vy],dict=True)[0]
cm=s.factor((x[Vx]+x[Vy])/2)
print('General DC collector KCL CM=',cm)
match=s.simplify(cm.subs({R1:R,R2:R,I1:I,I2:I}));print('matched quiescent=',match);assert match==Vcc-I*R
small=s.simplify(cm.subs({I1:I+d,I2:I-d})-cm.subs({I1:I,I2:I}));print('opposite signal CM perturbation=',small);assert s.simplify(small-d*(R2-R1)/2)==0
print('matched first order CM perturbation=',small.subs(R2,R1))
