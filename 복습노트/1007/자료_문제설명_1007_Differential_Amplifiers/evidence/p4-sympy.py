# p4 (E10.27): A_CM-DM of bipolar pair with degenerated tail Q3 (rO3 finite), VA=inf for Q1,Q2
import sympy as sp
gm, rpi, gm3, rpi3, rO3, R1, RC, dRC, vcm = sp.symbols('g_m r_pi g_m3 r_pi3 r_O3 R_1 R_C DeltaR_C v_cm', positive=True)
beta, beta3 = sp.symbols('beta beta3', positive=True)

# 1) R_out3: test source vx at collector of Q3, base of Q3 at AC ground
vx, ix, ve = sp.symbols('v_x i_x v_e')
vbe3 = -ve
eqs = [sp.Eq(ix, gm3*vbe3 + (vx-ve)/rO3),          # KCL at collector
       sp.Eq(ix, ve/R1 + ve/rpi3)]                  # KCL at emitter (ix flows into R1||rpi3)
s = sp.solve(eqs, [ix, ve], dict=True)[0]
Rout3 = sp.simplify(vx/s[ix])
Rp = R1*rpi3/(R1+rpi3)
target_R = (1+gm3*Rp)*rO3 + Rp
print("Rout3 =", sp.factor(Rout3))
print("Rout3 - [(1+gm3(R1||rpi3))rO3 + R1||rpi3] =", sp.simplify(Rout3-target_R))

# 2) CM input, node P. Q1,Q2: vbe = vcm - vP, ic = gm vbe, ie = (gm+1/rpi) vbe
R3 = sp.Symbol('R_out3', positive=True)
vP, v1, v2 = sp.symbols('v_P v_out1 v_out2')
vbe = vcm - vP
sol = sp.solve([sp.Eq(2*(gm+1/rpi)*vbe, vP/R3),
                sp.Eq(v1, -gm*vbe*RC),
                sp.Eq(v2, -gm*vbe*(RC+dRC))], [vP, v1, v2], dict=True)[0]
A = sp.simplify((sol[v1]-sol[v2])/vcm)
print("A_CM-DM (finite beta, Vout1-Vout2) =", A)
A_inf = sp.limit(A.subs(rpi, beta/gm), beta, sp.oo)
print("limit beta->oo :", sp.simplify(A_inf))
target = dRC/(1/gm + 2*R3)
print("A(beta->oo) - dRC/(1/gm+2Rout3) =", sp.simplify(A_inf-target))
print("A_finite - gm*dRC/(1+2(gm+1/rpi)Rout3) =", sp.simplify(A - gm*dRC/(1+2*(gm+1/rpi)*R3)))
# approximation: large Rout3 -> dRC/(2Rout3)
print("limit Rout3->oo of A/(dRC/(2Rout3)) =", sp.limit(A_inf/(dRC/(2*R3)), R3, sp.oo))
print("Full: A =", sp.simplify(target.subs(R3, target_R)))
# md form drops the +R1||rpi3 term of Rout3 (Razavi approximation, rO3 >> R1||rpi3)
approx_R = (1+gm3*Rp)*rO3
print("limit rO3->oo of Rout3_exact/Rout3_md =", sp.simplify(sp.limit(Rout3/approx_R, rO3, sp.oo)))
A_md = dRC/(1/gm + 2*approx_R)
A_ex = target.subs(R3, target_R)
print("limit rO3->oo of A_exact/A_md =", sp.limit(A_ex/A_md, rO3, sp.oo))
