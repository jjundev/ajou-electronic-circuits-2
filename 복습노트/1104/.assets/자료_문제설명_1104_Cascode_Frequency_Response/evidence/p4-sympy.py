import sympy as sp

s = sp.symbols("s")
Rs, Rp, Rd, gm1, gm2, Ci, Cx, Co, Cf = sp.symbols(
    "R_s R_p R_D g_m1 g_m2 C_i C_x C_o C_f", positive=True
)
G = gm2 + 1 / Rp
A = -gm1 / G
# KCL at gate, cascode junction, and output. Source is set to AC zero.
Y = sp.Matrix([
    [1 / Rs + s * (Ci + Cf), -s * Cf, 0],
    [gm1 - s * Cf, G + s * (Cx + Cf), 0],
    [0, -gm2, 1 / Rd + s * Co],
])
q = sp.expand(Y[:2, :2].det() * Rs / G)
tau_i = Rs * (Ci + Cf * (1 - A))
tau_x = (Cx + Cf * (1 - 1 / A)) / G
tau_o = Rd * Co
miller_q = sp.expand((1 + s * tau_i) * (1 + s * tau_x))
assert sp.simplify(Y.det() * Rs * Rd / G - q * (1 + s * tau_o)) == 0
assert sp.simplify(q.subs(Cf, 0) - miller_q.subs(Cf, 0)) == 0
assert sp.simplify(q.coeff(s, 1) - tau_i - (Cx + Cf) / G) == 0
assert sp.simplify(Y[:2, :2][1, 0].subs(s, 0) + G * A) == 0

a, b = (sp.factor(q.coeff(s, i)) for i in (1, 2))
vg, vx, vo = Y.inv() * sp.Matrix([1 / Rs, 0, 0])
assert sp.simplify(vo * q * (1 + s * tau_o) - gm2 * Rd * (s * Cf - gm1) / G) == 0
print("A(0) =", sp.factor(A))
print("Miller poles [rad/s] =", [-1 / tau for tau in (tau_i, tau_x, tau_o)])
print("Exact normalized characteristic = (1+s*R_D*C_o)*(1+a*s+b*s**2)")
print("a =", sp.expand(a))
print("b =", sp.factor(b))
print("Exact x/gate pair =", [(-a + sign * sp.sqrt(a**2 - 4*b))/(2*b) for sign in (1,-1)])
print("R_p -> infinity: G =", sp.limit(G, Rp, sp.oo))
print("R_p -> 0: A =", sp.limit(A, Rp, 0, dir="+"))
print("R_p -> 0: exact normalized gate/junction factor =", sp.simplify(sp.limit(q, Rp, 0, dir="+")))
print("C_f = 0: exact and Miller characteristics agree")
print("PASS: determinant, DC gain, first-order coefficient, zero-bridge limit, output transfer")
