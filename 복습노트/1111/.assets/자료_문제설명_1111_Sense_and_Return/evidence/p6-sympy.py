# p6 (E12.05) independent check: closed-loop response of single-pole amp, A0=200, K=0,0.1,0.5
import sympy as sp
w, w0, A0, K = sp.symbols('omega omega_0 A_0 K', positive=True)
s = sp.symbols('s')
A1 = A0/(1 + s/w0)                       # Eq 12.19
H = sp.simplify(A1/(1 + K*A1))           # negative feedback Y/X = A1/(1+K A1)
H22 = (A0/(1+K*A0))/(1 + s/((1+K*A0)*w0))  # Eq 12.22
print("H from A1/(1+K A1) - Eq12.22 =", sp.simplify(H - H22))
# pole / dc gain
pole = sp.solve(sp.denom(sp.together(H)), s)
print("pole:", pole, " dc gain:", sp.simplify(H.subs(s, 0)))
mag = sp.Abs(H22.subs(s, sp.I*w))
for k in [0, sp.Rational(1,10), sp.Rational(1,2)]:
    g = sp.simplify(H22.subs({A0:200, K:k, s:0}))
    bw = sp.simplify((1+k*200)*w0)
    m3 = sp.simplify(mag.subs({A0:200, K:k, w:bw})/g)
    print(f"K={k}: dc gain={g} = {sp.N(g,6)} ({sp.N(20*sp.log(g,10),5)} dB), -3dB BW={bw}, |H(BW)|/dc={m3}, GBW={sp.simplify(g*bw)}")
    # asymptote: high-frequency |H| -> A0*w0/w independent of K
    print("   lim w->oo |H|*w =", sp.limit(sp.simplify(mag.subs({A0:200, K:k}))*w, w, sp.oo))
    # sample points for plot (w/w0, dB)
    pts = [(r, round(float(20*sp.log(mag.subs({A0:200, K:k, w:r*w0}),10)),2)) for r in [0.1,1,10,21,101,200,1000]]
    print("   (w/w0, dB):", pts)
