"""P2 (2023-1 기말 Q3) 조정자 대조: 5T OTA + PMOS M1 출력단 전체 소신호 KCL(모든 r_o 유한, λ>0)을 SymPy로 풀고
explain-blind 결론·설명 조각·md 참고 풀이와 대조. g_m r_o≫1 근사는 비율이 1로 가는지 정확 유리수로 확인."""
import sympy as sp
g1,g3,g4,g5,g6,r1,r3,r4,r5,r6,RM,RL,vin,It = sp.symbols('g_m1 g_m3 g_m4 g_m5 g_m6 r_o1 r_o3 r_o4 r_o5 r_o6 R_M R_L v_in I_t', positive=True)
vT,vX,vY,vD,vF = sp.symbols('v_T v_X v_Y v_D v_F')

def solve(vin_val, gate4, laser=True):
    i3 = g3*(vin_val-vT) + (vX-vT)/r3          # M3 drain->source
    i4 = g4*(gate4-vT) + (vY-vT)/r4            # M4 drain->source
    i6 = g6*(-vY) + (-vY)/r6                   # M6 diode PMOS source->drain into Y
    i5 = g5*(-vY) + (-vX)/r5                   # M5 PMOS into X
    i1 = g1*(-vX) + (-vD)/r1                   # M1 PMOS into D
    eqs = [sp.Eq(i3+i4, 0), sp.Eq(i6, i4), sp.Eq(i5, i3)]
    if laser:
        eqs += [sp.Eq(i1, (vD-vF)/RL), sp.Eq(i1, vF/RM)]
    else:   # laser removed, test current It injected at D, extracted at F
        eqs += [sp.Eq(i1+It, 0), sp.Eq(vF/RM, -It)]
    return sp.solve(eqs, [vT,vX,vY,vD,vF], dict=True)[0]

par = lambda a,b: a*b/(a+b)
a1 = g3*par(r3,r5)
A_b = a1*g1*r1/(r1+RL+RM)                   # blind = fragment = md (A_OL)
T_b = RM*A_b
Acl_b = A_b/(1+T_b)
Routo_b = r1+RM
Routc_f = (r1+RM)*(1+a1*g1*r1*RM/(r1+RM))   # fragment: (r_o1+R_M)(1+T0)
Routc_md = r1+RM+g1*g3*par(r3,r5)*r1*RM
print('fragment R_out,closed - md:', sp.simplify(Routc_f - Routc_md))
print('fragment A_cl - md A_OL/(1+A_OL R_M):', sp.simplify(Acl_b - A_b/(1+A_b*RM)))

so = solve(vin, 0)                 # open loop: M4 gate AC 0, RM stays below laser
sc = solve(vin, vF)                # closed loop
sz = solve(0, 0, laser=False)      # open-loop R_out (laser view)
szc = solve(0, vF, laser=False)    # closed-loop R_out (laser view)
A_k = so[vF]/RM/vin; Acl_k = sc[vF]/RM/vin
Ro_k = (sz[vD]-sz[vF])/It; Rc_k = (szc[vD]-szc[vF])/It
print('R_out,open exact - (r_o1+R_M):', sp.simplify(Ro_k - Routo_b))
sym = {g4:g3, g5:g6}   # 대칭(M3=M4, M5=M6)
for k in [10, 100, 1000, 10000]:
    g = sp.Rational(1,1000)
    vals = {g1:g, g3:g, g6:g, r1:k/g, r3:k/g, r4:k/g, r5:k/g, r6:k/g, RM:500, RL:50}
    ev = lambda e: sp.nsimplify(e.subs(sym).subs(vals))
    print(f'g_m r_o={k}: A exact/approx={float(ev(A_k)/ev(A_b)):.6f}, A_cl exact/approx={float(ev(Acl_k)/ev(Acl_b)):.6f}, '
          f'R_out,closed exact/fragment={float(ev(Rc_k)/ev(Routc_f)):.6f}')
print('R_in,open = inf (M3 gate, no DC/AC gate current) by construction')
