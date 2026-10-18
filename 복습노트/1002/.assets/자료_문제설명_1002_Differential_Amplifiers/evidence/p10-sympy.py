# p10 (P10.65, Fig 10.45(a)): R_EE split into two 2R_EE (one per side); CM half circuit = CE with R_C and degeneration 2R_EE.
import sympy as sp
gm, rpi, RC, REE, vcm = sp.symbols('g_m r_pi R_C R_EE v_CM', positive=True)
vE, vo, vP = sp.symbols('v_E v_o v_P')
# (i) half circuit: emitter node E with 2R_EE to gnd (I_EE ideal -> open)
ie = (gm+1/rpi)*(vcm-vE)
s = sp.solve([sp.Eq(ie, vE/(2*REE)), sp.Eq(vo, -RC*gm*(vcm-vE))],[vE,vo],dict=True)[0]
A_half = sp.simplify(s[vo]/vcm)
# (ii) original circuit: both emitters at P, R_EE to gnd
s2 = sp.solve([sp.Eq(2*(gm+1/rpi)*(vcm-vP), vP/REE), sp.Eq(vo, -RC*gm*(vcm-vP))],[vP,vo],dict=True)[0]
A_orig = sp.simplify(s2[vo]/vcm)
print('A_CM half circuit (2R_EE) =', A_half)
print('A_CM original (R_EE)      =', A_orig)
print('difference =', sp.simplify(A_half-A_orig))
eq10180 = -(RC/2)/(REE + 1/(2*gm))
print('limit r_pi->oo, A_half - Eq(10.180) =', sp.simplify(sp.limit(A_half,rpi,sp.oo) - eq10180))
# the two split halves have equal node voltages, so joining them (line of symmetry) carries no current:
print('half-circuit emitter voltage equals original v_P:', sp.simplify(s[vE]-s2[vP]))
