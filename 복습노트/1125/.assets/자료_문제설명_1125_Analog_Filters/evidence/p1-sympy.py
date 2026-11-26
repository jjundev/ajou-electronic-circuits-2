"""P1 (2021-1 기말 Q4) 조정자 대조: SymPy 소신호 KCL 정확 해 ↔ explain-blind 결론 ↔ 설명 조각 ↔ md 참고 풀이.
λ=0, 몸체 효과 무시. M1 CG(소스=V_in, 게이트=V_F), M2 NMOS 소스 팔로워, 레이저 R_L, 감지 R_M."""
import sympy as sp
g1, g2, RD, RM, RL, vin, It = sp.symbols('g_m1 g_m2 R_D R_M R_L v_in I_t', positive=True)
vX, vS, vF = sp.symbols('v_X v_S2 v_F')

def solve(vin_val, laser=True, gate=None):
    vg = vF if gate is None else gate
    id1 = g1*(vg - vin_val)              # M1 drain->source
    id2 = g2*(vX - vS)                   # M2 source current toward laser
    eqs = [sp.Eq(-vX/RD, id1)]
    if laser:
        eqs += [sp.Eq(id2, (vS - vF)/RL), sp.Eq(id2, vF/RM)]
    else:                                # laser removed; test current It flows S2->F through the port
        eqs += [sp.Eq(id2, It), sp.Eq(It, vF/RM)]
    return sp.solve(eqs, [vX, vS, vF], dict=True)[0], id1

s, id1 = solve(vin)
Acl_kcl = sp.simplify((s[vF]/RM)/vin)
Rin_kcl = sp.simplify(vin/(-id1.subs(s)))
so, _ = solve(0, laser=False)
Rout_kcl = sp.simplify((so[vS] - so[vF])/(-It))   # 회로 쪽에서 본 두 단자 임피던스(크기)
# loop gain: M1 게이트에서 끊고 시험전압 1 인가, 돌아온 V_F
sl, _ = solve(0, gate=sp.Integer(1))
T_kcl = sp.simplify(-sl[vF])

# explain-blind 결론(독립 풀이)
T_b = g1*RD*RM/(1/g2+RL+RM)
Acl_b = g1*RD/(1/g2+RL+RM+g1*RD*RM)
Rin_b = (1/g1)*(1+T_b)
Rout_b = 1/g2+RM+g1*RD*RM
# 설명 조각 최종 답
T_f = g1*RD*RM/(1/g2+RL+RM)
Acl_f = g1*RD/(1/g2+RL+RM+g1*RD*RM)
Rin_f = (1+T_f)/g1
T0_f = g1*RD*RM/(1/g2+RM)
Rout_f = (1/g2+RM)*(1+T0_f)
# md 참고 풀이
Rout_md = 1/g2 + RM*(1+g1*RD)

for name, kcl, b, f in [('T', T_kcl, T_b, T_f), ('Iout/Vin', Acl_kcl, Acl_b, Acl_f),
                        ('R_in,closed', Rin_kcl, Rin_b, Rin_f), ('R_out,closed(laser view)', Rout_kcl, Rout_b, Rout_f)]:
    print(f'{name}: simplify(KCL-blind)={sp.simplify(kcl-b)}, simplify(blind-fragment)={sp.simplify(b-f)}')
print('R_out md - fragment:', sp.simplify(Rout_md - Rout_f))
mixed = (1/g2+RM)*(1+T_f)     # R_L 포함 T를 곱한 혼합형
print('혼합형 - 레이저에서 본 값 =', sp.factor(sp.simplify(mixed - Rout_f)), '(R_L->0에서만 0)')
print('레이저 포함 루프 전체 (1/g2+RL+RM)(1+T) - RL - fragment =', sp.simplify((1/g2+RL+RM)*(1+T_f) - RL - Rout_f))
