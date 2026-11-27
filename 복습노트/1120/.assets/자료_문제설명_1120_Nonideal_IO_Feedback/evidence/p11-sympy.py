# Razavi 12.47 (Fig. 12.110) independent verification, lambda > 0
# Topology (checked against figure): i_in -> node A = source of CG M1 (gate V_b);
# M1 drain = X, R_D1 from X to VDD; X drives gate of CS M2 (source grounded),
# M2 drain = v_out with ideal current-source load; R1: v_out-N, R2: N-gnd, RF: N-A.
import sympy as sp

gm1, gm2, rO1, rO2, RD1, R1, R2, RF = sp.symbols(
    'g_m1 g_m2 r_O1 r_O2 R_D1 R_1 R_2 R_F', positive=True)

def par(a, b):
    return a * b / (a + b)

lines = []
def out(label, expr):
    s = f"{label} = {sp.simplify(expr)}"
    lines.append(s)

# ---------------------------------------------------------------- (a) exact source-side resistance of M1
vA, vX, it = sp.symbols('v_A v_X i_t')
# i_d = drain current (into drain, out of source); gate AC ground
i_d = gm1 * (0 - vA) + (vX - vA) / rO1
eqs = [sp.Eq(it, -i_d),                 # test current injected into source = -i_d
       sp.Eq(vX / RD1 + i_d, 0)]        # KCL at X: R_D1 to AC ground
sol = sp.solve(eqs, [vA, vX], dict=True)[0]
RS_exact = sp.simplify(sol[vA] / it)
RS_class = par(1 / gm1, rO1)
out("R_S1,exact (KCL)", sp.factor(RS_exact))
out("R_S1,class = (1/gm1)||rO1", sp.factor(RS_class))
ratio_RS = sp.simplify(RS_class / RS_exact)
out("R_S1,class / R_S1,exact", ratio_RS)

# ---------------------------------------------------------------- (b) loaded two-port (replica) analysis
RLin = RF + par(R1, R2)        # feedback network seen at input with output port shorted
RLout = R1 + par(R2, RF)       # feedback network seen at output with input port shorted

def open_loop(RS):
    Rin_o = par(RS, RLin)
    Rout_o = par(rO2, RLout)
    # Thevenin of i_in || RLin: v_th = i_in*RLin, R_th = RLin
    # CG gain v_X/v_th = R_D1/(R_th + R_S1)  (current into source == current up through R_D1)
    A_cg = RLin * RD1 / (RLin + RS)        # v_X / i_in
    A_cs = -gm2 * Rout_o                   # v_out / v_X
    R0 = A_cg * A_cs
    return Rin_o, Rout_o, R0

Rin_o, Rout_o, R0 = open_loop(RS_class)
# K: apply v_out, short input (v_A = 0); i_fb = current drawn OUT of input node by network.
vN = RLin  # placeholder overwritten below
vN = par(R2, RF) / (R1 + par(R2, RF))      # v_N per unit v_out
i_into_A = vN / RF                          # current from N through RF into A per unit v_out
K = -i_into_A                               # convention: i_error = i_in - K*v_out
K = sp.simplify(K)

lines.append("")
lines.append("== Class-rule replica results (R_S1 = (1/gm1)||rO1) ==")
out("R_in,open", sp.factor(Rin_o))
out("R_out,open", sp.factor(Rout_o))
out("R_0 = v_out/i_in (open)", sp.factor(R0))
lines.append("  i.e. R_0 = -g_m2*R_D1*[rO2||(R1+R2||RF)] * (RF+R1||R2)/((RF+R1||R2)+(1/gm1||rO1))")
out("K (i_err = i_in - K v_out)", sp.factor(K))
lines.append("  i.e. K = -(R2||RF)/(RF*(R1+R2||RF)) = -R2/(R1R2+R1RF+R2RF)")
LG = sp.simplify(K * R0)
out("K*R_0 (loop gain)", sp.factor(LG))
# sign check: all symbols positive -> check positivity
lines.append(f"K*R_0 > 0 (negative feedback)? sympy is_positive: {sp.factor(LG).is_positive}")
lines.append(f"K at R_1 -> 0: {sp.limit(K, R1, 0)}   (Example 12.29 limit -1/R_F)")
Acl = R0 / (1 + LG)
Rin_c = Rin_o / (1 + LG)
Rout_c = Rout_o / (1 + LG)
lines.append("Closed-loop: v_out/i_in = R_0/(1+K R_0), R_in,closed = R_in,open/(1+K R_0), R_out,closed = R_out,open/(1+K R_0)")

