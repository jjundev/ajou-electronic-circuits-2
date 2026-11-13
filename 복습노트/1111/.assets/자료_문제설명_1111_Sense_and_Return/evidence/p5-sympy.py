# p5 (P12.08) independent: CS stage w/ ideal current-source load as A1
import sympy as sp
mu, WL, I, lam, T, a = sp.symbols('muCox WL I_D lambda T a', positive=True)
gm = sp.sqrt(2*mu*WL*I); ro = 1/(lam*I)
A1 = gm*ro           # |A1| (CS stage inverting: A1 = -gm*ro)
print("|A1| = gm*ro =", sp.simplify(A1))
x, y = sp.symbols('x y', positive=True)   # mu -> x*mu, lam -> y*lam
ratio = sp.simplify(A1.subs({mu: x*mu, lam: y*lam}, simultaneous=True)/A1)
print("A1'/A1 =", ratio)
corners = {(xv, yv): ratio.subs({x: xv, y: yv}) for xv in [sp.Rational(9,10), sp.Rational(11,10)] for yv in [sp.Rational(8,10), sp.Rational(12,10)]}
for k, v in corners.items():
    print("  mu x", k[0], " lam x", k[1], " -> A1'/A1 =", sp.N(v, 8))
amin = min(corners.values(), key=lambda v: float(v)); amax = max(corners.values(), key=lambda v: float(v))
print("A1 range factor:", sp.N(amin, 8), "to", sp.N(amax, 8))
rel = (a - 1)/(1 + a*T)    # G'/G - 1 with T = nominal K*A1
req = []
for av in [amin, amax]:
    t = sp.solve(sp.Eq(sp.Abs(rel.subs(a, av)), sp.Rational(5,100)), T)
    req += t
    print("exact: |change|=5% at a =", sp.N(av, 8), "-> T =", [sp.N(z, 8) for z in t])
Tmin = max(req, key=lambda z: float(z))
print("exact minimum loop gain T =", sp.N(Tmin, 8))
print("residual check |rel| at Tmin, amin:", sp.N(sp.Abs(rel.subs({a: amin, T: Tmin})), 10),
      " amax:", sp.N(sp.Abs(rel.subs({a: amax, T: Tmin})), 10))
# linearized sensitivity: dA/A = 0.5 dmu/mu - dlam/lam -> worst 0.5*10% + 20% = 25%
lin = sp.Rational(1,2)*sp.Rational(10,100) + sp.Rational(20,100)
Tl = sp.solve(sp.Eq(lin/(1+T), sp.Rational(5,100)), T)
print("linearized: dA/A =", lin, "-> 1+T = dA/A / 0.05 -> T =", Tl)
# alternative: use exact A1 spread but differential closed-loop formula
for av in [amin, amax]:
    print("  differential with |dA/A|=", sp.N(abs(av-1), 6), "-> T =", sp.N(abs(av-1)/sp.Rational(5,100) - 1, 6))
