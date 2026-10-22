import sympy as s

# Fig 10.19(a): upper pnp base and emitter are AC ground. Its controlled
# current vanishes but finite r_o3 remains at the output.
gm1, ro1, ro3 = s.symbols("g_m1 r_o1 r_o3", positive=True)
vin, vout, it = s.symbols("v_in v_out i_t")
eq = gm1 * vin + vout / ro1 + vout / ro3
v_solution = s.solve([eq], [vout], dict=True)[0][vout]
av = s.factor(v_solution / vin)
i_test = s.solve([it - vout / ro1 - vout / ro3], [it], dict=True)[0][it]
rout = s.factor(vout / i_test)
Gm = gm1

assert s.simplify(av + Gm * rout) == 0
assert s.simplify(rout - ro1 * ro3 / (ro1 + ro3)) == 0
assert s.simplify(s.limit(av, ro3, s.oo) + gm1 * ro1) == 0
print("p2 model: matched differential halves; pnp base/emitter AC ground; finite r_o3")
print("Gm =", Gm)
print("Rout =", rout)
print("Av_differential =", av)
print("limit ro3->infinity =", s.limit(av, ro3, s.oo))
print("equal-ro limit =", s.simplify(av.subs(ro3, ro1)))
