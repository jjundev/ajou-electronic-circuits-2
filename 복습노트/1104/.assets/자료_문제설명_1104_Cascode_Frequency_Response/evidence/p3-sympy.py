import sympy as sp

s, vb, ve, it = sp.symbols("s vb ve it")
a, b, gm, cu, cp = sp.symbols("a b gm cu cp", positive=True)
A, B = a + s*cu, b + s*cp
base = A*vb + B*(vb-ve)
emitter = (B+gm)*(ve-vb) - it
sol = sp.solve((base, emitter), (vb, ve))
zout = sp.factor(sol[ve]/it)
assert sp.cancel(zout - (A+B)/(A*(B+gm))) == 0
print("Base KCL:", base)
print("Emitter KCL:", emitter)
print("Zout =", zout)
print("Zout(0) =", zout.subs(s, 0))
print("lim s*Zout =", sp.limit(s*zout, s, sp.oo))
print("Cmu=0:", sp.factor(zout.subs(cu, 0)))
print("RB=0:", sp.limit(zout, a, sp.oo))
print("omega_z, omega_p1, omega_p2:", (a+b)/(cu+cp), a/cu, (b+gm)/cp)

x, P, Q, N = sp.symbols("x P Q N", positive=True)
mag_squared = (1+N*x)/((1+P*x)*(1+Q*x))
derivative_numerator = sp.factor(sp.diff(mag_squared, x)*((1+P*x)*(1+Q*x))**2)
assert sp.expand(derivative_numerator - (N-P-Q-2*P*Q*x-N*P*Q*x**2)) == 0
print("Normalized squared magnitude derivative numerator:", derivative_numerator)
print("x=omega^2, N=omega_z^-2, P=omega_p1^-2, Q=omega_p2^-2")
