"""Independent p6(1) calculation from original Fig Q2 and 15dd74db profile.

No source reference answer or author explanation is used here.
The exact hybrid-pi result is internal verification only; the displayed course
model is the explicit 1/gm large-beta block from CIRCUIT-01.
"""
import sympy as sp

gm, RP, beta, ron, rop = sp.symbols('g_m R_P beta r_on r_op', positive=True)
vt, vb = sp.symbols('v_t v_b')
rpi = beta/gm
parallel = lambda *xs: sp.simplify(1/sum(1/x for x in xs))

# Q3 is pnp with E at AC ground, C at output x, B connected via RP to C.
# Base and collector KCL provide an independent model check of the known block.
base_kcl = (vb-vt)/RP + vb/rpi
base_solution = sp.solve(base_kcl, vb)[0]
it = vt/rop + (vt-base_solution)/RP + gm*base_solution
R_Q3_exact = sp.simplify(vt/it)
R_Q3_known = parallel(rop, (RP+rpi)/(beta+1))
print('Q3 full hybrid-pi minus corrected known block:', sp.simplify(R_Q3_exact-R_Q3_known))

# Required displayed model: explicit 1/gm and RP/beta, with rop retained.
R_base = 1/gm + RP/beta
R_Q3_default = parallel(rop,R_base)
Rout_half = parallel(ron,R_Q3_default)
Rout_diff = 2*Rout_half
Gm = gm
Av = -Gm*Rout_half

values = {gm:sp.Rational(1,52), RP:sp.Integer(10000), beta:sp.Integer(100),
          ron:sp.Integer(20000), rop:sp.Integer(20000)}
print('conditions: low frequency, Q3 active, E/VCC AC ground, beta=100 treated as large-beta course model')
print('gmro3=',sp.simplify((gm*rop).subs(values)),'; beta=',values[beta])
for label, expr in [('1/gm',1/gm),('RP/beta',RP/beta),('R_base',R_base),
                    ('R_Q3_default',R_Q3_default),('Rout_half',Rout_half),
                    ('Rout_diff',Rout_diff),('Gm',Gm),('Av',Av)]:
    value = sp.simplify(expr.subs(values))
    print(label,'=',value,'≈',sp.N(value,16))

# Internal comparison only. The reference-like finite-beta block is not the
# default displayed formula under this profile snapshot.
Rout_half_corr = parallel(ron,R_Q3_known)
Av_corr = -gm*Rout_half_corr
print('internal corrected Rout_half=',sp.simplify(Rout_half_corr.subs(values)),
      '≈',sp.N(Rout_half_corr.subs(values),16))
print('internal corrected Av=',sp.simplify(Av_corr.subs(values)),
      '≈',sp.N(Av_corr.subs(values),16))
print('base corrected/default ratio=',sp.simplify(((RP+rpi)/(beta+1))/R_base))
print('limit beta->infinity base ratio=',sp.limit(((RP+rpi)/(beta+1))/R_base,beta,sp.oo))
print('limit beta->infinity complete Rout ratio=',sp.limit(Rout_half_corr/Rout_half,beta,sp.oo))
print('limit beta->infinity complete Av ratio=',sp.limit(Av_corr/Av,beta,sp.oo))
