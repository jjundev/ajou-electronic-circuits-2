import sympy as s

# Fig 10.42(a), one matched MOS differential half. M1 source and M3
# gate are AC ground, M1 drain=M3 source=x, M3 drain=output. Ideal upper
# current source is AC open. Positive i_t enters at output.
g1, g3, r1, r3 = s.symbols("g1 g3 r1 r3", positive=True)
u, x, v, it = s.symbols("u x v it")
eq_x = g1 * u + x / r1 + g3 * x + (x - v) / r3
eq_out_open = -g3 * x + (v - x) / r3
open_nodes = s.solve([eq_x, eq_out_open], [x, v], dict=True)[0]
Av_exact = s.factor(open_nodes[v] / u)

test_nodes = s.solve([eq_x.subs(u, 0), it - eq_out_open], [x, it], dict=True)[0]
Rout_exact = s.factor(v / test_nodes[it])

short_x = s.solve([eq_x.subs(v, 0)], [x], dict=True)[0][x]
Gm_exact = s.factor(eq_out_open.subs({x: short_x, v: 0}) / u)
assert s.simplify(Av_exact + Gm_exact * Rout_exact) == 0
assert s.simplify(Rout_exact - (r1 + r3 + g3 * r1 * r3)) == 0
assert s.simplify(Av_exact + g1 * r1 * (1 + g3 * r3)) == 0

gm, ro, z = s.symbols("gm ro z", positive=True)
equal_A = s.factor(Av_exact.subs({g1: gm, g3: gm, r1: ro, r3: ro}))
main_A = -(gm * ro) ** 2
relative = s.factor(equal_A / main_A)
assert s.limit(relative.subs(gm, z / ro), z, s.oo) == 1

mu = s.Rational(100, 10**6)  # A/V^2
w = s.Rational(20, 1) / s.Rational(18, 100)
lam = s.Rational(1, 10)  # V^-1
target = s.Integer(300)
# I_D = I_SS/2, gm=sqrt(2 mu w I_D), ro=1/(lambda I_D)
Iss_main = s.simplify(4 * mu * w / (lam**2 * target))
product_main = s.sqrt(target)
product_exact = s.simplify((s.sqrt(1 + 4 * target) - 1) / 2)
Iss_exact = s.simplify(4 * mu * w / (lam**2 * product_exact**2))
assert s.simplify((product_main**2) - target) == 0
assert s.simplify(product_exact * (1 + product_exact) - target) == 0
print("p3 KCL exact Gm =", Gm_exact)
print("p3 KCL exact Rout =", Rout_exact)
print("p3 KCL exact Av =", Av_exact)
print("equal-device exact Av =", equal_A)
print("main-term Av =", main_A)
print("exact/main ratio =", relative, "limit z=gm*ro->infinity =", s.limit(relative.subs(gm, z / ro), z, s.oo))
print("required I_SS main-term =", Iss_main, "A =", s.N(Iss_main * 1000, 10), "mA")
print("gm*ro at main-term design =", s.N(product_main, 8))
print("internal full-model I_SS for exact |Av|=300 =", s.N(Iss_exact * 1000, 10), "mA")
print("full-model |Av| at main-term design =", s.N(product_main * (1 + product_main), 8))
