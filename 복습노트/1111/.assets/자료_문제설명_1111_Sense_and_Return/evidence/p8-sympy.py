# p8 (E12.06) proof: unity-gain bandwidth of closed-loop single-pole system independent of K
import sympy as sp
w, w0, A0, K = sp.symbols('omega omega_0 A_0 K', positive=True)
G = A0/(1+K*A0); wp = (1+K*A0)*w0
mag2 = G**2/(1+(w/wp)**2)                     # |H(jw)|^2 from Eq 12.22
sol = sp.solve(sp.Eq(mag2, 1), w)
wu = sp.simplify(sol[0])
print("exact omega_u =", wu)
target = w0*sp.sqrt(A0**2 - (1+K*A0)**2)
print("omega_u - w0*sqrt(A0^2-(1+K A0)^2) =", sp.simplify(wu - target))
print("valid only if A0/(1+K A0) > 1 (closed-loop dc gain above unity)")
# approximation 1+K A0 ~ K A0 :
approx1 = w0*sp.sqrt(A0**2 - (K*A0)**2)
print("with 1+KA0~KA0:", sp.simplify(approx1), "= A0 w0 sqrt(1-K^2)")
x = sp.symbols('x', positive=True)  # x = 1/(K A0) -> 0 means 1+KA0>>1
r = sp.simplify((target/approx1).subs(A0, 1/(K*x)))
print("ratio exact/approx with A0=1/(K x):", r, " limit x->0:", sp.limit(r, x, 0))
r2 = sp.limit(approx1/(A0*w0), K, 0)
print("lim K->0 of A0 w0 sqrt(1-K^2)/(A0 w0) =", r2, " -> omega_u ~ A0*w0 (= open-loop GBW), independent of K")
print("d(omega_u)/dK exact =", sp.simplify(sp.diff(target, K)), " (relative sensitivity small when K^2<<1, KA0>>1)")
# numeric illustration A0=200
for k in [sp.Rational(1,10), sp.Rational(1,2)]:
    print(f"A0=200,K={k}: omega_u/w0 exact={sp.N(target.subs({A0:200,K:k,w0:1}),6)}, approx A0={200}")
