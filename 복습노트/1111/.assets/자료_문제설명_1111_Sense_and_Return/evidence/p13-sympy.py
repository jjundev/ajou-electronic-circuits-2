# p13 (P12.18) independent solver-s3: sense & return in Fig 12.85(a)-(f)
# Small-signal, ideal ISS (ac open), lambda=0 except a finite resistance R_n placed at the high-impedance
# node n2 (output resistance of I1 || r_O2) so the loop gain is finite. VDD = ac ground.
import sympy as sp
gm1, gm2, gm3, gm4, R1, R2, Rn = sp.symbols('g_m1 g_m2 g_m3 g_m4 R_1 R_2 R_n', positive=True)
vin, vfb, vt = sp.symbols('v_in v_fb v_t')
def idn(gm, vg, vs): return gm*(vg - vs)          # NMOS drain->source current
def idp(gm, vg, vs): return gm*(vs - vg)          # PMOS source->drain current

print("--- Return (common to all six): differential pair M1/M2 with ideal tail ---")
vn1 = sp.symbols('v_n1')
s = sp.solve(sp.Eq(idn(gm1, vin, vn1) + idn(gm1, vfb, vn1), 0), vn1)[0]   # matched pair gm1=gm2
id2 = sp.simplify(idn(gm1, vfb, s))
print("v_n1 =", s, "; i_d2 =", id2, " -> depends only on (v_fb - v_in): voltage subtraction")
print("v_in and v_fb enter at different nodes (gate M1, gate M2) => series (voltage) return")
print("check: d(i_d2)/dv_in + d(i_d2)/dv_fb =", sp.simplify(sp.diff(id2, vin) + sp.diff(id2, vfb)))

print("--- Sense: feedback voltage at M2 gate vs output quantity ---")
vout, iout = sp.symbols('v_out i_out')
sense = {
 'a': (vout, 'v_fb = V_out (M2 gate tied to V_out): voltage sense (shunt at output)'),
 'b': (vout, 'v_fb = V_out: voltage sense'),
 'c': (R1*iout, 'v_fb = V_n3 = R1*I_out (R1 in series with output current): current sense'),
 'd': (R1*iout, 'v_fb = V_n3 = R1*I_out: current sense'),
 'e': (R2/(R1+R2)*vout, 'v_fb = R2/(R1+R2)*V_out (divider across output): voltage sense'),
 'f': (vout, 'v_fb = V_out: voltage sense'),
}
for k, (expr, txt) in sense.items():
    print(f"({k}) v_fb =", expr, " |", txt)

print("--- Loop polarity check (break at M2 gate, v_in=0, v_t applied to M2 gate; return = v_fb) ---")
id2t = sp.simplify(id2.subs({vin: 0, vfb: vt}))       # = gm1/2 * vt, flows from n2 down into M2
n2, vo, n3 = sp.symbols('v_n2 v_o v_n3')
res = {}
# (a) n2: I1 open, R_n to ac gnd ; KCL: -n2/Rn = id2  ; M3 NMOS follower, I2 ideal -> id3=0 -> vo=n2
a_n2 = sp.solve(sp.Eq(-n2/Rn, id2t), n2)[0]; a_vo = sp.solve(sp.Eq(idn(gm3, a_n2, vo), 0), vo)[0]
res['a'] = a_vo
# (b)/(c) PMOS M3 CS into R1: vo = idp*R1
b_vo = sp.solve(sp.Eq(idp(gm3, a_n2, 0)*R1, vo), vo)[0]; res['b'] = b_vo; res['c'] = b_vo
# (d) NMOS follower M3 into R1: idn(gm3, n2, vo) = vo/R1
res['d'] = sp.solve(sp.Eq(idn(gm3, a_n2, vo), vo/R1), vo)[0]
# (e) output node = M2 drain, I1 open, R_n || (R1+R2); vfb = R2/(R1+R2)*vo
e_vo = sp.solve(sp.Eq(-vo/Rn - vo/(R1+R2), id2t), vo)[0]; res['e'] = R2/(R1+R2)*e_vo
# (f) n2 has diode M4: current from VDD into n2 = idp(gm4, n2, 0) = -gm4*n2 ; KCL: -gm4*n2 = id2
f_n2 = sp.solve(sp.Eq(idp(gm4, n2, 0), id2t), n2)[0]; res['f'] = sp.solve(sp.Eq(idp(gm3, f_n2, 0)*R1, vo), vo)[0]
for k, v in res.items():
    L = sp.simplify(v/vt)
    print(f"({k}) v_return/v_t =", L, "->", "negative feedback" if sp.simplify(L).could_extract_minus_sign() else "POSITIVE (return in phase with test)")
print("Note: loop polarity is not asked; it is recorded only as an observation about the figure as drawn.")
