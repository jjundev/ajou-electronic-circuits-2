# p14 (P12.19) independent solver-s3: sense & return in Fig 12.86(a)-(d)
# CG input device M1: source = V_in, gate = feedback node, drain = n1. VDD = ac ground.
# lambda=0 except R_n = finite resistance at n1 for the ideal-current-source loads (a)-(c).
import sympy as sp
gm1, gm2, gm3, R1, Rn = sp.symbols('g_m1 g_m2 g_m3 R_1 R_n', positive=True)
vin, vfb, vt, n1, vo = sp.symbols('v_in v_fb v_t v_n1 v_o')
def idn(gm, vg, vs): return gm*(vg - vs)
def idp(gm, vg, vs): return gm*(vs - vg)

print("--- Return (common to all four) ---")
id1 = idn(gm1, vfb, vin)
print("i_d1 =", id1, "; d/dv_in + d/dv_fb =", sp.simplify(sp.diff(id1, vin) + sp.diff(id1, vfb)),
      "-> M1 responds to v_GS = v_fb - v_in: voltage subtraction")
print("v_in drives M1 source, v_fb drives M1 gate: different nodes => series (voltage) return")
print("(input is a voltage V_in at the source; the feedback does not inject a current into the input node)")

print("--- Sense ---")
print("(a) M1 gate tied to V_out (M2 follower output): v_fb = V_out -> voltage sense")
print("(b) M1 gate tied to V_out (M2 PMOS drain, R1): v_fb = V_out -> voltage sense")
print("(c) output = I_out through R1; M1 gate at n2: v_fb = R1*I_out -> current sense")
print("(d) M1 gate tied to V_out: v_fb = V_out -> voltage sense")
iout = sp.symbols('i_out')
print("check (c): v_n2 =", R1*iout, "; d v_fb / d I_out =", sp.diff(R1*iout, iout))

print("--- Loop polarity check (break at M1 gate, v_in=0, v_t at gate; return = v_fb) ---")
id1t = id1.subs({vin: 0, vfb: vt})
res = {}
a_n1 = sp.solve(sp.Eq(-n1/Rn, id1t), n1)[0]
res['a'] = sp.solve(sp.Eq(idn(gm2, a_n1, vo), 0), vo)[0]           # NMOS follower, ideal I_SS
res['b'] = sp.solve(sp.Eq(idp(gm2, a_n1, 0)*R1, vo), vo)[0]         # PMOS CS into R1
res['c'] = res['b']
d_n1 = sp.solve(sp.Eq(idp(gm3, n1, 0), id1t), n1)[0]               # diode M3 load
res['d'] = sp.solve(sp.Eq(idp(gm2, d_n1, 0)*R1, vo), vo)[0]
for k, v in res.items():
    L = sp.simplify(v/vt)
    print(f"({k}) v_return/v_t =", L, "->", "negative feedback" if L.could_extract_minus_sign() else "POSITIVE (return in phase with test)")
print("Note: loop polarity is not asked; observation about the figure as drawn only.")
