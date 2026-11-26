"""P5 (예제 12.33) 조정자 대조: V-C 귀환 두 포트 결과 — explain-blind ↔ 설명 조각 ↔ md 참고 풀이(식 12.174–12.183), SymPy KCL 정확 해와의 근사 비."""
import sympy as sp
g1,g2,RD,RF,RM,r2,Iin,It = sp.symbols('g_m1 g_m2 R_D R_F R_M r_O2 I_in I_t', positive=True)
vN,vX,vP = sp.symbols('v_N v_X v_P')
par3 = lambda a,b,c: 1/(1/a+1/b+1/c)
Rp = par3(r2,RM,RF)
# blind
RO_b = -g2*RD*RF*Rp/(RF+1/g1); Rin_b = 1/(g1+1/RF); Ro_b = Rp; K_b = -1/RF; T_b = K_b*RO_b
# fragment
RO_f = -(g2*RD*RF)/(RF+1/g1)*Rp; Rin_f = 1/(g1+1/RF); Ro_f = Rp; K_f = -1/RF
T_f = g2*RD*Rp/(RF+1/g1)
for n,(b,f) in dict(R_O=(RO_b,RO_f), R_in=(Rin_b,Rin_f), R_out=(Ro_b,Ro_f), K=(K_b,K_f), T=(T_b,T_f)).items():
    print(f'{n}: simplify(blind - fragment) =', sp.simplify(b-f))
# md (식 12.181–12.183): /(1 - R_O/R_F)
for n,(md,f) in dict(R_O_closed=(RO_b/(1-RO_b/RF), RO_f/(1+T_f)), R_in_closed=(Rin_b/(1-RO_b/RF), Rin_f/(1+T_f)),
                     R_out_closed=(Ro_b/(1-RO_b/RF), Ro_f/(1+T_f))).items():
    print(f'{n}: simplify(md - fragment) =', sp.simplify(md-f))
print('T>>1 극한 R_O,closed -> 1/K:', sp.limit(RO_f/(1+T_f), g2, sp.oo).simplify())
# 정확 KCL
def kcl(Iv, test=False):
    i1 = g1*(0-vN); i2 = g2*(0-vX) + (0-vP)/r2
    eqs = [sp.Eq(Iv + i1 - (vN-vP)/RF, 0), sp.Eq(-vX/RD, i1),
           sp.Eq(i2 + (vN-vP)/RF + (It if test else 0), vP/RM)]
    return sp.solve(eqs, [vN,vX,vP], dict=True)[0]
s = kcl(Iin); RO_k = s[vP]/Iin; Rin_k = s[vN]/Iin
st = kcl(0, test=True); Rout_k = st[vP]/It
for k in [sp.Rational(64,100), 64, 6400, 640000]:
    vals = {g1:sp.Rational(1,100), g2:sp.Rational(1,100), RD:100*sp.sqrt(k), RF:100*sp.sqrt(k), RM:1000, r2:10**6}
    ev = lambda e: sp.N(e.subs(vals))
    print(f'g_m1 g_m2 R_D R_F={k}: R_O,cl exact/2port={ev(RO_k/(RO_f/(1+T_f))):.6f}, R_in exact/2port={ev(Rin_k/(Rin_f/(1+T_f))):.6f}, R_out exact/2port={ev(Rout_k/(Ro_f/(1+T_f))):.6f}')
