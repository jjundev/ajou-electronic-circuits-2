# p5 (P12.6) verify-B: noninverting amp, op amp gain A1 (ideal otherwise), R1/R2=7, X peak 2 mV
import sympy as sp
X,XF,Y,A1,R1,R2=sp.symbols('X X_F Y A1 R1 R2',positive=True)
sol=sp.solve([sp.Eq(Y,A1*(X-XF)),sp.Eq(XF,Y*R2/(R1+R2))],[Y,XF],dict=True)[0]
print("Y/X exact =",sp.simplify(sol[Y]/X))
print("XF/X exact =",sp.simplify(sol[XF]/X))
sub={A1:500,R1:7,R2:1,X:sp.Rational(2,1000)}
K=sp.Rational(1,8); print("K=R2/(R1+R2)=",K," KA1=",K*500)
Yv=sol[Y].subs(sub); XFv=sol[XF].subs(sub); Ev=(X-sol[XF]).subs(sub)
print("Y/X =",sp.nsimplify(sol[Y].subs(sub)/sp.Rational(2,1000)),"=",sp.N(Yv/sp.Rational(2,1000),6))
print("Output amplitude Y = %.5f mV (peak)"%float(Yv*1000))
print("Feedback amplitude X_F = %.5f mV (peak)"%float(XFv*1000))
print("Error E = X - X_F = %.5f mV (=X/(1+KA1))"%float(Ev*1000))
print("Ideal limit 1/K: Y=16 mV, X_F=2 mV; finite A1 gives 15.75 mV, 1.969 mV")
