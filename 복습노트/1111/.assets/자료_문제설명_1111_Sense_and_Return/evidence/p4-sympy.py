# p4 (P12.07) independent: A1 changes 20%, closed-loop change < 1%
import sympy as sp
T, a, A, K = sp.symbols('T a A1 K', positive=True)
G = lambda Ax: Ax/(1+K*Ax)
rel = sp.simplify(G(a*A)/G(A) - 1)       # a = A1'/A1
rel = sp.simplify(rel.subs(K, T/A))      # T = nominal loop gain K*A1
print("relative change of closed-loop gain =", sp.factor(rel))
# small-change (differential) form
S = sp.simplify(sp.diff(G(A), A)*A/G(A))
print("sensitivity (dG/G)/(dA/A) =", S)
Td = sp.solve(sp.Eq(sp.Rational(20,100)/(1+T), sp.Rational(1,100)), T)
print("differential: 0.2/(1+T)=0.01 -> T =", Td)
for av in [sp.Rational(8,10), sp.Rational(12,10)]:
    t = sp.solve(sp.Eq(sp.Abs(rel.subs(a, av)), sp.Rational(1,100)), T)
    print(f"exact a={av}: |change|=1% at T =", t, [sp.N(x, 8) for x in t])
# check residuals
print("check T=19 differential:", sp.Rational(20,100)/(1+19))
print("exact change at T=19, a=0.8:", sp.N(rel.subs({a: sp.Rational(8,10), T: 19}), 8),
      " a=1.2:", sp.N(rel.subs({a: sp.Rational(12,10), T: 19}), 8))
print("exact change at T=23.75, a=0.8:", sp.N(rel.subs({a: sp.Rational(8,10), T: sp.Rational(95,4)}), 8))
