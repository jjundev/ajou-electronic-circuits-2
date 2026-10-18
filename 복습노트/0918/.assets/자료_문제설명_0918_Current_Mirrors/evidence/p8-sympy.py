import sympy as sp
# Ideal BJT mirrors (beta->inf, no Early): I_C = A*I_S*exp(V_BE/V_T)
IREF, IC2 = sp.Rational(25,10**6), sp.Rational(1,1000)
VT, IS, VBE = sp.symbols('V_T I_S V_BE', positive=True)
n, m = sp.symbols('n m', positive=True)
# Mirror 1: QREF1 (area 1) -> QM (area n), same V_BE at X1
ICM = n*IS*sp.exp(VBE/VT) / (IS*sp.exp(VBE/VT)) * IREF
print("I_C,M/I_REF =", sp.simplify(ICM/IREF))
# Mirror 2: QREF2 (area 1) carries I_C,M -> Q2 (area m)
I2 = m*ICM
total_ratio = sp.nsimplify(IC2/IREF)
print("required n*m =", total_ratio)
# Count of unit devices in mirrors: 1 (QREF1) + n + 1 (QREF2) + m, with n*m = 40
best = []
for nn in sp.divisors(int(total_ratio)):
    mm = int(total_ratio)//nn
    best.append((2+nn+mm, nn, mm))
best.sort()
for b in best: print("units=%d  n=%d  m=%d" % b)
# continuous optimum
x = sp.symbols('x', positive=True)
f = 2 + x + total_ratio/x
xs = sp.solve(sp.diff(f, x), x)
print("continuous optimum n=m=sqrt(40)=", xs, float(xs[0]))
nb, mb = best[0][1], best[0][2]
print("check: I_C,M =", ICM.subs(n, nb)*10**6, "uA ; |I_C2| =", I2.subs({n:nb, m:mb})*1000, "mA")
print("ANSWER p8:main: I_C,M/I_REF = 5, |I_C2|/I_C,M = 8 (or 8 and 5); I_C,M = 125 uA, |I_C1|=|I_C2| = 1 mA; 15 unit mirror transistors (1+5+1+8)")
