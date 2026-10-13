# P10.67 (Fig 10.88): CM gain of MOS diff pair, lambda=0 for M1,M2, lambda!=0 for M3
import sympy as sp
vin, vP, vX, vY, gm, RD, ro3 = sp.symbols('v_in v_P v_X v_Y g_m R_D r_o3', real=True)
ISS, lam, Vov = sp.symbols('I_SS lambda V_ov', positive=True)

# Full (not half) small-signal circuit, both gates driven by v_in (CM input)
id1 = gm*(vin - vP)          # M1 drain current (lambda=0)
id2 = gm*(vin - vP)          # M2 drain current (lambda=0)
eqs = [sp.Eq(id1 + id2, vP/ro3),   # KCL at tail node P (M3 = r_o3 to ground)
       sp.Eq(vX, -RD*id1),         # KCL at X
       sp.Eq(vY, -RD*id2)]         # KCL at Y
sol = sp.solve(eqs, [vP, vX, vY], dict=True)[0]
Acm = sp.simplify(sol[vX]/vin)
print("A_CM (gm, ro3) =", Acm)
target_half = -(RD/2)/(1/(2*gm) + ro3)
print("A_CM - [-(R_D/2)/(1/(2gm)+r_o3)] =", sp.simplify(Acm - target_half))
print("v_X - v_Y =", sp.simplify(sol[vX]-sol[vY]))

# Bias relations: I_D1 = I_SS/2, gm = 2 I_D/Vov = I_SS/Vov, r_o3 = 1/(lambda I_SS)
sub = {gm: ISS/Vov, ro3: 1/(lam*ISS)}
Acm_b = sp.simplify(Acm.subs(sub))
print("A_CM (bias) =", Acm_b)
target = -RD*ISS/(2/lam + Vov)
print("A_CM - (10.224) =", sp.simplify(Acm_b - target))

# Limits
print("lim lambda->0 A_CM =", sp.limit(Acm_b, lam, 0))
print("lim r_o3->oo A_CM =", sp.limit(Acm, ro3, sp.oo))
# Numeric sanity: RD=1k, ISS=1mA, lambda=0.1, Vov=0.2
num = {RD:1000, ISS:1e-3, lam:0.1, Vov:0.2}
print("numeric A_CM =", sp.N(Acm_b.subs(num)), " target =", sp.N(target.subs(num)))