# ---------------------------------------------------------------- (c) exact source resistance and limits
Rin_e, Rout_e, R0_e = open_loop(RS_exact)
lines.append("")
lines.append("== Exact-R_S1 comparison ==")
out("R_0,exact", sp.factor(R0_e))
out("R_in,open,exact", sp.factor(Rin_e))
r_R0 = sp.simplify(R0 / R0_e)
r_Rin = sp.simplify(Rin_o / Rin_e)
out("R_0,class/R_0,exact", sp.factor(r_R0))
out("R_in,class/R_in,exact", sp.factor(r_Rin))
lines.append(f"limit rO1->oo (R_D1 fixed): R_S ratio {sp.limit(ratio_RS, rO1, sp.oo)}, R_0 ratio {sp.limit(r_R0, rO1, sp.oo)}, R_in ratio {sp.limit(r_Rin, rO1, sp.oo)}")
lines.append(f"limit R_D1->0: R_S ratio {sp.limit(ratio_RS, RD1, 0)}, R_0 ratio {sp.simplify(sp.limit(r_R0, RD1, 0))}, R_in ratio {sp.simplify(sp.limit(r_Rin, RD1, 0))}")
# also via x = R_D1/r_O1 -> 0
x = sp.symbols('x', positive=True)
lines.append(f"limit x=R_D1/rO1 -> 0 (R_D1 = x*rO1): R_0 ratio {sp.simplify(sp.limit(sp.simplify(r_R0.subs(RD1, x*rO1)), x, 0))}, R_in ratio {sp.simplify(sp.limit(sp.simplify(r_Rin.subs(RD1, x*rO1)), x, 0))}")

# ---------------------------------------------------------------- numeric cross-check with full nodal analysis
vA, vX, vO, vN_, iin = sp.symbols('vA vX vO vN iin')
i_d1 = gm1 * (0 - vA) + (vX - vA) / rO1
nod = [
    sp.Eq(iin, (vA - vN_) / RF - i_d1),               # node A
    sp.Eq(vX / RD1 + i_d1, 0),                         # node X
    sp.Eq(gm2 * vX + vO / rO2 + (vO - vN_) / R1, 0),   # node out
    sp.Eq((vN_ - vO) / R1 + vN_ / R2 + (vN_ - vA) / RF, 0),  # node N
]
ns = sp.solve(nod, [vA, vX, vO, vN_], dict=True)[0]
A_exact_full = sp.simplify(ns[vO] / iin)
Rin_full = sp.simplify(ns[vA] / iin)
# output resistance: i_in = 0, test current into out
it2 = sp.symbols('it2')
nod2 = [
    sp.Eq(0, (vA - vN_) / RF - i_d1),
    sp.Eq(vX / RD1 + i_d1, 0),
    sp.Eq(it2, gm2 * vX + vO / rO2 + (vO - vN_) / R1),
    sp.Eq((vN_ - vO) / R1 + vN_ / R2 + (vN_ - vA) / RF, 0),
]
ns2 = sp.solve(nod2, [vA, vX, vO, vN_], dict=True)[0]
Rout_full = sp.simplify(ns2[vO] / it2)

vals = {gm1: sp.Rational(5, 1000), gm2: sp.Rational(5, 1000), rO1: 20000, rO2: 20000,
        RD1: 2000, R1: 10000, R2: 5000, RF: 10000}
Acl_e = R0_e / (1 + K * R0_e); Rin_ce = Rin_e / (1 + K * R0_e); Rout_ce = Rout_e / (1 + K * R0_e)
lines.append("")
lines.append("== Numeric check: gm1=gm2=5mS, rO1=rO2=20k, RD1=2k, R1=10k, R2=5k, RF=10k ==")
lines.append(f"{'quantity':<14}{'class replica':>16}{'exact-RS replica':>18}{'full nodal':>14}")
for name, a, b, c in [("v_out/i_in", Acl, Acl_e, A_exact_full),
                      ("R_in,closed", Rin_c, Rin_ce, Rin_full),
                      ("R_out,closed", Rout_c, Rout_ce, Rout_full)]:
    lines.append(f"{name:<14}{float(a.subs(vals)):>16.3f}{float(b.subs(vals)):>18.3f}{float(c.subs(vals)):>14.3f}")
lines.append(f"open-loop R_0 class={float(R0.subs(vals)):.1f}, exact={float(R0_e.subs(vals)):.1f}, K*R_0 class={float(LG.subs(vals)):.3f}")
# with very large rO1 (R_D1/rO1 -> 0) class and exact agree
vals2 = dict(vals); vals2[rO1] = 10**9
lines.append(f"rO1=1e9: v_out/i_in class={float(Acl.subs(vals2)):.4f}, exact-RS={float(Acl_e.subs(vals2)):.4f}, nodal={float(A_exact_full.subs(vals2)):.4f}")

header = [
    "HEADER: Razavi 12.47 (Fig. 12.110), shunt-shunt feedback, lambda>0",
    "R_S1 = (1/gm1)||rO1 (class); exact = (rO1+R_D1)/(1+gm1 rO1)",
    "R_in,open = R_S1 || (R_F + R_1||R_2);  R_out,open = rO2 || (R_1 + R_2||R_F)",
    "R_0 = -gm2 R_D1 [rO2||(R_1+R_2||R_F)] (R_F+R_1||R_2)/(R_F+R_1||R_2+R_S1)",
    "K = -R_2/(R_1R_2+R_1R_F+R_2R_F) (-> -1/R_F as R_1->0); K R_0 > 0",
    "A_cl = R_0/(1+K R_0); R_in,cl = R_in,open/(1+K R_0); R_out,cl = R_out,open/(1+K R_0)",
    "-" * 70,
]
print("\n".join(header + lines))
