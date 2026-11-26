"""P3 (예제 12.32) 조정자 대조: explain-blind 두 포트 결론 ↔ 설명 조각 ↔ md 참고 풀이(식 12.166–12.173), 그리고 SymPy KCL 정확 해와의 근사 차이."""
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p3_common import *
# explain-blind 결론
b = dict(A=A_open, Rin=par(1/g1, RF+RM), Ro=Ro, K=K, Acl=A_open/(1+T), Rinc=par(1/g1,RF+RM)/(1+T), Routc=Ro*(1+T))
# 설명 조각
f = dict(A=(RF+RM)*RD/(RF+RM+1/g1)*(-g2*r2)/(r2+RL+par(RM,RF)), Rin=par(1/g1,RF+RM), Ro=r2+par(RF,RM), K=-RM/(RM+RF),
         Acl=A_open/(1-RM/(RM+RF)*A_open), Rinc=par(1/g1,RF+RM)/(1+T),
         Routc=Ro*(1+T0))
Routc_f_expanded = r2+par(RF,RM)+g2*r2*RD*RM/(RF+RM+1/g1)
print('fragment R_out,closed 전개형 일치:', sp.simplify(f['Routc']-Routc_f_expanded))
print('fragment T 전개형 일치:', sp.simplify(T - RM/(RF+RM+1/g1)*g2*r2*RD/(r2+RL+par(RM,RF))))
for k in ['A','Rin','Ro','K','Acl','Rinc']:
    print(f'{k}: simplify(blind - fragment) =', sp.simplify(b[k]-f[k]))
md_Routc = Ro*(1-RM/(RM+RF)*A_open)
print('md(식 12.173) - blind R_out,closed:', sp.simplify(md_Routc - b['Routc']))
ratio = sp.simplify(f['Routc']/b['Routc'])
print('fragment R_out,closed / 교과서(blind) 식: R_L->0 극한 =', sp.simplify(sp.limit(ratio, RL, 0)))
print('같은 비: R_L/(r_O2+R_F||R_M)->0 이면 1, 예) r_O2->oo 극한 =', sp.simplify(sp.limit(ratio, r2, sp.oo)))
# 정확 KCL 대비(두 포트 근사의 R_F 순방향 전달 무시): g_m r_O2 증가 시 비 -> 1
s, i2 = kcl(Iin)
Acl_k = i2/Iin
sz, _ = kcl(0, laser=False)
Rc_k = (sz[vD]-sz[vP])/It
for k in [10, 100, 1000, 10000]:
    g = sp.Rational(1,1000)
    vals = {g1:g, g2:g, r2:k/g, RD:2*k, RF:2*k, RM:500, RL:50}
    ev = lambda e: sp.nsimplify(e.subs(vals))
    print(f'g_m r_O2={k}: A_I,closed exact/2port={float(ev(Acl_k)/ev(b["Acl"])):.6f}, R_out exact/fragment={float(ev(Rc_k)/ev(f["Routc"])):.6f}, R_out exact/textbook={float(ev(Rc_k)/ev(b["Routc"])):.6f}')
