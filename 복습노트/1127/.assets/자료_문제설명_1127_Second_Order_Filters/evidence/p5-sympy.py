import sympy as sp

wn, q, w = sp.symbols("omega_n Q omega", positive=True)
gamma = sp.symbols("gamma", real=True)
den = (wn**2-w**2)**2 + (wn*w/q)**2
candidate = 2*w*(2*w**2+wn**2*(1/q**2-2))
assert sp.factor(sp.diff(den, w) - candidate) == 0
assert sp.factor(sp.diff(gamma**2/den, w) + gamma**2*candidate/den**2) == 0
boundary = sp.sqrt(2)/2
assert sp.factor(den.subs(q, boundary) - (wn**4+w**4)) == 0
print("D(omega) =", sp.expand(den))
print("D'(omega) = 2 omega [2 omega^2 + omega_n^2(1/Q^2 - 2)].")
print("With 0<Q<=1/sqrt(2), the bracket is strictly positive at every omega>0.")
print("D>0 and d|H|^2/domega = -gamma^2 D'/D^2. For gamma!=0 the response decreases strictly on omega>0.")
print("At Q=1/sqrt(2), D=omega_n^4+omega^4, so the flat derivative at DC still gives strict decay at positive frequencies.")
print("DC is the one-sided global maximum. There is no interior positive-frequency peak.")
print("If gamma=0, the response is identically zero and has no strict peak.")
