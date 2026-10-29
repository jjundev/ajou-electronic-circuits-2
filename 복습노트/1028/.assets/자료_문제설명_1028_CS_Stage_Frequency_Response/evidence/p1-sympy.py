# p1: omega_T = g_m/C_GS ; with C_GS=(2/3)WLCox, g_m=mu Cox (W/L) Vov -> omega_T = 3 mu Vov /(2 L^2)
# SymPy unavailable: stdlib random-point check.
import random, math
print("Definition: f_T = freq where |i_d/i_g| (drain AC-shorted) = 1; i_d=g_m v_gs, i_g = j w C_GS v_gs -> w_T=g_m/C_GS")
maxres=0
for _ in range(6):
    mu=random.uniform(0.01,0.1); Cox=random.uniform(1e-3,1e-2); W=random.uniform(1e-6,1e-4); L=random.uniform(5e-8,1e-6); Vov=random.uniform(0.05,0.5)
    gm=mu*Cox*W/L*Vov; Cgs=2/3*W*L*Cox
    wT=gm/Cgs
    # check |beta(j wT)| = gm/(wT Cgs) = 1
    beta=abs(gm/(1j*wT*Cgs))
    target=1.5*mu*Vov/L**2
    r=abs(wT-target)/target; maxres=max(maxres,r)
    print(f"wT={wT:.6e} target={target:.6e} |beta(wT)|={beta:.12f} relres={r:.2e}")
print("max relative residual", maxres)
