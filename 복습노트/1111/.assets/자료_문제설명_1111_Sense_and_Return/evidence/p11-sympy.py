# p11 (P12.16) independent solver-s3: NMOS cascode (M1 CS, M2 CG), output = I_out into M2 drain, lambda>0
import sympy as sp
gm1, gm2, gmb2, ro1, ro2 = sp.symbols('g_m1 g_m2 g_mb2 r_O1 r_O2', positive=True)
vin, vx, vd, it = sp.symbols('v_in v_x v_d i_t')
oo = sp.oo
id1 = gm1*vin + vx/ro1                       # M1: g=vin, d=vx, s=0
def id2(vd, vx): return gm2*(0-vx) - gmb2*vx + (vd-vx)/ro2   # M2: g=Vb(ac0), s=vx, body=gnd
# Gm: output shorted (vd=0)
sx = sp.solve(sp.Eq(id1, id2(0, vx)), vx)[0]
Gm = sp.simplify(id2(0, sx)/vin)
print("Gm exact (body effect kept) =", Gm)
print("Gm exact (gmb2=0)          =", sp.simplify(Gm.subs(gmb2, 0)))
print("Gm limit ro1->oo           =", sp.limit(Gm, ro1, oo))
print("Gm/g_m1 with ro1->oo, ro2 finite? ->", sp.simplify(sp.limit(Gm, ro1, oo)/gm1))
# Rout: vin=0, apply vd
sx = sp.solve(sp.Eq(vx/ro1, id2(vd, vx)), vx)[0]
Rout = sp.simplify(vd/id2(vd, sx))
print("Rout exact =", sp.expand(Rout))
print("Rout (gmb2=0) =", sp.expand(Rout.subs(gmb2, 0)))
print("ratio Rout/(g_m2 r_O1 r_O2) as g_m2*r_O->oo (gmb2=0, ro1=ro2=r, gm2*r=K):")
K, r = sp.symbols('K r', positive=True)
print("  ", sp.limit(sp.simplify(Rout.subs(gmb2,0).subs({ro1:r, ro2:r}).subs(gm2, K/r)/(K*r)), K, oo))
print("Rin = oo (MOS gate)")
# Norton check: Iout = Gm vin + vd/Rout
sx = sp.solve(sp.Eq(id1, id2(vd, vx)), vx)[0]
Iout = sp.simplify(id2(vd, sx))
print("Norton check Iout - (Gm vin + vd/Rout) =", sp.simplify(Iout - (Gm*vin + vd/Rout)))
