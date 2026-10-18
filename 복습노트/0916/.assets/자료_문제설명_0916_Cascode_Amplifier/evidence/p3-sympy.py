# P3 (P9.23): input at base of Q2 (top), Q1 (bottom, base Vb1 AC ground) -> r_O1, ideal current-source load.
import sympy as sp
gm, rpi, ro1, ro2, vin, x, i, vout, beta = sp.symbols('g_m r_pi r_O1 r_O2 v_in v_x i v_out beta', positive=True)
# (b) short-circuit Gm: vout=0, i = current into Q2 collector from output node
eqs = [sp.Eq(i, gm*(vin-x) + (0-x)/ro2), sp.Eq(i + (vin-x)/rpi, x/ro1)]
s = sp.solve(eqs, [i, x], dict=True)[0]
Gm = sp.simplify(s[i]/vin)
print('Gm exact =', sp.factor(Gm))
# open-circuit gain (ideal current source => collector current = 0)
eqs2 = [sp.Eq(0, gm*(vin-x) + (vout-x)/ro2), sp.Eq((vin-x)/rpi, x/ro1)]
s2 = sp.solve(eqs2, [vout, x], dict=True)[0]
Av = sp.simplify(s2[vout]/vin)
print('Av exact =', sp.factor(Av))
rp = ro1*rpi/(ro1+rpi)
Rout = (1+gm*rp)*ro2 + rp
print('check Av + Gm*Rout =', sp.simplify(Av + Gm*Rout))
# gm rO >> 1 with beta fixed (rpi = beta/gm)
Gm_b = Gm.subs(rpi, beta/gm)
print('Gm * rO1 as gm->oo (beta fixed) ->', sp.simplify(sp.limit(Gm_b*ro1, gm, sp.oo)), '  => Gm ~ beta/((beta+1) rO1) ~ 1/rO1 (for rO1~rO2, beta>>1)')
Gm_t = 1/ro1 + 1/(beta*ro1)
Avt = -gm*ro2*rpi/(rpi+ro1)
print('Av / [-gm rO2 rpi/(rpi+rO1)] as gm->oo:', sp.limit(sp.simplify((Av/Avt).subs(rpi, beta/gm)), gm, sp.oo))
print('-gm rO2 rpi/(rpi+rO1) == -beta rO2/(rpi+rO1):', sp.simplify(Avt.subs(rpi, beta/gm) + beta*ro2/(beta/gm+ro1)))
print('Gm_approx*Rout_approx check: -Gm*gm rO2 (rO1||rpi) with Gm=1/rO1 ->', sp.simplify(-(1/ro1)*gm*ro2*rp), ' (same as Avt:', sp.simplify(-(1/ro1)*gm*ro2*rp - Avt), ')')
print('rpi -> oo (no base current): Av ->', sp.limit(Av, rpi, sp.oo), '  (single-CE level, not gm^2 rO^2)')
print('rO1 >> rpi: Av ~ -beta rO2/rO1 ; with rO1=rO2: ~ -beta')
VA, VT, Ic = sp.symbols('V_A V_T I_C', positive=True)
same = Avt.subs({rpi: beta*VT/Ic, ro1: VA/Ic, ro2: VA/Ic, gm: Ic/VT})
print('same-current form: simplify(Avt + beta VA/(VA+beta VT)) =', sp.simplify(same + beta*VA/(VA+beta*VT)))
print('beta->oo (rpi->oo) exact Gm - gm/(1+gm rO1 + rO1/rO2) =', sp.simplify(sp.limit(Gm, rpi, sp.oo) - gm/(1+gm*ro1+ro1/ro2)))
