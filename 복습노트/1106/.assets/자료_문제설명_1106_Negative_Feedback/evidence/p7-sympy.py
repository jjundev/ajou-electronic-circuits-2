# p7 (P12.4) verify-B: loop gains of Fig 12.80(a)-(d)
# Convention: X=0, break between A1 output (N) and feedback input (M); inject V_t at M,
# returned signal V_r at A1 output; T = -V_r/V_t (T>0 => negative feedback). lambda=0.
import sympy as sp
A1,K,R1,R2,RD,gm3,gm1,gmb1,Vt=sp.symbols('A1 K R1 R2 R_D g_m3 g_m1 g_mb1 V_t',positive=True)
vn1,vn2,vs,vd=sp.symbols('v_n1 v_n2 v_s v_d')
res={}
# (a) Vt at Y-node: n1=Vt R2/(R1+R2); minus input = K*n1; Vr = A1*(0 - K n1)
n1=Vt*R2/(R1+R2); Vr=A1*(0-K*n1); res['a']=sp.simplify(-Vr/Vt)
# (b) Vt at Y: n1 divider -> M3 gate; drain n2 = -gm3 RD n1 -> + input; X(-input)=0
n1=Vt*R2/(R1+R2); n2=sp.solve(sp.Eq((0-vn2)/RD, gm3*n1),vn2)[0]; Vr=A1*(n2-0); res['b']=sp.simplify(-Vr/Vt)
# (c) Vt at M3 gate; n1 = -gm3 RD Vt -> + input
n1=sp.solve(sp.Eq((0-vn1)/RD, gm3*Vt),vn1)[0]; Vr=A1*n1; res['c']=sp.simplify(-Vr/Vt)
# (d) Vt at M1 gate; source follower into R2 (KCL at source, body effect kept, then gmb->0)
vy=sp.solve(sp.Eq(gm1*(Vt-vs)-gmb1*vs, vs/R2),vs)[0]; Vr=A1*(0-vy); Td=sp.simplify(-Vr/Vt)
res['d_body']=Td; res['d']=sp.simplify(Td.subs(gmb1,0))
for k,v in res.items(): print("T(%s) ="%k, v)
print("All T>0: negative feedback in (a)-(d).")
print("(d) with body effect: T = A1 gm1 R2/(1+(gm1+gmb1)R2); textbook-level answer ignores gmb.")
