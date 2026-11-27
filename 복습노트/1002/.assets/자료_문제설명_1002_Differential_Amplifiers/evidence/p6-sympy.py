import sympy as sp

vi, vo, vb, vn, vp = sp.symbols("v_i v_o v_b v_n v_p")
gn, gp, gon, gop, gpb = sp.symbols("g_mn g_mp g_on g_op g_pi_p", positive=True)
r, rpi = sp.symbols("R r_pi", positive=True)
tail, vt, va, beta = sp.Rational(1, 1000), sp.Rational(26, 1000), sp.Integer(10), sp.Integer(100)
alpha = beta / (beta + 1)
ic_input = alpha * tail / 2
ic_middle = alpha * ic_input

# (1) Q3's base sees its own collector through R, and its emitter is grounded.
base_kcl = (vb - vo) / r + vb / rpi
vb_out = sp.solve(base_kcl, vb)[0]
i_p = (gop * vo + gp * vb + (vo - vb) / r).subs(vb, vb_out)
i_half = sp.factor(gn * vi + gon * vo + i_p)
r_half = sp.factor(1 / i_half.diff(vo))
gain_1 = sp.factor(sp.solve(i_half, vo)[0] / vi)
vals_1 = {gn: ic_input / vt, gp: ic_middle / vt, gon: ic_input / va,
          gop: ic_middle / va, rpi: beta * vt / ic_middle, r: 10000}
vals_1_eq = {gn: tail / (2 * vt), gp: tail / (2 * vt), gon: tail / (2 * va),
             gop: tail / (2 * va), rpi: 2 * beta * vt / tail, r: 10000}

print("(1) PNP-load conductance =", sp.factor(i_p.diff(vo)))
print("(1) R_half =", r_half)
print("(1) Numerical R_half [ohm] =", r_half.subs(vals_1).evalf(12))
print("(1) Numerical R_diff [ohm] =", (2 * r_half).subs(vals_1).evalf(12))
print("(1) Numerical A_v =", gain_1.subs(vals_1).evalf(12))
print("(1) Equal-bias-current approximation [R_half (ohm), R_diff (ohm), A_v] =",
      [k.subs(vals_1_eq).evalf(12) for k in (r_half, 2 * r_half, gain_1)])

# (2) The cascode bases are AC ground and R/2 loads the upper emitter.
gm1, gm3, gm5, go1, go3, go5, go7, gpi3, gpi5 = sp.symbols(
    "g_m1 g_m3 g_m5 g_o1 g_o3 g_o5 g_o7 g_pi3 g_pi5", positive=True
)
i_n = go3 * vo - (go3 + gm3) * vn
i_p = go5 * vo - (go5 + gm5) * vp
node_kcl = [
    gm1 * vi + (go1 + gpi3) * vn - i_n,
    (go7 + 2 / r + gpi5) * vp - i_p,
]
nodes = sp.solve(node_kcl, [vn, vp])
i_n = i_n.subs(nodes)
i_p = i_p.subs(nodes)
g_eff = sp.factor(i_n.diff(vi))
r_n = sp.factor(1 / i_n.diff(vo))
r_p = sp.factor(1 / i_p.diff(vo))
r_half_2 = 1 / (1 / r_n + 1 / r_p)
gain_2 = sp.factor(sp.solve(i_n + i_p, vo)[0] / vi)
assert sp.simplify(gain_2 + g_eff * r_half_2) == 0

vals_2 = {
    gm1: ic_input / vt, gm3: ic_middle / vt, gm5: ic_middle / vt,
    go1: ic_input / va, go3: ic_middle / va, go5: ic_middle / va,
    go7: ic_input / va, gpi3: ic_middle / (beta * vt), gpi5: ic_middle / (beta * vt),
    r: 10000,
}
vals_2_eq = {
    gm1: tail / (2 * vt), gm3: tail / (2 * vt), gm5: tail / (2 * vt),
    go1: tail / (2 * va), go3: tail / (2 * va), go5: tail / (2 * va),
    go7: tail / (2 * va), gpi3: tail / (2 * beta * vt), gpi5: tail / (2 * beta * vt),
    r: 10000,
}
print("(2) G_m,eff =", g_eff)
print("(2) R_n =", r_n)
print("(2) R_p =", r_p)
print("(2) Numerical R_n [ohm] =", r_n.subs(vals_2).evalf(12))
print("(2) Numerical R_p [ohm] =", r_p.subs(vals_2).evalf(12))
print("(2) Numerical R_half [ohm] =", r_half_2.subs(vals_2).evalf(12))
print("(2) Numerical R_diff [ohm] =", (2 * r_half_2).subs(vals_2).evalf(12))
print("(2) Numerical A_v =", gain_2.subs(vals_2).evalf(12))
print("(2) Equal-bias-current approximation [R_half (ohm), R_diff (ohm), A_v] =",
      [k.subs(vals_2_eq).evalf(12) for k in (r_half_2, 2 * r_half_2, gain_2)])
