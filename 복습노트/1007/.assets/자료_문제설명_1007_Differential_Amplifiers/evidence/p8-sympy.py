# p8 (2023-1_중간-Q4) 독립 검산: 부하 불일치 MOS 차동쌍, 꼬리 전류원 M3
import sympy as sp

# ---------- 주어진 값 ----------
VDD = sp.Rational(18, 10); ID3 = sp.Rational(1, 1000)
RD = 1000; dRD = 20
WL12 = 1000; WL3 = 2000            # 200/0.2, 400/0.2
VTH = sp.Rational(4, 10); unCox = sp.Rational(100, 10**6); lam = sp.Rational(1, 10)

# ---------- 바이어스 (λ는 소신호 r_o에만 반영, 대신호 바이어스는 제곱법칙) ----------
ID1 = ID3 / 2
Vov = sp.symbols('Vov', positive=True)
Vov1 = sp.solve(sp.Eq(ID1, sp.Rational(1, 2)*unCox*WL12*Vov**2), Vov)[0]
Vov3 = sp.solve(sp.Eq(ID3, sp.Rational(1, 2)*unCox*WL3*Vov**2), Vov)[0]
VGS1 = VTH + Vov1
print("Vov1 =", Vov1, "V, Vov3 =", Vov3, "V, VGS1 =", VGS1, "V")

# ---------- (1) 입력 CM 범위 ----------
# 최소: M3 포화 V_P >= Vov3  ->  V_CM >= VGS1 + Vov3
VCM_min = VGS1 + Vov3
# 최대: M1, M2 포화 V_D >= V_CM - VTH, 낮은 쪽 드레인(R_D+ΔR_D 쪽)이 제한
VD1 = VDD - ID1*RD
VD2 = VDD - ID1*(RD + dRD)
VCM_max = sp.Min(VD1, VD2) + VTH
print("(1) VD1 =", VD1, "V, VD2 =", VD2, "V")
print("(1) VCM,min =", VCM_min, "V =", float(VCM_min))
print("(1) VCM,max =", VCM_max, "V =", float(VCM_max),
      " (ΔR_D 무시 시", VD1 + VTH, "V)")

# ---------- 소신호 파라미터 ----------
gm_v = 2*ID1/Vov1
ro3_v = 1/(lam*ID3)
ro1_v = 1/(lam*ID1)
print("gm1,2 =", gm_v, "S, ro3 =", ro3_v, "ohm, ro1,2 =", ro1_v, "ohm")

# ---------- (2) CM 입력 소신호 KCL (r_o1,2 포함 일반식) ----------
gm, R1, R2, ro, rss, vcm = sp.symbols('g_m R_1 R_2 r_o R_SS v_cm', positive=True)
vp, vo1, vo2 = sp.symbols('v_P v_o1 v_o2')
i1 = gm*(vcm - vp) + (vo1 - vp)/ro
i2 = gm*(vcm - vp) + (vo2 - vp)/ro
sol = sp.solve([sp.Eq(-vo1/R1, i1), sp.Eq(-vo2/R2, i2), sp.Eq(i1 + i2, vp/rss)],
               [vp, vo1, vo2], dict=True)[0]
A1 = sp.simplify(sol[vo1]/vcm); A2 = sp.simplify(sol[vo2]/vcm)
# r_o1,2 -> ∞ (g_m r_o >> 1)
A1i = sp.simplify(sp.limit(A1, ro, sp.oo)); A2i = sp.simplify(sp.limit(A2, ro, sp.oo))
print("A1(ro->oo) =", A1i, "; A2(ro->oo) =", A2i)
print("check A1 - [-R1/(1/gm+2Rss)] =", sp.simplify(A1i - (-R1/(1/gm + 2*rss))))
ACMDM = sp.simplify(A1i - A2i)   # (vo1 - vo2)/vcm
ACMDM_target = (R2 - R1)/(1/gm + 2*rss)
print("check A_CM-DM - (R2-R1)/(1/gm+2Rss) =", sp.simplify(ACMDM - ACMDM_target))
# 단일 출력 기준 A_CM (Razavi: 불일치 무시, -(R_D/2)/(1/(2gm)+R_SS))
ACM_target = -(R1/2)/(1/(2*gm) + rss)
print("check A1 - [-(RD/2)/(1/(2gm)+Rss)] =", sp.simplify(A1i - ACM_target))

