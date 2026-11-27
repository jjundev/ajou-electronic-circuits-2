from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import sympy as sp

wn, q, w, x = sp.symbols("omega_n Q omega x", positive=True)
den = (wn**2-w**2)**2 + (wn*w/q)**2
gain_sq = w**2/den
reciprocal = (wn**2/w-w)**2+(wn/q)**2
assert sp.factor(1/gain_sq - reciprocal) == 0
assert sp.factor(gain_sq.subs(w, wn) - q**2/wn**2) == 0
assert sp.factor(gain_sq.subs(w, x*wn)*wn**2 - 1/((1/x-x)**2+1/q**2)) == 0
print("For omega>0, (|H|/|beta|)^(-2) = (omega_n^2/omega-omega)^2 + (omega_n/Q)^2.")
print("The square is nonnegative and vanishes only at omega=omega_n, so the unique global peak is Q/omega_n.")
print("The response vanishes at DC and tends to zero at infinity.")
print("Plot coordinates are x=omega/omega_n and y=omega_n |H|/|beta|.")
print("Divide plotted ordinates by omega_n to recover |H|/|beta|.")
samples = np.linspace(0, 3, 3001)
fig, ax = plt.subplots(figsize=(7, 4.2), layout="constrained")
for quality in (2, 4, 8):
    response = samples/np.sqrt((1-samples**2)**2+(samples/quality)**2)
    peak_index = int(np.argmax(response))
    assert samples[peak_index] == 1 and response[peak_index] == quality
    print(f"Q={quality}: sampled peak x={samples[peak_index]:g}, y={response[peak_index]:g}")
    ax.plot(samples, response, lw=2, label=f"Q = {quality}")
ax.axvline(1, color="0.5", linestyle="--", linewidth=0.8)
ax.set(xlim=(0, 3), ylim=(0, 8.5), xlabel=r"$\omega/\omega_n$",
       ylabel=r"$\omega_n |H(j\omega)|/|\beta|$")
ax.legend()
ax.grid(alpha=0.25)
fig.savefig(Path(__file__).with_name("p6-response.png"), dpi=160)
