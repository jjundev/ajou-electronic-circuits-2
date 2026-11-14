# verifier-p1: P12.21 independent sense/return check (Fig 12.88 a,b)
# method: qualitative structure table + symbolic small-signal support (lambda=0, ideal sources ac-open)
import sympy as sp

print("== 1. Structural connection table (from problem.md netlist + figure) ==")
struct = {
 "a": {"R_F terminals": ("n1 = Q1 base = I_in node", "Vout = Q1 collector = output node"),
       "output side": "R_F end sits ON the Vout node, in parallel with R_C/load (Vout to ac ground) -> senses output VOLTAGE (parallel/shunt sense)",
       "input side": "R_F other end sits ON the I_in node n1; i_F and I_in sum as currents at that node (KCL) -> returns CURRENT (parallel/shunt return)",
       "verdict": "voltage sense (parallel) / current return (parallel) = voltage-current (shunt-shunt)"},
 "b": {"R_F terminals": ("n1 = M1 gate = I_in node", "Vout = M3 source = output node"),
       "output side": "R_F end sits ON the Vout node, in parallel with I_SS/load -> senses output VOLTAGE (parallel)",
       "input side": "R_F other end sits ON the I_in node n1 (M1 gate); currents summed at node -> returns CURRENT (parallel)",
       "verdict": "voltage sense (parallel) / current return (parallel) = voltage-current (shunt-shunt)"},
}
for k, v in struct.items():
    print("(%s)" % k)
    for kk, vv in v.items():
        print("   ", kk, ":", vv)
print("Ideal-network impedances: voltage sensing -> network input in parallel with output, ideal Z_in=inf;")
print("current return -> network output in parallel with I_in, ideal Z_out=inf. A large R_F approximates both (book Fig 12.24(d)).")
print("No element is in series with an output branch (no current sensing) and nothing is inserted in series with the")
print("input loop (no voltage subtraction), so series-type options are excluded in both circuits.")

gm, rpi, RC, RF, Iin, V1, Vo, Vx, vt = sp.symbols('g_m r_pi R_C R_F I_in V1 Vout V_x v_t', positive=True)

print("\n== 2. (a) BJT CE + collector-base R_F ==")
s = sp.solve([sp.Eq(Iin + (Vo - V1)/RF, V1/rpi),
              sp.Eq(gm*V1 + Vo/RC + (Vo - V1)/RF, 0)], [V1, Vo], dict=True)[0]
Zt_a = sp.simplify(s[Vo]/Iin); Rin_a = sp.simplify(s[V1]/Iin)
print("Vout/Iin =", Zt_a)
print("lim gm->oo Vout/Iin =", sp.limit(Zt_a, gm, sp.oo), " (ideal transimpedance set by R_F: current in, voltage out)")
print("Rin =", Rin_a)
Rin0 = rpi*(RF+RC)/(rpi+RF+RC)
print("lim gm->oo Rin =", sp.limit(Rin_a, gm, sp.oo), " ; Rin/Rin(gm=0) =", sp.simplify(Rin_a/Rin0))
v1s = sp.solve(sp.Eq((Vx - V1)/RF, V1/rpi), V1)[0]
Rout_a = sp.simplify(Vx/(gm*v1s + Vx/RC + (Vx - v1s)/RF))
Rout0 = RC*(RF+rpi)/(RC+RF+rpi)
print("Rout =", Rout_a)
print("lim gm->oo Rout =", sp.limit(Rout_a, gm, sp.oo), " ; Rout/Rout(gm=0) =", sp.simplify(Rout_a/Rout0))
print("-> both Rin and Rout fall with loop gain: parallel at output (voltage sense) and parallel at input (current return)")
vc = -gm*vt*Rout0
T_a = sp.simplify(-(vc*rpi/(rpi+RF))/vt)
print("loop gain T_a =", T_a, " > 0 -> negative feedback (CE inverts)")

print("\n== 3. (b) M1/M2 pair -> n3 (I1 load) -> follower M3 -> Vout, R_F back to M1 gate ==")
g1, g3, R3, RS = sp.symbols('g_m1 g_m3 R_3 R_S', positive=True)  # R3: ac R at n3; RS: ac R at Vout (finite to keep algebra regular)
v1, v3, vo = sp.symbols('v1 v3 vo')
id2 = -g1*v1/2   # ideal tail, Vb ac ground, gm1=gm2
sb = sp.solve([sp.Eq(0, id2 + v3/R3),
               sp.Eq(g3*(v3 - vo), vo/RS + (vo - v1)/RF),
               sp.Eq(Iin + (vo - v1)/RF, 0)], [v1, v3, vo], dict=True)[0]
print("v3/v1 =", sp.simplify(sb[v3]/sb[v1]), " (>0: M1 gate -> M2 drain is NON-inverting)")
Zt_b = sp.simplify(sb[vo]/Iin); Rin_b = sp.simplify(sb[v1]/Iin)
print("Vout/Iin =", Zt_b)
print("Rin =", Rin_b)
k = (g1*R3/2)*g3*RS/(1 + g3*RS)   # v_ret/v_t with loop broken at M1 gate (no current in R_F, v_ret = vo)
T_b = sp.simplify(-k)
print("loop gain T_b =", T_b, " < 0 -> forward path non-inverting, R_F feedback is POSITIVE in sign")
den = sp.denom(sp.together(Rin_b))
print("denominator of Rin_b == 2(1+g_m3 R_S)(1+T_b):", sp.simplify(den - 2*(1+g3*RS)*(1+T_b)) == 0, " (1+T_b -> 0 possible: positive-feedback signature)")
print("Structure (sense/return type) is unaffected by sign: still voltage sense (parallel) / current return (parallel).")

print("\n== RESULT ==")
print("(a) sense: output voltage (parallel); return: current to input (parallel)")
print("(b) sense: output voltage (parallel); return: current to input (parallel)")
