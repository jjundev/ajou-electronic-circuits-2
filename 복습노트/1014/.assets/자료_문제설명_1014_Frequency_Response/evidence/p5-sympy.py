import sympy as sp, math
f = sp.symbols('f', positive=True)
fp1, fz, fp2 = 1e8, 1e9, 1e10
H = sp.sqrt(1+(f/fz)**2)/(sp.sqrt(1+(f/fp1)**2)*sp.sqrt(1+(f/fp2)**2))
dB = lambda x: float(20*sp.log(H.subs(f, x), 10))
for x in [1e6, 1e7, 1e8, 3e8, 1e9, 3e9, 1e10, 1e11, 1e12]:
    print('f=%.0e  |H|/A0 = %7.2f dB' % (x, dB(x)))
for a, b in [(1e5, 1e6), (2e8, 5e8), (2e9, 5e9), (1e12, 1e13)]:
    print('slope %.0e-%.0e: %6.2f dB/dec' % (a, b, (dB(b)-dB(a))/math.log10(b/a)))
print('asymptotic: flat to 100MHz, -20 dB/dec to 1GHz (down 20 dB), flat 1-10GHz at -20 dB, -20 dB/dec beyond 10GHz')
