import sympy as sp

vi, vo, ve, vl, vx = sp.symbols("v_i v_o v_e v_l v_x")
gm, ge, gload, rc, re = sp.symbols("g_m g_e g_load R_C R_E", positive=True)
r1, r2, ron, rop = sp.symbols("R_1 R_2 r_on r_op", positive=True)
gm1, gm2, go1, go2, gpi2 = sp.symbols("g_m1 g_m2 g_o1 g_o2 g_pi2", positive=True)
alpha = sp.symbols("alpha", positive=True)
iee = i1 = sp.Rational(1, 2000)
vt = sp.Rational(1, 40)
values_a = {gm: alpha * iee / vt, ge: iee / vt, gload: alpha * iee / vt, rc: 450, re: 100}

# (a) The diode-connected upper device's emitter is v_l.
eq_a = [
    ge * (ve - vi) + ve / (re / 2),
    gm * (vi - ve) + (vo - vl) / rc,
    gload * vl + (vl - vo) / rc,
]
gain_a = sp.factor(sp.solve(eq_a, [ve, vo, vl])[vo] / vi)
gain_a_dc = sp.factor(gain_a.subs(values_a))
print("(1) KCL gain =", gain_a)
print("(1) Equal-beta DC relation gives A_v =", gain_a_dc)
print("(1) High-beta limit =", sp.limit(gain_a_dc, alpha, 1))

# (b) R1 + R2 bridges the two outputs, so the differential half circuit
# sees (R1 + R2)/2. Both transistor output resistances end at AC ground.
eq_b = gm * vi + vo / ron + vo / rop + vo / ((r1 + r2) / 2)
gain_b = sp.factor(sp.solve(eq_b, vo)[0] / vi)
current_b = alpha * iee / 2
gain_b_dc = gain_b.subs(
    {gm: current_b / vt, ron: 5 / current_b, rop: 5 / current_b, r1: 10000, r2: 10000}
)
print("(2) KCL gain =", gain_b)
print("(2) Finite-alpha relation gives A_v =", sp.factor(gain_b_dc))
print("(2) High-beta limit =", sp.limit(gain_b_dc, alpha, 1))

# (c) An ideal current source is open at signal frequencies.
i_out = go2 * vo - (go2 + gm2) * vx
eq_c = [gm1 * vi + (go1 + gpi2) * vx - i_out, i_out]
gain_c = sp.factor(sp.solve(eq_c, [vx, vo])[vo] / vi)
beta = sp.Integer(200)
alpha_c = beta / (beta + 1)
ic2 = i1
ic1 = i1 / alpha_c
values_c = {gm1: ic1 / vt, gm2: ic2 / vt, go1: ic1 / 5, go2: ic2 / 5, gpi2: ic2 / (beta * vt)}
values_c_equal_current = {**values_c, gm1: ic2 / vt, go1: ic2 / 5}
gain_c_dc = gain_c.subs(values_c)
print("(3) KCL gain =", gain_c)
print("(3) I_C1, I_C2 [mA] =", 1000 * ic1, 1000 * ic2)
print("(3) A_v =", gain_c_dc, "=", gain_c_dc.evalf(12))
print("(3) Equal-bias-current approximation =", gain_c.subs(values_c_equal_current))