subs = {gm: gm_v, R1: RD, R2: RD + dRD, rss: ro3_v}
print("(2) A_CM (vout1, R_D 쪽) =", A1i.subs(subs), "=", float(A1i.subs(subs)))
print("(2) A_CM (vout2, R_D+ΔR_D 쪽) =", A2i.subs(subs), "=", float(A2i.subs(subs)))
print("(2) A_CM-DM = (vo1-vo2)/vcm =", ACMDM.subs(subs), "=", float(ACMDM.subs(subs)))
# r_o1,2 포함 시 영향 (참고)
subs_ro = dict(subs); subs_ro[ro] = ro1_v
print("   [참고 ro1,2=20k 포함] A_CM1 =", float(A1.subs(subs_ro)),
      ", A_CM-DM =", float((A1 - A2).subs(subs_ro)))

# ---------- (3) CMRR ----------
# 차동 이득 (불일치 무시 gm*RD, 또는 평균 부하 gm*(RD+ΔRD/2)), ro1,2 -> ∞
vd = sp.symbols('v_d')
s2 = sp.solve([sp.Eq(-vo1/R1, gm*(vd/2 - vp)), sp.Eq(-vo2/R2, gm*(-vd/2 - vp)),
               sp.Eq(gm*(vd/2 - vp) + gm*(-vd/2 - vp), vp/rss)], [vp, vo1, vo2], dict=True)[0]
ADM = sp.simplify((s2[vo1] - s2[vo2])/vd)
print("A_DM (exact, ro1,2->oo) =", ADM, "=", float(ADM.subs(subs)))
CMRR_exact = sp.simplify(sp.Abs(ADM/ACMDM))
CMRR_razavi = gm*R1*(1/gm + 2*rss)/(R2 - R1)    # = (1+2 gm Rss) RD/ΔRD
print("(3) CMRR (A_DM=gmRD) =", CMRR_razavi.subs(subs), "=", float(CMRR_razavi.subs(subs)),
      "->", float(20*sp.log(CMRR_razavi.subs(subs), 10)), "dB")
print("(3) CMRR (A_DM 정확) =", float(CMRR_exact.subs(subs)),
      "->", float(20*sp.log(CMRR_exact.subs(subs), 10)), "dB")
print("check CMRR_razavi - (1+2gmRss)RD/ΔRD =",
      sp.simplify(CMRR_razavi - (1 + 2*gm*rss)*R1/(R2 - R1)))

# ---------- (3) 보충: r_o1,2 처리 일관성 비교 ----------
s3 = sp.solve([sp.Eq(-vo1/R1, gm*(vd/2 - vp) + (vo1 - vp)/ro),
               sp.Eq(-vo2/R2, gm*(-vd/2 - vp) + (vo2 - vp)/ro),
               sp.Eq(gm*(vd/2 - vp) + (vo1 - vp)/ro + gm*(-vd/2 - vp) + (vo2 - vp)/ro, vp/rss)],
              [vp, vo1, vo2], dict=True)[0]
ADM_ro = (s3[vo1] - s3[vo2])/vd
ACMDM_ro = A1 - A2
ADM_ro_n = abs(float(ADM_ro.subs(subs_ro))); ACMDM_ro_n = abs(float(ACMDM_ro.subs(subs_ro)))
print("[r_o1,2 양쪽 모두 포함] |A_DM| =", ADM_ro_n, ", |A_CM-DM| =", ACMDM_ro_n,
      ", CMRR =", ADM_ro_n/ACMDM_ro_n, "->", 20*float(sp.log(ADM_ro_n/ACMDM_ro_n, 10)), "dB")
gRpar = float(gm_v*RD*ro1_v/(RD + ro1_v))
mixed = gRpar/float(ACMDM.subs(subs))
print("[혼합: A_DM에만 r_o1 포함, A_CM-DM은 r_o1 무시] gm(RD||ro1) =", gRpar,
      ", CMRR =", mixed, "->", 20*float(sp.log(mixed, 10)), "dB")
