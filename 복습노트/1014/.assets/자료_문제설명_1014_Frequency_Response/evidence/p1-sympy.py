# p1 (E11.3) qualitative: a video system with insufficient bandwidth acts as a low-pass filter.
# Model: first-order LPF H(s)=1/(1+s/wp); its response to an ideal edge (step) has a finite rise time.
import sympy as sp
s, t, wp = sp.symbols('s t omega_p', positive=True)
v = sp.inverse_laplace_transform(1/(s*(1+s/wp)), s, t)
print('step response:', sp.simplify(v))
t10 = sp.solve(sp.Eq(1-sp.exp(-wp*t), sp.Rational(1, 10)), t)[0]
t90 = sp.solve(sp.Eq(1-sp.exp(-wp*t), sp.Rational(9, 10)), t)[0]
tr = sp.simplify(t90-t10)
print('rise time 10-90% =', tr, '=', sp.N(tr*wp), '/omega_p')
print('limit wp->oo of rise time:', sp.limit(tr, wp, sp.oo), ' (ideal sharp edge only with infinite bandwidth)')
for f in [5e6, 1e6]:
    print('f_-3dB = %.0e Hz -> rise time %.1f ns' % (f, float(tr.subs(wp, 2*sp.pi*f))*1e9))
print('Conclusion: smaller bandwidth -> slower edges -> sharp black/white transitions smear; image looks blurry, fine detail lost.')
