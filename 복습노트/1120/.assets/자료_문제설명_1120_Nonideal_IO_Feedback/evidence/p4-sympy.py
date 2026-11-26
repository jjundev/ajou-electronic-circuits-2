"""Independent nodal analysis of Figure 12.105. Currents enter each port."""
import sympy as sp

r1, r2, rc, rp, beta = sp.symbols("R1 R2 RC rpi beta", positive=True)
ve, vb, vo, ix = sp.symbols("ve vb vo ix")
gm = beta / rp
total = r1 + r2
f = r2 / total
p = r1 * r2 / total
load = rc * total / (rc + total)

base_kcl = (vb-vo)/r1 + vb/r2 + (vb-ve)/rp
collector_kcl = vo/rc + (vo-vb)/r1 + gm*(vb-ve) - ix
emitter_current = (ve-vb)*(1/rp+gm)
solution = sp.solve([base_kcl, collector_kcl], [vb, vo])
gain = solution[vo].subs(ix, 0) / ve
rin = ve / emitter_current.subs(solution).subs(ix, 0)
rout = solution[vo].subs(ve, 0) / ix

g = (beta+f)/(rp+p)
g_forward = beta/(rp+p)
loop = f*load*g
vbase_open = sp.solve(vb/p + (vb-ve)/rp, vb)[0]
isc_into = gm*(vbase_open-ve)
open_rin = ve / emitter_current.subs(vb, vbase_open)
open_rout = vo / (vo/rc + vo/total + gm*(vbase_open-ve).subs(ve,0))

checks = {
    "exact closed Av": (gain, load*g/(1+loop)),
    "exact closed Rin": (rin, (rp+p)*(1+loop)/(beta+1)),
    "exact closed Rout": (rout, load/(1+loop)),
    "split Gm into short": (isc_into/ve, -g_forward),
    "split Rin": (open_rin, (rp+p)/(beta+1)),
    "split Rout": (open_rout, load),
    "finite-beta correction from divider": (g/g_forward-1, f/beta),
}
for name, (nodal, compact) in checks.items():
    assert sp.cancel(nodal-compact) == 0, name
    print(name, "OK  ", sp.factor(nodal))
print("Set S=R1+R2, F=R2/S, P=R1||R2, L=RC||S.")
print("Exact G=(beta+F)/(rpi+P), T=F L G.")
print("Av=L G/(1+T), Rin=(rpi+P)(1+T)/(beta+1), Rout=L/(1+T).")
print("Large beta: use G0=beta/(rpi+P), T0=F L G0 instead of G,T.")
print("The relative excess of exact G over G0 is F/beta.")
