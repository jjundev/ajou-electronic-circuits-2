# p7 (P12.09) independent check: "-1 dB" bandwidth = frequency where gain drops 10%
import sympy as sp
w, w0, A0, K = sp.symbols('omega omega_0 A_0 K', positive=True)
def bw_at(frac, dc, wp):
    # |dc/(1+j w/wp)| = frac*dc
    sol = sp.solve(sp.Eq(1/(1+(w/wp)**2), frac**2), w)
    return [sp.simplify(x) for x in sol]
f = sp.Rational(9,10)
ol = bw_at(f, A0, w0)
cl = bw_at(f, A0/(1+K*A0), (1+K*A0)*w0)
print("open-loop -1dB(10%) BW:", ol, "=", [sp.N(x.subs(w0,1),6) for x in ol], "* w0")
print("closed-loop -1dB(10%) BW:", cl)
print("ratio closed/open:", sp.simplify(cl[0]/ol[0]))
print("check sqrt(19)/9 =", sp.N(sp.sqrt(19)/9, 8))
# exact -1 dB variant (gain factor 10^(-1/20) = 0.8913, i.e. ~10.9% drop)
f2 = 10**sp.Rational(-1,20)
ol2 = bw_at(f2, A0, w0); cl2 = bw_at(f2, A0/(1+K*A0), (1+K*A0)*w0)
print("strict -1 dB: open", [sp.N(x.subs(w0,1),6) for x in ol2], "*w0; ratio", sp.simplify(cl2[0]/ol2[0]))
print("10% drop in dB:", sp.N(20*sp.log(f,10),5), "dB")
