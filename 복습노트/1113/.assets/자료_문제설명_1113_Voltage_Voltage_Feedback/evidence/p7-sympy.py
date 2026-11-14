# p7 (E12.14) 독립 검산: Fig 12.30 귀환 극성
# 절차: (a) 입력 I_in = 0 (이상 전류원 -> 개방) (b) M2 게이트에서 루프 절단
#       (c) M2 게이트에 V_test 인가, 루프를 따라 M1 드레인(V_out)에서 V_ret 계산, V_ret/V_test 부호 판정
# 소신호 모델: M1, M2 포화 NMOS, 소스 접지, 게이트 전류 0. i_d = g_m v_gs + v_ds/r_o (드레인->소스 방향)
import sympy as sp

gm1, gm2, ro1, ro2, RD = sp.symbols('g_m1 g_m2 r_o1 r_o2 R_D1', positive=True)
Vt, Vx, Vr, Iin = sp.symbols('V_test V_X V_ret I_in')

print("=== 1) 루프 절단: V_test -> M2 gate, V_ret = M1 drain(V_out), I_in = 0 ===")
# KCL @ X: I_in 유입(=0) = M2 드레인 전류(X->접지) ; M1 게이트 전류 0
kclX = sp.Eq(0, gm2*Vt + Vx/ro2)
# KCL @ Vout(M1 drain): RD1 로 들어오는 전류 (0 - Vr)/RD (소신호 VDD=0) = M1 드레인 전류
kclO = sp.Eq((0 - Vr)/RD, gm1*Vx + Vr/ro1)
sol = sp.solve([kclX, kclO], [Vx, Vr], dict=True)[0]
Vx_s = sp.simplify(sol[Vx]); Vr_s = sp.simplify(sol[Vr])
LG = sp.simplify(Vr_s/Vt)
print("V_X/V_test   =", sp.simplify(Vx_s/Vt))
print("V_ret/V_test =", sp.factor(LG))
print("V_ret/V_test is positive (all g_m, r_o, R>0):", sp.ask(sp.Q.positive(LG)) , "| sign:", sp.sign(LG))
LG_inf = sp.limit(sp.limit(LG, ro1, sp.oo), ro2, sp.oo)
print("limit r_o1->oo then r_o2->oo:", LG_inf, " (ro2=oo 이면 X 노드가 이상 전류원만으로 구동되어 루프 이득 무한대 - 부호는 +)")
LG_ro1 = sp.limit(LG, ro1, sp.oo)
print("limit r_o1->oo:", sp.simplify(LG_ro1))

print()
print("=== 2) 닫힌 루프 교차 확인: I_in -> V_X, V_out 전체 응답 ===")
Vo = sp.symbols('V_out')
kX = sp.Eq(Iin, gm2*Vo + Vx/ro2)            # I_in 이 X 로 유입 = M2 드레인 전류
kO = sp.Eq(-Vo/RD, gm1*Vx + Vo/ro1)
s2 = sp.solve([kX, kO], [Vx, Vo], dict=True)[0]
A = sp.simplify(s2[Vx]/Iin)
A0 = ro2                                    # 귀환 없을 때(gm2 -> 0) 트랜스임피던스
print("V_X/I_in (closed) =", sp.factor(A))
print("open-loop (g_m2=0):", sp.simplify(A.subs(gm2, 0)))
# 부귀환이면 A = A0/(1+LG), 정귀환이면 A = A0/(1-LG)
print("A - A0/(1-LG) =", sp.simplify(A - A0/(1 - LG)))
print("A - A0/(1+LG) == 0 ?", sp.simplify(A - A0/(1 + LG)) == 0)

print()
print("=== 3) 정성 경로 (부호 연쇄) ===")
chain = [
 ("I_in 증가", "X 노드 전압 V_X 증가 (+)"),
 ("V_X 증가 -> M1 게이트", "CS 반전: V_out 감소 (-)"),
 ("V_out 감소 -> M2 게이트", "M2 드레인 전류(X에서 접지로 끌어내는 전류) 감소 (-)"),
 ("M2가 X에서 덜 끌어냄", "V_X 추가 증가 (+) : 원래 효과를 강화"),
]
for a,b in chain: print(f"  {a:28s} => {b}")
print("부호 곱: CS 반전(-) x M2 트랜스컨덕턴스가 X에서 전류를 빼는 방향(-) = (+) -> 정귀환")
print()
print("VERDICT: Fig 12.30 = POSITIVE feedback (정귀환), V_ret/V_test = +g_m1 g_m2 r_o2 (R_D1||r_o1) > 0")
