import sympy as s

# Fig 10.18(a), one differential half. Ideal upper current source opens
# in AC; the tail symmetry plane is AC ground. Positive output current
# is into the amplifier at the collector.
gm, ro = s.symbols("g_m r_o", positive=True)
vin, vout, it = s.symbols("v_in v_out i_t")
open_solution = s.solve([gm * vin + vout / ro], [vout], dict=True)[0]
av = s.simplify(open_solution[vout] / vin)
test_solution = s.solve([it - vout / ro], [it], dict=True)[0]
rout = s.simplify(vout / test_solution[it])
short_current = gm * vin
Gm = s.simplify(short_current / vin)

assert s.simplify(av + Gm * rout) == 0
assert s.simplify(av + gm * ro) == 0
print("p1 model: matched BJT halves, pure differential input, ideal upper current sources, tail AC open")
print("Gm =", Gm)
print("Rout =", rout)
print("Av_differential =", av)
print("factor_of_two: vin1=vid/2 and vout1=vod/2, so vod/vid=vout1/vin1")
print("limit ro->infinity: |Av| diverges in this idealized low-frequency model")
