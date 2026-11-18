"""Qualitative test: series current sampling versus a parallel voltage tap."""
import sympy as sp

gm, K, Rout = sp.symbols('G_m K R_out', positive=True)
vx, ix, io, va = sp.symbols('v_test i_test i_out v_error')
# Delivered output current io points away from the amplifier. Test current enters it.
series_model = [io+ix, va+K*io, ix-vx/Rout+gm*va]
sol = sp.solve(series_model, (io, va, vx), dict=True)[0]
assert sp.simplify(sol[vx]/ix-Rout*(1+gm*K))==0
print("Fig. 12.45 attaches K to the output node as a tap.")
print("The branch does not put the current-sense port in series with the output test source.")
print("A common node specifies the same voltage but does not force the same branch current.")
print("With a series sensor, i_out=-i_test, v_error=-K*i_out.")
print("Illustration for ideal sampling and unilateral transconductance: v_test/i_test =", sp.factor(sol[vx]/ix))
print("This expression follows from the corrected series model, not the pictured tap.")
