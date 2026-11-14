# p4 (X12.12) independent polarity check: R1 top terminal moved from vout (M2 drain) to n1 (M1 drain / M3 diode node).
# Method (textbook 12.5): input to zero, break loop at M2 gate (gate draws no current -> no loading change),
# apply V_test at M2 gate, follow loop, find V_ret = V_X, check sign of V_ret/V_test.
# Small-signal: all g_m, r_o (as conductances g_o=1/r_o), R1, R2 > 0; tail I_SS modeled as conductance gss>=0 (ideal: gss=0).
import sympy as sp

gm1, gm2, gm3, gm4 = sp.symbols('g_m1 g_m2 g_m3 g_m4', positive=True)
go1, go2, go3, go4 = sp.symbols('g_o1 g_o2 g_o3 g_o4', positive=True)   # 1/r_o
G1, G2 = sp.symbols('G1 G2', positive=True)                             # 1/R1, 1/R2
gss = sp.symbols('g_ss', nonnegative=True)                              # 1/R_SS of tail source
v1, vo, v2, vX, vt, vin = sp.symbols('v1 vo v2 vX vt vin')

def solve_circuit(R1_top, vin_val, vg2, unknowns):
    # NMOS drain->source currents
    iD1 = gm1*(vin_val - v2) + go1*(v1 - v2)
    iD2 = gm2*(vg2 - v2) + go2*(vo - v2)
    # PMOS source(VDD=0 ac)->drain currents; M3 diode: gate=drain=n1, M4 gate=n1
    i3 = gm3*(0 - v1) + go3*(0 - v1)
    i4 = gm4*(0 - v1) + go4*(0 - vo)
    top = {'n1': v1, 'vout': vo}[R1_top]
    iR1 = G1*(top - vX)            # current leaving 'top' through R1 into X
    eqs = [
        sp.Eq(i3, iD1 + (iR1 if R1_top == 'n1' else 0)),   # KCL n1
        sp.Eq(i4, iD2 + (iR1 if R1_top == 'vout' else 0)), # KCL vout
        sp.Eq(iD1 + iD2, gss*v2),                          # KCL tail n2
        sp.Eq(iR1, G2*vX),                                 # KCL X
    ]
    return sp.solve(eqs, unknowns, dict=True)[0]

def sign_report(name, expr):
    expr = sp.factor(sp.simplify(expr))
    num, den = sp.fraction(sp.together(expr))
    num, den = sp.expand(num), sp.expand(den)
    vars_ = [gm1, gm2, gm3, gm4, go1, go2, go3, go4, G1, G2, gss]
    pn = sp.Poly(num, *vars_); pd = sp.Poly(den, *vars_)
    sn = set(sp.sign(c) for c in pn.coeffs()); sd = set(sp.sign(c) for c in pd.coeffs())
    print(f'--- {name} ---')
    print('factored :', expr)
    print('num coeff signs:', sn, ' den coeff signs:', sd)
    if len(sn) == 1 and len(sd) == 1:
        s = list(sn)[0]*list(sd)[0]
        print('=> sign for all positive params:', '+' if s > 0 else '-')
    lim = sp.factor(sp.limit(expr, gss, 0))
    print('ideal tail (g_ss->0):', lim)
    lim2 = sp.factor(sp.limit(sp.limit(sp.limit(sp.limit(lim, go1, 0), go2, 0), go3, 0), go4, 0))
    print('also r_o->inf (all g_o->0):', lim2)
    return expr

# ---- Case A (the problem): R1 top at n1. Loop broken at M2 gate, vin = 0.
solA = solve_circuit('n1', 0, vt, [v1, vo, v2, vX])
LA = sign_report('Case A (R1 at n1): V_ret/V_test = vX/vt', solA[vX]/vt)
print('vn1/vt (A):', sp.factor(sp.limit(solA[v1]/vt, gss, 0)))

# ---- Sanity Case B (original Fig 12.28): R1 top at vout -> textbook-style negative feedback expected.
solB = solve_circuit('vout', 0, vt, [v1, vo, v2, vX])
LB = sign_report('Case B (R1 at vout, original): V_ret/V_test = vX/vt', solB[vX]/vt)

# ---- Closed-loop forward-tracing check for Case A: vin drives, X tied to M2 gate.
# Effect of vin up on n1: open-loop (X held at 0) vs closed loop; positive feedback => |closed| > |open| (same sign).
solA_open = solve_circuit('n1', vin, 0, [v1, vo, v2, vX])
solA_cl = solve_circuit('n1', vin, vX, [v1, vo, v2, vX])
ol = sp.factor(sp.limit(solA_open[v1]/vin, gss, 0))
cl = sp.factor(sp.limit(solA_cl[v1]/vin, gss, 0))
print('--- Case A forward trace (ideal tail) ---')
print('v_n1/vin open (X grounded):', ol)
print('v_n1/vin closed           :', cl)
print('vX/vin closed             :', sp.factor(sp.limit(solA_cl[vX]/vin, gss, 0)))
print('closed/open ratio (=1/(1-L)):', sp.factor(sp.simplify(cl/ol)))
print('check ratio - 1/(1-L_A) == 0:', sp.simplify(cl/ol - 1/(1 - sp.limit(LA, gss, 0))))
