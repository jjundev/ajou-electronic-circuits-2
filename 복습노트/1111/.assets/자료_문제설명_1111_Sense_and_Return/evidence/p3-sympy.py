# p3 (E12.04) independent: noninverting amp, nominal gain 4
import sympy as sp
A, R1, R2 = sp.symbols('A1 R1 R2', positive=True)
# KCL at X_F: Y = A*(X - XF), XF = Y*R2/(R1+R2)
X, Y, XF = sp.symbols('X Y X_F')
sol = sp.solve([sp.Eq(Y, A*(X-XF)), sp.Eq(XF, Y*R2/(R1+R2))], [Y, XF], dict=True)[0]
G = sp.simplify(sol[Y]/X)
print("Y/X =", G)
print("limit A->oo:", sp.limit(G, A, sp.oo))
# nominal 1+R1/R2 = 4 -> R1 = 3 R2, K = 1/4
Gn = sp.simplify(G.subs(R1, 3*R2))
print("Y/X with R1=3R2:", Gn)
Ga = Gn.subs(A, 1000); Gb = Gn.subs(A, 500)
print("(a) A1=1000: Y/X =", Ga, "=", sp.N(Ga, 10))
pct = sp.simplify((Gb - Ga)/Ga*100)
print("(b) A1=500: Y/X =", Gb, "=", sp.N(Gb, 10))
print("(b) % change exact =", pct, "=", sp.N(pct, 10), "%")
# approx: dG/G ~ (dA/A)/(1+KA)
approx = sp.Rational(-50)/(1+sp.Rational(1,4)*1000)
print("(b) sensitivity approx (-50%)/(1+KA1) =", sp.N(approx, 10), "%")
print("(a) approx 4*(1-1/(KA1)) =", sp.N(4*(1-sp.Rational(1,250)), 10))
